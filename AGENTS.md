<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

---

# 项目交接文档

> 最后更新：2026-09-24 · 作者休假前整理

这是一个**中文 AI Agent 学习路径站**。本文件记录了项目目标、已确认的决策、踩过的坑与后续计划 —— 目的是让接手的会话（无论是人还是 AI）能快速进入状态，而不必重新推导一遍。

**先读这三份，再动手写内容：**

1. 本文件（决策与坑）
2. `CONTENT_GUIDE.md`（内容规范，硬性要求）
3. `VERIFY.md`（待验证清单与验证方法）

---

## 0. 快速上手

```bash
pnpm dev          # 本地开发，http://localhost:3000
pnpm build        # 构建（41+ 静态页面）
pnpm typecheck    # next typegen && tsc --noEmit
pnpm test         # vitest，内容完整性 + SSE 编解码
pnpm lint         # eslint
node scripts/check-links.mjs   # 巡检所有外链可用性
```

**实跑 API 需要的凭据**：写在 `.env.local`（已被 `.gitignore` 覆盖）。`scripts/verify-api.mjs` 会从那里读，且**不会打印 Key**。

## 1. 项目是什么

**目标读者**：作者本人 —— 一个有 Java/Python/Go 背景、正在转 AI Agent 开发的后端工程师。

**要解决的问题**：市面教程有两个通病 ——（一）知识点没有依赖顺序，学完不知道下一步；（二）假设读者从零开始，把有多年工程经验的人当新手教。

**差异化主线**：每一章都有「后端视角对照」，明确列出**哪些已有经验可以直接迁移**、**哪些直觉会失效**。后者是真正值钱的部分。

**当前定位**：先本地自用，架构保证可静态导出、随时可上线。不做营销页与 SEO。

## 2. 已确认的决策（不要推翻）

| 维度 | 决策 |
|---|---|
| 技术栈 | Next.js 16 App Router + React 19 + Tailwind 4 + TypeScript |
| 内容格式 | 每章一目录：`meta.ts`（纯元数据）+ `body.ts`（server-only 加载器）+ 每节一个 `.mdx` |
| 产品形态 | 第一版纯静态内容站，无账号无数据库；进度存储预留服务端扩展接口 |
| 内容生产 | 正文手工精编，外部资源精确外链，**不做爬虫抓取** |
| 模型厂商 | 多厂商，Claude 为主，DeepSeek 有 Anthropic 兼容端点 |
| API Key | BYOK + 服务端中转；Key 只存浏览器 localStorage |
| 语言 | 简体中文正文，技术术语保留英文原词 |
| 代码示例 | Python 为主，涉及浏览器/MCP/Node 时补 TypeScript |

## 3. 内容标准（核心）

### 3.1 准确性机制

`Checkpoint.basis` 是**必填字段**，三种取值没有中间态：

| 取值 | 含义 | 强制要求 |
|---|---|---|
| `documented` | 官方文档明确写着 | **必须**有 `sourceIds`，且只能引用 `resources.ts` 里的条目 |
| `inferred` | 基于工程经验的判断 | 建议用 `note` 说明 |
| `unverified` | 无法核实 | **必须**用 `note` 说明为什么核实不了 |

`tests/curriculum.test.ts` 会强制这些规则。**`sourceIds` 只能引用资源库条目**，是为了保证每条依据都经过链接巡检。

### 3.2 篇幅与内容结构

**用户明确要求：教科书级，每节 4000–6000 字。**

标杆是 `llm-api-basics/01-tokens-and-context.mdx`（中文字符 3922 / 说明文字 6704）。它的四块内容是可复用的模板：

1. **一组实测数据** —— 最好有反直觉的地方（如「7 个字符要 35 个 token」）
2. **Mermaid 图** —— 把机制画出来
3. **完整可运行的代码** —— 读者能直接复制执行
4. **真实错误案例** —— 有原始报错、有排查过程

**判定标准不是字数，是这四块齐不齐。** 缺两块以上就该补，靠注水凑字数是错的。

### 3.3 具体数字的处理

**要么标注来源与核实日期，要么不写。** 不写进正文的：模型价格、基准分数、GitHub star 数、token 倍率。

替代做法：教**估算方法**，把数字留给读者现查。

### 3.4 代码示例

必须实际跑过才写；跑不了的标注「**实跑状态**」。这个标注不能省 —— 它让读者知道该信到什么程度。

