# Stage 5 隔离冷启动与 PostgreSQL integration 记录

日期：2026-10-20（Asia/Shanghai）  
执行者：本次实现者（不是独立接手者）  
用途：记录 RUNBOOK 部署路径的本地可执行性；**不是发布、live provider 或独立交接证据**。

## 输入快照

- 仓库 HEAD：`1a7c942009ed768ca620904b8cc64a7d9d291d9b`。
- 工作区当时包含未提交改动；执行时从该工作区导出 P4、P5 和 `support_agent` 三个目录到临时隔离目录，不含 `.git`、密钥或已有 `.venv`。
- 快照共 82 个文件。清单算法：按相对路径排序，对每个文件计算 SHA-256，再依次将 `相对路径 + NUL + 文件 SHA-256 + LF` 写入 SHA-256 累计器。结果：`58d56ec2c4c2b0505e141e1e2a023d338f17b860b005c2b3b274e54774f5a19c`。
- 临时路径：`/tmp/p5-stage5-clean-run.tztC4n`。测试已结束；临时目录未作为发布材料保存。

## 环境与操作

- macOS arm64；Python 3.11.14；uv 0.12.15；Docker Engine 29.3.1；Docker Compose 5.1.1。
- 在隔离副本运行 `uv sync --frozen`：成功安装 24 个锁定依赖。
- PostgreSQL 18.0：Compose health check 通过；`uv run python -m app.db migrate` 与 `seed` 成功；合成检索语料、provider endpoint 和 budget account 初始化成功。
- 从该快照构建 API 与 sink 镜像成功。`/health/ready` 对 API 与 sink 均返回 ready；API 创建的 Alice 合成任务返回 `queued`，随后 GET 仍为 `queued`，release id 为 `p5-local-smoke-v1`。
- 在隔离副本运行 `uv run --frozen pytest -m integration -q`：**123 passed, 17 deselected**，耗时 125.60 秒；唯一 warning 是 Starlette 关于 `httpx` 测试客户端的弃用提示。
- 清理了本次专用 Compose 容器、网络与 PostgreSQL volume。没有配置 provider 凭据，也没有发出模型请求。

## 结论边界

这次结果证明：RUNBOOK 的依赖安装、容器构建、数据库初始化、API/sink readiness、合成任务 API 路径，以及当前快照中的 P4 PostgreSQL integration suite 可运行。快照源于 dirty worktree，测试由实现者执行；它不能证明某个已冻结 Git commit 可从全新 clone 复现，也不能替代独立接手者、真实 provider smoke、人工 review、holdout 或发布审批。Task 3 与 Stage 5 仍保持 open。
