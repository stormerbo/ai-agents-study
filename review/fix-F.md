# 深度批次 F 修复报告（MCP 协议 + 评估）

> 执行时间：2026-10-12。
> 范围：**只改** `src/content/chapters/mcp/` 与 `src/content/chapters/evaluation/` 下的 `.mdx`（共 16 个文件）。未碰其他章、未碰 `meta.ts`、未碰 `src` 其他文件、未加 MDX 组件与 frontmatter 字段。
> 依据：`docs/CONTENT-DEPTH.md`（五要素）＋ `review/depth-F.md`（逐节审计）＋ `AGENTS.md` §3.2。
> 数字纪律：新增数字只有两个来源 —— 站内已有实测（`verify-output/*.py` 的实验脚本/输出）与本次真跑；构造出来的报文、配置、用例 JSON 一律就地标注 **（示例：构造数据，未实跑）**。

## 验收输出

```text
$ node scripts/depth-check.mjs --chapter=mcp
## 术语首现无解释（0/1）
汇总：硬错误 0 条，建议项 0 条            -> exit 0

$ node scripts/depth-check.mjs --chapter=evaluation
汇总：硬错误 0 条，建议项 0 条            -> exit 0
（E1/E2/E3/E4 全为 0；W 建议项由修复前的 6 条降到 0 条）

$ node scripts/verify-depth-fixes.mjs --chapter=mcp
改动文件 5 / 未改动 0，净增 14727 字符
没有实质性的字数下降

$ node scripts/verify-depth-fixes.mjs --chapter=evaluation
改动文件 11 / 未改动 0，净增 20517 字符
没有实质性的字数下降
```

`content-stats` 对照修复前（中文 / 说明文字）：16 节全部上升，无一下降。选摘：

| 节 | 修复前 | 修复后 |
|---|---|---|
| mcp/01-why-protocol | 2227 / 3713 | 2825 / 4796 |
| mcp/02-roles-and-capabilities | 1772 / 3104 | 2307 / 4066 |
| mcp/03-stateless-2026 | 2134 / 3551 | 3253 / 5596 |
| mcp/04-build-a-server | 1616 / 3051 | 1845 / 3514 |
| mcp/05-security-boundary | 2423 / 3719 | 3017 / 4755 |
| evaluation/04-contamination | 2164 / 3058 | 3013 / 4419 |
| evaluation/05-eval-env | 2142 / 3004 | 2456 / 3422 |
| evaluation/06-ablation | 2109 / 3079 | 2904 / 4414 |
| evaluation/10-confidence | 1959 / 3174 | 2453 / 4050 |
| evaluation/11-regression | 2253 / 3240 | 2998 / 4453 |

```text
$ pnpm test
Test Files  4 passed (4)
Tests       65 passed (65)
```

`pnpm test` 最终 **65/65 全绿**（4 个测试文件）。过程中有一次瞬时失败来自 `agent-frameworks/05-selection-matrix.mdx`（并发批次正在写该文件，**不在我负责的章内**）；对方修好后重跑即全绿。

---

## MCP 章

### mcp/01-why-protocol ｜审计等级 A
- **补**：
  - 术语首现解释：`stdio`（L58，展开为「标准输入输出」，说明换传输只换管道）、`_meta`（L61 后新增一段，说明它是 `params` 的保留元信息字段）、`tool_use / tool_result` 与 `MRTR`（新增小节「那一跳具体长什么样」，L105）。
  - 新增 host 侧适配函数 `handle_tool_use`（L134 起）＋ `tools/call` 请求/响应两条原始 JSON（L116–L130）。
  - 新增「怎么把它跑起来」（L305）：`printf | python3 mcp_server.py` 手工路径＋指向第 4 节 `Client`。
- **依据**：报文为**构造示例**（已标注）；适配函数与第 4 节 `Client` 形态一致。
- **仍未解决**：无。

