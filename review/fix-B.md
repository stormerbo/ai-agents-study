# 深度修复报告 B：章 3 上下文工程 + 章 4 Tool Calling

> 依据 [review/depth-B.md](depth-B.md) 与 [docs/CONTENT-DEPTH.md](../docs/CONTENT-DEPTH.md)。
> 只改动了下列 13 个 `.mdx`；未碰 `meta.ts`、未碰 `src` 其它文件、未新增 MDX 组件或 frontmatter 字段。
> 全部新增数字只有两个来源：站内已有实测，或本次构造的示例（一律就地标注「示例：构造数据，未实跑」）。

## 验收结果（本报告末尾附命令与原始输出）

| 检查 | 结果 |
|---|---|
| `node scripts/depth-check.mjs --chapter=context-engineering` | 硬错误 **0**、建议项 **0**、术语首现无解释 **0/3** |
| `node scripts/depth-check.mjs --chapter=tool-calling` | 硬错误 **0**、建议项 **0**、术语首现无解释 **0/3** |
| `node scripts/content-stats.mjs` | 13/13 达标；全站 134/134 仍达标；负责章节中文/说明文字**全部上升** |
| `pnpm test` | **67 passed / 5 files** 全绿（含新增的 `tests/depth.test.ts`） |
| `node scripts/verify-depth-fixes.mjs` | 无实质性字数下降（12 节均上升） |

---

## 章 3 上下文工程（8 节）

### 3.1 上下文不是越多越好：两个实证 ｜ 01-context-is-finite.mdx
- **补了什么**：
  - 定义（L12 起）：「注意力」的白话机制（加权求和，不是精确查表）、Lost in the Middle 的结论与其**经验观察**性质、context rot 与「窗口满了」的区别、语义 needle 与机械标记的区别、prompt caching 的机制一句。
  - 判据（L48 起）：答案必须由两个字段联合推出；并给出造干扰项的步骤（为每个单独条件各造一批只满足它的条目）。
  - 产物（L48）：三条真实形态的项目条目（正确条目 + 两类干扰项各一条）。
  - 步骤（L186 起）：把 `DOCS/NEEDLE_INDEX/QUESTION/ANSWER` 四个 `...` 占位替换为**确定性语料生成器** `build_corpus()`，并加 `check_criterion()` 自检题目是否真能区分「读懂」与「关键字匹配」；脚本现在可直接跑通。
  - 定义（L86 起）：补 `max_tokens` / `stop_reason` 的字段含义。
- **依据**：语料片段是构造示例；判据由生成器代码自证（`check_criterion`）。原有 5 组实测数字与日期一字未动。
- **仍未解决**：原文那句「论文测的是『读完之后能不能用』…对注意力的要求不同」保留原样 —— 现在「注意力」在 L12 已定义，读者能跟上，但**论文与本节任务的差异是否就是注意力要求不同**，仍只是合理推断，没有实验支撑；未改写成断言。

### 3.2 system prompt 的高度 ｜ 02-system-prompt-altitude.mdx
- **补了什么**：
  - 产物（L110）：「原则式」prompt 全文（4 条原则 + 正/反例各一），标注为等价重写；并列出逐条式 18 条的**完整表格**，逐条标出「判断原则 / 输出形态 / 场景枚举」，点明 7 与 12 冲突、13/14/15 在抢同一个预算。
  - 步骤（L158）：「4 条原则怎么拆出来」的 5 步（从失败对话归纳、一条原则=一次取舍、按不可逆程度排序、同场景相反答案即冲突、示例用一正一反）。
  - 步骤（L260）：CI 自检那句提示词原文 + 最小接入形态。
- **依据**：原则式/18 条为构造示例（原文未逐字留存，就近标注）；三段实测数字（311/334/81、4/4 vs 0/4、8/12、4 次审规则）均为站内已有实测，未动。
- **仍未解决**：无。

### 3.3 即时检索 ｜ 03-just-in-time.mdx
- **补了什么**：
  - 产物（L105）：20 行索引样例 + 三个字段（编号/标题/摘要）各自用途表 + 摘要由谁写、多长、写主题不写结论。
  - 产物（L290）：三种「取不到」的 JSON 回填各一份 + 动作映射表（not_found / unavailable / forbidden 各自该做什么、不该做什么）。
  - 步骤（L126）：从目录到选中那一轮的输入输出示例。
  - 定义：`is_error`（L233 首次出现处随代码解释）、`checkpoint`（L98，明确是每节自检题而非框架检查点）、prompt caching 机制（L83）。
  - 修一致性（L200 起）：`catalogue` 从只拼 `id + title` 改为拼 `id + title + summary`，与正文建议一致；工具回填改为结构化 `not_found` + `is_error`。
