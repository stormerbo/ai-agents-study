import { createSSEDecoder } from '../sse';
import {
  UpstreamError,
  normalizeStopReason,
  type AgentMessage,
  type ContentBlock,
  type ErrorCode,
  type NormalizedEvent,
  type ProviderAdapter,
  type ToolSpec,
} from '../types';

/**
 * OpenAI Chat Completions 兼容适配器。
 *
 * 覆盖 OpenAI 官方以及所有自称兼容的端点（DeepSeek、各类自建网关等）。
 *
 * 与 Anthropic 侧的差异比想象中大，这个文件里能直接看到三处：
 * 1. system 不是顶层字段，而是 messages 里的第一条
 * 2. 工具结果要用独立的 `role: "tool"` 消息，不能塞进 user 消息的 content 里
 * 3. **最后一帧的 choices 是空数组**（只带 usage），朴素地读 choices[0] 会崩
 *
 * ⚠️ 未实跑验证：本文件只做过类型检查，没有对着真实 API 跑过。
 * 协议字段依据 OpenAI Chat Completions 参考文档与各兼容端点的公开说明。
 */

const DEFAULT_MODELS = ['gpt-5.5', 'gpt-5'] as const;

// ---------------------------------------------------------------------------
// 请求转换
// ---------------------------------------------------------------------------

function textOf(blocks: ContentBlock[]): string {
  return blocks
    .filter((b): b is Extract<ContentBlock, { type: 'text' }> => b.type === 'text')
    .map((b) => b.text)
    .join('');
}

function toOpenAIMessages(system: string | undefined, messages: AgentMessage[]) {
  const out: Record<string, unknown>[] = [];

  // 差异之一：system 是 messages 的第一条，不是顶层字段
  if (system) out.push({ role: 'system', content: system });

  for (const m of messages) {
    if (m.role === 'assistant') {
      const text = textOf(m.content);
      const toolCalls = m.content
        .filter((b): b is Extract<ContentBlock, { type: 'tool_use' }> => b.type === 'tool_use')
        .map((b) => ({
          id: b.id,
          type: 'function',
          function: { name: b.name, arguments: JSON.stringify(b.input ?? {}) },
        }));

      const msg: Record<string, unknown> = { role: 'assistant' };
      if (text) msg.content = text;
      // 没有工具调用时不要带空数组，部分兼容端点会因此报错
      if (toolCalls.length > 0) msg.tool_calls = toolCalls;
      out.push(msg);
      continue;
    }

    // 差异之二：工具结果必须是独立的 tool 消息，且排在 user 消息之前
    const toolResults = m.content.filter(
      (b): b is Extract<ContentBlock, { type: 'tool_result' }> => b.type === 'tool_result',
    );
    for (const tr of toolResults) {
      out.push({ role: 'tool', tool_call_id: tr.toolUseId, content: tr.content });
    }

    const rest = m.content.filter((b) => b.type !== 'tool_result');
    if (rest.length > 0) {
      const hasImage = rest.some((b) => b.type === 'image');
      if (hasImage) {
        out.push({
          role: 'user',
          content: rest.map((b) =>
            b.type === 'text'
              ? { type: 'text', text: b.text }
              : {
                  type: 'image_url',
                  image_url: { url: `data:${(b as any).mediaType};base64,${(b as any).dataBase64}` },
                },
          ),
        });
      } else {
        out.push({ role: 'user', content: textOf(rest) });
      }
    }
  }

  return out;
}

/** 工具定义：包一层 function，参数键名是 parameters 而非 input_schema */
function toOpenAITools(tools: ToolSpec[]) {
  return tools.map((t) => ({
    type: 'function',
    function: { name: t.name, description: t.description, parameters: t.inputSchema },
  }));
}

// ---------------------------------------------------------------------------
// 响应流解析
// ---------------------------------------------------------------------------

