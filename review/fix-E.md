# 深度修复报告 E：agent-loop / multi-agent / agent-frameworks

> 修复对象：`depth-E.md` 审计的三个章共 16 节。
> 改动范围：**仅** `src/content/chapters/agent-loop/`、`multi-agent/`、`agent-frameworks/` 下的 `.mdx`。
> 未触碰 `meta.ts`、`body.ts`、`src` 其它文件、其它章。
> 日期：2026-10-12。行号为写报告时的文件行号。

---

## 0. 验收（本人实跑，输出附后）

| 命令 | 结果 |
|---|---|
| `node scripts/depth-check.mjs --chapter=agent-loop` | 硬错误 0 / 建议 0，术语首现无解释 0/3 |
| `node scripts/depth-check.mjs --chapter=multi-agent` | 硬错误 0 / 建议 0，术语首现无解释 0/3 |
| `node scripts/depth-check.mjs --chapter=agent-frameworks` | 硬错误 0 / 建议 0，术语首现无解释 0/1 |
| `node scripts/verify-depth-fixes.mjs --chapter=<三章>` | 三章均「没有实质性的字数下降」 |
| `pnpm test` | **4 files / 65 tests 全绿** |
| 占位符巡检 | 三章无 `@@`、无 `@@CODE@@/TODO/待补` |

验收输出（摘）：

```text
### depth agent-loop          汇总：硬错误 0 条，建议项 0 条   EXIT=0
### depth multi-agent         汇总：硬错误 0 条，建议项 0 条   EXIT=0
### depth agent-frameworks    汇总：硬错误 0 条，建议项 0 条   EXIT=0

### verify:depth
改动文件 5 / 净增 15452 字符   ✅ 没有实质性的字数下降
改动文件 6 / 净增 10962 字符   ✅ 没有实质性的字数下降
改动文件 5 / 净增  8139 字符   ✅ 没有实质性的字数下降

### pnpm test
 Test Files  4 passed (4)
      Tests  65 passed (65)
```

**content-stats：16 节全部上升（中文 / 说明文字，基线 → 修复后）**

```text
agent-loop/01  2267/3083 → 3139/5143      multi-agent/01  2150/3017 → 2576/3603
agent-loop/02  2233/3092 → 2563/3612      multi-agent/02  2072/3034 → 2369/3474
agent-loop/03  2212/3146 → 2735/4028      multi-agent/03  2200/3015 → 2719/3778
agent-loop/04  2311/3271 → 2498/3600      multi-agent/04  2380/3150 → 2779/3751
agent-loop/05  2093/3001 → 2416/3675      multi-agent/05  2179/3008 → 2516/3547
                                          multi-agent/06  2073/3017 → 2328/3443
agent-frameworks/01  2508/3411 → 2590/3649
agent-frameworks/02  2152/3037 → 2495/3610
agent-frameworks/03  2374/3709 → 2608/4058
agent-frameworks/04  2310/3223 → 2917/4188
agent-frameworks/05  2305/3128 → 2647/3611
```

> 注：`git status` 里还有大量其它章的改动，那是并行批次的工作，本次未触碰。

---

## 1. 本次新增的实跑数据（2026-10-12，全部可复现）

脚本都写在 `verify-output/`（已 gitignore）。写入正文的部分都标了「本次实跑 2026-10-12」。

| 数据 | 来源脚本 | 写入哪节 |
|---|---|---|
| 真实两轮工具调用：TURN1 `stop_reason=tool_use` + `usage{input 320, output 81}`；TURN2 `end_turn` + `usage{input 175, cache_read 256, output 27}`；完整 messages 数组 | `probe-tooluse.py`（stdlib urllib，deepseek-flash） | agent-loop/01 |
| 两条 400 原文：漏 `tool_result` / `tool_use_id` 不匹配 | `probe-400.py` | agent-loop/01 |
| 只读并发 + 副作用串行调度：0.81 秒 | `probe-sched.py` | agent-loop/02 |
| 信息增量判据：第 3 轮判定无进展 | `probe-progress.py` | agent-loop/03 |
| 崩溃恢复：孤立 `tool_use` 补 `tool_result` | `probe-recover.py` | agent-loop/04 |
| LangGraph 1.2.14 最小状态图 + checkpoint JSON；轨迹 `['search','fetch','fetch','summarize']` | `probe-langgraph.py`（venv） | agent-loop/05 |
| 链 / 图 / 自主三种抽象同轨迹 | `probe-three.py`（venv） | agent-frameworks/02 |
| 并发读-改-写：裸版「期望 8 实际 1」，锁版「实际 8」 | `probe-concurrency.py` | multi-agent/06 |
| 硬约束断言 + 长度分布 | `probe-assert.py` | multi-agent/04 |
| `--baseline` 脚手架 + 退回信号探针 | `probe-harness.py` | multi-agent/05 |
| AST 检查签名渗透：1 处 | `probe-ast.py` | agent-frameworks/05 |

