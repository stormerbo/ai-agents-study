import type { NextRequest } from 'next/server';

import { isModelAllowed, resolveProvider } from '@/lib/llm/registry';
import { encodeSSE, encodeSSEComment } from '@/lib/llm/sse';
import {
  UpstreamError,
  type AgentMessage,
  type ChatParams,
  type ToolSpec,
} from '@/lib/llm/types';

/**
 * BYOK 中转端点 —— 本站唯一的运行时后端逻辑。
 *
 * ## 安全模型
 *
 * 用户自带 Key（BYOK）。Key 通过**请求头**传入而不是请求体：请求体更容易被
 * 中间层、网关或错误日志记录下来。Key 在这个文件里只被读取一次、直接透传给
 * 上游，**不写库、不写日志、不回显**。
 *
 * 风险模型要说清楚：BYOK 模式下攻击者带的是**自己的** Key，本站不替他付费。
 * 真正的风险是「本站被当成免费代理」—— 用我们的域名与带宽绕过他自己网络的
 * 出站限制。所以拦截手段是**白名单**（provider + model 都必须在注册表里），
 * 而不是密钥校验。
 *
 * ## 错误的两阶段契约
 *
 * - **首字节之前**（校验失败、缺 Key、模型不在白名单）→ 返回**真实 HTTP 状态码**
 *   + JSON body。客户端能明确区分「配置错了」和「生成中断了」。
 * - **首字节之后**（上游报错、超时、连接断）→ HTTP 已经是 200，改发 `event: error`。
 *
 * 这个契约很重要：如果统一用 200 + error 帧，客户端就无法区分"你的 Key 错了"
 * 和"生成到一半断了"——前者要改配置，后者重试即可。
 */

export const runtime = 'nodejs';
// 防止被静态化 —— 这个路由必须是动态的
export const dynamic = 'force-dynamic';
// 构建期产物，Vercel 读取；自托管时下方代码里的超时兜底才是唯一保护
export const maxDuration = 120;

// ---------------------------------------------------------------------------
// 限制
// ---------------------------------------------------------------------------

const MAX_BODY_BYTES = 256 * 1024;
const MAX_TOKENS_CEILING = 4096;
const MAX_MESSAGES = 100;
const UPSTREAM_TIMEOUT_MS = 110_000;
/** 心跳间隔：防中间代理在长时间无数据时掐断连接 */
const HEARTBEAT_MS = 15_000;
const MAX_OUTPUT_TOKENS = Number(process.env.MAX_OUTPUT_TOKENS_CEILING ?? MAX_TOKENS_CEILING);

// ---------------------------------------------------------------------------
// 请求体校验（手写，不引 zod 以保持这个文件自包含且依赖最少）
// ---------------------------------------------------------------------------

interface ParsedBody {
  provider: string;
  model: string;
  system?: string;
  messages: AgentMessage[];
  tools?: ToolSpec[];
  maxTokens?: number;
  effort?: ChatParams['effort'];
}

function badRequest(requestId: string, message: string, code = 'invalid_request', status = 400) {
  return Response.json({ code, message, requestId }, { status });
}

/**
 * 把 content 是**字符串**的消息归一化成 block 数组。
 *
 * 为什么要做这一步：官方 SDK 允许 `{role, content: "文本"}` 这种简写，
 * 而适配层内部统一按 block 数组处理（因为它是 Anthropic 与 OpenAI 的
 * 最小公共上界）。如果不在这里归一化，每个调用方都要记得包一层数组 ——
 * 而忘记包的后果是适配器里一个难以理解的 `content.map is not a function`。
 *
 * 这个坑在实测中真的踩到了：直接调端点传字符串，得到 502 与上面那句报错。
 */
function normalizeMessages(messages: AgentMessage[]): AgentMessage[] {
  return messages.map((m) => {
    const content = m.content as unknown;
    if (typeof content === 'string') {
      return { role: m.role, content: [{ type: 'text', text: content }] };
    }
    return m;
  });
}

const EFFORT_LEVELS = ['low', 'medium', 'high', 'xhigh', 'max'] as const;

/** 只接受已知的 effort 取值 —— 传了别的就让上游去报错，不在这里静默放行 */
function parseEffort(value: unknown): ChatParams['effort'] {
  return typeof value === 'string' && (EFFORT_LEVELS as readonly string[]).includes(value)
    ? (value as ChatParams['effort'])
    : undefined;
}

function parseBody(raw: unknown, requestId: string): ParsedBody | Response {
  if (typeof raw !== 'object' || raw === null) {
    return badRequest(requestId, '请求体必须是 JSON 对象');
  }
  const b = raw as Record<string, unknown>;

  if (typeof b.provider !== 'string' || typeof b.model !== 'string') {
    return badRequest(requestId, 'provider 与 model 都是必填的字符串');
  }
  if (!Array.isArray(b.messages) || b.messages.length === 0) {
    return badRequest(requestId, 'messages 必须是非空数组');
  }
  if (b.messages.length > MAX_MESSAGES) {
    return badRequest(requestId, `messages 数量超过上限 ${MAX_MESSAGES}`, 'payload_too_large', 413);
  }

  const maxTokens =
    typeof b.maxTokens === 'number' && Number.isFinite(b.maxTokens)
      ? Math.min(Math.max(1, Math.floor(b.maxTokens)), MAX_OUTPUT_TOKENS)
      : undefined;

  return {
    provider: b.provider,
    model: b.model,
    system: typeof b.system === 'string' ? b.system.slice(0, 32_000) : undefined,
    messages: normalizeMessages(b.messages as AgentMessage[]),
    tools: Array.isArray(b.tools) ? (b.tools.slice(0, 32) as ToolSpec[]) : undefined,
    maxTokens,
    effort: parseEffort(b.effort),
  };
}

