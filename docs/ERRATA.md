# 勘误登记

每项会改变读者结论的纠错使用稳定编号。原始观测、旧评分、解释与新证据分开记录；勘误未验证前保持 `investigating`，不可写成已确认的事实。

状态：`investigating`、`verified`、`rejected`。`verified` 必须附验证方法或来源与日期。

| ID | 小节 | 旧结论 / 问题 | 修正方向 | 状态 | 验证 |
|---|---|---|---|---|---|
| ERR-001 | `mcp/03-stateless-2026`、`mcp/04-build-a-server` | 规范版本、错误码、MRTR 报文形状与请求关联规则需要对照固定版本官方规范核实 | 以官方规范及兼容实现重新验证；保留自定义协议示例为明确标注的本地约定 | verified | 2026-10-19 对照 [2026-07-28 base spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/index)、[MRTR](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)、[tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)；官方 Python SDK 2.3.0 与教学 stdio server/client 双向跑通 tools/list、tools/call；手写 MRTR 回归通过 |
| ERR-002 | `capstone/02-skeleton` | 审批后宿主重入若未正确暂停/恢复或把拒绝当完成，可能产生错误成功状态 | 明确 `input_required`、`denied`、完成状态与重复执行语义，覆盖首步/中间步/末步审批 | verified | 2026-10-19 执行正文代码及新增“审批后停止后续步骤”场景，8/8 断言通过 |
| ERR-003 | `structured-output/02-json-schema-strict` | Schema 字段存在、类型、业务规则和事实正确性可能被混为一层，端点观测可能泛化 | 按保证层拆分结论，并限定已实测端点与严格模式 | verified | 2026-10-19 逐段核对约束层次、实测端点范围及表格结论；未新增未经实跑的厂商能力结论 |
| ERR-004 | `evaluation/02-pass-k` | `Pass@k` 未校验 `k <= n`；若干指标描述需区分估计量与观测事件 | 加边界校验，明确任务聚合与运行数，按代码重算输出 | verified | 2026-10-19 固定种子代码输出为单次 91.0%、Pass@5 100.0%、Pass^5 60.0%、bootstrap 区间宽 11.0pp；函数现拒绝 `k>n` 与每题运行数不等于 k |
| ERR-005 | `evaluation/10-confidence` | 单比例区间精度公式被称为版本差异的“分辨”样本量；缺少比较设计、power 等条件 | 限定为单比例估计精度；比较实验单独声明设计参数与独立单位 | verified | 2026-10-19 用 `ceil(4·1.96²·p·(1-p)/delta²)` 独立重算 p=.9、全宽 1/2/5/10pp，得到 13,830 / 3,458 / 554 / 139；正文明确不用于版本差异检验 |
| ERR-006 | `human-in-the-loop/03-interrupt-and-resume` | 数据库或 Redis 状态操作可能被误读成外部副作用的原子保证 | 区分同库事务与外部调用；补 outbox、外部幂等、未知状态和对账边界 | verified | 2026-10-19；`examples/reliability` 用两个独立 SQLite 数据库模拟接收方，覆盖外部调用前崩溃与接收方提交后、本地回执落库前崩溃；恢复后一次投递。只证明依赖接收方唯一键去重的教学模型，不证明真实网络或生产数据库语义；见 `exp-outbox-task-retry-sqlite-model` |
| ERR-007 | `agent-deployment/01-deployment-shape` | 同步执行超时后再排队可能重复运行同一任务 | 先持久化并调度唯一任务；HTTP 等待超时只返回同一任务标识 | verified | 2026-10-19；同一实验以 8 个并发请求提交相同 tenant/idempotency key，仅得到一个持久任务；两个竞争 worker 仅一个领取，等待后再次提交返回原 task id。SQLite 线程模型，不覆盖多进程部署与租约过期 |
| ERR-008 | `human-in-the-loop/01-automation-levels`、`capstone/02-skeleton` | 可逆性被写成审批的唯一依据 | 将影响范围、金额、敏感度、主体授权与可逆性合并到策略判据 | verified | 2026-10-19 核对策略函数边界用例与审批章节；高影响可逆动作可复核，越权动作拒绝，低风险放行仍受明确授权限制 |
| ERR-009 | `coding-agent/01-why-coding-agent` | 对验证信号的绝对化表述超出证据范围 | 说明测试/编译是代理信号，并展示需求错误但测试通过的反例 | verified | 2026-10-19 将绝对表述改为局部可程序化信号，并加入缺少租户过滤但测试全绿的反例；检查结论与代码语义一致 |
| ERR-010 | `retrieval/01-why-retrieval` | 将 `0.497 token/字符` 解释为比 `1 token/字符` 更贵，算术方向错误 | 改为该样本中每字符平均 token 更少；避免把混合文本样本推广成中文通用比例 | verified | 比率比较：0.497 < 1；原始实测样本仍保留 |
| ERR-011 | `what-is-an-agent/what-counts-as-agent` | 将 workflow 的成本优势写成精确可预测，并让成本可预测性看起来像 workflow/agent 的定义依据 | 回到控制流归属作为定义；成本表述改为相对更易估算，并注明输入、分支、重试、缓存、价格与计量口径仍影响实际账单；限定原实验仅支持其任务与端点内的观测 | verified | 2026-10-20 对照 [Anthropic Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) 对 workflow/agent 的控制流区分与成本/延迟取舍；修正文案保留 2026-09-24 原实测值，不改变样本或重算结果 |
| ERR-012 | `agent-paradigms/react-loop` | 把 ReAct 模型返回的 action/stop 信号描述成直接控制宿主继续或执行工具，弱化宿主控制权 | 明确模型提出动作/结束信号；宿主负责解析、授权、策略、预算、工具执行和状态转移 | verified | 2026-10-20 对照 [ReAct 原论文](https://arxiv.org/abs/2210.03629) 的 thought/action 交替，以及本文采用的工具调用运行模型；这是架构语义校正，未修改实测代码和观测 |
| ERR-013 | `llm-api-basics/tokens-and-context` | 将上下文容量约束与计费 usage 混为一谈，并把输入 + 输出当作通用成本/容量口径 | 区分容量规划与供应商账单；公式限定为明确 API 语义下的近似，并说明 usage / 定价按模型、模态、缓存、reasoning 与工具维度核对 | verified | 2026-10-20 对照 [Anthropic context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)、[Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)、[OpenAI conversation state](https://developers.openai.com/api/docs/guides/conversation-state) 与 [Responses API usage](https://developers.openai.com/api/docs/api-reference/responses/object#responses/object-usage)；只调整概念说明，不改原实测 token 数 |
