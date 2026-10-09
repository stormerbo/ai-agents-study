<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

---

# 项目交接文档（入口）

> 最后更新：2026-10-09

这是一个**中文 AI Agent 学习路径站**。本文件是入口，只放「接手时立刻要知道的东西」。
更细的参考材料拆成了四份，按**你什么时候需要它**分类：

| 什么时候读 | 读哪一份 | 里面有什么 |
|---|---|---|
| **动笔写内容之前** | [docs/PITFALLS.md](docs/PITFALLS.md) | 16 条真实踩过的坑（原 §4） |
| **引用实测数字时** | [docs/DATA.md](docs/DATA.md) | 全部实测数据 +「未复现」清单（原 §6.3 / §6.4） |
| **决定接下来做什么** | [docs/PROGRESS.md](docs/PROGRESS.md) | 各章完成情况 + 逐节进度表（原 §6.1 / §6.2） |
| **规划与设计依据** | [docs/ROADMAP.md](docs/ROADMAP.md) | 章节大纲、未实现功能、推进策略（原 §7） |

另外两份仍在根目录：[CONTENT_GUIDE.md](CONTENT_GUIDE.md)（内容规范，硬性要求）与 [VERIFY.md](VERIFY.md)（待验证清单与验证方法）。

> **为什么拆分**：本文档长到 67,810 字节时超过了工作区指令的 **65,536 字节注入预算**，会被静默截断 ——
> 也就是结尾的「给接手的会话的话」一度读不到。拆完之后入口约 15KB，四份参考文档按需读取，
> 既回到预算内，也让「先读什么」变得明确。
>
> 拆分时**保留了原来的 § 编号**（§4 仍是那 16 条坑、§6.3 仍是实测数据），因为源码与测试里
> 有多处「见 AGENTS.md §4.9」这类引用 —— 改编号会让它们全部失效。

---

## 0. 快速上手