// ---------------------------------------------------------------------------
// POST
// ---------------------------------------------------------------------------

export async function POST(req: NextRequest) {
  const requestId = crypto.randomUUID();

  // ---- 阶段一：首字节之前的所有校验，出错返回真实状态码 ----

  // Key 走请求头。这里读一次，之后只在透传时使用。
  const apiKey = req.headers.get('x-byok-key');
  if (!apiKey) {
    return badRequest(requestId, '缺少 API Key（请求头 x-byok-key）', 'unauthorized', 401);
  }

  // 体积上限：先看 content-length，避免读入超大 body
  const contentLength = Number(req.headers.get('content-length') ?? 0);
  if (contentLength > MAX_BODY_BYTES) {
    return badRequest(requestId, '请求体过大', 'payload_too_large', 413);
  }

  let rawBody: unknown;
  try {
    rawBody = await req.json();
  } catch {
    return badRequest(requestId, '请求体不是合法 JSON');
  }

  const parsed = parseBody(rawBody, requestId);
  if (parsed instanceof Response) return parsed;

  // provider 必须在注册表里
  const provider = resolveProvider(parsed.provider);
  if (!provider) {
    return badRequest(
      requestId,
      `未知的 provider：${parsed.provider}。支持的是：${Object.keys(
        (await import('@/lib/llm/registry')).PROVIDERS,
      ).join(', ')}`,
      'model_not_allowed',
      400,
    );
  }

  // model 必须在白名单里 —— 这是把端点从「通用 LLM 代理」收窄成
  // 「本站课程用到的几个模型」的关键一步
  if (!isModelAllowed(parsed.provider, parsed.model)) {
    return badRequest(
      requestId,
      `模型 ${parsed.model} 不在允许列表中`,
      'model_not_allowed',
      400,
    );
  }

  // ---- 阶段二：流式转发。此后所有错误都只能以事件形式发出 ----

  const upstream = new AbortController();
  const abortUpstream = (reason: string) =>
    upstream.abort(new DOMException(reason, 'AbortError'));

  // 客户端断开时中断上游，否则会为孤儿请求付费
  req.signal.addEventListener('abort', () => abortUpstream('client aborted'), { once: true });
  const timeoutTimer = setTimeout(() => abortUpstream('upstream timeout'), UPSTREAM_TIMEOUT_MS);

  const startedAt = Date.now();

  try {
    const { events, meta } = await provider.adapter.streamChat({
      creds: { apiKey, baseUrl: provider.baseUrl },
      params: {
        model: parsed.model,
        system: parsed.system,
        messages: parsed.messages,
        tools: parsed.tools,
        maxTokens: parsed.maxTokens,
        effort: parsed.effort,
      },
      signal: upstream.signal,
    });

    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        const encoder = new TextEncoder();
        const send = (event: string, data: unknown) =>
          controller.enqueue(encoder.encode(encodeSSE(event, data)));

        const heartbeat = setInterval(() => {
          controller.enqueue(encoder.encode(encodeSSEComment('ping')));
        }, HEARTBEAT_MS);

        try {
          send('start', {
            requestId,
            provider: parsed.provider,
            model: parsed.model,
            startedAt: new Date(startedAt).toISOString(),
          });

          for await (const ev of events) {
            // 上游返回的 error 事件里 requestId 是空的，这里补上本站的
            if (ev.type === 'error') send('error', { ...ev, requestId });
            else send(ev.type, ev);
          }

          send('done', { requestId, durationMs: Date.now() - startedAt });
        } catch (err) {
          // 流已开始 —— 不能再改 HTTP 状态码，只能发 error 事件
          send('error', {
            type: 'error',
            code: upstream.signal.aborted ? 'aborted' : 'upstream_error',
            message: describeError(err),
            requestId,
          });
        } finally {
          clearInterval(heartbeat);
          clearTimeout(timeoutTimer);
          try {
            controller.close();
          } catch {
            /* 已经关了 */
          }
        }
      },
      cancel() {
        abortUpstream('client cancelled');
        clearTimeout(timeoutTimer);
      },
    });

    void meta; // 目前不需要往客户端透出上游元信息

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        // no-transform 很重要：它告诉中间层不要缓冲/压缩改写这个响应，
        // 否则流式会退化成「卡住很久然后一次性出现」
        'Cache-Control': 'no-store, no-transform',
        'X-Accel-Buffering': 'no',
        Connection: 'keep-alive',
      },
    });
  } catch (err) {
    clearTimeout(timeoutTimer);

    // 上游在首字节前就失败了 —— 这里仍可以返回真实状态码
    if (err instanceof UpstreamError) {
      const status = err.upstreamStatus ?? 502;
      return Response.json(
        { code: err.code, message: err.message, requestId },
        { status: status >= 400 && status < 600 ? status : 502 },
      );
    }

    return Response.json(
      {
        code: 'upstream_error',
        // 注意：错误信息里绝不包含 Key。上游的错误体通常只是描述性问题，
        // 但为稳妥起见这里只保留 message，不原样透传整个对象。
        message: describeError(err),
        requestId,
      },
      { status: 502 },
    );
  }
}

function describeError(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}

// ---------------------------------------------------------------------------

/** 探针：确认中转是否启用（不暴露任何配置细节） */
export async function GET() {
  return Response.json({
    enabled: process.env.BYOK_RELAY_ENABLED !== 'false',
    note: 'POST 到此端点，Key 通过 x-byok-key 请求头传入',
  });
}