- **依据**：索引与错误 JSON 为构造示例；两处成本表（1888/3259、0.64x~3.60x）与 `is_error` 的 4/4 结果为站内已有实测，未动。
- **仍未解决**：无。

### 3.4 压缩与结构化笔记 ｜ 04-compaction.mdx
- **补了什么**：
  - 产物（L95）：填满实测二那 8 条信息的结构化笔记 JSON（7 字段、带 source/turn）。
  - 判据（L104）：字段设计的 3 条（程序会比较/拼接的、丢了会重复执行的、丢了会越界的）；冲突记 `superseded_by`。
  - 步骤（L126）：笔记生命周期四步（触发时机 / 存放位置=稳定前缀 / 读回顺序 / 按类别+值 merge）+ 消息数组示例 + `merge_notes`、`missing_fields` 伪码。
  - 失败形态（L160）：在线丢字段检测必须拦在答题之前（接「必填逼幻觉」）。
  - 边界（L183）：笔记 = 本任务状态 / 记忆 = 跨会话 / RAG = 外部只读知识，并展开 RAG 缩写。
  - 定义：`checkpoint`（L58）。
- **依据**：笔记 JSON 与伪码为构造示例；摘要 7/8、880 字/2776 token、1952/2272/4246、5/5 与 0/5 均为站内已有实测，未动。
- **仍未解决**：实测里那份「138 字摘要 / 880 字笔记」的**原文产物没有留存**，无法补出，只能给出等价的构造笔记；已在文中标注。

### 3.5 子智能体 ｜ 05-subagent-isolation.mdx
- **补了什么**：
  - 定义（L9）：子智能体 = 一次独立的模型调用序列（独立 system / 上下文 / 工具循环 / 轮次上限）；主 agent 的定义。
  - 判据（L24）：主上下文峰值的测量口径（取所有请求输入 token 的最大值）。
  - **重写代码**（L207）：删掉只做顺序直调、却声称「每个子任务一个子 agent」的 `with_subagents`，改为真正的最小实现 `run_subagent()`：独立 `messages`、自己的工具循环、独立 `max_rounds`、独立 JSON 收尾调用。
  - 产物（L304）：`{"did": [...], "failed": [...], "not_found": [...]}` schema + 主 agent 对三字段的处理 + 「只追加 dict、不追加原始轨迹」。
  - 步骤：`pick_relevant()` 把共享背景收窄；失败模式②接了 `failed` 字段的修法。
- **依据**：代码里的待检查项与规则为构造示例；主上下文峰值 1258 vs 6816、总 token 9182 vs 25913、8.1 倍 68548 vs 8430 均为站内已有实测，未动。
- **仍未解决**：`run_subagent` 是**可运行的最小实现**，但未在官方端点实跑（脚本头部与实跑状态已如实标注）；本节的 8.1 倍结论仍来自采集脚本，不是这段新代码跑出来的。

### 3.6 Chat Template ｜ 06-chat-template.mdx
- **补了什么**：
  - 产物（L47）：真实的 messages JSON 两版（合并成 1 轮 / 拆 10 轮 21 条），并说明差异来自 20 个角色边界。
  - 代码（L135）：把原来「收一个从未实现的 `render_and_count` 形参」改成真正能跑的 `input_tokens()`（发请求读 usage 三项）+ `compare_structures()`。
  - 判据（L161）：把含魔法数 `3` 的估算函数**明确定位为「只配用来建立量级直觉」**，与实测函数分开，消除「不要手写估算公式」与「给了估算函数」的自相矛盾。
  - 失败形态：第 18 章那个「插系统提醒断缓存」的真实错误保留；补实跑标注（L22）。
- **依据**：messages 示例为构造数据；238/298/234/254 与 25% 为站内已有实测，未动。
- **仍未解决**：无。

### 3.7 KV Cache ｜ 07-kv-cache.mdx
- **补了什么**：
  - 定义（L44 起）：自回归生成、注意力与 Query/Key/Value、KV Cache 为什么可复用；给出「只记加粗结论就够」的跳读提示。
  - 定义（L29）：`cache_control` 是什么；L94：`effort` 是什么、为什么参与渲染。
  - **代码替换**（L138）：把用 `json.dumps(tools)+system` 冒充「渲染后前缀」的 `diagnose_prefix` 换成以 `usage` 为准的三件套 —— `hit_rate()`、`cache_state()`、`request_fingerprint()`，并写明「渲染后 token 串只有服务端算得出，客户端只能做上界比较」。
  - 步骤（L163）：开发期三步排查（打 hit_rate 指标 → 比指纹 → 指纹相同才看厂商文档）。
  - **改一句错话**（L120）：「缓存读取单价只有基础输入价一成左右」→ 「因厂商与模型而异、本站不写死；教读者去账单里用 cache_read / input 用量乘单价算占比」。