**构造数据一律就地标注**（示例：构造数据，未实跑）：multi-agent/01 的两份、03 的回查工具、04 的断言与切分表、05 的脚手架、06 的来源字段、agent-frameworks/01 的两处、03 的登记表、05 的 AST 示例源码、agent-loop/04 的崩溃现场。multi-agent/05 的工具形状标注为「示例：伪代码，说明形状，不可直接运行；真实项目里用第 13 章那套工具装饰器」。

---

## 2. 逐节修复

### 第 11 章 agent-loop

#### 01 最小循环 ｜ 审计等级 B
- **定义**：ReAct（15 行）；`stop_reason` 首现即解释（33 行代码注释 + 76 行正文）；`system 提示`（219）；`schema`（227）；`协议层`（230）；`max_tokens`（69 行注释）。`call_model / tool_use_blocks / tool_result` 三个接口点给出职责（43–49）。
- **产物/步骤**（53–199）：新增「真模型那一侧」整节。① 只依赖 `urllib` 的可运行调用函数（含 `ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / VERIFY_MODEL` 三个环境变量来源说明与 `import os`）；② TURN1、TURN2 原始响应 JSON 逐字贴出；③ 回填后的完整 `messages` 数组（user → assistant tool_use → user tool_result），旁注 `tool_use.id ↔ tool_result.tool_use_id`；④ 假模型字段 ↔ 真实字段映射表（159–170）；⑤ `tool_use_id` 写错/漏 `tool_result` 的 400 原文与判据（172–184）。
- **依据**：本次真跑（API）；站内已有实测在第 4 章（引用非新增）。

#### 02 工具注册表 ｜ A
- **定义**：`动作空间`（69）；`poka-yoke`（79，给「防呆」类比）；`tool_use_id`（144，首现即解释）。
- **产物/步骤**（146 起）：新增「『可并行』这个标记落在哪」。给出注册表条目字段 `parallel_safe`（含默认值 `False` 与理由）、自包含可运行的 `dispatch`/`backfill` 调度代码、实跑输出（0.81 秒）、`{tool_use_id: result}` 的判据。
- **依据**：字段设计=判据推导；调度代码=本次真跑。

#### 03 预算与循环检测 ｜ B
- **定义**：`token`（13，含第 1 章「7 字符 35 token」类比）；`截图指纹`（26，解释指纹=压缩后的可比短值）。
- **步骤/产物**：新增「token 从哪来」（22–46）：`add_usage` 累加 `input/output/cache_read/cache_creation` 四项，说明用 `input+output` 做预算判据、`cache_read` 算容量不算全价；用第 1 节真跑数据算出「两步任务处理 859 token 的量」。
- **判据/失败形态**：新增「补上盲区：信息增量判据」（80–117）：`result_keys` + `ProgressGuard`（键集合差集，连续 N 轮无新键判无进展）+ 实跑输出 + 两个已知缺口 + `tighten()` 收紧预算代码。
- **依据**：usage 数字=本次真跑（同一 endpoint）；判据代码=本次真跑。

#### 04 状态与持久化 ｜ A
- **补掉审计点名的矛盾**：新增说明块，明确前面实验「只把 `step` 落盘」是为隔离变量的实验设计，不是推荐的持久化格式（120 行）。
- **步骤/产物**（118 起）：新增「把『补一条 tool_result』写成代码」——自包含可运行的恢复脚本 `orphan_tool_uses / repair`，读回完整 messages、扫描孤立 `tool_use`、补「状态未知」的 `tool_result`，并贴出补完后的两条消息原文与实跑输出。
- **依据**：恢复脚本=本次真跑（含「示例：构造数据，未实跑」标注）。

