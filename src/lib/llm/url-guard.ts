/**
 * 自定义端点的 URL 安全校验。
 *
 * ## 为什么需要这一层
 *
 * 为了支持第三方中转平台，必须允许用户指定 baseUrl。但开放任意 URL 有两个风险：
 *
 * 1. **SSRF**：让别人有机会让本站服务器去请求内网地址（`https://10.0.0.1/admin`）
 *    或云元数据端点（`https://169.254.169.254/`），把这里当成内网探测跳板。
 * 2. **开放代理**：端点被当成通用 HTTP 转发器使用。
 *
 * 应对是**校验 + 开关**两层：这个文件负责校验，`ALLOW_CUSTOM_BASE_URL`
 * 环境变量负责开关。本地自用可以打开，公网部署建议关闭。
 *
 * ## 一个诚实的局限
 *
 * 这里只做**静态校验**（检查 URL 本身），不做 DNS 解析后的二次校验。
 * 因此理论上存在 DNS rebinding 的可能：一个域名先解析到公网 IP 通过校验，
 * 实际请求时改解析到内网。
 *
 * 在本项目的部署形态（本地 / 个人使用）下，这个残余风险可以接受。
 * **若要对外提供服务，应当补上解析后的 IP 检查**（在 fetch 之前解析域名、
 * 确认解析结果不是私有地址，并使用解析到的 IP 直连以防二次解析）。
 */

const BLOCKED_HOSTNAMES = new Set([
  'localhost',
  'metadata.google.internal',
  'metadata.goog',
]);

/** 私有网段与保留地址 */
function isPrivateOrReserved(host: string): boolean {
  // IPv4
  const v4 = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (v4) {
    const a = Number(v4[1]);
    const b = Number(v4[2]);
    if (a === 0) return true; // 0.0.0.0/8
    if (a === 10) return true; // 10.0.0.0/8
    if (a === 127) return true; // 回环
    if (a === 172 && b >= 16 && b <= 31) return true; // 172.16.0.0/12
    if (a === 192 && b === 168) return true; // 192.168.0.0/16
    if (a === 169 && b === 254) return true; // 链路本地，含云元数据 169.254.169.254
    return false;
  }

  // IPv6
  const h = host.replace(/^\[|\]$/g, '').toLowerCase();
  if (h === '::' || h === '::1') return true;
  if (h.startsWith('fe80:')) return true; // 链路本地
  if (h.startsWith('fc') || h.startsWith('fd')) return true; // 唯一本地 fc00::/7
  // IPv4-mapped IPv6，如 ::ffff:10.0.0.1
  const mapped = h.match(/^::ffff:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$/);
  if (mapped?.[1]) return isPrivateOrReserved(mapped[1]);

  return false;
}

export type UrlCheckResult = { ok: true; url: string } | { ok: false; reason: string };

/**
 * 校验用户提供的 baseUrl。
 * 通过时返回**规范化后**的地址（去掉结尾斜杠，保留路径）。
 */
export function validateCustomBaseUrl(raw: string): UrlCheckResult {
  const trimmed = raw.trim();
  if (!trimmed) return { ok: false, reason: 'baseUrl 不能为空' };

  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    return { ok: false, reason: '不是合法的 URL（需要包含 https://）' };
  }

  // 强制 https —— http 会让 API Key 与对话内容以明文经过网络
  if (url.protocol !== 'https:') {
    return { ok: false, reason: '必须是 https —— 用 http 你的 API Key 会明文传输' };
  }

  if (url.username || url.password) {
    return { ok: false, reason: 'URL 里不能包含用户名或密码' };
  }

  const host = url.hostname.toLowerCase();

  if (BLOCKED_HOSTNAMES.has(host)) {
    return { ok: false, reason: '不允许指向本机或云元数据端点' };
  }
  if (isPrivateOrReserved(host)) {
    return { ok: false, reason: '不允许指向内网地址（防 SSRF）' };
  }
  if (host.endsWith('.local') || host.endsWith('.internal')) {
    return { ok: false, reason: '不允许指向内网域名' };
  }

  // 保留路径 —— 很多第三方平台的 baseUrl 自带 /v1 或 /anthropic
  const normalized = (url.origin + url.pathname).replace(/\/+$/, '');
  return { ok: true, url: normalized };
}

/** 是否允许自定义端点。默认关闭，本地自用时在 .env.local 里打开。 */
export function isCustomBaseUrlAllowed(): boolean {
  return process.env.ALLOW_CUSTOM_BASE_URL === 'true';
}
