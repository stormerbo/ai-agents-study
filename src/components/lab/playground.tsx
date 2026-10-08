'use client';

import { useEffect, useMemo, useState } from 'react';

import { useSyncExternalStore } from 'react';

import { useChatRelay, type TraceEntry } from '@/hooks/use-chat-relay';
import {
  getCredential,
  loadByok,
  maskKey,
  setCredential,
  setMode,
  type ByokState,
} from '@/lib/byok/storage';
import type { Lab } from '@/content/curriculum/schema';
import { cn } from '@/lib/utils';

/**
 * 一个永不触发的订阅源。
 *
 * 只用来回答一个问题：**当前是否已经挂载到客户端**。
 * 服务端没有 localStorage，直接读会让两端首次渲染不一致（hydration mismatch）。
 * getServerSnapshot 返回 false、客户端返回 true，是这个问题最干净的解法 ——
 * 比 useEffect + setState 好，后者会触发级联渲染且被 React 19 的
 * react-hooks/set-state-in-effect 规则禁止。
 */
const subscribeNothing = () => () => {};

/**
 * 站内代码实验。
 *
 * 设计取舍（见 AGENTS.md）：
 * - **BYOK**：用户自带 Key，存浏览器；经本站中转端点转发给厂商，服务端不存储
 * - **轨迹优先**：默认展示每一步事件，而不只是最终文本 —— 这才是实验的价值
 * - **原始事件可查**：教学面板能看到厂商实际发出的 SSE 行
 */

interface ProviderOption {
  id: string;
  label: string;
  keyHint?: string;
  models: string[];
  defaultModel: string;
}

