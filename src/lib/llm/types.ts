/**
 * 多厂商 LLM 适配层的类型契约。
 *
 * 设计目标：让上层（API route、前端 Playground、agent 循环）**永远不接触
 * 任何厂商的原始格式**。Anthropic 与 OpenAI 的差异全部在适配器内部消化，
 * 出口只有一套规范化事件。
 *
 * 这套接口本身也是教学内容 —— 第 8 章会讲它的设计取舍。
 */

import type { AgentMessage, ContentBlock, ToolSpec } from '@/content/curriculum/schema';

export type { AgentMessage, ContentBlock, ToolSpec };

// ---------------------------------------------------------------------------
// 厂商
// ---------------------------------------------------------------------------

export const KNOWN_PROVIDER_IDS = ['anthropic', 'deepseek', 'openai'] as const;
export type KnownProviderId = (typeof KNOWN_PROVIDER_IDS)[number];

/** 允许自定义（OpenAI 兼容端点），但服务端仍会校验 */
export type ProviderId = KnownProviderId | (string & {});

export interface ProviderCredentials {
  apiKey: string;
  /** 仅当服务端注册表里为该 provider 配了 baseUrl 时使用 */
  baseUrl?: string;
}

// ---------------------------------------------------------------------------
// 请求
// ---------------------------------------------------------------------------

export interface ChatParams {
  model: string;
  system?: string;
  messages: AgentMessage[];
  tools?: ToolSpec[];
  maxTokens?: number;
  /** 仅 Anthropic 系模型支持；不支持的厂商会忽略 */
  effort?: 'low' | 'medium' | 'high' | 'xhigh' | 'max';
}

// ---------------------------------------------------------------------------
// 规范化事件
//
// 前端只认这些。注意几个刻意设计：
// - 工具调用被拆成 tool_call（开始）/ tool_args（参数分片）/ tool_call_end（完整入参）
//   三个事件，因为厂商都是这么流的，且这样前端才能展示"参数正在流入"的过程
// - stop_reason 被归一化：Anthropic 的 end_turn 与 OpenAI 的 stop 是同一件事
// - error 是事件流内的事件，不是抛异常 —— 因为流已经开始后无法再改 HTTP 状态码
// ---------------------------------------------------------------------------

export type StopReason =
  | 'end_turn'
  | 'max_tokens'
  | 'tool_use'
  | 'stop_sequence'
  | 'refusal'
  | 'content_filter'
  | 'pause'
  | 'unknown';

export type ErrorCode =
  | 'unauthorized'
  | 'forbidden'
  | 'model_not_allowed'
  | 'rate_limited'
  | 'payload_too_large'
  | 'invalid_request'
  | 'upstream_error'
  | 'upstream_timeout'
  | 'upstream_overloaded'
  | 'aborted'
  | 'relay_disabled'
  | 'unknown';

export type NormalizedEvent =
  | { type: 'start'; requestId: string; provider: string; model: string; startedAt: string }
  /**
   * 原始上游 SSE 行（含 `event:` / `data:` 前缀）。
   *
   * 刻意放进同一个事件流而不是走单独通道：这样顺序天然正确，
   * 教学面板能精确看到「哪一行原始数据产生了哪个规范化事件」。
   * 这也是本站不用现成 SDK 的原因之一 —— SDK 会把这层藏起来，
   * 而「看清厂商到底发了什么」正是第 1 章实验要教的东西。
   */
  | { type: 'raw'; line: string }
  | { type: 'text'; delta: string }
  | { type: 'thinking'; delta: string }
  | { type: 'tool_call'; index: number; id: string; name: string }
  | { type: 'tool_args'; index: number; delta: string }
  | { type: 'tool_call_end'; index: number; input: unknown }
  | { type: 'usage'; inputTokens?: number; outputTokens?: number; cacheReadTokens?: number }
  | { type: 'stop_reason'; stopReason: StopReason }
  | { type: 'done'; requestId: string; durationMs: number }
  | {
      type: 'error';
      code: ErrorCode;
      message: string;
      requestId: string;
      retryAfterMs?: number;
    };

/**
 * 上游返回错误时抛出。
 *
 * 与「事件流里的 error 事件」区分开：这个用于**首字节之前**的失败
 * （HTTP 状态码非 2xx），此时还能返回真实的 HTTP 状态码给客户端；
 * 一旦流已经开始，就只能发 error 事件了。这个两阶段契约是刻意的 ——
 * 客户端需要能区分「配置错了」和「生成中途断了」。
 */
export class UpstreamError extends Error {
  constructor(
    readonly code: ErrorCode,
    message: string,
    readonly upstreamStatus?: number,
  ) {
    super(message);
    this.name = 'UpstreamError';
  }
}

// ---------------------------------------------------------------------------
// 适配器
// ---------------------------------------------------------------------------

export interface StreamChatArgs {
  creds: ProviderCredentials;
  params: ChatParams;
  signal: AbortSignal;
}

export interface StreamChatResult {
  events: AsyncIterable<NormalizedEvent>;
  meta: { baseUrl: string; upstreamStatus?: number };
}

export interface ProviderAdapter {
  readonly id: ProviderId;
  readonly label: string;
  readonly defaultBaseUrl: string;
  /** 该适配器支持的模型（也作为服务端白名单来源之一） */
  readonly models: readonly string[];
  /** 该厂商是否支持 effort 参数 */
  readonly supportsEffort: boolean;

  streamChat(args: StreamChatArgs): Promise<StreamChatResult>;

  /** 把上游错误体翻译成统一的错误码 */
  mapError(status: number, body: unknown): { code: ErrorCode; message: string };
}

// ---------------------------------------------------------------------------
// 归一化辅助
// ---------------------------------------------------------------------------

/**
 * 各厂商的停止原因映射到统一取值。
 *
 * 这张表本身就是教学内容：两家的取值集合并不一一对应，
 * 「映射」这个动作必然会丢信息 —— 这里用 unknown 兜底而不是硬塞一个近似值。
 */
export function normalizeStopReason(provider: ProviderId, raw: string | null | undefined): StopReason {
  if (!raw) return 'unknown';

  if (provider === 'anthropic') {
    switch (raw) {
      case 'end_turn':
        return 'end_turn';
      case 'max_tokens':
        return 'max_tokens';
      case 'tool_use':
        return 'tool_use';
      case 'stop_sequence':
        return 'stop_sequence';
      case 'refusal':
        return 'refusal';
      case 'pause_turn':
        return 'pause';
      default:
        return 'unknown';
    }
  }

  // OpenAI 兼容系
  switch (raw) {
    case 'stop':
      return 'end_turn';
    case 'length':
      return 'max_tokens';
    case 'tool_calls':
    case 'function_call':
      return 'tool_use';
    case 'content_filter':
      return 'content_filter';
    default:
      return 'unknown';
  }
}
