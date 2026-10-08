import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { InlineMd, plainText } from '@/components/ui/inline-md';

const render = (text: string) => renderToStaticMarkup(createElement(InlineMd, { text }));

describe('InlineMd 渲染契约', () => {
  // 这一组守卫的来历（AGENTS.md §4.15）：InlineMd 曾经返回 Fragment，
  // 而调用方的父容器常是 flex（章节日里的「可以直接迁移 / 会失效的直觉」
  // 列表用 flex 排版）。Fragment 的多个子节点会各自成为一个 flex item，
  // 把一句完整的话拆成并排的三列，文字交错、完全读不通。
  //
  // 修法是让它返回单个 <span>。这条断言就是那次修复的形状。
  it('只返回一个顶层元素（否则在 flex/grid 父容器里会被拆成并排几列）', () => {
    const html = render('把上下文窗口当成内存：**放进去不等于读得到**，中间部分最容易被忽略');

    expect(html.startsWith('<span>')).toBe(true);
    expect(html.endsWith('</span>')).toBe(true);
    // 老实现会输出 `文本<strong>粗体</strong>文本` —— 三个顶层节点，无外层 span
    expect(html).toContain('<strong');
  });

  it('粗体与行内代码都能渲染，且不残留字面标记', () => {
    const html = render('用 `temperature` 控制，**不要随手调**');

    expect(html).toContain('<code');
    expect(html).toContain('<strong');
    expect(html).toContain('temperature');
    expect(html).not.toContain('**');
    expect(html).not.toContain('`');
  });

  it('没有标记时也包一层 span（结构一致，父容器行为可预测）', () => {
    const html = render('一句普通的话');
    expect(html).toBe('<span>一句普通的话</span>');
  });

  it('空值返回 null', () => {
    expect(renderToStaticMarkup(createElement(InlineMd, { text: null }))).toBe('');
    expect(renderToStaticMarkup(createElement(InlineMd, { text: '' }))).toBe('');
  });

  it('plainText 去掉标记，用于 <title> 这类不能放 JSX 的位置', () => {
    expect(plainText('把**重点**去掉')).toBe('把重点去掉');
    expect(plainText('用 `code` 时')).toBe('用 code 时');
    expect(plainText(null)).toBe('');
  });
});