export function Playground({
  lab,
  providers,
  allowCustomEndpoint,
}: {
  lab: Lab;
  providers: ProviderOption[];
  /** 服务端是否开放自定义端点（读 ALLOW_CUSTOM_BASE_URL 环境变量） */
  allowCustomEndpoint: boolean;
}) {
  const [byok, setByok] = useState<ByokState>(() => loadByok());

  /**
   * 是否已经挂载到客户端。
   *
   * 依赖 localStorage 的部分（Key 表单、Key 状态条、不匹配提示）**必须**等挂载后才渲染：
   * 服务端读不到 localStorage，直接渲染会让两端 HTML 不一致 —— 这正是
   * 「服务端渲染不匹配提示、客户端渲染 Key 表单」那个 hydration 错误的成因。
   */
  const mounted = useSyncExternalStore(
    subscribeNothing,
    () => true,
    () => false,
  );
  const [providerId, setProviderId] = useState(providers[0]?.id ?? '');
  const provider = providers.find((p) => p.id === providerId) ?? providers[0];

  /**
   * 自定义端点（第三方中转平台）。
   *
   * 开启后，厂商选择器只决定**走哪套协议**（Anthropic 还是 OpenAI 兼容），
   * 实际的地址与模型名都由你自己填。这样以后换平台不用改代码。
   */
  const [useCustom, setUseCustom] = useState(false);
  const [customBaseUrl, setCustomBaseUrl] = useState('');
  const [customModel, setCustomModel] = useState('');

  const allowedModels = useMemo(
    () => lab.allowedModels.map((m) => m.model).filter((m) => provider?.models.includes(m)),
    [lab.allowedModels, provider],
  );
  const [model, setModel] = useState(allowedModels[0] ?? provider?.defaultModel ?? '');
  const [system, setSystem] = useState(lab.system?.content ?? '');
  const [input, setInput] = useState('');
  // 原始事件现在折叠在轨迹卡片里，不再需要单独的开关

  const apiKey = provider ? (getCredential(byok, provider.id) ?? '') : '';
  // 别的厂商有没有存过 Key —— 用于在「选错厂商」时给出可操作的提示
  const savedForOtherProvider = providers.find(
    (p) => p.id !== provider?.id && getCredential(byok, p.id),
  );
  const relay = useChatRelay();

  // provider 变化时，把模型切到该 provider 下可用的第一个
  useEffect(() => {
    if (!provider) return;
    const next = allowedModels[0] ?? provider.defaultModel;
    setModel(next);
  }, [provider, allowedModels]);

  if (!provider) {
    return (
      <div className="border-border text-muted-foreground rounded-lg border border-dashed p-6 text-sm">
        这个实验没有可用的模型配置。
      </div>
    );
  }

  // 自定义端点时用用户填的模型名，否则用下拉选中的
  const effectiveModel = useCustom ? customModel.trim() : model;

  const canRun =
    apiKey.length > 0 &&
    input.trim().length > 0 &&
    !relay.state.running &&
    // 自定义端点时必须先填地址与模型名，否则运行必然失败
    (!useCustom || (customBaseUrl.trim().length > 0 && effectiveModel.length > 0));

  const onRun = () => {
    void relay.run({
      provider: provider.id,
      model: effectiveModel,
      apiKey,
      baseUrl: useCustom ? customBaseUrl.trim() : undefined,
      system: system.trim() || undefined,
      messages: [{ role: 'user', content: input.trim() }],
      maxTokens: lab.defaults?.maxTokens,
    });
  };

  return (
    <section className="border-border bg-card not-prose overflow-hidden rounded-xl border">
      {/* 头部：实验目标 */}
      <header className="border-border border-b px-4 py-3">
        <h3 className="text-sm font-medium">{lab.title}</h3>
        <p className="text-muted-foreground mt-1 text-xs leading-relaxed">{lab.goal}</p>
        {lab.objectives.length > 0 && (
          <ul className="text-muted-foreground mt-2 space-y-1 text-xs">
            {lab.objectives.map((o) => (
              <li key={o} className="flex gap-2">
                <span aria-hidden className="text-muted-foreground/50">
                  —
                </span>
                <span>{o}</span>
              </li>
            ))}
          </ul>
        )}
      </header>

      {/* Key 未填时的引导。等挂载后再渲染 —— 见 mounted 的注释 */}
      {mounted && !apiKey && (
        <ApiKeyForm
          providers={providers}
          providerId={providerId}
          onProviderChange={setProviderId}
          provider={provider}
          mode={byok.mode}
          onSave={(key) => setByok(setCredential(byok, provider.id, key))}
          onModeChange={(m) => setByok(setMode(byok, m))}
        />
      )}

      {mounted && apiKey && (
        <div className="border-border flex flex-wrap items-center gap-2 border-b px-4 py-2 text-xs">
          <span className="text-muted-foreground">
            {provider.label} · Key {maskKey(apiKey)}
            {byok.mode === 'session' && ' · 仅本次会话'}
          </span>
          <button
            type="button"
            className="text-muted-foreground hover:text-foreground ml-auto underline-offset-2 hover:underline"
            onClick={() => setByok(setCredential(byok, provider.id, ''))}
          >
            清除
          </button>
        </div>
      )}

      {/* 选中的厂商没有 Key，但别的厂商填过 —— 这是最容易困惑的状态：
          填了 Key 却点不动运行按钮，而界面上没有任何解释 */}
      {mounted && !apiKey && savedForOtherProvider && (
        <div className="border-b border-amber-500/40 bg-amber-500/5 px-4 py-3 text-xs">
          <p className="text-muted-foreground leading-relaxed">
            当前厂商是「{provider.label}」，但你填过的是「{savedForOtherProvider.label}」的 Key。
            不同厂商的 Key 不能混用 —— 可以
            <button
              type="button"
              onClick={() => setProviderId(savedForOtherProvider.id)}
              className="text-foreground mx-1 font-medium underline underline-offset-2"
            >
              切到 {savedForOtherProvider.label}
            </button>
            ，或者填入当前厂商的 Key。
          </p>
        </div>
      )}

      {/* 配置区 */}
      {allowCustomEndpoint && (
        <div className="border-border border-b px-4 py-2">
          <label className="text-muted-foreground flex flex-wrap items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={useCustom}
              onChange={(e) => setUseCustom(e.target.checked)}
            />
            <span>使用自定义端点（第三方中转平台）</span>
            <span className="text-muted-foreground/70">
              勾选后，上面选的厂商只表示「走哪套协议」，地址与模型名由你填
            </span>
          </label>
        </div>
      )}

      <div className="border-border grid gap-3 border-b px-4 py-3 sm:grid-cols-2">
        <Field label={useCustom ? '协议（按你平台的文档选）' : '厂商'}>
          <select
            value={providerId}
            onChange={(e) => setProviderId(e.target.value)}
            className="border-border bg-background w-full rounded-md border px-2 py-1.5 text-xs"
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </Field>

        {useCustom ? (
          <Field label="模型名（按你平台的叫法填）">
            <input
              value={customModel}
              onChange={(e) => setCustomModel(e.target.value)}
              placeholder="例如 deepseek-chat"
              className="border-border bg-background w-full rounded-md border px-2 py-1.5 font-mono text-xs"
            />
          </Field>
        ) : (
          <Field label="模型">
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="border-border bg-background w-full rounded-md border px-2 py-1.5 text-xs"
            >
              {(allowedModels.length > 0 ? allowedModels : provider.models).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </Field>
        )}

        {useCustom && (
          <div className="sm:col-span-2">
            <Field label="端点地址（baseUrl）">
              <input
                value={customBaseUrl}
                onChange={(e) => setCustomBaseUrl(e.target.value)}
                placeholder="https://your-platform.com/v1"
                className="border-border bg-background w-full rounded-md border px-2 py-1.5 font-mono text-xs"
              />
            </Field>
            <p className="text-muted-foreground/70 mt-1.5 text-[11px] leading-relaxed">
              服务端会校验：必须 https、不能指向内网或云元数据地址。
              用 http 的话你的 Key 会明文传输，所以被拒绝了。
            </p>
          </div>
        )}

        <div className="sm:col-span-2">
          <Field label={lab.system?.locked ? 'system 提示（本实验锁定）' : 'system 提示（可修改）'}>
            <textarea
              value={system}
              onChange={(e) => setSystem(e.target.value)}
              disabled={lab.system?.locked}
              rows={3}
              className="border-border bg-background disabled:opacity-60 w-full resize-y rounded-md border px-2 py-1.5 font-mono text-xs leading-relaxed"
            />
          </Field>
        </div>
      </div>

      {/* 输入区 */}
      <div className="px-4 py-3">
        {lab.presets && lab.presets.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {lab.presets.map((p) => (
              <button
                key={p.label}
                type="button"
                title={p.hint}
                onClick={() =>
                  setInput(
                    p.messages
                      .map((m) => m.content.map((c) => (c.type === 'text' ? c.text : '')).join(''))
                      .join('\n\n'),
                  )
                }
                className="border-border text-muted-foreground hover:bg-muted hover:text-foreground rounded-md border px-2 py-1 text-xs transition-colors"
              >
                {p.label}
              </button>
            ))}
          </div>
        )}

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={2}
          placeholder="输入一句话，观察模型的完整响应过程"
          className="border-border bg-background w-full resize-y rounded-md border px-3 py-2 text-sm"
        />

        <div className="mt-2 flex items-center gap-2">
          <button
            type="button"
            onClick={onRun}
            disabled={!canRun}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              canRun
                ? 'bg-foreground text-background hover:opacity-90'
                : 'bg-muted text-muted-foreground cursor-not-allowed',
            )}
          >
            {relay.state.running ? '生成中…' : '运行'}
          </button>

          {relay.state.running && (
            <button
              type="button"
              onClick={relay.stop}
              className="border-border hover:bg-muted rounded-md border px-3 py-1.5 text-sm"
            >
              中断
            </button>
          )}

          {!apiKey && (
            <span className="text-muted-foreground text-xs">需要先填入你的 API Key</span>
          )}
        </div>
      </div>

      {/* 输出区 */}
      {(relay.state.text || relay.state.thinking || relay.state.error) && (
        <div className="border-border border-t px-4 py-3">
          {relay.state.error && (
            <div className="mb-3 rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-xs">
              <span className="font-medium text-amber-700 dark:text-amber-500">
                {relay.state.error.code}
              </span>
              <span className="text-muted-foreground ml-2">{relay.state.error.message}</span>
              {relay.state.error.code === 'unauthorized' && (
                <div className="text-muted-foreground mt-1.5 space-y-1 leading-relaxed">
                  <p>两种可能，按可能性排序：</p>
                  <ul className="ml-4 list-disc space-y-0.5">
                    <li>
                      <strong className="text-foreground/80 font-medium">Key 本身无效</strong>
                      　—— 复制不完整、已被吊销、或者不是「{provider.label}」的 Key
                    </li>
                    <li>
                      <strong className="text-foreground/80 font-medium">厂商选错了</strong>
                      　—— 在别家申请的 Key 用不到这里
                    </li>
                  </ul>
                  <p>
                    你当前这把 Key 的末尾四位是{' '}
                    <code className="bg-background rounded px-1 font-mono">
                      {apiKey.slice(-4)}
                    </code>
                    ，可以拿它跟厂商后台里的 Key 核对一下。
                  </p>
                </div>
              )}
              {relay.state.error.code === 'model_not_allowed' && (
                <p className="text-muted-foreground mt-1.5 leading-relaxed">
                  这个模型不在服务端的白名单里。白名单是为了防止中转端点被当成通用
                  LLM 代理使用（见 AGENTS.md 的安全模型）。
                </p>
              )}
            </div>
          )}

          {relay.state.thinking && (
            <details className="mb-3">
              <summary className="text-muted-foreground cursor-pointer text-xs">
                思考过程（{relay.state.thinking.length} 字符）
              </summary>
              <pre className="text-muted-foreground mt-2 max-h-60 overflow-auto text-xs whitespace-pre-wrap">
                {relay.state.thinking}
              </pre>
            </details>
          )}

          {relay.state.text && (
            <div className="text-sm leading-relaxed whitespace-pre-wrap">{relay.state.text}</div>
          )}

          <UsageBar usage={relay.state.usage} />
        </div>
      )}

      {/* 轨迹 */}
      {relay.state.trace.length > 0 && <TraceCards trace={relay.state.trace} />}
    </section>
  );
}

