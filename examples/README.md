# 教学示例

这些示例与学习站分开运行。每个脚本由 `manifest.json` 显式登记；`pnpm verify:examples` 只运行登记的离线测试，校验入口 SHA-256，设置超时和临时目录，并且不把进程环境里的 API Key 传给测试。

## 第一轮只读 Agent

`first-loop/readonly_support.py` 调用 Anthropic Messages API 或兼容端点，只提供一个查本地合成订单的只读工具。真模型请求需要 `ANTHROPIC_AUTH_TOKEN`、`VERIFY_MODEL`，以及可选的 `ANTHROPIC_BASE_URL`。请从项目已忽略的 `.env.local` 或本地密钥管理器加载环境变量；不要把真实订单、密钥或客户信息放进示例。

离线控制流测试：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s examples/first-loop -v
```

测试使用固定响应来验证宿主循环，不代表模型选择工具的能力。需要在线证据时应单独记录端点、请求/响应模型标识、参数、usage、结束原因与重复次数。

## 检索索引生命周期

`index-lifecycle/index_catalog.py` 是一个本地 SQLite 目录模型，用于验证文档来源修订、内容 hash、删除 tombstone、generation 快照和活动指针切换。它不调用 embedding 或向量服务，也不证明跨进程/跨服务事务。运行 `pnpm verify:examples` 时会与其他显式登记的离线套件一起执行。

## 检索权限过滤

`permission-filtering/retrieval_access.py` 演示候选文档 ID 如何经可信 principal、租户和显式 ACL 检查后才读取正文。它是 SQLite 教学模型；生产身份校验、PostgreSQL RLS、向量服务过滤和缓存撤权仍需独立配置与集成测试。

## 持久任务执行权

`execution-ownership/task_ownership.py` 用 SQLite 条件写入演示租约到期后的接管、epoch fencing、迟到 worker 拒绝和 checkpoint。它不验证 PostgreSQL 多进程调度、跨机器时钟、真实外部副作用或接收方幂等；生产阶段仍需针对目标数据库和副作用服务做集成与故障注入测试。

## MCP 远程授权边界

`mcp-remote-auth/auth_policy.py` 对已完成密码学验证的合成 claims 判定 issuer、audience、expiry 和 scope，并演示 stdio 子进程环境变量白名单。它不实现 OAuth、JWT 签名验证、真实 HTTP middleware 或授权服务器互操作；生产授权链需使用目标 IdP 与 MCP SDK 单独做集成测试。

## Agent 身份与租户隔离

`identity-tenancy/access_policy.py` 用 SQLite 合成主体和资源演示可信 active tenant、每请求成员资格检查、同租户读取与 owner 写入。6 项负向/正向测试覆盖跨租户 IDOR、伪造请求 tenant、撤销成员、未知 action 和非 owner 更新。该模型不验证真实认证中间件、PostgreSQL RLS、连接池或生产授权矩阵。

## 综合项目验收门禁

`capstone-acceptance/acceptance.py` 检查 19 个固定 gate 的重复、缺项、失败、未验证状态和证据定位，并要求真模型 gate 使用 `live` 证据类型。验收器还校验冻结材料、盲测结果与 registry receipt、签名状态、外部状态新鲜度和双见证链；challenge reducer 只接受 v2 事件，并要求调用方分别提供已验证的 challenge trigger 与 resolution evidence 摘要，且 fresh snapshot 必须绑定到相应 source 或 policy/rule 及当前 environment/log；它只在上游已验证的事件前缀上派生状态，不验证签名、monitor 身份或实时 source。使用 `pnpm verify:examples` 在锁定的 Python 环境中运行离线套件。通过只证明仓库内合同实现符合固定测试，不证明外部 registry、身份服务、witness、隐藏数据隔离或真实 holdout 已通过；完整报告仍须人工验收，不自动批准发布。

## Provider 迁移门禁

`provider-migration/migration_gate.py` 验证内部状态分类、工具调用字段、拒绝/截断区分与 usage 缺失语义。6 项测试只验证固定 fixture 的判定逻辑，不发起模型请求，不构成任何 provider 的能力或质量证据。真实迁移报告应保存端点、模型、SDK、数据集版本、逐例结果与未验证能力。

## 并发准入与背压

`concurrency-backpressure/admission.py` 是确定性的本地策略模型：限制活动并发、队列长度、请求预算、重试次数和 deadline，并将 `Retry-After` 作为最短等待时间。7 项离线测试不运行真实并发 worker、provider SDK、分布式限额或端到端账单；生产系统仍需对目标 SDK 的自动重试、全局限流和取消行为做集成验证。

## 故障边界模型

`reliability/fault_models.py` 使用两个独立 SQLite 数据库模拟服务数据库与接收方，覆盖调用前崩溃、接收方提交后回执丢失、同键任务提交和竞争 worker 领取。它用于解释 outbox 与接收方幂等的条件，不代替 PostgreSQL、多进程部署或真实网络故障演练。

## 阶段 2：有依据的售后政策答复

`p2-grounded-support/grounded_support.py` 是不依赖第三方库的离线词法检索基线。它先按 principal、tenant、授权名单、有效期和删除标记筛选，再对有权候选做词项重合排序；答案直接摘录第一条原文，并附 `doc_id` 与版本。无候选时返回 `insufficient_evidence`。

运行 `PYTHONDONTWRITEBYTECODE=1 python3 examples/p2-grounded-support/grounded_support.py --evaluate` 可得到固定合成集的 `recall@k`、引用精确度、答案 exact match 和正确 abstain 数；默认 `top-k=3` 的引用精确度为 0.6667，使用 `--top-k 1` 时为 1.0（仅 3 条固定样例），展示候选数量对引用精确度的影响，不构成质量结论。测试覆盖租户边界、无答案、版本和有效期、删除抑制及指标计算。该基线用于让检索流程和评分口径可运行；词法重合不具备语义理解能力，固定集上的结果不能外推为线上质量。命令行的 principal 参数只用于合成演示，生产身份必须由认证边界提供，不能采信请求体中的主体或租户字段。阶段作业要求的真实 embedding 应作为独立实验替换检索器，并继续复用同一权限和评估边界。

## 阶段 3：受控的售后 Agent

`p3-controlled-agent` 使用官方 Anthropic Python SDK 和 MCP Python SDK：独立 MCP stdio 子进程只提供两个合成数据只读工具；Agent 宿主读取 MCP schema、只暴露 allowlist 工具、调用模型，并在执行前再次验证参数。循环默认最多 4 轮、4 次工具调用与每轮 512 个输出 token，CLI 可覆盖这些预算，自动重试关闭。平行工具调用会逐个返回匹配的 `tool_use_id`，遇到未知工具、非法参数或工具错误时主循环停止。

安装依赖并验证真实 MCP 协议：

```bash
uv sync --project examples/p3-controlled-agent
uv run --project examples/p3-controlled-agent python examples/p3-controlled-agent/cli.py --mcp-smoke
```

运行真模型闭环：

```bash
uv run --project examples/p3-controlled-agent python examples/p3-controlled-agent/cli.py --live
```

在线调用只使用 A-1001 等本地合成 fixture，不连接真实订单。脚本从被忽略的 `.env.local` 读取 `ANTHROPIC_AUTH_TOKEN`（或 `ANTHROPIC_API_KEY`）、`VERIFY_MODEL` 和可选 `ANTHROPIC_BASE_URL`；凭据不会传给 MCP 子进程。每次结果写入 gitignored 的 `verify-output/stage3-mcp/`，包含状态、端点主机、模型、SDK 版本、停止原因、工具名/参数校验/结果关联、token usage 与终止轮数；不会保存密钥、请求头或原始 HTTP 错误正文。线上报告仅证明该模型、端点和这次提示的有限工具往返，不能外推为普遍成功率。

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s examples/p3-controlled-agent -v` 的 9 项标准库测试只验证本地控制逻辑；`--mcp-smoke` 验证独立进程上的 `tools/list` 和 `tools/call`；`--live --max-rounds 4 --max-tool-calls 4 --max-output-tokens 512` 展示默认预算参数，只有 `--live` 报告才代表真实模型证据。

