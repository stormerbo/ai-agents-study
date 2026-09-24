import { describe, expect, it } from 'vitest';

import { createSSEDecoder, encodeSSE, encodeSSEComment } from '@/lib/llm/sse';

/**
 * SSE 编解码测试。
 *
 * 这些不是形式化的覆盖率测试 —— 它们对应真实的失败模式：
 * 网络分片不会按事件边界对齐，一次 read 可能拿到半个事件，
 * 也可能一次拿到三个半。分帧写错的表现是「平时都对，偶尔少一段」，
 * 那种 bug 在生产里极难定位。
 */

describe('编码', () => {
  it('具名事件', () => {
    expect(encodeSSE('text', { delta: '你好' })).toBe('event: text\ndata: {"delta":"你好"}\n\n');
  });

  it('注释帧以冒号开头（不会被当成事件）', () => {
    expect(encodeSSEComment('ping')).toBe(': ping\n\n');
  });
});

describe('解码', () => {
  it('解析单个完整事件', () => {
    const d = createSSEDecoder();
    expect(d.push('event: text\ndata: {"delta":"a"}\n\n')).toEqual([
      { event: 'text', data: '{"delta":"a"}' },
    ]);
  });

  it('一次推入多个事件', () => {
    const d = createSSEDecoder();
    const messages = d.push(
      'event: a\ndata: 1\n\n' + 'event: b\ndata: 2\n\n' + 'event: c\ndata: 3\n\n',
    );
    expect(messages.map((m) => m.event)).toEqual(['a', 'b', 'c']);
  });

  it('跨分片：事件被切成两半时不会提前产出', () => {
    const d = createSSEDecoder();
    // 第一片只到一半
    expect(d.push('event: text\ndata: {"del')).toEqual([]);
    // 第二片补全
    expect(d.push('ta":"a"}\n\n')).toEqual([{ event: 'text', data: '{"delta":"a"}' }]);
  });

  it('跨分片：恰好切在空行中间', () => {
    const d = createSSEDecoder();
    expect(d.push('event: text\ndata: x\n')).toEqual([]);
    expect(d.push('\nevent: text\ndata: y\n\n')).toEqual([
      { event: 'text', data: 'x' },
      { event: 'text', data: 'y' },
    ]);
  });

  it('多行 data 用换行连接', () => {
    const d = createSSEDecoder();
    expect(d.push('event: text\ndata: line1\ndata: line2\n\n')).toEqual([
      { event: 'text', data: 'line1\nline2' },
    ]);
  });

  it('忽略注释帧（心跳）', () => {
    const d = createSSEDecoder();
    expect(d.push(': ping\n\n')).toEqual([]);
    expect(d.push(': ping\nevent: text\ndata: x\n\n')).toEqual([{ event: 'text', data: 'x' }]);
  });

  it('兼容 \\r\\n 换行', () => {
    const d = createSSEDecoder();
    expect(d.push('event: text\r\ndata: x\r\n\r\n')).toEqual([{ event: 'text', data: 'x' }]);
  });

  it('没有 event 行时默认为 message', () => {
    const d = createSSEDecoder();
    expect(d.push('data: x\n\n')).toEqual([{ event: 'message', data: 'x' }]);
  });

  it('data 冒号后只移除一个空格，多余的前导空格保留', () => {
    const d = createSSEDecoder();
    expect(d.push('event: t\ndata:  两个前导空格\n\n')).toEqual([
      { event: 't', data: ' 两个前导空格' },
    ]);
  });

  it('flush 处理未以空行结尾的尾部', () => {
    const d = createSSEDecoder();
    expect(d.push('event: text\ndata: tail')).toEqual([]);
    expect(d.flush()).toEqual([{ event: 'text', data: 'tail' }]);
    // flush 后缓冲区应清空
    expect(d.flush()).toEqual([]);
  });

  it('空块不产出事件', () => {
    const d = createSSEDecoder();
    expect(d.push('\n\n\n\n')).toEqual([]);
  });
});

describe('往返一致性', () => {
  it('编码后解码得到原事件', () => {
    const d = createSSEDecoder();
    const payload = { type: 'text', delta: '包含 "引号" 和 \\反斜杠 与换行\n' };
    const messages = d.push(encodeSSE('text', payload) + encodeSSEComment('ping'));
    expect(messages).toHaveLength(1);
    expect(messages[0]!.event).toBe('text');
    expect(JSON.parse(messages[0]!.data)).toEqual(payload);
  });

  it('把一整段流按随机切分喂入，结果与整体喂入相同', () => {
    const full =
      encodeSSE('start', { model: 'x' }) +
      encodeSSE('text', { delta: '你' }) +
      encodeSSEComment('ping') +
      encodeSSE('text', { delta: '好' }) +
      encodeSSE('done', { ms: 12 });

    const expected = createSSEDecoder().push(full);

    // 按 7 个字符一段切开（刻意不落在任何边界上）
    const chunked = createSSEDecoder();
    const got: unknown[] = [];
    for (let i = 0; i < full.length; i += 7) {
      got.push(...chunked.push(full.slice(i, i + 7)));
    }
    got.push(...chunked.flush());

    expect(got).toEqual(expected);
    expect(expected.map((m) => m.event)).toEqual(['start', 'text', 'text', 'done']);
  });
});