#### 05 你写的这些，框架替你做了什么 ｜ B
- **产物**（92 起）：新增「真框架长什么样：LangGraph 的最小状态图」——真框架代码（`StateGraph` + `add_conditional_edges` + `InMemorySaver`）、实跑轨迹、**checkpoint JSON 原文**（`channel_values / channel_versions / updated_channels`）、`get_state().next/metadata.step`，并逐条说明框架藏起了什么。`checkpointer` 就地定义。
- **依据**：本次真跑（venv 安装 langgraph 1.2.14）。

### 第 12 章 multi-agent

#### 01 三种拓扑 ｜ B
- 修正「唯一被验证」的断言为工程判断并给理由（15）。
- **产物**（115 起）：新增「主管的提示与工人的回传格式」——完整主管 system 提示（含「逐条检查冲突 / 结论带来源编号 / 无法判断保留冲突」三条约束，示例标注）；工人结构化回传 JSON（`worker_id/doc_id/key_points/must_keep/not_found`）；「错误有归属」的定位字段要求（91）。
- 补 `stop_reason / max_tokens` 首现解释（153）。
- **依据**：构造示例（已标注）。

#### 02 成本模型 ｜ A
- 给「压成很短的约定」具体实现：≤10 条清单 + 由小模型跑一次 BG（82）。
- **产物**（145 起）：新增「把 usage 拆开，自己复算一遍」——`split_usage` 三类拆分 + `multiplicity` 公式 + 用第 1 节真跑的 input/output/cache 复算（预测 3.46 / 3.62），并说明与实测 1.91–1.99 的偏差来自输出占比与缓存计价。
- **依据**：usage 数字=本次真跑；倍数为**公式预测**（正文明确标注非实测）。

#### 03 真正的收益是隔离 ｜ B
- 把「注意力不被稀释」改写为可解释的「容量不被挤占」，`context rot` 就地定义并说明第 3 章未复现（21）。
- **产物**（63 起）：新增工人回传 JSON（`doc_id/worker_id/key_points/must_keep[].{text,kind,source_span}/not_found`）+ 三条字段判据（可校验 / 不可空 / 可追溯原文位置）+ `must_keep.kind` 三类；新增「回查通道是一个工具」的 `ask_worker` 定义与判据（88）。
- 补 `is_error` 解释（96）。
- **依据**：构造示例（已标注）。

#### 04 边界上的三种失败 ｜ B
- **产物**（107 起）：新增「把检查点一写成能在 CI 里跑的断言」——`check_constraint`（字符串包含）+ `length_outliers`（中位数 + 绝对偏差）+ 实跑输出 + 断言失败措辞说明；新增「第二个失败的切分维度对照」表（按地区 vs 按时间，数字为构造）。
- **依据**：断言脚本=本次真跑；切分表=构造示例。

#### 05 先别用：三个替代方案 ｜ B
- **产物**（39 起）：替代二给工具形状（标注为伪代码 + 替代路径）；替代三给自包含可运行的 workflow 代码 + 实跑输出。
- **产物**（152 起）：新增「一个可复用的基线脚手架」——`--baseline` 分支 + `measure` + `retreat_signals` 两个探针，实跑输出。把「三个退回信号」从判据变成可算的探针。
- **依据**：harness 实跑（输入构造，已标注）；workflow 本次真跑。

#### 06 协作层三种失败 ｜ B（含 W3）
- `Jaccard 相似度` 就地定义（99，0.24 的含义）。
- **产物**（38 起）：新增可复现的并发读-改-写脚本（`threading` + 显式 sleep）与实跑输出「期望 8 实际 1」「锁罩住读-改-写 → 8」；并自曝第一版把 `lock.acquire()` 放在「读」之后的 bug。
- **产物**（167 起）：级联失败的来源标注字段 `source / derived_from / as_of` 与回溯判据。
- 补「本次实跑 2026-10-12」标注，消除 W3。
- **依据**：并发脚本=本次真跑；来源字段=构造示例。

### 第 13 章 agent-frameworks

#### 01 框架替你做了什么 ｜ A
- **删掉重复段**（见 §4）。
- `args_schema` 就地解释 + 说明未使用的 `ChatAnthropic` 导入（248）。
- **产物**：四类能力展开成「能力清单」表（25，右列必须逐条回答）；新增「三个问题各自的验收动作」与「有无可观测性的输出差别」（57 起）。用来补偿删重复后的字数，使该节仍净增。
- **依据**：清单/输出为构造示例（已标注）。

