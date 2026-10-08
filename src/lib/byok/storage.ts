/**
 * BYOK 凭据的浏览器端存储。
 *
 * ## 三个刻意的设计决定
 *
 * **1. 不加密。**
 * 直觉上应该用 WebCrypto 从口令派生密钥、做 AES-GCM 加密。但这防不住真正的威胁：
 * 解密逻辑和解密密钥都在同一个页面里，XSS 可以直接调用解密函数。它带来的只有
 * 真实的体验损失（每次打开实验都要输一次口令），安全收益接近于零。
 * 真正的防线是严格 CSP 与不引第三方脚本（见 AGENTS.md）。
 *
 * **2. 提供「仅本次会话」模式。**
 * 凭据只存在内存里、不写 localStorage。这才是真正有效的安全选项，
 * 且实现成本几乎为零。共享电脑上应该用它。
 *
 * **3. Key 通过请求头传给中转端点，不走请求体。**
 * 请求体更容易被中间层、网关或错误日志记录下来。
 */

const STORAGE_KEY = 'aas.byok.v1';

export interface ProviderCredential {
  apiKey: string;
  updatedAt: string;
  /** 上次连通性校验的时间与结果，避免每次运行都重试错误的 Key */
  lastValidatedAt?: string;
  lastValidationOk?: boolean;
}

export interface ByokState {
  version: 1;
  /** persistent = 存 localStorage；session = 只存内存，关闭标签页即失效 */
  mode: 'persistent' | 'session';
  credentials: Record<string, ProviderCredential>;
}

const EMPTY: ByokState = { version: 1, mode: 'persistent', credentials: {} };

/** session 模式下的内存存储。刷新页面即丢失 —— 这是刻意的。 */
let memoryFallback: ByokState | null = null;

// ---------------------------------------------------------------------------
// 读写
// ---------------------------------------------------------------------------

export function loadByok(): ByokState {
  if (typeof window === 'undefined') return EMPTY;
  if (memoryFallback) return memoryFallback;

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    const parsed = JSON.parse(raw) as ByokState;
    // 版本不匹配时丢弃而不是尝试迁移 —— 这里的数据可以随时重建，
    // 为一个存凭据的结构写迁移逻辑不值得
    if (parsed.version !== 1) return EMPTY;
    return parsed;
  } catch {
    return EMPTY;
  }
}

export function saveByok(state: ByokState): void {
  if (typeof window === 'undefined') return;
  if (state.mode === 'session') {
    memoryFallback = state;
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }
  memoryFallback = null;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // 隐私模式或配额满时 localStorage 会抛错。降级到内存，不阻断使用。
    memoryFallback = state;
  }
}

// ---------------------------------------------------------------------------
// 便捷操作
// ---------------------------------------------------------------------------

export function getCredential(state: ByokState, providerId: string): string | undefined {
  return state.credentials[providerId]?.apiKey || undefined;
}

export function setCredential(
  state: ByokState,
  providerId: string,
  apiKey: string,
): ByokState {
  const next: ByokState = {
    ...state,
    credentials: {
      ...state.credentials,
      [providerId]: { apiKey, updatedAt: new Date().toISOString() },
    },
  };
  saveByok(next);
  return next;
}

export function clearCredential(state: ByokState, providerId: string): ByokState {
  const credentials = { ...state.credentials };
  delete credentials[providerId];
  const next: ByokState = { ...state, credentials };
  saveByok(next);
  return next;
}

export function setMode(state: ByokState, mode: ByokState['mode']): ByokState {
  const next: ByokState = { ...state, mode };
  // 从 persistent 切到 session 时，要把已经落盘的内容清掉 ——
  // 否则「切到仅本次会话」这个动作本身没有达到目的
  if (mode === 'session' && typeof window !== 'undefined') {
    window.localStorage.removeItem(STORAGE_KEY);
  }
  saveByok(next);
  return next;
}

/** 用于 UI 展示：只显示尾部四位，避免完整 Key 出现在屏幕上 */
export function maskKey(apiKey: string): string {
  if (apiKey.length <= 8) return '••••';
  return `••••••••${apiKey.slice(-4)}`;
}
