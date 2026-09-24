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
 * Anthropic Messages API 适配器。
 *
 * 这个文件承载了 Anthropic 侧的全部协议细节。写它时对照的是官方文档：
 * - Messages API 参考：https://platform.claude.com/docs/en/api/messages
 * - Streaming：https://platform.claude.com/docs/en/build-with-claude/streaming
 *
 * ⚠️ 未实跑验证：本文件的实现只做过类型检查与逻辑推演，没有对着真实 API 跑过
 * （撰写时本机无可用 API Key）。协议的字段名取自上述文档，但行为未经验证。
 */

/** 文档要求显式声明 API 版本，否则请求会被拒绝 */
const ANTHROPIC_VERSION = '2023-06-01';

/** 模型白名单。新增模型时改这里一处即可。 */
const MODELS = [
  'claude-fable-5-1',
  'claude-opus-5-5',
  'claude-sonnet-5',
  'claude-haiku-4-5-20251001',
] as const;

// ---------------------------------------------------------------------------
// 请求转换
// ---------------------------------------------------------------------------

/**
 * 把统一消息模型转成 Anthropic 的格式。
 *
 * 注意 system 不在 messages 里 —— Messages API 没有 system 角色，
 * 它是请求的顶层字段。
 */
function toAnthropicMessages(messages: AgentMessage[]) {
  return messages.map((m) => ({
    role: m.role,
    content: m.content.map(toAnthropicBlock),
  }));
}

function toAnthropicBlock(block: ContentBlock): Record<string, unknown> {
  switch (block.type) {
    case 'text':
      return { type: 'text', text: block.text };
    case 'image':
      return {
        type: 'image',
        source: { type: 'base64', media_type: block.mediaType, data: block.dataBase64 },
      };
    case 'tool_use':
      return { type: 'tool_use', id: block.id, name: block.name, input: block.input };
    case 'tool_result':
      return {
        type: 'tool_result',
        tool_use_id: block.toolUseId,
        content: block.content,
        ...(block.isError ? { is_error: true } : {}),
      };
    case 'thinking':
      return { type: 'thinking', thinking: block.text, signature: block.signature ?? '' };
  }
}

/** 工具定义：Anthropic 用 input_schema，且工具的 name 有字符集限制 */
function toAnthropicTools(tools: ToolSpec[]) {
  return tools.map((t) => ({
    name: t.name,
    description: t.description,
    input_schema: t.inputSchema,
  }));
}

// ---------------------------------------------------------------------------
// 响应流解析
// ---------------------------------------------------------------------------

interface ToolCallAccumulator {
  id: string;
  name: string;
  /** 累积的 JSON 字符串片段，最后统一解析 */
  args: string;
}

/**
 * 把 Anthropic 的 SSE 流归一化成统一事件。
 *
 * 关键点：**工具调用的参数是分片到达的**。
 * `content_block_start` 给出 id 与 name；后续的 `input_json_delta` 只带
 * `index` 与 `partial_json`，**没有 id**，所以必须自己维护 index → 调用的映射。
 */