### mcp/02-roles-and-capabilities ｜审计等级 B
- **补**：新增「三类能力长什么样」（L91）—— `resources/list`（uri/name/mimeType）、`resources/read` 往返、`prompts/list`（含 `arguments`）与用户选择后的渲染结果；写明 resources 内容拼进 system 或首条 user 消息；补「三类能力如何合并进同一次模型调用」；给出**权限桶的可执行写法** `ALLOW` 查表函数。L30 的「权限桶」就地解释。
- **依据**：报文为**构造示例**（已标注）。第 4 节 server 未实现 resources/prompts，已在正文说明，避免读者以为能直接跑。
- **仍未解决**：无。

### mcp/03-stateless-2026 ｜审计等级 A（本批最严重）
- **补**：
  - 新增「回程报文长什么样（MRTR 的另一半）」（L99）：第一次 `tools/call` 请求（含 `_meta`）＋ `input_required` 响应＋**第二次完整请求**（原样带回同一 `id`、回答放 `params.inputResponses` 并按 `inputRequests[].id` 对应）＋第二次响应；补 `id` 对不上时的处理。
  - **醒目标注**：`_confirmed` 是本节自造字段、非规范字段，并加一条常见坑。
  - 三种不顺利回程形态表：拒绝 / 超时 / 部分满足（含「MRTR 可往返多轮、收敛条件是 complete 或报错」）。
  - 新增 `server/discover` 时机与缓存三条规则（L199）、`subscriptions/listen` 报文形态（L209）、迁移 before/after 代码对照（L226）。
- **依据**：报文为**构造示例**（已标注「不是从规范逐字抄来」）；`_confirmed` 与 `input_required` 行为来自本节实现（实跑数据 2026-10-09）。
- **明确错误的句子（已改并在此说明）**：L144 原有笔误多打了一个反引号（`_meta` 后跟了两个），已删掉多余的那个。
- **仍未解决**：规范里回答字段的**确切键名**无法从站内核实，正文已显式声明「以对方规范/实现为准」，没有把 `inputResponses` 说成规范字段。

### mcp/04-build-a-server ｜审计等级 A（最透）
- **补**：新增「怎么把 server 注册进 host」（L316，`mcpServers` 配置形态）与「host 侧那一跳」（L334，15 行适配函数），补上审计点名的唯一缺口（模型 tool_use -> JSON-RPC -> 回填）。
- **依据**：配置与适配为**构造示例**（配置已标注；适配函数与本节 `Client` 接口一致）。
- **仍未解决**：配置文件字段名随 host 不同，正文已注明。

### mcp/05-security-boundary ｜审计等级 B
- **补**：新增「把五条落成代码」（L229）：完整 `tools/call` 请求（让读者看到「你发出去的整个请求」）＋工具白/黑名单拦截函数 `gate()` ＋数据流脱敏 `redact()` ＋容器最小权限启动命令 ＋组合风险 `DANGEROUS_COMBOS` 整体拒绝。
- **依据**：请求/命令/函数为**构造示例**（报文与启动命令已标注）；组合风险场景沿用本节正文原有例子。
- **仍未解决**：容器命令未在本机 docker 实跑（正文已说明它能挡住什么、挡不住什么）。

---

## 评估章

### evaluation/01-define-good ｜审计等级 A
- **补**：`LLM-as-judge` 首现解释（L61）；「反例从哪翻」及无追踪时先做第 11 节第一周；「判据放哪、怎么被 CI 调起」（L250）＋ `evals/run_criteria.py` CI 入口。
- **依据**：CI 入口为**构造示例**；结构沿用本节已有 `CRITERIA/judge`。
- **仍未解决**：无。

### evaluation/02-pass-k ｜审计等级 A
- **补**：bootstrap 置信区间机制解释（L182 前）；「一道题长什么样」三道完整题目（题面/期望来源/判定，L84）；环境终态判定解释；「加检查点与重试」最小可运行示例。
- **依据**：三道题来自本节已有 `EXP`（题干为重构，已标注「构造数据，未实跑」）；第 5 行实测表与 100% 数据未动。
- **仍未解决**：其余 8 道题的答案仍未列全（与已有 `EXP` 一致，未新增）。

