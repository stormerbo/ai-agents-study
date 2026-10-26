import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

describe('first read-only agent path', () => {
  it('provides a staged route from API and prompt basics to the minimal loop', () => {
    const content = readFileSync('src/content/chapters/what-is-an-agent/04-how-to-use-this-site.mdx', 'utf8');
    expect(content).toContain('第一轮动手路径');
    expect(content.indexOf('llm-api-basics/messages-api')).toBeLessThan(content.indexOf('prompt-engineering/instruction-clarity'));
    expect(content.indexOf('prompt-engineering/instruction-clarity')).toBeLessThan(content.indexOf('tool-calling/what-really-happens'));
    expect(content.indexOf('tool-calling/what-really-happens')).toBeLessThan(content.indexOf('agent-loop/minimal-loop'));
    expect(content).toContain('只读订单 fixture');
  });

  it('shows explicit output and round limits in the registered first-loop exercise', () => {
    const manifest = readFileSync('examples/manifest.json', 'utf8');
    const registered = manifest.includes('first-loop-readonly-support');
    expect(registered).toBe(true);
    if (!registered) return;
    const source = readFileSync('examples/first-loop/readonly_support.py', 'utf8');
    expect(source).toContain('MAX_OUTPUT_TOKENS = 512');
    expect(source).toContain('MAX_ROUNDS = 4');
    expect(source).toContain('def lookup_order');
    expect(source).toContain('stop_reason');
  });

  it('states the minimal-loop lesson prerequisites and scope limits', () => {
    const lesson = readFileSync('src/content/chapters/agent-loop/01-minimal-loop.mdx', 'utf8');
    expect(lesson).toContain('短路径前置');
    expect(lesson).toContain('不包含身份认证、持久化恢复或写工具');
  });
});

