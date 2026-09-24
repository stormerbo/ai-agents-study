import createMDX from '@next/mdx';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // 让 Next 把 .mdx 视为可路由的页面扩展名。注意只有 app/ 下的 MDX 会成为路由；
  // content/ 下的正文通过 import 加载，不受此影响。
  pageExtensions: ['ts', 'tsx', 'js', 'jsx', 'mdx'],

  // Turbopack 会向上寻找项目根，而本机主目录（~/）下存在无关的
  // package-lock.json，导致它把根推断到仓库之外并在每次构建时警告。
  // 显式钉死：只有此目录之上的文件才会被 Turbopack 解析。
  turbopack: {
    root: process.cwd(),
  },
};

/**
 * MDX 配置。
 *
 * ⚠️ 关键约束：Turbopack 下 remark / rehype 插件必须写成**字符串名**，
 * 不能传函数引用 —— 因为 JS 函数无法传给 Rust 侧。这同时意味着依赖函数实例的
 * transformer（如 @shikijs/transformers 的 diff 标记高亮）在这里用不了。
 *
 * 另一个已知限制：@next/mdx 默认不处理 frontmatter，这里用 remark-frontmatter
 * 让它在解析时被识别而不被当成正文渲染。章节元数据本来也不放在 frontmatter 里
 * （见 CONTENT_GUIDE.md：元数据全在 meta.ts），所以只需让它别渲染出来即可。
 */
const withMDX = createMDX({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: ['remark-frontmatter', 'remark-gfm'],
    rehypePlugins: [
      'rehype-slug',
      [
        'rehype-autolink-headings',
        { behavior: 'wrap', properties: { className: ['heading-anchor'] } },
      ],
      [
        'rehype-pretty-code',
        {
          theme: { light: 'github-light', dark: 'github-dark' },
          // 背景交给 Tailwind，双主题靠 CSS 变量切换（见 globals.css）
          keepBackground: false,
        },
      ],
    ],
  },
});

export default withMDX(nextConfig);