// ---------------------------------------------------------------------------

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-muted-foreground mb-1 block text-xs">{label}</span>
      {children}
    </label>
  );
}

function UsageBar({
  usage,
}: {
  usage: { inputTokens?: number; outputTokens?: number; cacheReadTokens?: number };
}) {
  const total = (usage.inputTokens ?? 0) + (usage.cacheReadTokens ?? 0) + (usage.outputTokens ?? 0);
  if (total === 0) return null;

  return (
    <div className="text-muted-foreground/70 mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-dashed pt-2 text-[11px]">
      <span>输入 {usage.inputTokens ?? 0}</span>
      {usage.cacheReadTokens ? <span>缓存命中 {usage.cacheReadTokens}</span> : null}
      <span>输出 {usage.outputTokens ?? 0}</span>
    </div>
  );
}

function ApiKeyForm({
  providers,
  providerId,
  onProviderChange,
  provider,
  mode,
  onSave,
  onModeChange,
}: {
  providers: ProviderOption[];
  providerId: string;
  onProviderChange: (id: string) => void;
  provider: ProviderOption;
  mode: ByokState['mode'];
  onSave: (key: string) => void;
  onModeChange: (m: ByokState['mode']) => void;
}) {
  const [draft, setDraft] = useState('');

  return (
    <div className="border-border bg-muted/30 border-b px-4 py-4">
      <p className="text-sm font-medium">填入你的 API Key 才能运行</p>

      {/* 厂商选择放在 Key 输入**之前** —— 顺序反了会让人填错：
          先填了 Key 才发现厂商选的是另一家，是最常见的困惑 */}
      <label className="mt-3 block">
        <span className="text-muted-foreground mb-1 block text-xs">
          1. 先选你要用哪家的模型（Key 要跟这里对应）
        </span>
        <select
          value={providerId}
          onChange={(e) => onProviderChange(e.target.value)}
          className="border-border bg-background w-full rounded-md border px-2 py-1.5 text-xs"
        >
          {providers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
      </label>

      <p className="text-muted-foreground mt-3 text-xs leading-relaxed">
        Key 只存在你的浏览器里。运行时它经本站服务器转发给模型厂商，
        <strong className="text-foreground font-medium">服务端不存储、不记录日志</strong>。
        建议用一把限额的、专用的 Key，用完随时吊销。
        {provider.keyHint && <> 申请地址：{provider.keyHint}</>}
      </p>

      <label className="mt-3 block">
        <span className="text-muted-foreground mb-1 block text-xs">
          2. 粘贴 {provider.label} 的 API Key
        </span>
        <div className="flex flex-wrap gap-2">
          <input
            type="password"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="粘贴 API Key"
            className="border-border bg-background min-w-0 flex-1 rounded-md border px-2 py-1.5 font-mono text-xs"
          />
          <button
            type="button"
            disabled={draft.trim().length === 0}
            onClick={() => onSave(draft.trim())}
            className="bg-foreground text-background rounded-md px-3 py-1.5 text-xs font-medium disabled:opacity-40"
          >
            保存
          </button>
        </div>
      </label>

      <label className="text-muted-foreground mt-3 flex items-start gap-2 text-xs">
        <input
          type="checkbox"
          className="mt-0.5"
          checked={mode === 'session'}
          onChange={(e) => onModeChange(e.target.checked ? 'session' : 'persistent')}
        />
        <span>
          仅本次会话（不写入 localStorage，关闭标签页即失效）
          <span className="text-muted-foreground/70 block">在共享电脑上建议勾选。</span>
        </span>
      </label>
    </div>
  );
}

/** 扁平事件流折叠后的结构 */
interface FoldedTrace {
  thinking: string;
  text: string;
  toolCalls: { index: number; id: string; name: string; argsText: string; input?: unknown }[];
  usage: { inputTokens?: number; outputTokens?: number; cacheReadTokens?: number };
  stopReason?: string;
  durationMs?: number;
  rawCount: number;
  total: number;
}

/**
 * 把扁平的事件流折叠成结构化的轨迹。
 *
 * 为什么要折叠：原始事件流是**协议层**的样子（几十上百个 delta），
 * 而人想看的是**语义层**的东西 —— 模型想了什么、说了什么、调了什么工具。
 * 两者都需要，但顺序应该是「先给语义、再给协议」。
 */
function foldTrace(trace: { event: unknown }[]): FoldedTrace {
  const out: FoldedTrace = {
    thinking: '',
    text: '',
    toolCalls: [],
    usage: {},
    rawCount: 0,
    total: trace.length,
  };
  const byIndex = new Map<number, FoldedTrace['toolCalls'][number]>();

  for (const entry of trace) {
    const ev = entry.event as { type: string; [k: string]: unknown };
    switch (ev.type) {
      case 'thinking':
        out.thinking += String(ev.delta ?? '');
        break;
      case 'text':
        out.text += String(ev.delta ?? '');
        break;
      case 'tool_call': {
        const rec = {
          index: Number(ev.index),
          id: String(ev.id ?? ''),
          name: String(ev.name ?? ''),
          argsText: '',
        };
        byIndex.set(rec.index, rec);
        out.toolCalls.push(rec);
        break;
      }
      case 'tool_args': {
        const rec = byIndex.get(Number(ev.index));
        if (rec) rec.argsText += String(ev.delta ?? '');
        break;
      }
      case 'tool_call_end': {
        const rec = byIndex.get(Number(ev.index));
        if (rec) rec.input = ev.input;
        break;
      }
      case 'usage':
        out.usage = {
          inputTokens: (ev.inputTokens as number) ?? out.usage.inputTokens,
          outputTokens: (ev.outputTokens as number) ?? out.usage.outputTokens,
          cacheReadTokens: (ev.cacheReadTokens as number) ?? out.usage.cacheReadTokens,
        };
        break;
      case 'stop_reason':
        out.stopReason = String(ev.stopReason ?? '');
        break;
      case 'done':
        out.durationMs = Number(ev.durationMs);
        break;
      case 'raw':
        out.rawCount += 1;
        break;
    }
  }
  return out;
}

/**
 * 轨迹卡片视图 —— 实验的核心价值所在。
 *
 * 先给语义（思考 / 工具调用 / 输出），原始事件折叠在最后。这样默认视图能读懂，
 * 需要核对时又能下钻到协议层。教学上这两层缺一不可：
 * 只有语义层就成了黑盒，只有协议层就看不懂全局。
 */
function TraceCards({ trace }: { trace: TraceEntry[] }) {
  const t = foldTrace(trace);
  if (t.total === 0) return null;

  const summaryParts = [
    t.thinking && '思考',
    t.toolCalls.length > 0 && `${t.toolCalls.length} 次工具调用`,
    t.text && '输出',
  ].filter(Boolean) as string[];

  return (
    <div className="border-border border-t">
      <div className="border-border flex flex-wrap items-baseline gap-2 border-b px-4 py-2">
        <span className="text-xs font-medium">轨迹</span>
        <span className="text-muted-foreground/70 text-[11px]">
          {summaryParts.join(' + ') || '无内容'}
          {t.durationMs != null && ` · 耗时 ${t.durationMs}ms`}
        </span>
      </div>

      <div className="space-y-2 p-4">
        {/* 思考过程 */}
        {t.thinking && (
          <details className="border-border bg-muted/30 group rounded-lg border">
            <summary className="flex cursor-pointer list-none items-baseline gap-2 px-3 py-2 text-xs marker:hidden">
              <span
                aria-hidden
                className="text-muted-foreground/40 transition-transform group-open:rotate-90"
              >
                ▸
              </span>
              <span className="font-medium">思考过程</span>
              <span className="text-muted-foreground/60 ml-auto">{t.thinking.length} 字符</span>
            </summary>
            <pre className="border-border text-muted-foreground overflow-x-auto border-t px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap">
              {t.thinking}
            </pre>
          </details>
        )}

        {/* 工具调用：参数与结果并排 */}
        {t.toolCalls.map((tc) => (
          <div key={tc.index} className="overflow-hidden rounded-lg border border-sky-500/30">
            <div className="flex items-baseline gap-2 border-b border-sky-500/20 bg-sky-500/5 px-3 py-2 text-xs">
              <span className="font-mono font-medium text-sky-700 dark:text-sky-400">
                {tc.name}
              </span>
              <span className="text-muted-foreground/50 ml-auto font-mono text-[10px]">
                {tc.id.slice(0, 24)}
              </span>
            </div>
            <div className="grid sm:grid-cols-2">
              <div className="border-border border-b p-3 sm:border-r sm:border-b-0">
                <p className="text-muted-foreground/60 mb-1 text-[10px] tracking-wide uppercase">
                  参数
                </p>
                <pre className="text-muted-foreground overflow-x-auto font-mono text-[11px]">
                  {tc.input !== undefined
                    ? JSON.stringify(tc.input, null, 2)
                    : tc.argsText || '（无参数）'}
                </pre>
              </div>
              <div className="p-3">
                <p className="text-muted-foreground/60 mb-1 text-[10px] tracking-wide uppercase">
                  结果
                </p>
                <p className="text-muted-foreground text-[11px] leading-relaxed">
                  本站实验暂不执行工具，只展示模型的调用意图与参数。
                  工具的实际执行与结果回填是第 4 章的内容。
                </p>
              </div>
            </div>
          </div>
        ))}

        {/* 模型输出 */}
        {t.text && (
          <div className="border-border bg-card rounded-lg border p-3">
            <p className="text-muted-foreground/60 mb-1.5 text-[10px] tracking-wide uppercase">
              模型输出
            </p>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{t.text}</p>
          </div>
        )}

        {/* 用量 */}
        <div className="text-muted-foreground/70 flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
          <span>输入 {t.usage.inputTokens ?? '-'}</span>
          {t.usage.cacheReadTokens ? <span>缓存命中 {t.usage.cacheReadTokens}</span> : null}
          <span>输出 {t.usage.outputTokens ?? '-'}</span>
          {t.stopReason && <span>停止原因 {t.stopReason}</span>}
        </div>

        {/* 原始事件：折叠在最后。教学上你需要能核对「语义层与协议层对不对得上」 */}
        {t.total > 0 && (
          <details className="border-border group rounded-lg border border-dashed">
            <summary className="text-muted-foreground flex cursor-pointer list-none items-baseline gap-2 px-3 py-2 text-xs marker:hidden">
              <span
                aria-hidden
                className="text-muted-foreground/40 transition-transform group-open:rotate-90"
              >
                ▸
              </span>
              <span>原始事件（协议层）</span>
              <span className="text-muted-foreground/60 ml-auto">{t.total} 个</span>
            </summary>
            <ol className="border-border max-h-72 overflow-y-auto border-t">
              {trace.map((entry) => {
                const ev = entry.event as { type: string; [k: string]: unknown };
                return (
                  <li key={entry.id} className="border-border/40 border-b last:border-0">
                    <details>
                      <summary className="hover:bg-muted/40 flex cursor-pointer list-none gap-2 px-3 py-1 text-[11px] marker:hidden">
                        <span className="text-muted-foreground/40 w-7 shrink-0 font-mono tabular-nums">
                          {String(entry.seq).padStart(3, '0')}
                        </span>
                        <span className={cn('w-20 shrink-0 font-mono', eventTone(ev.type))}>
                          {ev.type}
                        </span>
                        <span className="text-muted-foreground min-w-0 flex-1 truncate font-mono">
                          {summarize(ev)}
                        </span>
                      </summary>
                      <pre className="bg-muted/40 text-muted-foreground overflow-x-auto px-3 py-2 pl-12 font-mono text-[10px] leading-relaxed">
                        {JSON.stringify(ev, null, 2)}
                      </pre>
                    </details>
                  </li>
                );
              })}
            </ol>
          </details>
        )}
      </div>
    </div>
  );
}

function eventTone(type: string): string {
  switch (type) {
    case 'text':
    case 'thinking':
      return 'text-emerald-700 dark:text-emerald-500';
    case 'tool_call':
    case 'tool_args':
    case 'tool_call_end':
      return 'text-sky-700 dark:text-sky-400';
    case 'error':
      return 'text-amber-700 dark:text-amber-500';
    case 'usage':
    case 'stop_reason':
    case 'done':
      return 'text-muted-foreground';
    default:
      return 'text-muted-foreground/60';
  }
}

/** 换行会破坏单行摘要的布局，用可见符号代替 */
function oneLine(s: string): string {
  return s.replace(/\n/g, '⏎');
}

/**
 * 把事件压成一行摘要。
 *
 * 文本类事件**直接显示内容**而不是 JSON 转义 —— 后者满是 `\n` 与 `\"`，
 * 一眼看不出模型说了什么。想看原始结构的话，展开那一行就是完整 JSON。
 */
function summarize(ev: { type: string; [k: string]: unknown }): string {
  switch (ev.type) {
    case 'text':
      return oneLine(String(ev.delta));
    case 'thinking':
      return oneLine(String(ev.delta)).slice(0, 70);
    case 'tool_call':
      return `${ev.name}(index ${ev.index})`;
    case 'tool_args':
      return oneLine(String(ev.delta));
    case 'tool_call_end':
      return JSON.stringify(ev.input);
    case 'usage':
      return `输入 ${ev.inputTokens ?? '-'} · 输出 ${ev.outputTokens ?? '-'}${
        ev.cacheReadTokens ? ` · 缓存命中 ${ev.cacheReadTokens}` : ''
      }`;
    case 'stop_reason':
      return String(ev.stopReason);
    case 'raw':
      return oneLine(String(ev.line)).slice(0, 120);
    case 'error':
      return `${ev.code}: ${ev.message}`;
    case 'done':
      return `耗时 ${ev.durationMs}ms`;
    case 'start':
      return `${ev.provider} / ${ev.model}`;
    default:
      return '';
  }
}