## 阶段 4：PostgreSQL 持久任务服务（Task 1–4）

`p4-durable-support/` 是基于 FastAPI + PostgreSQL 18 的本地合成服务。它实现 trusted principal、幂等任务/event API、lease/epoch worker、审批恢复、ACL 前置过滤与索引切换、并发/预算限制、transactional outbox、本地合成 HTTP sink、未知投递对账和 operator 审计关闭。`support_agent/` 是阶段 3/4 共用的 provider/tool/runtime 边界。

```bash
cd examples/p4-durable-support
uv sync --frozen
uv run pytest -m 'not integration' -q
uv run pytest -m integration -q
```

集成门禁 `uv run pytest -m integration -q` 自动启动临时 Compose PostgreSQL 与两个独立 API 进程，涵盖多进程幂等、重启恢复、租约竞争、审批、租户/ACL、预算、取消/撤权竞态、未知投递与人工对账；Docker、镜像、PostgreSQL 或任一门禁缺失都会非零退出。离线测试只证明 fixture/control-flow；PostgreSQL 集成证明本地服务事务与竞争行为；它们都不是 provider 能力证据。`pnpm verify:examples` 只运行 hash-pinned 的离线安全示例，不会启动该数据库集成。尚未调用真实模型，故不证明模型质量或真实系统行为；真实模型验收、独立接手、发布/回滚和冻结 holdout 评测仍属于阶段 5。详见 [`p4-durable-support/README.md`](p4-durable-support/README.md)。