- **依据**：1205/181/1024 与 6.7 倍为站内已有实测，未动；新增的全是机制与使用方法。
- **仍未解决**：客户端仍**无法精确指出缓存断在第几个 token**；文中明确说了这一点并给了 usage 侧的替代判据，没有假装能定位。

### 3.8 Agent Skills ｜ 08-agent-skills.mdx
- **补了什么**：
  - 产物（L22）：「skill 在磁盘上长什么样」—— 一个目录 + `SKILL.md`（YAML frontmatter 元数据 + 正文），给出 `amount-norm` 全文约 110 字，并指出它如何对应四个要点。
  - 产物（L101）：两阶段选择那轮的提示词（含「只输出标识符」）、返回示例（`select_skill`）、第二阶段拼正文。
  - 产物（L185）：两层索引的形态（第一层大类常驻、第二层组内描述），并说明「换组会断缓存」的代价与适用场景。
  - 判据：把「每个描述约 20 token」这个拍出来的数字换成「用一次请求读 usage 实测」，讲法对齐第 4 章。
  - 补实跑标注（L36）。
- **依据**：SKILL.md、索引、两阶段提示词为构造示例；5/5、4/5、3/3、516/148/201 为站内已有实测，未动。
- **仍未解决**：`SKILL.md` 是 Anthropic Agent Skills 的通用形态；站内资源库没有对应条目，正文按「常见形态」表述，未声称是唯一规范。

---

## 章 4 Tool Calling（5 节）

### 4.1 工具调用到底发生了什么 ｜ 01-what-really-happens.mdx
- **补了什么**：L15 补 `stop_reason` / `max_tokens` 的字段含义；L30 补半句「thinking 是模型的思考块，第 2 章讲过，下一轮必须原样带回」。
- **依据**：审计点名的两个小缺口，均为定义补充；实测报文未动。
- **仍未解决**：无。

### 4.2 工具描述即 prompt ｜ 02-schema-design.mdx
- **补了什么**：产物（L225）—— 把原来说「不到二十行」却没有的注册期自检写成可运行函数 `validate_tools()`（名字正则+唯一性、顶层 object、`required ⊆ properties`），并给出会触发它的坏 schema 与调用方式。另在 L86 首次提到 poka-yoke 处补了中英解释。
- **依据**：代码为自包含实现；三类 schema 错误的 400/200 结果为站内已有实测，未动。
- **仍未解决**：无。

### 4.3 poka-yoke：让错误在结构上不可能 ｜ 03-poka-yoke.mdx
- **补了什么**：
  - **明确两个前提**（L39）：编号不可枚举 + 与本次会话绑定；并指出只做存在性校验 = 假防护（这正是审计点名的「机制被夸大」）。
  - **代码替换**（L123）：`FILE_ID` 改成 `secrets.token_urlsafe` 发放、写进 `SESSION_FILES`；`delete_file` 只认本会话编号，且用完即作废防重放。
  - 产物（L240）：直接传 `f_002` / 传路径都被拒、正常路径可删、重复删被拒的输出示例。
  - 边界（L240）：单进程内存成立；跨服务必须换共享存储或 HMAC 签名 token。
  - 常见坑新增一条「只做存在性校验就以为防住了」。
- **依据**：拒绝日志与代码为构造示例；实测一/二的行为表（两个变体都没删、3/3 同传）为站内已有实测，未动。
- **仍未解决**：会话存储换成 Redis 或签名 token 的具体实现没有给完整代码（只给形态），因为那属于分布式存储的范畴，给了反而跑不了。

### 4.4 并行调用、错误处理与幂等 ｜ 04-parallel-and-errors.mdx
- **补了什么**：步骤与产物（L105）—— 幂等键在 LLM 循环里的注入实现：`idempotent(scope_id, tool_call_id, fn)` 包装工具函数、去重表命中即返首次结果；给出三种键作用域的对照表；点明流式整轮重放时 `scope_id` 必须来自客户端 request id，不能用服务端自增。
- **依据**：代码为构造示例；1 次/1 次、3/3 与 2/3 的失败回填对照、400 报文均为站内已有实测，未动。
- **仍未解决**：`_done` 用进程内字典演示，真实系统换 Redis 的 SETNX 语义只提了一句，未展开（属于分布式既有知识，不是 Agent 特有问题）。