### evaluation/03-dataset ｜审计等级 A
- **补**：用例 JSON 五字段（id/question/expected/source/added，L121）＋ `evals/` 目录布局；三个环境变量出处（`VERIFY_MODEL / ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN`，指回第 1 章与 `.env.local`）；污染机制解释；`max_tokens / stop_reason` 解释。
- **依据**：用例 JSON 与目录为**构造示例**（已标注）；环境变量名与本机 `.env.local` 及 `scripts/verify-api.mjs` 一致。
- **仍未解决**：已有实跑输出块缺「题量 8」那一行（代码会打印它），属于修复前就存在的粘贴疏忽；**未改动已有实测数据**，仅记录。

### evaluation/04-contamination ｜审计等级 B
- **补**：**few-shot 定义**（zero/one/few-shot，说明示范与评测集物理分离）＋ 一段带分界的示范提示词；三种消融的提示词 diff（原样/删掉/换无关）；「掉多少算泄漏」用区间口径；配平代码 `balance()`；留出集的执行方式（独立目录、不进 CI）；卡方/自由度/7.81 的机制；两道真实生成题展示「换皮」。
- **依据**：提示词与配平为**构造示例**（提示词已标注）；卡方 16.80、B 占 60%/73.7%、62.5%/95%、19->6 均为站内已有实测；两道生成题取自 `verify-output/eval-gen-raw.json`。
- **仍未解决**：无。

### evaluation/05-eval-env ｜审计等级 B
- **补**：`initial_state` 真实 JSON；把 `run_case` 签名统一为 `run_case(initial_state, case, agent_fn)` 并补 env 构造；新增验证器 `validate()`、终止条件 `should_stop()`、隔离方式说明；三条自检改为同一签名并真正并发 4 路；修掉标题与内容错位的「质数倍的分布」->「换并发度再跑一遍」。
- **依据**：**本次真跑**（2026-10-12）：修复后的骨架 + 自检脚本在本机 `python3` 跑通，输出「环境自检通过」；开头 3/5 实验仍为 2026-10-09 实测。
- **仍未解决**：无。

### evaluation/06-ablation ｜审计等级 B
- **补**：列全**8 条机器可校验约束原文**（L12 后）；新增可直接使用的 `metric_fn()`（正则判 8 条）；「什么算一个组件」边界判据；冗余/互补/拮抗的**结果判读表**；结果记录 JSONL 格式；`marginal_effect` 的边际效应定义。
- **依据**：8 条约束与任务原文取自 `verify-output/eval-env-ablation.py`；**本次真跑** `metric_fn` 自检（合规 8 / 带表头 2 / 截断 7，2026-10-12）；冗余那一行来自本节实测，互补/拮抗两行标注为**构造示例**。
- **仍未解决**：完整 `run_fn` 仍是指向模型 API 的接口（正文已交代它接哪个函数、8 条约束与判分函数均给全），没有在本机重跑整套 API 消融。

### evaluation/07-paired-comparison ｜审计等级 A
- **补**：A/B 两个提示词全文与共用任务原文；**7 条约束清单**（可运行 `score()`）；依赖型任务怎么切（配对单位改成一次完整执行、每次重置初始状态）。
- **依据**：提示词、任务、判分函数取自 `verify-output/eval-paired.py`（实跑原文）；248.6/206.8/p=0.145 等数字未动。
- **仍未解决**：无。

### evaluation/08-llm-as-judge ｜审计等级 A
- **补**：`评分量规` 定义 ＋ 1/3/5 三档「可观察行为」示例；一致率计算式与告警阈值（区间半宽）＋记录 JSON；补 V2/V3 两组实验原文材料。
- **依据**：V2/V3 材料取自 `verify-output/eval-judge-verbosity.py`；量规与一致率记录为**构造示例**。
- **仍未解决**：一致率的告警阈值没有给具体数值（标注量不足），正文给的是判据而非硬阈值。

