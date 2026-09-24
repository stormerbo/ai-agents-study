import Link from 'next/link';

import type { Chapter, Stage } from '@/content/curriculum/schema';
import {
  HEADER_HEIGHT,
  NODE_HEIGHT,
  NODE_WIDTH,
  computeMapLayout,
  truncateTitle,
} from '@/lib/map/layout';

/**
 * 知识地图。
 *
 * 整张图是服务端渲染的静态 SVG：零客户端 JS、节点是真的链接
 * （可点击、可 Tab 聚焦、可被搜索引擎抓取），深色模式靠 CSS 变量。
 *
 * 窄屏下容器横向滚动。这张图在手机上本来就不适合精读 ——
 * 首页的阶段列表是它的等价文本视图。
 */
export function KnowledgeMap({ chapters, stages }: { chapters: Chapter[]; stages: Stage[] }) {
  const layout = computeMapLayout(chapters, stages);

  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-card p-4">
      <svg
        viewBox={`0 0 ${layout.width + 8} ${layout.height + 8}`}
        width={layout.width + 8}
        height={layout.height + 8}
        role="img"
        aria-label="AI Agent 学习路径知识地图，按阶段从左到右排列"
        className="max-w-none"
      >
        <defs>
          <marker
            id="map-arrow"
            viewBox="0 0 8 8"
            refX="7"
            refY="4"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 8 4 L 0 8 z" className="fill-border" />
          </marker>
        </defs>

        {/* 阶段标题 */}
        {layout.columns.map((column) => (
          <g key={column.stage.id}>
            <text
              x={column.x + 4}
              y={22}
              className="fill-muted-foreground text-[11px] tracking-wide"
            >
              阶段 {column.stage.order} · {column.stage.title}
            </text>
            {column.chapters.length === 0 && (
              <text
                x={column.x + 4}
                y={HEADER_HEIGHT + 26}
                className="fill-muted-foreground/50 text-[11px]"
              >
                内容建设中
              </text>
            )}
          </g>
        ))}

        {/* 依赖连线。画在节点下层，避免压住文字 */}
        <g>
          {layout.edges.map((edge) => (
            <path
              key={edge.id}
              d={edge.path}
              fill="none"
              strokeWidth={1.25}
              markerEnd="url(#map-arrow)"
              className="stroke-border"
            />
          ))}
        </g>

        {/* 章节节点 */}
        {layout.nodes.map((node) => {
          const { chapter } = node;
          const hasBody = chapter.lessons.some((l) => l.hasBody);

          return (
            <g key={chapter.id}>
              <Link href={`/chapters/${chapter.id}`}>
                <title>{`${chapter.title} —— ${chapter.summary}`}</title>
                <rect
                  x={node.x}
                  y={node.y}
                  width={NODE_WIDTH}
                  height={NODE_HEIGHT}
                  rx={10}
                  strokeWidth={1}
                  className="fill-background stroke-border transition-colors hover:stroke-accent"
                />
                {/* 有正文的章用一条左侧色条标记，一眼看出哪些能读 */}
                {hasBody && (
                  <rect
                    x={node.x}
                    y={node.y + 12}
                    width={3}
                    height={NODE_HEIGHT - 24}
                    rx={1.5}
                    className="fill-accent"
                  />
                )}
                <text
                  x={node.x + 14}
                  y={node.y + 24}
                  className="fill-muted-foreground font-mono text-[10px] tabular-nums"
                >
                  {String(chapter.order).padStart(2, '0')}
                  {!hasBody && ' · 待写'}
                </text>
                <text x={node.x + 14} y={node.y + 45} className="fill-foreground text-[13px]">
                  {truncateTitle(chapter.title, 12)}
                </text>
              </Link>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
