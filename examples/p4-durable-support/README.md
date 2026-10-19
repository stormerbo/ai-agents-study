# 阶段 4：持久任务服务（Task 1）

这是独立于学习站的本地合成售后服务。目前实现 PostgreSQL 任务提交、可信身份边界、幂等与事件续读；任务停在 `queued`。worker、审批决定、检索生命周期、预算、outbox 与 HTTP sink 属于后续任务，尚未实现，不能据此宣称阶段 4 或综合项目完成。

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
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

第二个终端可运行第二个 API 进程（设置同一个 `DATABASE_URL`）：

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 --no-access-log
```

迁移按 SQL 文件名顺序运行，用数据库事务 advisory lock 串行化，并登记 checksum；已应用文件被改写会失败。seed 可重复执行但不会恢复已经撤销的身份或角色。应用不自动 migrate/seed，readiness 会拒绝未迁移数据库。停止手工服务后清理：

```bash
docker compose down --volumes --remove-orphans
```

容器可从仓库根目录构建：`docker build -f examples/p4-durable-support/Dockerfile -t p4-support .`。容器需显式提供数据库地址，发布端口时绑定 `127.0.0.1`；默认 Compose 只启动数据库。数据库账户是本地教学初始化账户，不提供生产最小权限或 RLS 保证。

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
| `GET /v1/tasks/{uuid}/approvals` | 501 | 仅预留身份/owner 校验边界；Task 2 才实现审批列表与决定 |
| `GET /health/live` | 200 | 无需认证，不依赖数据库 |
| `GET /health/ready` | 200 | 无需认证，检查 PostgreSQL 可连接且基础迁移已登记 |

任务视图包含 `id`（UUID）、`tenant_id`、`owner_id`、`status`、`state_version`、`release_id`、`created_at`（UTC 时间戳），不返回 prompt。Task 1 新建状态只有 `queued`。

事件页为 `{"events":[{"seq":1,"kind":"task.created","payload":{"status":"queued","release_id":"stage4-local-v1"},"redaction_version":"synthetic-v1","created_at":"..."}],"next_after":1}`。返回 `seq > after`，`next_after` 是最后返回的 seq；空页保留输入 after。下一次传入该值，允许重读但不会因服务重启改变游标。超前游标返回空页。此任务只提供轮询，没有 SSE。

幂等作用域为 `(tenant_id, caller_id, idempotency_key)`。Pydantic 校验并补默认值后，用排序 key、UTF-8、无多余空白的 canonical JSON 计算 SHA-256；字段顺序和显式/省略默认值等价，prompt 的首尾空白被归一化，Unicode 不做额外 NFC/NFD 合并。同作用域/同 key/同 canonical payload 返回原 task id 及当前任务视图；不同 canonical payload 返回 409，不创建新任务。同 key 的不同调用方互不冲突。事务 advisory lock 协调不同 API 进程，SQL 唯一约束与复合外键约束仍是最终约束。

任务、第一条 `task.created` 事件及幂等记录在同一事务提交，且 `Depends(..., scope="function")` 确保提交发生在发送成功响应之前。集成测试注入延迟到 COMMIT 的失败验证不会先返回 201。事件追加通过任务行锁分配 seq，`(task_id,seq)` 主键保证唯一，触发器拒绝 UPDATE/DELETE/TRUNCATE。内部存储 helper 只面向可信宿主代码，不是公开事件写入端点；后续 worker 会加 lease/epoch fencing。

| 状态码 | error.code | 说明 |
| --- | --- | --- |
| 401 | unauthenticated | 缺失或无效 bearer；带 `WWW-Authenticate: Bearer` |
| 403 | access_revoked | 当前身份停用或缺少 caller 角色 |
| 404 | not_found | 任务不存在或不属于当前 tenant/owner，避免暴露存在性 |
| 409 | idempotency_conflict | 同幂等 key 的 canonical payload 不同 |
| 422 | validation_error | 非法字段、额外身份字段、UUID、游标、长度或缺失 key |
| 501 | approvals_unavailable | 有权访问任务，但审批工作流尚未实现 |
| 503 | database_unavailable / schema_unavailable | 数据库不可用、事务失败或基础迁移未登记 |

## 共享运行时

`../support_agent/providers.py`、`tool_gateway.py`、`runtime.py` 从阶段 3 提取。阶段 3 的 `controlled_agent.py` 仅作兼容入口，CLI、MCP server 与原有测试继续复用。Messages 规范化契约保留 `final / tool_calls / refusal / truncated / transport_error` 与原始 `stop_reason`；未知 block/stop 组合报协议错误。runtime 继续沿用阶段 3 对外状态 `completed / refused / truncated / transport_error / protocol_error` 等；`completed` 只是此只读 CLI 的回合结果，不能直接提交为阶段 4 业务任务完成。

工具名先经过只读 allowlist，参数执行前按 schema 的受支持子集验证；未支持的 schema 关键字、错误类型、缺字段、多余字段、越界 enum 均失败关闭。验证失败不会调用 MCP。runtime 不直接授权写入，也不把 MCP description 当权限。模型连接/超时/SDK 上游错误保留为独立失败且仅记录异常类型，不保存异常正文；不支持的程序异常继续抛出便于定位。此任务仅接入共享边界，没有替阶段 4 调用真实模型。

实现时核对的官方资料（2026-10-19）：[Psycopg 事务](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)、[FastAPI yield 依赖 scope](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#early-exit-and-scope)、[Compose healthcheck](https://docs.docker.com/reference/compose-file/services/#healthcheck)。
