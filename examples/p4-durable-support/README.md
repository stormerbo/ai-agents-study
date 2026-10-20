# 阶段 4：持久任务服务（Task 1–3）

这是独立于学习站的本地合成售后服务。Task 1–2 已实现 PostgreSQL 任务 API、租约/epoch worker 所有权、冻结动作与审批恢复、合成 ACL 检索和索引切换、并发限制与共享预算。当前完整 API 入口为 `app.runtime:create_app --factory`；`app.main:app` 保留 Task 1 兼容契约，其提交入口不执行 Task 2 的队列准入检查，不用于完整服务。模型调用仍需可信宿主显式注入，worker CLI 只领取一次任务，没有自动调用模型。Task 3 增加 transactional outbox、本地合成 HTTP sink、持久去重回执与未知结果对账。`authorized_pending_delivery` 仍是不可投递的 Task 2 交接态，须经 `outbox.schedule` 原子建立投递工作。阶段 4 的整体验收与证据登记仍待 Task 4，不能据此宣称阶段 4 或综合项目完成。

## 环境与安装

需要 Python 3.11+、`uv`、Docker Engine / Docker Desktop 与 Docker Compose v2（支持 `up --wait`）。依赖在 `pyproject.toml` 精确锁版本，完整传递依赖及分发包 hash 在 `uv.lock`。PostgreSQL 镜像固定为 `postgres:18.0-bookworm`；容器构建固定 Python 与 uv 版本。此处固定版本用于复现教学实验，公开部署前需独立评估维护与补丁。

以下命令均从本目录执行：

```bash
cd examples/p4-durable-support
uv sync --frozen
uv run pytest -m 'not integration' -q
uv run pytest -m integration -q
```

最后一个命令是必需的 PostgreSQL 集成入口。pytest 自动创建独立 Compose project 与临时数据库卷，选取本轮固定的 loopback 端口，等待数据库健康，运行版本迁移与合成 seed，独立启动两个 uvicorn OS 进程，并在成功或失败后关闭 API、删除该 project 的服务与卷。测试包含 API 重启与 PostgreSQL 停止后的 readiness；不会改动手工启动的数据库。Docker、镜像、PostgreSQL 或 API 不可用会导致命令非零退出，不会 skip 或回退到 SQLite。首次运行需拉取镜像。测试不能与 `pytest-xdist` 并行分片共享此服务。

离线测试只检查合成 provider 响应和控制流，不启动数据库、不调用模型。集成测试证明本机 PostgreSQL/HTTP 进程的事务、权限与竞争不变量，不证明生产 IdP、PostgreSQL RLS、网络分区、高可用或供应商能力。没有模型调用，不能推导模型质量或价格。Task 4 才登记实验结果与更新全站示例 manifest。

## 手工运行与迁移

固定主机端口使数据库 stop/start 后地址仍有效；端口冲突时改为其他空闲端口。`.env.example` 仅作模板，应用不自动读取站点 `.env.local`。这里的数据库密码和 bearer token 都是公开合成凭据，不要替换为客户数据后继续使用。