### evaluation/09-traces ｜审计等级 A
- **补**：`is_error` 字段解释；**一条存储后的轨迹 JSON**（step/tool/args/result/tokens_in/out/ms）；agent 循环里的插入点；1%–10% 采样的落点代码；「失败轨迹 -> 用例」转换函数（含人工接口 `reverse_expected`）。
- **依据**：轨迹 JSON 为**构造示例**（已标注）；字段与本节原有实测例一致；转换函数为可运行示意，依赖 `from datetime import date`。
- **仍未解决**：无。

### evaluation/10-confidence ｜审计等级 A
- **补**：`Clopper-Pearson` 实现 ＋「Wilson 够用」判据；多重比较（Bonferroni / BH-FDR）与主指标声明规则；「持续积累几周」的监控记录形态。
- **依据**：**本次真跑**（2026-10-12）：40 次全通过时 Wilson 下界 91.24% / CP 91.19%；26/30 时 Wilson [70.32%, 94.69%] / CP [69.28%, 96.24%]。原 13,830 / 554 / 91.2% 等实测数字未动。
- **仍未解决**：无。

### evaluation/11-regression ｜审计等级 B（本批最严重）
- **补**：最小 CI 工作流（触发条件 push/release、命令、退出码约定）；基线 JSON 格式（用例 id、通过与否、model/prompt/env 版本、日期、ci90 区间）；temperature 四问（是什么/在哪设/为何 0 不消除/3 次成本）。
- **改**（口径冲突，审计点名）：代码里把区间宽度与半宽分开算，裁决显式使用半宽；正文加「口径提醒」；「常见坑」那条由「±20 个点」改写为「宽度约 20（半宽 ±10）」。**原有数值一个未改。**
- **依据**：CI/基线 JSON 为**构造示例**（已标注）；**本次真跑**（2026-10-12）修正后脚本：噪声宽度 20.4、半宽 ±10.2，三个改动的裁决仍全部落在噪声内（与原文结论一致）。实跑输出块按新代码重跑后同步，数值未变。
- **仍未解决**：正文那句「±20.0 个百分点」与脚本打印的 20.4 之间有 0.4 的既存误差；因该行属已有实测口径、**按纪律未删改**，只在正文加了一句「脚本按同一公式打印 20.4，这里约作 20」。

---

## 未能修复 / 遗留

1. **无（`pnpm test` 最终 65/65 全绿）。** 过程中的一次失败来自并发批次的 `agent-frameworks/05-selection-matrix.mdx`，非本批次范围，对方已修。
2. **规范字段名无法核实**（mcp/03 的 `inputResponses`、`subscriptions/listen`）：站内没有规范原文，只能给「本节约定的形态」并显式声明。
3. **evaluation/03 实跑输出块缺「题量 8」一行**：代码会打印该行，粘贴块漏了；未删改已有实测，故保留原样。
4. **evaluation/11 的 20.0 vs 20.4**：见上。
5. **depth-check 的「术语首现无解释」仍报 Pass^k / stop_reason / max_tokens**：这三处已在正文各自补了机制解释，但脚本的 CUE 正则不识别我的句式 —— 属机器启发式误报，非内容缺失。
6. 我**没有**重跑任何 API 实验（无新增 API 实测数字），所有新增「实测」声明都来自站内已有实验或本地无依赖脚本的本次真跑。

## 未触碰
- 未改 `meta.ts`、未改 ``body.ts`、未改 ``src` 其他文件、未加 MDX 组件或 frontmatter 字段、未在 Mermaid 图内引入 Markdown 标记（未新增 Mermaid 图）。
- 未删改任何已有实测数据、口径与日期（仅一处明确笔误与一处审计点名的口径表述按说明修正）。