```bash
pnpm dev          # 本地开发，http://localhost:3000
pnpm build        # 构建（152 个静态页面）
pnpm typecheck    # next typegen && tsc --noEmit
pnpm test         # vitest，内容完整性 + SSE 编解码
pnpm lint         # eslint
node scripts/content-stats.mjs  # 每节中文/说明文字/图/代码块，对照 §3.2 验收标准
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

**验收标准（2026-10-08 用户明确确认）：四块齐全 + 中文 ≥1500 字 + 说明文字 ≥3000 字。**

> 这里此前写的是「每节 4000–6000 字」。那个数字不是门槛 —— 现有 24 节里只有标杆 1-1 到过 3922，而它恰好是标杆；用 4000 当门槛会把已经验收过的 23 节全判为不合格。真正决定质量的是下面四块，字数只是它们的结果。下限定在 1500 / 3000，是为了拦住「看起来写了一节、其实没讲透」。

标杆是 `llm-api-basics/01-tokens-and-context.mdx`（中文字符 3922 / 说明文字 6704）。它的四块内容是可复用的模板：

1. **一组实测数据** —— 最好有反直觉的地方（如「7 个字符要 35 个 token」）
2. **Mermaid 图** —— 把机制画出来
3. **完整可运行的代码** —— 读者能直接复制执行
4. **真实错误案例** —— 有原始报错、有排查过程

**缺两块以上就该补，靠注水凑字数是错的。** 统计时同时看「中文」与「说明文字」以及代码块数 —— 单看中文字符会误导（§4.4）。

**指标口径**（用标杆 1-1 校准过，`node scripts/content-stats.mjs` 就是按它实现的）：

| 指标 | 算法 | 标杆 1-1 应为 |
|---|---|---|
| 中文 | 剔除围栏代码块后的 CJK 字符数 | 3922 |
| 说明文字 | 剔除围栏代码块后的**非空白**字符数 | 6704 |

> 两者都排除 frontmatter，但**不**排除行内代码与 Mermaid 组件 —— 早期手工统计就是这个口径，脚本必须复现它，否则新旧数据不可比。

### 3.3 具体数字的处理

**要么标注来源与核实日期，要么不写。** 不写进正文的：模型价格、基准分数、GitHub star 数、token 倍率。

替代做法：教**估算方法**，把数字留给读者现查。

### 3.4 代码示例

必须实际跑过才写；跑不了的标注「**实跑状态**」。这个标注不能省 —— 它让读者知道该信到什么程度。

## 5. 已建立的机制

### 5.1 内容完整性测试

`tests/curriculum.test.ts`（39 个断言）：id 唯一性、引用完整性、依赖无环、依据标注合规、资源质量、纯文本字段与 MDX 正文的**行内标记渲染等价性**（见 §4.8）、以及**正文登记四方一致性**（见 §4.9）。

`tests/sse.test.ts`（15 个断言）：SSE 编解码，含跨分片、多行 data、按 7 字符随机切分的往返一致性。

`tests/inline-md.test.ts`（5 个断言）：`InlineMd` 的**渲染契约** —— 必须只返回一个顶层元素，否则在 flex/grid 父容器里会被拆成并排几列（见 §4.15）。用 `renderToStaticMarkup` 断言，不需要 DOM 环境。

`tests/image-tokens.test.ts`（4 个断言）：图像 token 估算函数与第 8 章**实测阶梯**的一致性 —— 锚定两个结构上确定的边界（≤512px 取下限 186、≥1280px 取上限 996），中间段给 2% 容差。

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

**`playwright_cli.sh` 会回显它执行的代码，参数一并打印。** 用它 `fill` 填 API Key 会把 Key 明文写进日志 ——
本次端到端验证时就发生了。**凡是涉及密钥的操作，不要走会回显参数的 CLI 路径**（改成人工操作，或用不回显的方式注入）。

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

## 8. 待办清单

**内容缺口：** 无 —— 章 0-5 共 28 节的每节都齐了「实测数据 + Mermaid 图 + 完整可运行代码 + 真实错误案例」。2026-10-08 收尾时补上了 0-3 的两张图。

**之后：**

- [x] **章 5「结构化输出」**（4 节正文，2026-10-08 完成）
- [ ] **第 21 章「源码研读」起逐章写正文**（第 21-22 章共 2 章已有完整大纲与自检项，等待写正文）
- [x] **章 0-5 全部 28 节补到新验收标准**（2026-10-08）：字数、真实报错案例、以及章 3 的四处静默失效排查
- [x] **章 6「检索」5 节正文**（2026-10-08 完成）：用本站 28 篇正文当语料，跑出 5 组实测（语料 8.9 万 token、切分四策略对照、改写查询失败与重排天花板、完美检索上界、单次 vs 多轮检索）
- [x] **章 7「记忆」5 节正文**（2026-10-08 完成）：6 组实测（上下文上限 104 万 token、13 万 token 海捞针、12 轮成本 6.5 倍、写入策略对照、误召回静默改写、冲突裁决各跑 3 次）
- [x] **给 Playground 加图像上传 + 第 8 章的视觉实验 `lab-vision-extract`**（2026-10-09）
- [x] **章 8「多模态输入」5 节正文**（2026-10-08 完成）：6 组实测（图像 token 阶梯 186→996、URL 图服务端下载 400、PDF 三路线 59/337/123、分辨率 290↔1061 准确率相同、对比度与 JPEG 未复现、一致性校验召回 67% 精确 100%）
- [ ] 实现学习进度（兑现章 0-4 的说明）
- [ ] 全文搜索（计划用 Pagefind）
- [ ] 按 `VERIFY.md` 验证所有「未实跑」的代码

**工具链现状**：`pnpm test`（63 断言 / 4 个文件）、`pnpm typecheck`、`pnpm lint`、`pnpm build`（152 页）；内容体量 **73/73 达标**。**全部干净**。

## 9. 给接手的会话的话

**先建立视觉验证能力**（§5.2 的 playwright 流程）。这个项目最耗时的不是写内容，而是**发现「构建通过但看起来是错的」**。我在这上面猜错了三次、浪费了大量轮次。

**端口检查是第一步**：`pnpm start` 起不来时会 `EADDRINUSE`，而**你看到的仍是旧构建的页面** —— 这会让你误判改动没生效（本次就踩了）。启动后先确认日志里有 `Local:`。

**实测数据是内容质量的支点。** 每一节如果有真实数据支撑，说服力会完全不同。凭据在 `.env.local`，采集脚本可以照 `scripts/verify-api.mjs` 的模式写。

**答案键尽量让代码算。** 我在章 2 手工写答案键，**错了两次，而且两次都"自查"通过** —— 用同一套直觉检查同一套直觉，查不出错。能由程序生成的题目与答案，就交给程序。

**长上下文任务必须给足 `max_tokens`，并且永远检查 `stop_reason`。** 这是一个在本次写作里**撞了三次**的陷阱：模型会先思考再回答，而长上下文让它思考更久 —— 输出预算不够时返回的是**空文本 + `stop_reason=max_tokens`**，看起来就像「模型做不到」。章 3 第 1 节和第 5 节都差点因此写出错误结论。判据很简单：**没确认 `stop_reason` 之前，不要解释任何「没答出来」的结果。**

**同一个实验结论可能因为对照组选得不同而完全反转。** 章 3 第 5 节里，「子智能体贵不贵」在两种对照下给出 8.1 倍与 0.4 倍两个相反答案。写「A 比 B 好/差」之前，先问清楚**你在跟什么比**。

**对照组里必须有正确答案。** 章 4 第 5 节我第一次按「3 / 8 / 20 / 43 个工具」分组测选择准确率，结果 3 个工具那组只有 3/8 —— 因为问发票、优惠券时**那些工具压根没提供**。那不是选择失败，是题目超出了工具集。测「能力类」指标时，先确认每一题在对照组里都有解。

**测量缺陷在这几轮写作里累计出现八类**（答案键写错两次、`max_tokens` 截断多次、对照组缺答案、测试数据漏字段、解析器只认对象不认顶层数组、**解析器贪婪匹配把解析失败记成「模型全错」**见 §4.16、判分口径不一致见 §4.12、把未复现当噪声丢掉见 §3.4）。它们的共同点是：**看起来都像「模型的行为异常」**。所以每当你要解释一个反直觉结果时，先用一句话自问 ——「这有没有可能是我这边的 bug？」

**如实报告「未复现」的结果。** 本项目已积累十八个未复现的实验（§6.4），它们比成功案例更有教学价值 —— 它们演示了「论文结论需要在自己的场景验证」这件事。

**不要为了字数注水。** 用 §3.2 的四块内容检查清单代替字数指标。

**用户很在意两件事**：内容的准确性与可验证性（所以有 `basis` 标注机制），以及页面的实际观感（所以要截图验证，并 curl 页面剔除 `<pre>`/`<code>` 后 grep 字面 `**`，见 §4.8）。