```bash
export P4_POSTGRES_PORT=55432
docker compose up -d --wait --wait-timeout 90 postgres
export DATABASE_URL=postgresql://support:local-only-demo@127.0.0.1:55432/support
uv run python -m app.db migrate
uv run python -m app.db seed
export PYTHONPATH=..
uv run uvicorn app.runtime:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

第二个终端可运行第二个 API 进程（设置同一个 `DATABASE_URL`）：

```bash
export PYTHONPATH=..
uv run uvicorn app.runtime:create_app --factory --host 127.0.0.1 --port 8001 --no-access-log
```

迁移按 SQL 文件名顺序运行，用数据库事务 advisory lock 串行化，并登记 checksum；已应用文件被改写会失败。seed 可重复执行但不会恢复已经撤销的身份或角色。应用不自动 migrate/seed，readiness 会拒绝未迁移数据库。停止手工服务后清理：

```bash
docker compose down --volumes --remove-orphans
```

容器可从仓库根目录构建：`docker build -f examples/p4-durable-support/Dockerfile -t p4-support .`。容器需显式提供数据库地址，发布端口时绑定 `127.0.0.1`；默认 Compose 只启动数据库。Dockerfile 默认 CMD 保留 Task 1 兼容入口；下面的 runtime profile 显式覆盖为完整 Task 2 factory。数据库账户是本地教学初始化账户，不提供生产最小权限或 RLS 保证。

## 身份与授权

`Authorization: Bearer <token>` 的本地映射：

| 公开 demo token | tenant / caller | 初始角色 |
| --- | --- | --- |
| `dev-alice` | tenant-a / alice | caller |
| `dev-bob` | tenant-a / bob | caller |
| `dev-approver` | tenant-a / approver | caller, approver |
| `dev-mallory` | tenant-b / mallory | caller |

token 比较使用 `hmac.compare_digest`，逐一比较全部候选。身份由该映射建立，当前 active membership 与角色每次从 PostgreSQL 读取；token 不缓存授权。身份行 share lock 保持到请求事务结束，与撤权/角色变更的提交顺序构成授权边界；已开始并持有该锁的请求可先结束，撤权提交后的新请求必须拒绝。任务读取同时限制 tenant 与 owner；其他调用方即使同租户也不能读该任务。请求 JSON 不接受 `tenant_id`、`caller_id`、`owner_id`、`roles` 等额外字段。

该映射是公开本地演示身份提供方，不是 OAuth/JWT 或真实安全凭据。应用仅在 loopback 运行。API 不接收真实客户输入；详细合成输入存于任务表，事件不复制 prompt，校验错误与数据库错误不回显输入、SQL 或 DSN。

## HTTP 契约

所有任务路由要求 bearer。错误统一为 `{"error":{"code":"...","message":"..."}}`，OpenAPI 可在 `/openapi.json` 查看。

| 路由 | 成功 | 行为 |
| --- | --- | --- |
| `POST /v1/tasks` | 201 新建；200 重放 | 必须有 `Idempotency-Key`（1–200 字符）；JSON 为 `prompt`（去首尾空白后 1–8000 字符）、可选 `release_id`（默认 `stage4-local-v1`，1–100 字符） |
| `GET /v1/tasks/{uuid}` | 200 | 返回 owner 可见的任务视图 |
| `GET /v1/tasks/{uuid}/events?after=0&limit=100` | 200 | 严格按 seq 升序读取；`after` 为非负整数，`limit` 为 1–100 |
| `GET /v1/tasks/{uuid}/approvals` | 200 | owner 可读的审批列表，含动作 id、冻结资格、有效期与状态 |
| `POST /v1/tasks/{uuid}/cancel` | 200 | owner 停止未投递任务；终态返回 409 |
| `POST /v1/approvals/{uuid}/decision` | 200 | JSON `decision=approved/denied`；由 bearer 决定审批身份；要求冻结的 eligible approver 与当前 approver 角色 |
| `GET /health/live` | 200 | 无需认证，不依赖数据库 |
| `GET /health/ready` | 200 | 无需认证，完整入口检查 PostgreSQL 可连接且 `0002_execution.sql` 已登记 |

任务视图包含 `id`（UUID）、`tenant_id`、`owner_id`、`status`、`state_version`、`release_id`、`created_at`（UTC 时间戳），不返回 prompt。新建状态为 `queued`；领取、审批等待、恢复、失败与取消均持久化，事件按任务行锁分配序号。

事件页为 `{"events":[{"seq":1,"kind":"task.created","payload":{"status":"queued","release_id":"stage4-local-v1"},"redaction_version":"synthetic-v1","created_at":"..."}],"next_after":1}`。返回 `seq > after`，`next_after` 是最后返回的 seq；空页保留输入 after。下一次传入该值，允许重读但不会因服务重启改变游标。超前游标返回空页。此任务只提供轮询，没有 SSE。

幂等作用域为 `(tenant_id, caller_id, idempotency_key)`。Pydantic 校验并补默认值后，用排序 key、UTF-8、无多余空白的 canonical JSON 计算 SHA-256；字段顺序和显式/省略默认值等价，prompt 的首尾空白被归一化，Unicode 不做额外 NFC/NFD 合并。同作用域/同 key/同 canonical payload 返回原 task id 及当前任务视图；不同 canonical payload 返回 409，不创建新任务。同 key 的不同调用方互不冲突。事务 advisory lock 协调不同 API 进程，SQL 唯一约束与复合外键约束仍是最终约束。

任务、第一条 `task.created` 事件及幂等记录在同一事务提交，且 `Depends(..., scope="function")` 确保提交发生在发送成功响应之前。集成测试注入延迟到 COMMIT 的失败验证不会先返回 201。事件追加通过任务行锁分配 seq，`(task_id,seq)` 主键保证唯一，触发器拒绝 UPDATE/DELETE/TRUNCATE。内部存储 helper 只面向可信宿主代码，不是公开事件写入端点；Task 2 worker 的所有权写入另经 lease/epoch fence，不向外部提供通用事件写接口。

| 状态码 | error.code | 说明 |
| --- | --- | --- |
| 401 | unauthenticated | 缺失或无效 bearer；带 `WWW-Authenticate: Bearer` |
| 403 | access_revoked | 当前身份停用或缺少 caller 角色 |
| 404 | not_found | 任务不存在或不属于当前 tenant/owner，避免暴露存在性 |
| 409 | idempotency_conflict | 同幂等 key 的 canonical payload 不同 |
| 422 | validation_error | 非法字段、额外身份字段、UUID、游标、长度或缺失 key |
| 403 | approver_required | 当前角色或冻结的 eligible approver 不符合 |
| 409 | approval_conflict / task_terminal | 重复、冲突、过期审批、deadline 已过或任务已停止 |
| 429 | queue_full | 队列已满，带 `Retry-After: 1`；相同幂等提交仍可重放 |
| 501 | approvals_unavailable | 只存在于 Task 1 兼容入口 |
| 503 | database_unavailable / schema_unavailable | 数据库不可用、事务失败或基础迁移未登记 |

## 共享运行时

`../support_agent/providers.py`、`tool_gateway.py`、`runtime.py` 从阶段 3 提取。阶段 3 的 `controlled_agent.py` 仅作兼容入口，CLI、MCP server 与原有测试继续复用。Messages 规范化契约保留 `final / tool_calls / refusal / truncated / transport_error` 与原始 `stop_reason`；未知 block/stop 组合报协议错误。runtime 继续沿用阶段 3 对外状态 `completed / refused / truncated / transport_error / protocol_error` 等；`completed` 只是此只读 CLI 的回合结果，不能直接提交为阶段 4 业务任务完成。

工具名先经过只读 allowlist，参数执行前按 schema 的受支持子集验证；未支持的 schema 关键字、错误类型、缺字段、多余字段、越界 enum 均失败关闭。验证失败不会调用 MCP。runtime 不直接授权写入，也不把 MCP description 当权限。模型连接/超时/SDK 上游错误保留为独立失败且仅记录异常类型，不保存异常正文；不支持的程序异常继续抛出便于定位。此任务仅接入共享边界，没有替阶段 4 调用真实模型。

实现时核对的官方资料（2026-10-19）：[Psycopg 事务](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)、[FastAPI yield 依赖 scope](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#early-exit-and-scope)、[Compose healthcheck](https://docs.docker.com/reference/compose-file/services/#healthcheck)。

## Task 2 运行与边界

迁移、基础 seed 后，显式建立合成资源（重复执行不会复活已删除资源或撤销权限）：

```bash
PYTHONPATH=.. uv run python - <<'PY'
from app.config import Settings
from app.db import connect
from app.retrieval import seed_corpus
with connect(Settings.from_env().database_url) as conn:
    seed_corpus(conn)
