import type { Chapter, Stage } from '@/content/curriculum/schema';

/**
 * 知识地图的布局计算 —— 纯函数，没有 DOM、没有 React。
 *
 * 为什么自绘而不引 Mermaid / React Flow：
 * - 这张图是**固定且精心编排的**（6 个阶段横排、阶段内按学习顺序纵排），
 *   自动布局算法在这里只会帮倒忙；
 * - 节点必须是真的链接（可点、可键盘 Tab、可被搜索引擎抓到），
 *   图形库的节点是画出来的图元，做不到；
 * - 纯函数 + 服务端渲染意味着整张图零客户端 JS。
 */

export const NODE_WIDTH = 208;
export const NODE_HEIGHT = 62;
export const COLUMN_GAP = 44;
export const ROW_GAP = 16;
export const HEADER_HEIGHT = 40;
/** 同列节点之间连线的水平偏移，避免箭头压在节点边框上 */
const SAME_COLUMN_OFFSET = 18;

export interface MapNode {
  chapter: Chapter;
  x: number;
  y: number;
}

export interface MapEdge {
  id: string;
  fromId: string;
  toId: string;
  /** SVG path 的 d 属性 */
  path: string;
}

export interface MapColumn {
  stage: Stage;
  x: number;
  chapters: Chapter[];
}

export interface MapLayout {
  nodes: MapNode[];
  edges: MapEdge[];
  columns: MapColumn[];
  width: number;
  height: number;
}

/** 三次贝塞尔：从起点水平出发、到终点水平进入 */
function curve(x1: number, y1: number, x2: number, y2: number): string {
  const dx = Math.max(24, (x2 - x1) / 2);
  return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}

export function computeMapLayout(chapters: Chapter[], stages: Stage[]): MapLayout {
  const sortedStages = [...stages].sort((a, b) => a.order - b.order);

  const columns: MapColumn[] = sortedStages.map((stage, index) => ({
    stage,
    x: index * (NODE_WIDTH + COLUMN_GAP),
    chapters: chapters.filter((c) => c.stageId === stage.id).sort((a, b) => a.order - b.order),
  }));

  const nodes: MapNode[] = [];
  const nodeById = new Map<string, MapNode>();

  for (const column of columns) {
    column.chapters.forEach((chapter, rowIndex) => {
      const node: MapNode = {
        chapter,
        x: column.x,
        y: HEADER_HEIGHT + rowIndex * (NODE_HEIGHT + ROW_GAP),
      };
      nodes.push(node);
      nodeById.set(chapter.id, node);
    });
  }

  const edges: MapEdge[] = [];
  for (const chapter of chapters) {
    const to = nodeById.get(chapter.id);
    if (!to) continue;

    for (const prereqId of chapter.prerequisiteIds) {
      const from = nodeById.get(prereqId);
      if (!from) continue; // 引用完整性由测试保证，这里只是防御

      const sameColumn = from.x === to.x;
      const path = sameColumn
        ? // 同阶段内的前置关系：画一条贴近左侧的短弧，避免与右侧连线混淆
          `M ${from.x + SAME_COLUMN_OFFSET} ${from.y + NODE_HEIGHT} C ${from.x + SAME_COLUMN_OFFSET - 12} ${from.y + NODE_HEIGHT + 10}, ${to.x + SAME_COLUMN_OFFSET - 12} ${to.y - 10}, ${to.x + SAME_COLUMN_OFFSET} ${to.y}`
        : curve(from.x + NODE_WIDTH, from.y + NODE_HEIGHT / 2, to.x, to.y + NODE_HEIGHT / 2);

      edges.push({
        id: `${from.chapter.id}->${to.chapter.id}`,
        fromId: from.chapter.id,
        toId: to.chapter.id,
        path,
      });
    }
  }

  const maxRows = Math.max(1, ...columns.map((c) => c.chapters.length));
  const width = Math.max(NODE_WIDTH, columns.length * (NODE_WIDTH + COLUMN_GAP) - COLUMN_GAP);
  const height = HEADER_HEIGHT + maxRows * (NODE_HEIGHT + ROW_GAP);

  return { nodes, edges, columns, width, height };
}

/**
 * 节点标题截断。
 * 中文按字符宽度估算，超过宽度就截断并加省略号 ——
 * SVG 的 <text> 不会自动换行，不截断就会溢出到相邻节点上。
 */
export function truncateTitle(title: string, maxChars: number): string {
  return title.length <= maxChars ? title : `${title.slice(0, maxChars - 1)}…`;
}
