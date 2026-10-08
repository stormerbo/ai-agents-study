'use client';

import { useCallback, useRef, useState } from 'react';

import { createSSEDecoder } from '@/lib/llm/sse';
import type { NormalizedEvent } from '@/lib/llm/types';

/**
 * 调用本站 BYOK 中转端点的客户端 hook。
 *
 * ## 为什么循环在客户端
 *
 * 服务端只做**无状态转发**（见 /api/chat），不保存任何会话。带来三个好处：
 *
 * 1. 服务端不需要会话存储，天然可水平扩展
 * 2. 每一次请求、工具调用、结果回填都发生在浏览器里 —— 轨迹可视化是自然的副产品
 * 3. Key 只在客户端持有，每次请求随带
 *
 * 代价是每一轮多一次网络往返。对教学实验完全可以接受。
 *
 * ## 轨迹（trace）
 *
 * 所有事件都被记录下来，而不只是最终文本。这是本站实验的核心价值：
 * **看到模型到底做了什么**，而不只是它说了什么。
 */

export interface TraceEntry {
  id: string;
  /** 事件序号，用于稳定排序 */
  seq: number;
  at: number;
  event: NormalizedEvent;
}

export interface RelayState {
  running: boolean;
  /** 累积的可见文本 */
  text: string;
  /** 累积的思考内容 */
  thinking: string;
  trace: TraceEntry[];
  error?: { code: string; message: string };
  usage: { inputTokens?: number; outputTokens?: number; cacheReadTokens?: number };
}

const INITIAL: RelayState = {
  running: false,
  text: '',
  thinking: '',
  trace: [],
  usage: {},
};

export interface RunOptions {
  provider: string;
  model: string;
  apiKey: string;
  /** 自定义端点地址（第三方中转平台）。不传则用服务端注册表里的地址。 */
  baseUrl?: string;
  system?: string;
  messages: { role: 'user' | 'assistant'; content: unknown }[];
  maxTokens?: number;
  effort?: string;
}

export function useChatRelay() {
  const [state, setState] = useState<RelayState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);
  const seqRef = useRef(0);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setState((s) => ({ ...s, running: false }));
  }, []);

  const reset = useCallback(() => {
    setState(INITIAL);
    seqRef.current = 0;
  }, []);

  const run = useCallback(async (opts: RunOptions) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    seqRef.current = 0;

    setState({ ...INITIAL, running: true });

    const push = (event: NormalizedEvent) => {
      setState((s) => ({
        ...s,
        trace: [...s.trace, { id: `${seqRef.current}`, seq: seqRef.current++, at: Date.now(), event }],
      }));
    };

    let response: Response;
    try {
      response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          // Key 走请求头，不走请求体 —— 请求体更容易被中间层记录
          'x-byok-key': opts.apiKey,
        },
        body: JSON.stringify({
          provider: opts.provider,
          model: opts.model,
          baseUrl: opts.baseUrl,
          system: opts.system,
          messages: opts.messages,
          maxTokens: opts.maxTokens,
          effort: opts.effort,
        }),
        signal: controller.signal,
      });
    } catch (err) {
      if (controller.signal.aborted) return;
      setState((s) => ({
        ...s,
        running: false,
        error: { code: 'network_error', message: describe(err) },
      }));
      return;
    }

    // 首字节之前失败 —— 服务端返回的是真实状态码 + JSON
    if (!response.ok || !response.headers.get('content-type')?.includes('event-stream')) {
      let code = 'unknown';
      let message = `HTTP ${response.status}`;
      try {
        const body = (await response.json()) as { code?: string; message?: string };
        if (body.code) code = body.code;
        if (body.message) message = body.message;
      } catch {
        /* 保持默认 */
      }
      setState((s) => ({ ...s, running: false, error: { code, message } }));
      return;
    }

    // 流式解析
    const reader = response.body?.getReader();
    if (!reader) {
      setState((s) => ({ ...s, running: false, error: { code: 'no_body', message: '响应没有 body' } }));
      return;
    }

    const textDecoder = new TextDecoder();
    const sse = createSSEDecoder();

    const handle = (name: string, data: string) => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(data);
      } catch {
        return;
      }
      const ev = parsed as NormalizedEvent;

      push(ev);

      if (ev.type === 'text') {
        setState((s) => ({ ...s, text: s.text + ev.delta }));
      } else if (ev.type === 'thinking') {
        setState((s) => ({ ...s, thinking: s.thinking + ev.delta }));
      } else if (ev.type === 'usage') {
        setState((s) => ({
          ...s,
          usage: {
            inputTokens: ev.inputTokens ?? s.usage.inputTokens,
            outputTokens: ev.outputTokens ?? s.usage.outputTokens,
            cacheReadTokens: ev.cacheReadTokens ?? s.usage.cacheReadTokens,
          },
        }));
      } else if (ev.type === 'error') {
        setState((s) => ({ ...s, error: { code: ev.code, message: ev.message } }));
      }
    };

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const msg of sse.push(textDecoder.decode(value, { stream: true }))) {
          handle(msg.event, msg.data);
        }
      }
      for (const msg of sse.flush()) handle(msg.event, msg.data);
    } catch (err) {
      if (!controller.signal.aborted) {
        setState((s) => ({ ...s, error: { code: 'stream_error', message: describe(err) } }));
      }
    } finally {
      setState((s) => ({ ...s, running: false }));
      abortRef.current = null;
    }
  }, []);

  return { state, run, stop, reset };
}

function describe(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}