async function* normalizeAnthropicStream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<NormalizedEvent> {
  const reader = body.getReader();
  const textDecoder = new TextDecoder();
  const sse = createSSEDecoder();

  /** 按 index 累积工具调用，直到 content_block_stop 才能解析出完整入参 */
  const pendingToolCalls = new Map<number, ToolCallAccumulator>();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      for (const msg of sse.push(textDecoder.decode(value, { stream: true }))) {
        // 先原样透出，教学面板要靠它展示"厂商到底发了什么"
        yield { type: 'raw', line: `event: ${msg.event}\ndata: ${msg.data}` };

        const payload = safeJson(msg.data) as Record<string, any> | null;
        if (!payload) continue;

        switch (msg.event) {
          case 'message_start': {
            // 输入 token 在这里就有，不必等结束
            const usage = payload.message?.usage;
            if (usage) {
              yield {
                type: 'usage',
                inputTokens: usage.input_tokens,
                cacheReadTokens: usage.cache_read_input_tokens,
              };
            }
            break;
          }

          case 'content_block_start': {
            const block = payload.content_block;
            if (block?.type === 'tool_use') {
              pendingToolCalls.set(payload.index, {
                id: block.id,
                name: block.name,
                args: '',
              });
              yield { type: 'tool_call', index: payload.index, id: block.id, name: block.name };
            }
            break;
          }

          case 'content_block_delta': {
            const delta = payload.delta;
            if (delta?.type === 'text_delta') {
              yield { type: 'text', delta: delta.text };
            } else if (delta?.type === 'thinking_delta') {
              yield { type: 'thinking', delta: delta.thinking };
            } else if (delta?.type === 'input_json_delta') {
              const entry = pendingToolCalls.get(payload.index);
              if (entry) entry.args += delta.partial_json;
              yield { type: 'tool_args', index: payload.index, delta: delta.partial_json };
            }
            // signature_delta 是 thinking 块的完整性校验，前端用不到，忽略
            break;
          }

          case 'content_block_stop': {
            const entry = pendingToolCalls.get(payload.index);
            if (entry) {
              yield {
                type: 'tool_call_end',
                index: payload.index,
                input: parseToolArgs(entry.args),
              };
              pendingToolCalls.delete(payload.index);
            }
            break;
          }

          case 'message_delta': {
            if (payload.delta?.stop_reason) {
              yield {
                type: 'stop_reason',
                stopReason: normalizeStopReason('anthropic', payload.delta.stop_reason),
              };
            }
            // 文档明确：这里的 usage 是**累积值**，不是增量
            if (payload.usage?.output_tokens != null) {
              yield { type: 'usage', outputTokens: payload.usage.output_tokens };
            }
            break;
          }

          case 'error': {
            yield {
              type: 'error',
              code: 'upstream_error',
              message: payload.error?.message ?? '上游返回了错误事件',
              requestId: '', // 由 route 层补齐
            };
            break;
          }

          // message_stop / ping 无需单独处理：
          // 流的结束由 HTTP body 的结束表示，ping 只是保活
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * 解析累积的工具参数。
 * 解析失败时**不抛异常**，而是把原始字符串包起来返回 ——
 * 让模型有机会看到自己产生的畸形内容并纠正，比直接中断循环有用。
 */
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
  529: 'upstream_overloaded',
};

function mapError(status: number, body: unknown): { code: ErrorCode; message: string } {
  const code = STATUS_TO_CODE[status] ?? (status >= 500 ? 'upstream_error' : 'unknown');

  // Anthropic 的错误体形如 { type: 'error', error: { type, message } }
  const err = (body as { error?: { message?: string; type?: string } } | null)?.error;
  const message = err?.message ?? err?.type ?? `上游返回 ${status}`;

  return { code, message };
}

// ---------------------------------------------------------------------------
// 适配器
// ---------------------------------------------------------------------------

export const anthropicAdapter: ProviderAdapter = {
  id: 'anthropic',
  label: 'Anthropic (Claude)',
  defaultBaseUrl: 'https://api.anthropic.com',
  models: [...MODELS],
  supportsEffort: true,

  async streamChat({ creds, params, signal }) {
    const baseUrl = creds.baseUrl ?? anthropicAdapter.defaultBaseUrl;

    const body: Record<string, unknown> = {
      model: params.model,
      // max_tokens 在 Messages API 里是必填项，给一个合理默认
      max_tokens: params.maxTokens ?? 4096,
      stream: true,
      messages: toAnthropicMessages(params.messages),
    };

    if (params.system) body.system = params.system;
    if (params.tools?.length) body.tools = toAnthropicTools(params.tools);
    if (params.effort) body.output_config = { effort: params.effort };

    const res = await fetch(`${baseUrl}/v1/messages`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': creds.apiKey,
        'anthropic-version': ANTHROPIC_VERSION,
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
      events: normalizeAnthropicStream(res.body),
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