PY
uv run python -m app.worker --once --owner local-worker-1
```

`--task <uuid>` 可指定已提交任务；多个 worker OS 进程可连接同一个数据库。领取发生在独立事务中，每次接管递增 `execution_epoch`，默认租约 30 秒、任务 deadline 为创建后 5 分钟。`worker.fence(conn, lease)` 先锁任务行，再以 `clock_timestamp()` 核对 owner/epoch/租约/deadline/取消/运行状态，返回 `None` 的写入影响零行。宿主需在自己的短事务内调用 `renew/checkpoint/emit/propose_turn/authorize_action`；helper 不自行提交。claim/续约同时维护 task slot，审批暂停、终态、取消和 deadline 释放 slot。CLI 不循环、无隐式模型调用；宿主可用共享 provider adapter + `consume_response` 驱动规范化响应，再用 `resume_turn/execute_reads` 恢复冻结动作。Task 3 提供显式一次性投递与对账入口，见下文。

Compose 默认仍只启动 PostgreSQL。迁移与 seed 后可用已配置的完整 API profile，镜像已包含 `PYTHONPATH`：

```bash
docker compose --profile runtime up -d --build api
docker compose run --rm worker --once --owner compose-worker-1
```

可信注册表保持 Stage 3 MCP 签名 `lookup_order(order_id)` 与 `search_policy(query)`，资源分别由服务端映射到订单 id 与 `policy-public`。共享 `provider_tools` / schema validator 限制只读 MCP 边界；新增 `send_notice(resource_id,message)` 仅指本地合成 sink，始终要求审批。模型不能自填风险等级、身份或 approved 字段。一次响应的每个调用都有独立 action id（模型 tool_call_id 仅用于结果关联）；任一调用需要审批时，整个 turn 保存 pending ids 后暂停，不填充成功占位结果。冻结保存租户、动作、canonical args hash、资源/ACL/policy 版本、唯一 eligible approver、requested_by 和有效期。审批决定用任务/审批行锁串行化；重复点击、冲突决定和过期决定返回 409。拒绝使任务失败，批准后回到 queued，由新 worker 从冻结动作恢复。读取工具只执行存储参数，已持久化的结果不重复调用；所有动作解决前不能 completed。

只读 MCP 调用在结果持久化之前采用 **at-least-once** 恢复语义：远端读取已经返回，但 worker 在保存结果前失去租约时，旧 worker 仍被 fence 拒绝写入动作、事件和检查点；后继 worker 可按同一冻结参数重试该无副作用读取。读取完成不等于结果已可靠保存，也不意味着远端 exactly-once。结果及检查点提交后，后续恢复复用持久结果，不再调用该工具，也不重放整段模型历史。每次实际重试仍需独立预算预留；该规则只适用于无副作用读取，不能用于写入投递的未知结果恢复。

授权重检当前身份、资源 ACL、资源/ACL/policy 版本、参数 hash、审批有效期和当前审批人资格。任何变化都使旧动作失效。`authorized_pending_delivery` 仅为 Task 2 的待交接状态：该转换不会建立 outbox 或发送网络请求。Task 3 的 `schedule` 在同一受 fence 保护的事务里把可调度动作转换并插入 outbox，派送前再重查授权。Task 3 已扩展 dispatching/unknown 的取消与对账语义，见下文。

`retrieval` 是小型合成词法检索，没有 embedding 或质量声明。tenant/caller 来自 principal；SQL 在候选选择及 LIMIT 前联接当前 membership、resource ACL、删除状态和 active index。上下文引用保留 resource_id、doc_version、chunk id。索引采用完整替换快照：`build_index` → `validate_index`（内容 hash）→ `cutover`（同事务激活新索引、退役旧索引），旧版本显式查询也被拒绝。删除/撤权立即在查询层拒绝，清除结果缓存与相关记忆；缓存和记忆只保存 provenance，绝不跳过当前查询授权返回旧正文。生命周期操作与上下文构造使用同租户事务 advisory lock 作为本地授权顺序边界；这不是 PostgreSQL RLS 或跨系统原子性保证。

`service_limits` 控制全局 queued 上限与运行 task slot 上限，完整 API 在准入锁内检查容量，幂等重放不占新位置。每任务同时只有一个 epoch slot。`provider_endpoints` 配置端点并发与最大尝试数；`acquire_provider` 在端点行锁内分配，响应处理后以受 owner/epoch 保护的 `release_provider` 释放供应商 slot、保留任务所有权；`schedule_429` 只接受可信 adapter 解析的 Retry-After 和 `[0,1]` 秒抖动采样，持久化 next_retry_at，过 deadline 或尝试数则失败并释放 slot。fixture 的 429 只验证调度逻辑，未验证任何真实供应商行为。

`budget_accounts` / `budget_reservations` 由可信宿主使用；发送前预留已知输入估计 + 输出上限、工具成本额度。`reserve` 在共享 account 的条件 UPDATE 中原子扣减可用额度；`mark_sent` 同样要求原 owner/epoch 有效。真实发送后的未知 usage 保留整笔 unknown reservation，重试须另预留；可靠 usage 通过 `reconcile` 核销，已知实耗超估计也如实记录并禁止继续超额预留。只有未发送的 reservation 可用 `release_unsent` 释放。消费、未知预留和可用余额分开报告；本地估计不是供应商最终账单的绝对上限。宿主不能跳过这些 helper 直接请求付费端点。模型发送宿主必须先提交 reservation/send intent，再跨网络发送；不能把预留仅放在可能回滚的长事务里。`execute_reads(..., budget_account=...)` 为每次 MCP 调用预留一个合成工具成本单位，并在调用前提交 sent marker；该协调方法有明确提交边界，不能包在更大的原子事务中。进程死亡后已发送预留保守保留，不能随 lease 失效释放。

Task 2 聚焦集成入口（同样创建独立 Compose PostgreSQL 并自动清理）：

```bash
uv run pytest -m integration -q tests/test_worker_ownership.py tests/test_approval_recovery.py tests/test_retrieval_acl.py tests/test_index_lifecycle.py tests/test_limits.py
```

完整回归入口保持 `uv run pytest -m integration -q`。测试包括 worker 强制进程死亡/租约接管、API 与审批等待 worker 重启、并发决定、七类冻结失效、ACL/删除前置过滤、索引切换、队列/slot/deadline、并发共享预算及未知用量保留。所有输入与响应均为合成夹具；不包含真实 provider 观测。Task 3 的 outbox/sink/对账另见下文；Stage 4 的整体验收与 Stage 5 真模型验收仍未完成。

## Task 3：合成投递、取消边界与对账

先运行全部迁移（包括 `0003_delivery.sql`）、基础 seed 与上文合成资源初始化，再启动独立接收进程：

```bash
uv run uvicorn app.sink:app --host 127.0.0.1 --port 8002 --no-access-log
```

Docker 路径在迁移后启动 `docker compose --profile delivery up -d --build sink`。接收端只写 PostgreSQL 的 `sink_effects` 合成记录，**不会发送真实通知**。公开的 `local-only-sink` bearer 是本地教学协议，不是生产接收方认证。HTTP 客户端拒绝非 loopback/Compose `sink` 的地址，不跟随重定向，不读取环境代理。两个进程共用教学 PostgreSQL，但接收事务与 outbox 事务完全独立，没有跨 HTTP 原子提交。

可信宿主在一个短事务中调用 `outbox.schedule(conn, lease, action_id)`：`worker.fence` 核对当前 epoch/租约/deadline，复用 `validate_frozen` 核对批准、参数 hash、资源/ACL/policy 版本，再同时提交 `action.authorized` 与唯一 queued outbox。稳定键为 `p4-notice:<action UUID>`；事务回滚不会留下单边动作或投递行。Task 2 的 `resume_turn` 继续只产生 `authorized_pending_delivery`，不会自动发送。模型结果中的通知参数不能直接越过此边界。

`delivery.dispatch_once(dsn, lease, action_id, sink_url)` 用另一个短事务重查当前 worker fence、任务取消、调用方权限、审批资格/有效期、冻结参数及资源版本，将动作/outbox 原子变为 dispatching，并为接收回执建立独立 dispatch token。这个**事务的提交**是授权判定时点：取消/撤权先提交，不能领取；领取先提交，则即使网络尚未发送，之后的取消/撤权也不能承诺撤回。领取后任务进入 reconciling，释放 worker slot；数据库锁不跨 HTTP 持有。

取消 queued outbox 将其标为 cancelled，停止新调用与新投递。已有 dispatching/unknown 时，API 返回 `status=reconciling`，记录 `task.cancel_requested`，保留已领取动作，等待真实结果；回执确认后才记录 `task.cancelled`。已经发生的合成效果不会被这一状态变化撤销。撤权在领取后只影响新的授权，不改变已领取请求。接收成功仅使动作 succeeded：没有取消时任务回到 queued，由新 worker 恢复检查点、补全其他动作并校验最终输出，**不会直接 completed**。

接收端在同一事务持久化 external_key、完整 payload hash、回执和合成效果；并发/重启后的同键同参数请求返回同一回执，参数替换返回 409。`GET /v1/receipts/<external_key>` 返回该持久回执；不存在时返回 404，并显式声明版本化 `p4-synthetic-durable-idempotency-v1` 与 `safe_retry=true`。单独一个 404 不足以证明安全重试。

网络/响应错误按 unknown 处理，不当成效果失败。`delivery.reconcile(dsn, action_id, sink_url)` 接管过期 dispatching/unknown token，**先查询接收方**；已有回执则按键、action、tenant、payload hash 和 outcome 校验后保存，没有回执且接收契约明确保证持久幂等时，才重试同一冻结请求。查询失败、协议未知或回执不匹配均保持 reconciling，不盲重试。dispatch token 过期/被接管后，旧 token 不能写回执；epoch 不能替代这一能力。接收方的持久去重保证这里的一个合成效果，本地 fencing 本身不保证远程 exactly-once。

可在审批通过、任务重新 queued 后，用一次性宿主命令领取、schedule 并发送指定合成动作；该 CLI 不轮询模型或队列：

```bash
uv run python -m app.delivery dispatch --action <action-uuid> --sink http://127.0.0.1:8002
uv run python -m app.delivery reconcile --action <action-uuid> --sink http://127.0.0.1:8002
# Compose 接收地址与容器主机地址不同：
docker compose run --rm dispatcher dispatch --action <action-uuid> --sink http://sink:8000
```

已被宿主领取的任务应直接使用持有的 lease 调 `schedule/dispatch_once`；CLI 不抢占有效 worker。dispatch token 默认有效 30 秒，进程崩溃后等其过期再对账。重试次数持久化；没有后台无限重试循环，单次 reconcile 最多查一次、按契约重试一次。不支持此接收契约的真实业务端点、人工核实工作流、通知撤销、自动补偿与生产部署均未实现；查不到可靠结果时任务保持 unresolved，须由后续明确设计的人工流程处理。

聚焦验证与完整回归：

```bash
uv run pytest -m integration -q tests/test_delivery_reconciliation.py tests/test_cancel_and_revoke_races.py
uv run pytest -m integration -q
uv run pytest -m 'not integration' -q
```

集成测试使用真实 Compose PostgreSQL、独立 sink/dispatcher OS 进程与 SIGKILL。注入点为 `before_claim`、`after_claim_before_send`、`after_sink_commit_before_receipt`：分别覆盖取消与撤权在三个时点的边界，以及发送前/接收提交后进程死亡。断言事件严格递增、任务状态、接收效果数量、查询先于重试、sink 重启后去重与 stale epoch 无权建立 outbox。只读 MCP 的 at-least-once 结果持久化边界保持上文契约。这些是本机数据库和合成 HTTP 协议证据，不是供应商或真实消息系统的保证。