async function* normalizeOpenAIStream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<NormalizedEvent> {
  const reader = body.getReader();
  const textDecoder = new TextDecoder();
  const sse = createSSEDecoder();

  /** index → { id, name, args }。与 Anthropic 一样要按 index 累积参数。 */
  const pendingToolCalls = new Map<number, { id: string; name: string; args: string }>();
  let announced = new Set<number>();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      for (const msg of sse.push(textDecoder.decode(value, { stream: true }))) {
        yield { type: 'raw', line: `event: ${msg.event}\ndata: ${msg.data}` };

        // OpenAI 用 [DONE] 哨兵标记结束，它不是一个 JSON
        if (msg.data.trim() === '[DONE]') continue;

        const payload = safeJson(msg.data) as Record<string, any> | null;
        if (!payload) continue;

        // 差异之三：最后一帧只带 usage，choices 是空数组。
        // 先处理 usage，再判断 choices —— 顺序反过来就会在这里崩。
        if (payload.usage) {
          yield {
            type: 'usage',
            inputTokens: payload.usage.prompt_tokens,
            outputTokens: payload.usage.completion_tokens,
            cacheReadTokens: payload.usage.prompt_tokens_details?.cached_tokens,
          };
        }

        const choice = Array.isArray(payload.choices) ? payload.choices[0] : undefined;
        if (!choice) continue;

        const delta = choice.delta ?? {};

        if (typeof delta.content === 'string' && delta.content.length > 0) {
          yield { type: 'text', delta: delta.content };
        }

        // DeepSeek 等推理模型的思考内容走这个字段
        if (typeof delta.reasoning_content === 'string' && delta.reasoning_content.length > 0) {
          yield { type: 'thinking', delta: delta.reasoning_content };
        }

        if (Array.isArray(delta.tool_calls)) {
          for (const tc of delta.tool_calls) {
            const index: number = tc.index ?? 0;
            const entry = pendingToolCalls.get(index) ?? { id: '', name: '', args: '' };

            // id 与 name 只在第一帧出现，之后都是参数分片
            if (tc.id) entry.id = tc.id;
            if (tc.function?.name) entry.name = tc.function.name;
            pendingToolCalls.set(index, entry);

            // 等拿到 name 再宣布这次调用，避免发出一个没有名字的 tool_call
            if (entry.name && !announced.has(index)) {
              announced.add(index);
              yield { type: 'tool_call', index, id: entry.id, name: entry.name };
            }

            const argsDelta: string | undefined = tc.function?.arguments;
            if (typeof argsDelta === 'string' && argsDelta.length > 0) {
              entry.args += argsDelta;
              yield { type: 'tool_args', index, delta: argsDelta };
            }
          }
        }

        if (choice.finish_reason) {
          yield {
            type: 'stop_reason',
            stopReason: normalizeStopReason('openai', choice.finish_reason),
          };
        }
      }
    }

    // 流结束时把还没解析的工具入参补上
    for (const [index, entry] of pendingToolCalls) {
      yield { type: 'tool_call_end', index, input: parseToolArgs(entry.args) };
    }
  } finally {
    reader.releaseLock();
  }
}

function parseToolArgs(raw: string): unknown {
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return { __unparsed: raw };
  }
}

// ---------------------------------------------------------------------------
// 错误映射
// ---------------------------------------------------------------------------

const STATUS_TO_CODE: Record<number, ErrorCode> = {
  400: 'invalid_request',
  401: 'unauthorized',
  403: 'forbidden',
  404: 'model_not_allowed',
  413: 'payload_too_large',
  429: 'rate_limited',
  500: 'upstream_error',
  503: 'upstream_overloaded',
};

function mapError(status: number, body: unknown): { code: ErrorCode; message: string } {
  const code = STATUS_TO_CODE[status] ?? (status >= 500 ? 'upstream_error' : 'unknown');
  // OpenAI 的错误体形如 { error: { message, type, code, param } }
  const err = (body as { error?: { message?: string } } | null)?.error;
  return { code, message: err?.message ?? `上游返回 ${status}` };
}

// ---------------------------------------------------------------------------
// 适配器
// ---------------------------------------------------------------------------

export const openAICompatibleAdapter: ProviderAdapter = {
  id: 'openai',
  label: 'OpenAI 兼容',
  defaultBaseUrl: 'https://api.openai.com',
  models: [...DEFAULT_MODELS],
  // effort 是 Anthropic 侧的概念，OpenAI 系没有对应参数
  supportsEffort: false,

  async streamChat({ creds, params, signal }) {
    const baseUrl = creds.baseUrl ?? openAICompatibleAdapter.defaultBaseUrl;

    const body: Record<string, unknown> = {
      model: params.model,
      stream: true,
      messages: toOpenAIMessages(params.system, params.messages),
      // 不显式要求的话，多数端点不会在流里返回 usage
      stream_options: { include_usage: true },
    };

    if (params.maxTokens) body.max_tokens = params.maxTokens;
    if (params.tools?.length) body.tools = toOpenAITools(params.tools);

    const res = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${creds.apiKey}`,
        accept: 'text/event-stream',
      },
      body: JSON.stringify(body),
      signal,
    });

    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => '');
      const mapped = mapError(res.status, safeJson(text));
      throw new UpstreamError(mapped.code, mapped.message, res.status);
    }

    return {
      events: normalizeOpenAIStream(res.body),
      meta: { baseUrl, upstreamStatus: res.status },
    };
  },

  mapError,
};

// ---------------------------------------------------------------------------

function safeJson(text: string): unknown | null {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}
