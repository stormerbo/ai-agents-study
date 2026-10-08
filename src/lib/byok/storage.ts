/**
 * BYOK 端点配置的浏览器端存储。
 *
 * ## 为什么存的是「配置」而不是「Key」
 *
 * 一次可用的调用需要**四样东西成套**：协议（用哪个适配器）、端点地址、
 * 模型名、API Key。只保存 Key 是不够的 —— 下次打开页面时地址与模型名会
 * 退回默认值，用户每次都得重填。这是最初实现漏掉的点。
 *
 * 所以存储单位是 **EndpointProfile**（端点配置），并且支持保存多套
 * （例如「官方」与「某中转平台」），可以一键切换。
 *
 * ## 安全设计
 *
 * **1. 不加密。**
 * 直觉上应该用 WebCrypto 从口令派生密钥做 AES-GCM。但它防不住真正的威胁：
 * 解密逻辑和解密密钥都在同一个页面里，XSS 可以直接调用解密函数。
 * 它带来的只有真实的体验损失（每次打开都要输一次口令），安全收益接近于零。
 * 真正的防线是严格 CSP 与不引第三方脚本。
 *
 * **2. 提供「仅本次会话」模式。**
 * 凭据只存在内存里、不写 localStorage。这才是真正有效的安全选项，
 * 且实现成本几乎为零。共享电脑上应该用它。
 *
 * **3. Key 通过请求头传给中转端点，不走请求体。**
 * 请求体更容易被中间层、网关或错误日志记录下来。
 */

const STORAGE_KEY = 'aas.byok.v2';

export interface EndpointProfile {
  id: string;
  /** 用户起的名字，如「官方」「某中转」 */
  name: string;
  /** 用哪个适配器 —— 决定走哪套协议 */
  providerId: string;
  baseUrl: string;
  model: string;
  apiKey: string;
}

export interface ByokState {
  version: 2;
  /** persistent = 存 localStorage；session = 只存内存，关标签页即失效 */
  mode: 'persistent' | 'session';
  profiles: EndpointProfile[];
  /** 当前使用的配置 id */
  activeId: string | null;
}

export const EMPTY_BYOK: ByokState = {
  version: 2,
  mode: 'persistent',
  profiles: [],
  activeId: null,
};

/** session 模式下的内存存储。刷新页面即丢失 —— 这是刻意的。 */
let memoryFallback: ByokState | null = null;

// ---------------------------------------------------------------------------
// 读写
// ---------------------------------------------------------------------------

function isProfile(v: unknown): v is EndpointProfile {
  if (typeof v !== 'object' || v === null) return false;
  const p = v as Record<string, unknown>;
  return (
    typeof p.id === 'string' &&
    typeof p.name === 'string' &&
    typeof p.providerId === 'string' &&
    typeof p.baseUrl === 'string' &&
    typeof p.model === 'string' &&
    typeof p.apiKey === 'string'
  );
}

export function loadByok(): ByokState {
  if (typeof window === 'undefined') return EMPTY_BYOK;
  if (memoryFallback) return memoryFallback;

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY_BYOK;

    const parsed = JSON.parse(raw) as Partial<ByokState>;
    if (parsed.version !== 2 || !Array.isArray(parsed.profiles)) return EMPTY_BYOK;

    // 逐条校验结构 —— 存储里的内容可能被手工改过或来自旧版本
    const profiles = parsed.profiles.filter(isProfile);
    const activeId =
      typeof parsed.activeId === 'string' && profiles.some((p) => p.id === parsed.activeId)
        ? parsed.activeId
        : (profiles[0]?.id ?? null);

    return {
      version: 2,
      mode: parsed.mode === 'session' ? 'session' : 'persistent',
      profiles,
      activeId,
    };
  } catch {
    return EMPTY_BYOK;
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
// 配置操作
// ---------------------------------------------------------------------------

export function getActiveProfile(state: ByokState): EndpointProfile | null {
  if (!state.activeId) return null;
  return state.profiles.find((p) => p.id === state.activeId) ?? null;
}

/** 生成一个不与人冲突的配置名 */
function nextProfileName(profiles: EndpointProfile[], base: string): string {
  if (!profiles.some((p) => p.name === base)) return base;
  let n = 2;
  while (profiles.some((p) => p.name === `${base} ${n}`)) n += 1;
  return `${base} ${n}`;
}

export function createProfile(
  state: ByokState,
  seed: Omit<EndpointProfile, 'id' | 'name'> & { name?: string },
): ByokState {
  const id = `p_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  const profile: EndpointProfile = {
    id,
    name: nextProfileName(state.profiles, seed.name ?? '新配置'),
    providerId: seed.providerId,
    baseUrl: seed.baseUrl,
    model: seed.model,
    apiKey: seed.apiKey,
  };
  const next: ByokState = {
    ...state,
    profiles: [...state.profiles, profile],
    activeId: id,
  };
  saveByok(next);
  return next;
}

/** 更新某个配置。传 patch 而不是整条替换，避免调用方需要先读一遍。 */
export function updateProfile(
  state: ByokState,
  id: string,
  patch: Partial<Omit<EndpointProfile, 'id'>>,
): ByokState {
  const next: ByokState = {
    ...state,
    profiles: state.profiles.map((p) => (p.id === id ? { ...p, ...patch } : p)),
  };
  saveByok(next);
  return next;
}

export function deleteProfile(state: ByokState, id: string): ByokState {
  const profiles = state.profiles.filter((p) => p.id !== id);
  const next: ByokState = {
    ...state,
    profiles,
    activeId: state.activeId === id ? (profiles[0]?.id ?? null) : state.activeId,
  };
  saveByok(next);
  return next;
}

export function setActiveProfile(state: ByokState, id: string): ByokState {
  const next: ByokState = { ...state, activeId: id };
  saveByok(next);
  return next;
}

export function setMode(state: ByokState, mode: ByokState['mode']): ByokState {
  const next: ByokState = { ...state, mode };
  // 切到 session 时要把已经落盘的内容清掉 ——
  // 否则「切到仅本次会话」这个动作本身没有达到目的
  if (mode === 'session' && typeof window !== 'undefined') {
    window.localStorage.removeItem(STORAGE_KEY);
    memoryFallback = next;
  } else {
    saveByok(next);
  }
  return next;
}

/** 用于 UI 展示：只显示尾部四位，避免完整 Key 出现在屏幕上 */
export function maskKey(apiKey: string): string {
  if (!apiKey) return '（未填）';
  if (apiKey.length <= 8) return '••••';
  return `••••••••${apiKey.slice(-4)}`;
}