## 4. 踩过的坑（务必避免重犯）

### 4.1 代码高亮配色 ×2 —— 同一个根因

**症状**：浅色模式下代码块「深色文字 + 深色背景」，几乎不可读。

**根因**：`next.config.ts` 里设了 `keepBackground: false`，注释还写着「背景交给 Tailwind」—— **但从没真正设置过那个背景**。注释描述了一个不存在的实现。于是代码块落到 Tailwind typography 的 `pre` 默认样式上（那是为深色背景配的浅色文字）。

**两次的具体触发条件不同**：

| 次数 | 触发场景 | 原因 |
|---|---|---|
| 第一次 | 浅色模式全部代码块 | 没给 `pre` 设背景与前景 |
| 第二次 | ````text` 纯文本块 | Shiki 对**无语法高亮**的内容不输出内联 CSS 变量，导致 `color: var(--shiki-light)` 取不到值而失效 |

**修复**（见 `globals.css`）：给 `.prose pre` 显式设置 `background-color: var(--color-muted)` 和 `color: var(--color-foreground)` 兜底。

**教训**：**关掉某个默认值时必须补上自己的**。而且这类问题构建通过、内容完整、肉眼才看得出 —— 见 §5.2 的验证流程。

### 4.2 长行溢出

代码示例的某些行超出正文栏被裁掉。已加 `overflow-x: auto` 兜底，同时**把示例代码拆行** —— 教程代码不该逼读者横向滚动。

### 4.3 我（AI）在同一个 bug 上猜错三次

记录这个过程，因为它是本项目准确性标准的**现实依据**：

| 猜测 | 实际情况 |
|---|---|
| 「内联样式优先级高，加 `!important`」 | 错。span 上根本没有内联 `color` |
| 「`.dark` 类没加上」 | 错。类加上了，规则也生效了 |
| 真实根因 | `keepBackground: false` 没有配套的背景设置 |

**教训**：**不要猜运行时状态，去读它。** 装 playwright 之后可以直接截图与读计算样式（见 §5.2）。

### 4.4 统计指标陷阱

用「中文字符数」衡量篇幅会误导 —— `messages-api.mdx` 因为含大量 JSON 与事件序列，中文字符只有 1366，但实际内容量远超。**要同时看「说明文字总量」与「代码块数」。**

### 4.5 实验数据被 prompt caching 污染

做「工具定义成本」实验时，数据出现 `1 个工具 306 token，3 个工具 174 token` 的矛盾结果 —— 表面上像是「工具越多越便宜」。

**真相**：DeepSeek 自动做了 prompt caching，而 `input_tokens` 的语义是「**未命中缓存的**输入」。必须用三项之和：

```
总输入 = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
```

**教训**：数据自相矛盾时，先怀疑测量方法，不要急着解释或丢弃。

### 4.6 其他技术坑

| 坑 | 处理 |
|---|---|
| Turbopack 下 remark/rehype 插件必须用**字符串名**，不能传函数 | `next.config.ts` 里全用字符串 |
| `mdx-components.tsx` 必须放在 `src/` 下 | 已就位 |
| Tailwind 4 只为 `@theme` 里定义过的 `--color-*` 生成工具类，写错类名**不报错、静默失效** | 用 `grep` 构建产物验证过 |
| Next 16 的 `params` 全是 Promise | 所有页面 `await props.params` |
| `next build` 不再跑 lint | `typecheck` 脚本改为 `next typegen && tsc --noEmit` |
| React 19 的 `react-hooks/set-state-in-effect` | 主题切换改用 `useSyncExternalStore` |
| `useSearchParams` 在静态页必须包 `<Suspense>`，否则**生产构建失败**（开发环境不报） | 暂未用到，用到时注意 |

### 4.7 localStorage 导致的 hydration mismatch（**重犯**）

**症状**：

```
Hydration failed because the server rendered HTML didn't match the client
...
+ className="border-b border-amber-500/40 bg-amber-500/5 px-4 py-3 text-xs"   ← 客户端
- className="border-border border-b px-4 py-2"                               ← 服务端
```

**根因**：`useState(() => loadByok())` —— `loadByok()` 读 localStorage，
而**服务端没有 localStorage**，返回空状态；客户端返回实际状态。两端首次渲染必然不一致。

**讽刺之处**：这个项目在 `theme-toggle.tsx` 里**已经用 `useSyncExternalStore` 正确
解决过同样的问题**，但写 Playground 时忘了。所以这条要单独记。

**修复**：

```ts
const subscribeNothing = () => () => {};
const mounted = useSyncExternalStore(subscribeNothing, () => true, () => false);
```

所有依赖 localStorage 的渲染都加 `mounted &&` 门控。

**规则**：**任何读 localStorage / sessionStorage 的状态，首次渲染必须与服务端一致。**
用 `useSyncExternalStore` 的 `getServerSnapshot` 区分，或用 `mounted` 门控。
不要用 `useEffect + setState` —— React 19 的 lint 规则会直接报错。

### 4.8 `meta.ts` 的纯文本字段不解析 Markdown（静默失效）

**症状**：章节摘要、自检项、资源推荐理由、实验目标里写的 `**强调**`，页面上**原样显示成星号**。全站一度有 8 个页面中招。

**根因**：这些字段是 `meta.ts` 里的普通字符串，通过 `{field}` 直接插进 JSX —— **不走 MDX 管线**。内容是按 Markdown 写的，渲染层却当纯文本。

同一个文件里还有第二种表现：MDX 正文里的 `**` 若**紧贴 CJK 标点**，CommonMark 的 flanking 规则会让它失效：

| 写法 | 为什么失效 |
|---|---|
| `而**「独立」是关键词**` | 开头 `**` 后紧跟 `「`，且前面是普通字 → 不构成左闭合分隔符 |
| `采用**子词（subword）**方案` | 结尾 `**` 前紧贴 `）`，后面又是普通字 → 不构成右闭合分隔符 |

**修复**：

1. 新增 `src/components/ui/inline-md.tsx` —— `<InlineMd>` 渲染 `**粗体**` 与 `` `代码` ``，`plainText()` 用于不能放 JSX 的位置（`<meta description>`、SVG `<title>`）。所有渲染这些字段的组件都已接入。
2. 修掉 MDX 里两处紧贴标点的写法（把标点移到标记**外面**）。
3. `tests/curriculum.test.ts` 加两组断言：纯文本字段的标记必须成对；MDX 正文的粗体两端必须构成合法分隔符（按奇偶位置认开/闭标记，再套 flanking 规则）。

**验证方式**：`curl` 每个页面，剔掉 `<pre>`/`<code>` 后 grep 字面 `**`。**这条比读源码可靠** —— 靠肉眼看源码发现不了，靠构建也发现不了。

**教训**：和 §4.1 是同一类 —— **内容按一种格式写、渲染层按另一种处理，且失败是静默的**。凡是「塞进 JSX 的字符串字段」，都要问一句：作者会不会在里面写标记？

## 5. 已建立的机制

### 5.1 内容完整性测试

`tests/curriculum.test.ts`（35 个断言）：id 唯一性、引用完整性、依赖无环、依据标注合规、资源质量、纯文本字段与 MDX 正文的**行内标记渲染等价性**（见 §4.8）。

`tests/sse.test.ts`（15 个断言）：SSE 编解码，含跨分片、多行 data、按 7 字符随机切分的往返一致性。

### 5.2 视觉验证流程（重要）

**构建通过 ≠ 看起来是对的。** §4.1 的两个 bug 都是「构建成功、页面正常、但看不见」。

```bash
export PWCLI="$HOME/.codex/skills/playwright/scripts/playwright_cli.sh"
PORT=3100 pnpm start &
"$PWCLI" open "http://localhost:3100/chapters/..."
"$PWCLI" resize 1300 1000
"$PWCLI" eval "() => { document.documentElement.className='light'; ... }"   # 切主题
"$PWCLI" screenshot
```

然后用 Read 工具查看生成的 PNG。**每写完一节都该做一次，深浅两种模式各一张。**

注意 `eval` 的限制：playwright-cli 会把结果再包一层引号并转义，**不要返回 JSON**（解析极易出错），用 `|` 或 `;;` 分隔的简单格式。另外**不要用 `\n` 做分隔符** —— 它会在跨层传递时被解释成真实换行，让 eval 源码里出现裸换行而语法错误。

**切主题必须走 next-themes，不能直接改 `className`。** 两种做法对 CSS 类驱动的样式都有效，但对**依赖 React 状态的组件无效** —— `mermaid.tsx` 是根据 `resolvedTheme` 重绘的，`document.documentElement.className = 'dark'` 不会触发它重绘，你截图看到的仍是浅色图，会误判成 bug（本次就误判了一次）。正确做法：

```bash
"$PWCLI" eval "() => { localStorage.setItem('theme','dark'); location.reload(); return 'ok'; }"
sleep 3   # 等 next-themes 水合 + mermaid 重新渲染
# 验证确实生效：document.documentElement.className 应为 'dark'
```

另外，**低分辨率截图里的反引号不可信** —— `<code>` 元素的内联样式看起来很像反引号，我据此误判过两次。要确认是否有字面标记残留，读 DOM：

```bash
"$PWCLI" eval "() => { const c=document.querySelector('.prose').cloneNode(true); c.querySelectorAll('pre,code').forEach(n=>n.remove()); const t=c.textContent; return 'STAR='+(t.match(/\*\*/g)||[]).length+' TICK='+(t.match(/\`/g)||[]).length; }"
```

### 5.3 实测数据采集

`scripts/verify-api.mjs` 采集真实数据（凭据、认证方式、流式事件、token 计数、错误响应），输出到 `verify-output/`（已 gitignore）。

**认证方式**：DeepSeek 的 Anthropic 兼容端点用 **`x-api-key`**，不是 `Authorization: Bearer`（文档说两种都支持，实测只有前者可用）。

### 5.4 链接巡检

`scripts/check-links.mjs` 检查所有外链可用性。**它只能验证「页面还在」，验证不了「内容还对」。**

首轮核实中就修正了三处二手资料带来的错误：一个仓库已归档、一个仓库改了组织、一个只有 2 star 的仓库被描述成「知名教程」。

## 6. 当前进度

### 6.1 已完成

**基础设施**：脚手架、Tailwind 4 设计令牌、深色模式、MDX 管线、Mermaid 组件、资源库（47 条）、术语表（30 条）、实验定义（4 个）、作业（1 个）、准确性机制、50 个测试断言

**章 0「起点」** —— 4 节完整正文（从中途开始写，此前只有大纲）

**章 1「LLM 基础与 API 调用」** —— 5 节完整正文

**章 2「Prompt 工程」** —— 5 节完整正文（2026-10-08 全部完成）

### 6.2 进度明细

| 节 | 中文 | 图 | 代码块 | 实测数据 | 错误案例 | 状态 |
|---|---:|---:|---:|:--:|:--:|---|
| 0-1 为什么是现在 | 2561 | 1 | 5 | ✓ | ✓ | 缺图（可加一节成本图） |
| 0-2 什么算 agent | 2106 | 2 | 3 | ✓ | ✓ | ✅ |
| 0-3 三个失效直觉 | 2625 | 2 | 6 | ✓ | ✓ | ✅ 已补两张图 |
| 0-4 怎么用这个站 | 1729 | 1 | 2 | — | — | 内容性质偏说明，不需实测 |
| 1-1 token（**标杆**） | 3922 | 2 | 7 | ✓ | ✓ | ✅ |
| 1-2 采样参数 | 3026 | 1 | 5 | ✓ | ✓ | ✅ 已补迁移案例 |
| 1-3 Messages API | 1661 | 1 | 8 | ✓ | ✓ | 代码为主，中文偏少但内容不缺 |
| 1-4 模型选型 | 1903 | 2 | 11 | ✓ | ✓ | ✅ 已补成本误判案例 |
| 1-5 prompt caching | 1958 | 1 | 10 | ✓ | ✓ | ✅ 已补缓存排查案例 |
| **2-1 清晰直接** | 1762 | 1 | 2 | ✓ | ✓ | ✅ |
| **2-2 指令与数据分离** | 2551 | 1 | 3 | ✓ | ✓ | ✅ |
| **2-3 少样本示例** | 1780 | 1 | 1 | ✓ | ✓ | ✅ |
| **2-4 思维链与 prefill** | 1516 | 1 | 3 | ✓ | ✓ | ✅ |
| **2-5 可靠性增强** | 3299 | 2 | 2 | ✓ | ✓ | ✅ |
| **3-1 上下文不是越多越好** | 2024 | 1 | 3 | ✓ | ✓ | ✅ 五次设计都未复现位置/容量效应 |
| **3-2 system prompt 的高度** | 1735 | 1 | 3 | ✓ | ✓ | ✅ 矛盾规则导致行为随机（8/12） |
| 3-3 即时检索 | — | — | — | — | — | 待写 |
| 3-4 压缩与结构化笔记 | — | — | — | — | — | 待写 |
| 3-5 子智能体隔离 | — | — | — | — | — | 待写 |

**章 2（2026-10-08）完成的工作**：

1. 五节正文，全部含「实测数据 + Mermaid 图 + 完整可运行代码 + 真实错误案例」四块
2. **7 组新实测**：否定式 vs 正面指令、提示注入 6 种形式、少样本（典型 vs 边界）、CoT 成本、self-consistency 多数投票、self-eval 判别力、temperature 透传对照
3. **章 1 遗留的 5 处 Mermaid 代码块转成了 `<Mermaid>` 组件**（1-2/1-3/1-4/1-5）
4. 修了全站 8 个页面的静默渲染失效（见 §4.8）

### 6.3 已采集的实测数据（可复用）

全部标注了模型与日期，写正文时直接引用：

- **token 密度**：短中文 7 字符→35 tok、长英文 1050 字符→381 tok，推出约 30 token 固定开销
- **工具成本**：tools 数组入场费约 200 token，每个工具约 60 token（**注意缓存污染**，见 §4.5）
- **温度对比**：`temperature=0` 三次里一次不同（「三味咖啡/三味咖啡/三咖小馆」）
- **三种实现成本**：单次调用 365 / workflow 619 / agent 1625 token
- **多轮成本**：每轮输入 +32 token，累计 `57N + 16N(N-1)`，是 O(N²)
- **缓存行为**：命中使未缓存输入从 2688 降到 256、耗时快 3.4 倍；**改一个字全部失效**
- **流式事件**：63 个事件的完整序列，工具参数 18 个分片拼成完整 JSON
- **enum 约束**：模型正确拒绝不在枚举内的城市，**未编造参数**
- **否定式 vs 正面指令**：否定式越界 0 次（完美达成约束），但平均只写 74 字（要求 200 字）—— 抑制约束的同时把合法内容一起压掉了
- **提示注入 6 种形式**：脚本式/伪装式 0/6（完全失败）；格式操纵 6/6 → 加 XML 标签 2/6；内容操纵 6/6 → 加标签**仍 6/6**（标签只挡一半）
- **少样本**：10 个典型示例 = 零样本（都是 9/10，且错同一条）；3 个边界示例 = 10/10；边界+典型 = 10/10（典型纯属陪跑）
- **CoT**：多步推理题准确率 15/15 → 15/15，成本 +85%；简单题 6/9 → 6/9，成本 +125%
- **self-consistency**：唯一答案题 5 次采样**零分歧**（temperature 1 与 0 都一样）；创作题 6/6 各不相同 → 投票无事可做，成本 5.4x
- **self-eval**：喂入构造的错答 8/8 捉住、0/8 误报 —— 但那是**独立重算**，不是审阅推理

### 6.4 六个「未复现」的实验

如实记录，**不要删掉这些结论**，它们本身是教学内容 —— 也说明这个领域流传的很多经验之谈没有实测支撑：

| 实验 | 预期 | 结果 |
|---|---|---|
| 温度对结构化输出成功率的影响 | 高温更不可靠 | 三档温度都 6/6 成功，**未复现** |
| Lost in the Middle 位置效应 | 中间最易忽略 | 12000 字符干扰下三位置都遵守，**未复现** |
| 工具成本线性增长 | 线性 | 数据被缓存污染，**修正后才得到正确结论** |
| 示例格式不一致会被复制 | 输出跟着乱 | 12/12 照常遵守约定，**未复现** |
| CoT 提升准确率 | 准确率上升 | 准确率不变、成本 +85%（模型已内置思考），**未复现** |
| 多数投票提升准确率 | 过滤随机错误 | 5 次采样零分歧、收益为零、成本 5.4x，**未复现** |

## 7. 后续设计

### 7.1 章节大纲（19 章 / 6 阶段）

```
阶段 0 起点（1 章）    ✅ 章 0 已完成正文
阶段 1 地基（3 章）    ✅ 章 1、2 已完成正文 <- 当前所在（下一章：3 上下文工程）
阶段 2 原语（4 章）    已注册 2 章（4 Tool Calling / 5 结构化输出），均仅大纲
阶段 3 编排（5 章）    仅大纲：Agent 范式 / 手写循环 / 多智能体 / 框架 / MCP
阶段 4 生产化（4 章）  仅大纲：评估 / 沙箱 / 成本 / 部署
阶段 5 实战（2 章）    仅大纲：源码研读 / 综合项目
```

> ⚠️ 注意：`stages.ts` 里 `chapterIds` 已被**移除**（改为从 `Chapter.stageId` 派生），所以「有哪些章」取决于 `content/chapters/index.ts` 里注册了什么。当前只注册了 6 章，顺序为：0 what-is-an-agent / 1 llm-api-basics / 2 prompt-engineering / 3 context-engineering / 4 tool-calling / 5 structured-output。

### 7.2 未实现的功能（已在章 0-4 如实告知读者）

| 功能 | 状态 | 优先级 |
|---|---|---|
| 站内 Playground（BYOK + 轨迹可视化） | ✅ **已完成**（2026-10-08），见下方说明 | — |
| 学习进度（章节完成 / 自检项勾选） | 未开始，schema 已预留 | 中 |
| 全文搜索 | 未开始（计划用 Pagefind） | 中 |
| 资源库筛选 | 未开始（当前按优先级分组） | 低 |

**Playground 现状**（`/labs` 与 `/labs/[labId]`）：

- `src/lib/llm/`：`types.ts`（统一事件模型）、`sse.ts`（同构编解码）、`registry.ts`（
  provider 注册表 **兼白名单**）、`adapters/anthropic.ts`、`adapters/openai-compatible.ts`
- `src/lib/byok/storage.ts`：Key 的浏览器端存储，支持「仅本次会话」模式
- `src/hooks/use-chat-relay.ts`：客户端驱动循环 + SSE 解析 + 轨迹记录
- `src/components/lab/playground.tsx`：实验 UI（Key 表单、预设、流式输出、轨迹时间线）
- `src/app/api/chat/route.ts`：BYOK 中转端点（**唯一运行时后端**）
- `src/app/labs/`：实验索引页与详情页

**已实测通过**（2026-10-08）：

| 测试项 | 结果 |
|---|---|
| 正常流式调用（字符串 content） | HTTP 200，294 事件，输出正确 |
| 正常流式调用（block 数组 content） | HTTP 200，212 事件 |
| system 生效 | 输出英文（system 指令被遵守） |
| 模型不在白名单 | 400 `model_not_allowed` |
| provider 不存在 | 400，并列出支持的 provider |
| 缺 Key | 401 `unauthorized` |
| UI 渲染 | 完整（Key 表单、厂商/模型选择、预设、轨迹区） |
| 错误展示 | 正确显示上游错误原文 |

**已知未验证**：浏览器里的完整成功路径（填 Key → 运行 → 看到流式输出）尚未端到端跑通 ——
playwright 操作 React 受控组件的表单时遇到了 ref 失效问题。**建议人工在页面上试一次**。

**设计要点**（值得保留的判断）：

1. **适配器选的是协议，不是厂商**。`registry.ts` 里 DeepSeek 用的是 `anthropicAdapter`
   —— 因为它提供 Anthropic 兼容端点。同一个适配器可以被多个 provider 复用。
2. **Key 走请求头不走请求体**。请求体更容易被中间层记录。
3. **错误两阶段契约**。首字节前返回真实 HTTP 状态码；之后只能发 `error` 事件。
   客户端因此能区分「配置错了」和「生成中断了」。
4. **`content` 归一化**。官方 SDK 允许 `content: "文本"` 简写，适配层内部统一按 block
   数组处理。实测中真的踩到了这个坑（传字符串得到 502 与 `content.map is not a function`），
   现在在 `/api/chat` 的 `normalizeMessages` 里统一处理。
5. **表单只有一套**（设计迭代，值得记住教训）。

   第一版把 provider 等同于「厂商官方端点」，baseUrl 硬编码 —— 结果第三方平台的
   用户必然 401。第二版加了个「使用自定义端点」开关来区分两种模式，那是**多余的
   心智负担**：用户要么得先理解那个概念，要么在填错 Key 之后困惑于为什么点不动
   运行按钮（这个困惑真的发生了）。

   现在的设计：**端点地址 / 模型名 / API Key 三个字段始终可见、始终可改**，
   厂商选择只负责把前两者预填成默认值。

   - 模型名用 `<input list=...>` + `<datalist>` —— 给建议但**不限制输入**，
     因为第三方平台的模型名往往不在白名单里，做成强制下拉就没法用了
   - 服务端对应地只对「**非注册表地址**」要求 `ALLOW_CUSTOM_BASE_URL` 与 SSRF
     校验：预填的默认地址属于正常用法，不该被开关拦住，否则本地默认配置下
     连官方端点都用不了

6. **四样东西成套保存**（来自使用反馈）。

   一次可用的调用需要：**协议、端点地址、模型名、API Key**。最初的实现
   **只存了 Key** —— 结果是刷新页面后地址与模型名退回默认值，用户每次
   都得重填。

   存储单位因此从「Key」改成 **EndpointProfile**（`src/lib/byok/storage.ts`），
   支持保存多套配置（如「官方」与「某中转平台」）并一键切换。

   两个实现细节值得保留：
   - **改字段即保存**（`patch()`），且没有配置时**自动创建** ——
     用户不该先理解「配置」这个概念才能开始用
   - 组件内**不保留第二份状态**：每次都从 localStorage 读、用版本号触发重渲染。
     这样不会出现「内存状态与存储不同步」这类经典 bug

### 7.3 章 1 / 章 2 的补缺口清单

**章 1（2026-10-08 完成）**：1-2/1-3/1-4/1-5 的 Mermaid 图已全部补齐（其中 1-3/1-4/1-5 是把正文里已有的 Mermaid **代码块**转成 `<Mermaid>` 组件）。三个真实案例（1-2 迁移、1-4 成本误判、1-5 缓存门槛）也已补上。

**章 2（2026-10-08 完成）**：5 节全部含「实测数据 + Mermaid 图 + 完整可运行代码 + 真实错误案例」。

**仍缺**：无。0-3 的两张图已于 2026-10-08 补齐（一张总览三个失效直觉，一张画「上下文 ≠ 精确状态」的机制）。

> 批量转换 Mermaid 代码块的方式：`node -e '...replace(/```mermaid\n([\s\S]*?)```/g, ...)'`（见 0-1 的做法）

### 7.4 推进策略（用户已确认）

**逐章完成、整章验收**：先把一章的全部小节写完整（形成一个可验收的样板），再推进下一章。原因：如果中途发现方向要调整，返工只涉及一章。

已按此完成章 1、章 2。用户明确说过「质量非常好，所有内容都按这个标准执行」。**下一章：3 上下文工程**（已有 5 节大纲，见 `context-engineering/meta.ts`）。

## 8. 待办清单

**内容缺口：** 无 —— 章 0/1/2 的每节都齐了「实测数据 + Mermaid 图 + 完整可运行代码 + 真实错误案例」。2026-10-08 收尾时补上了 0-3 的两张图。

**之后：**

- [ ] **章 3「上下文工程」起逐章推进**（先写 meta.ts → 各节 mdx → 实测数据 → 截图验证）
- [ ] 实现学习进度（兑现章 0-4 的说明）
- [ ] 全文搜索（计划用 Pagefind）
- [ ] 按 `VERIFY.md` 验证所有「未实跑」的代码

**工具链现状**：`pnpm test`（50 断言）、`pnpm typecheck`、`pnpm lint`、`pnpm build`（46 页）**全部干净**。

## 9. 给接手的会话的话

**先建立视觉验证能力**（§5.2 的 playwright 流程）。这个项目最耗时的不是写内容，而是**发现「构建通过但看起来是错的」**。我在这上面猜错了三次、浪费了大量轮次。

**端口检查是第一步**：`pnpm start` 起不来时会 `EADDRINUSE`，而**你看到的仍是旧构建的页面** —— 这会让你误判改动没生效（本次就踩了）。启动后先确认日志里有 `Local:`。

**实测数据是内容质量的支点。** 每一节如果有真实数据支撑，说服力会完全不同。凭据在 `.env.local`，采集脚本可以照 `scripts/verify-api.mjs` 的模式写。

**答案键尽量让代码算。** 我在章 2 手工写答案键，**错了两次，而且两次都"自查"通过** —— 用同一套直觉检查同一套直觉，查不出错。能由程序生成的题目与答案，就交给程序。

**如实报告「未复现」的结果。** 本项目已积累六个未复现的实验（§6.4），它们比成功案例更有教学价值 —— 它们演示了「论文结论需要在自己的场景验证」这件事。

**不要为了字数注水。** 用 §3.2 的四块内容检查清单代替字数指标。

**用户很在意两件事**：内容的准确性与可验证性（所以有 `basis` 标注机制），以及页面的实际观感（所以要截图验证，并 curl 页面剔除 `<pre>`/`<code>` 后 grep 字面 `**`，见 §4.8）。