### 4.5 工具数量的代价 ｜ 05-tool-count.mdx
- **补了什么**：
  - 定义与判据（L82）：`答案键` 的定义 + 「唯一且可机判」两条判据 + 把本节那题改写成无歧义版的正反对照 + 复核方法（让另一个模型列出所有能达成目标的工具）。
  - 产物（L120）：分组按需加载的最小实现（`CORE` 常驻 + `GROUPS` 场景组 + `select_tool_group` 路由 + `tools_for`），三个代价（断缓存 / 多一次调用 / 核心必须常驻），以及与 3.8 skill 两阶段的对照表。
  - 步骤（L291）：工具单价的生产监控做法 —— 带 tools 与不带 tools 各发一次，差值为定义成本，除以工具数得自己的单价。
- **依据**：分组代码与改写题为构造示例；678/1326/2623/4945、8/8、1/5 逐条复盘、64/200/600 → 3037/6077/17661 均为站内已有实测，未动。
- **仍未解决**：分组加载**没有独立实测**（只有成本侧实测、准确率侧未复现下降），所以正文把它定位为「成本优化」，没有声称能提升准确率。

---

## 改动的「明确错误」句子（只加不删原则的例外，共 2 处）

1. **3.7 L120**：原「缓存读取的单价通常只有基础输入价的一成左右」—— 无来源、无日期的价格数字，与站内「不写价格只教估算」的规范冲突，改为教读者从账单现算占比。
2. **4.3 L37**：原「`file_id` 只能从 `list_files` 拿到：你想删一个没看过的文件，连表达都表达不出来」—— 审计指出按当时实现（可枚举编号 + 存在性校验）并不成立，改为先声明两个前提，再用新实现满足它。

其余全部为新增，未删改任何实测数据、口径与日期。

## 纪律自查
- 未引入新的 MDX 组件；未动任何 frontmatter；Mermaid 图内无 Markdown 标记（`pnpm test` 的两条 Mermaid 断言通过）。
- 新增代码块全部标注语言（`depth-check` 的 W4 由 8 条降为 0）。
- 所有 `os.environ` 用法都已 `import os` 并在正文/注释交代需要哪几个环境变量、怎么拿。
- 全部新增产物均就地标注「（示例：构造数据，未实跑）」；未新增任何实测数字。

---

## 附：验收命令与原始输出

```text
$ node scripts/depth-check.mjs --chapter=context-engineering
## 术语首现无解释（0/3）

汇总：硬错误 0 条，建议项 0 条

$ node scripts/depth-check.mjs --chapter=tool-calling
## 术语首现无解释（0/3）

汇总：硬错误 0 条，建议项 0 条

$ node scripts/content-stats.mjs --chapter=context-engineering
context-engineering/01-context-is-finite         2794      4376   1   4  ✅
context-engineering/02-system-prompt-altitude    2905      4258   1   5  ✅
context-engineering/03-just-in-time              2567      4079   1   7  ✅
context-engineering/04-compaction                3006      4398   1   6  ✅
context-engineering/05-subagent-isolation        2670      4237   1   2  ✅
context-engineering/06-chat-template             2307      3452   1   7  ✅
context-engineering/07-kv-cache                  2231      3781   1   3  ✅
context-engineering/08-agent-skills              2416      3699   1   6  ✅
共 8 节，达标 8 节

$ node scripts/content-stats.mjs --chapter=tool-calling
tool-calling/01-what-really-happens              1877      3177   1   5  ✅
tool-calling/02-schema-design                    1764      3278   1   3  ✅
tool-calling/03-poka-yoke                        2134      3880   1   2  ✅
tool-calling/04-parallel-and-errors              2226      3502   1   5  ✅
tool-calling/05-tool-count                       2896      4822   1   4  ✅
共 5 节，达标 5 节

$ node scripts/content-stats.mjs | tail -2
共 134 节，达标 134 节（标准：中文≥1500 且 说明文字≥3000）

$ pnpm test
 ✓ tests/sse.test.ts (15 tests)
 ✓ tests/image-tokens.test.ts (4 tests)
 ✓ tests/inline-md.test.ts (5 tests)
 ✓ tests/depth.test.ts (2 tests)
 ✓ tests/curriculum.test.ts (41 tests)
 Test Files  5 passed (5)
      Tests  67 passed (67)

$ node scripts/verify-depth-fixes.mjs
✅ 没有实质性的字数下降
（context-engineering 净增 21340 字符；tool-calling 净增 8067 字符）
```