#### 02 三种抽象模型 ｜ B
- **产物**（99 起）：新增「三种抽象的可运行对照」——链（LCEL）/ 图（LangGraph）/ 自主 agent 三份实现产出同一轨迹，附控制流位置表、与第 11 章手写循环的逐段对应、以及「链写不出未知次数循环」的判据。
- 把节末 schema 实验的标题改为「附：schema 生成实验（与第 1 节同一份实跑）」并说明它与链/图/自主无关（193），消除「产物与论题错位」。
- 补 `stop_reason` 解释。
- **依据**：三抽象对照=本次真跑。

#### 03 抽象在哪里泄漏 ｜ A
- **产物**（82 起）：新增「泄漏登记表」字段（`need / workaround / scope / breaks_other / repro / cleanup`）+ 一行完整示例 + 每字段判据，接回第 5 节迁移成本。
- **依据**：构造示例（已标注）。

#### 04 反方立场 12-Factor ｜ B
- **产物**（25 起）：新增 12 条完整清单表（每条含自测问题），并给原文外链。
- **统一 enum 叙述**（54）：证据三加「更准确的机制见第 3 节末尾修正」的指向。
- **补成本**（60、62）：`MCP` 就地展开 + 两个维护动作；第二、三薄弱处各配具体代价。
- **依据**：12 条标题来自官方 README（本文档已核）。

#### 05 选型矩阵与迁移成本 ｜ A
- `escape hatch` 就地定义（16）。
- **产物**（213 起）：新增「把『渗透进签名』变成一条能跑的检查」——`ast` 脚本（只统计函数参数/返回注解里的框架符号）+ 实跑输出（1 处 / 1 个函数）+ 判据（0 处可迁移 / >0 处属于业务层），并说明它补上了 `grep` 只数文件数的缺口。
- **依据**：AST 脚本=本次真跑；示例源码=构造（已标注）。

---

## 3. 未完全解决 / 保留的点

1. **multi-agent/01 的「唯一被大规模验证」**：无法给出可核实的出处（审计也只要你说明「谁验证、多大规模」）。本次改成「工程经验判断 + 你要自己验证」，未伪造来源 —— **这是表述降级，不是补齐出处**。
2. **multi-agent 01–05 仍共用同一份成本实验代码**（审计称 md5 `2fe029ae`）。按「只加不删」没有删除它；改为**每节新增一节与本节论题对应的可运行产物**（01 提示/回传、02 复算、03 结构/通道、04 断言/切分、05 脚手架/workflow），并在 02 说明该实验是成本对照。若要彻底拆分共享代码，需要删除或改写既有实测脚本，超出「只加不删」约束。
3. **agent-loop/05 的 checkpoint 来自 `InMemorySaver`**，不是磁盘持久化文件；正文如实写成「checkpoint 内容」而非「持久化文件」。跨进程恢复的真实验证未做（需要 SQLite/Postgres saver），未写入。
4. **multi-agent/04 的长度分布探针**用的是「中位数 + 绝对偏差」，样本仅 3 个工人，阈值 k=2 是经验值，未做敏感性实验 —— 正文只把它当「信号」而非「判据」。
5. **multi-agent/05 的脚手架倍数是 1.25x**（构造输入）。它演示的是**流程**，不是真实成本；正文已注明。

## 4. 「只加不删」的例外（唯一一处）

- `agent-frameworks/01` 删除了**文内完全重复的第二份**（原「一个常被忽略的成本」+「一份可以逐条过的清单」，审计 E3-01 明确要求「删掉重复的那一份」）。这是审计点名的错误，不是实测数据；为满足「字数不下降」，已在同节补入「能力清单表」「三问验收动作」「可观测性对照」三块，使该节中文 2508→2590、说明 3411→3649 仍为净增。

## 5. 运行脚本位置（gitignore，不随正文发布）

`verify-output/probe-tooluse.py`、`probe-400.py`、`probe-sched.py`、`probe-progress.py`、`probe-recover.py`、`probe-langgraph.py`、`probe-three.py`、`probe-concurrency.py`、`probe-assert.py`、`probe-harness.py`、`probe-ast.py`。其中凡写入正文的代码，均已去掉对 `verify-output/` 的依赖（正文里 `repro` 用通用脚本名 `check_tool_schema.py`），保证读者可自包含运行。
