/**
 * Server-Sent Events 编解码。
 *
 * 刻意做成**同构**的：不引用任何 Node 专属 API，服务端用它编码、
 * 浏览器用它解码，共用同一份实现。这不是为了炫技 —— 第 8 章要讲的
 * 「浏览器直连模式」需要在前端解析上游 SSE，如果这里依赖了 Node API，
 * 那部分代码就得写第二遍。
 *
 * 解码器是增量式的，因为网络分片不会按事件边界对齐：
 * 一次 read 可能拿到半个事件，也可能一次拿到三个半。
 */

export interface SSEMessage {
  /** 事件名。没有 `event:` 行时按 SSE 规范默认为 `message` */
  event: string;
  /** 多行 data 按规范用 \n 连接 */
  data: string;
}

/** 编码一个具名事件 */
export function encodeSSE(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

/**
 * 编码一个注释帧。
 * SSE 的注释不会被客户端当成事件，但能保持连接活跃 —— 用来做心跳，
 * 防止中间的代理在长时间无数据时掐断连接。
 */
export function encodeSSEComment(text: string): string {
  return `: ${text}\n\n`;
}

/**
 * 增量解码器。
 *
 * 用法：
 *   const decoder = createSSEDecoder();
 *   for await (const chunk of stream) {
 *     for (const msg of decoder.push(chunk)) { ... }
 *   }
 */
export function createSSEDecoder() {
  let buffer = '';

  return {
    push(chunk: string): SSEMessage[] {
      // 兼容 \r\n 与 \r 两种换行（规范允许，实践中也真的会遇到）
      buffer += chunk.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

      const messages: SSEMessage[] = [];
      let boundary = buffer.indexOf('\n\n');

      while (boundary !== -1) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        const parsed = parseBlock(block);
        if (parsed) messages.push(parsed);

        boundary = buffer.indexOf('\n\n');
      }

      return messages;
    },

    /** 流结束时调用，处理最后一个没有以空行结尾的事件 */
    flush(): SSEMessage[] {
      if (buffer.trim() === '') {
        buffer = '';
        return [];
      }
      const parsed = parseBlock(buffer);
      buffer = '';
      return parsed ? [parsed] : [];
    },
  };
}

/** 解析一个事件块（已按空行切分） */
function parseBlock(block: string): SSEMessage | null {
  let event = 'message';
  const dataLines: string[] = [];

  for (const line of block.split('\n')) {
    // 注释行（心跳）直接跳过
    if (line.startsWith(':')) continue;

    if (line.startsWith('event:')) {
      event = line.slice('event:'.length).trim();
    } else if (line.startsWith('data:')) {
      // 规范：冒号后若有一个空格应被移除，但其余前导空格保留
      const value = line.slice('data:'.length);
      dataLines.push(value.startsWith(' ') ? value.slice(1) : value);
    }
    // 其他字段（id: / retry:）本场景用不到，忽略
  }

  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join('\n') };
}
