import { anthropicAdapter } from './adapters/anthropic';
import { openAICompatibleAdapter } from './adapters/openai-compatible';
import type { ProviderAdapter } from './types';

/**
 * Provider 注册表 —— 同时承担两个职责。
 *
 * **职责一：把「协议」与「厂商」解耦。**
 * 注意 DeepSeek 用的是 `anthropicAdapter` 而不是自己的适配器 —— 因为它提供了
 * Anthropic 兼容端点。适配器选的是**协议**，不是厂商名。这是整个设计里
 * 最值得注意的一点，第 8 章会展开讲。
 *
 * **职责二：当白名单用（安全边界）。**
 * 这是本站唯一的运行时后端接口。客户端传来的 provider 与 model 必须落在这里，
 * 否则 /api/chat 直接拒绝。这样即使在公开部署后被扫描到，端点也无法被当成
 * 通用 LLM 代理使用 —— 只能调本站课程里用到的这几个模型。
 */
export interface ProviderRegistration {
  /** 使用的适配器（决定走哪套协议） */
  adapter: ProviderAdapter;
  /** 该 provider 的 baseUrl */
  baseUrl: string;
  /** UI 显示名 */
  label: string;
  /** 引导用户去哪申请 Key */
  keyHint?: string;
  /** 允许的模型白名单 */
  models: string[];
  /** 默认模型 */
  defaultModel: string;
}

export const PROVIDERS = {
  anthropic: {
    adapter: anthropicAdapter,
    baseUrl: 'https://api.anthropic.com',
    label: 'Anthropic（Claude）',
    keyHint: 'console.anthropic.com',
    models: ['claude-fable-5-1', 'claude-opus-5-5', 'claude-sonnet-5', 'claude-haiku-4-5-20251001'],
    defaultModel: 'claude-haiku-4-5-20251001',
  },
  deepseek: {
    // 注意：这里用的是 Anthropic 适配器 —— DeepSeek 提供 Anthropic 兼容端点。
    // 适配器选的是协议，不是厂商。同一个适配器可以被多个 provider 复用。
    adapter: anthropicAdapter,
    baseUrl: 'https://api.deepseek.com/anthropic',
    label: 'DeepSeek（Anthropic 兼容端点）',
    keyHint: 'platform.deepseek.com',
    models: ['deepseek-flash', 'deepseek-v4-pro'],
    defaultModel: 'deepseek-flash',
  },
  openai: {
    adapter: openAICompatibleAdapter,
    baseUrl: 'https://api.openai.com',
    label: 'OpenAI',
    keyHint: 'platform.openai.com',
    models: ['gpt-5.5', 'gpt-5'],
    defaultModel: 'gpt-5',
  },
} as const satisfies Record<string, ProviderRegistration>;

export type KnownProviderId = keyof typeof PROVIDERS;

export function isKnownProvider(id: string): id is KnownProviderId {
  return Object.prototype.hasOwnProperty.call(PROVIDERS, id);
}

export function resolveProvider(id: string): ProviderRegistration | undefined {
  return isKnownProvider(id) ? PROVIDERS[id] : undefined;
}

/**
 * 模型白名单校验。
 *
 * 除了注册表里的固定清单，还支持通过环境变量扩展 —— 这样厂商发布新模型时
 * 不必改代码重新部署：
 *
 *   MODEL_ALLOWLIST_EXTRA=["claude-new-model"]
 */
export function isModelAllowed(providerId: string, model: string): boolean {
  const provider = resolveProvider(providerId);
  if (!provider) return false;
  if ((provider.models as readonly string[]).includes(model)) return true;

  const extra = process.env.MODEL_ALLOWLIST_EXTRA;
  if (!extra) return false;

  try {
    const parsed: unknown = JSON.parse(extra);
    return Array.isArray(parsed) && parsed.includes(model);
  } catch {
    // 环境变量格式错误时不放行任何模型 —— 宁可拒绝，不要静默放宽
    return false;
  }
}

/** 给前端用的 provider 清单（不含任何密钥） */
export function getPublicProviderList() {
  return Object.entries(PROVIDERS).map(([id, p]) => ({
    id,
    label: p.label,
    keyHint: p.keyHint,
    /** 默认端点地址 —— 前端用它预填表单，用户可以改 */
    defaultBaseUrl: p.baseUrl,
    models: p.models,
    defaultModel: p.defaultModel,
    supportsEffort: p.adapter.supportsEffort,
  }));
}
