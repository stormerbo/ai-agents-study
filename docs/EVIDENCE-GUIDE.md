# 实验与论断证据指南

本目录把可复核的观测、正文解释和教学建议分开登记。登记只覆盖高风险论断，不表示未登记内容已完成准确性审计。截至 2026-10-19，登记包含 8 条高风险论断与 9 项实验：首批 4 条论断/5 项实验覆盖 W1，第二批增加 Retry-After 下限、PostgreSQL 备份校验范围、provider fixture 证据边界，以及 OpenAI Structured Outputs 拒绝/不完整响应契约。全书其余论断尚未完成登记或准确性复审。

## 证据类型

| 类型 | 能支持什么 | 不能支持什么 |
| --- | --- | --- |
| `deterministic-local` | 固定输入下的代码行为、公式与输出 | 真实模型能力或线上厂商行为 |
| `postgres-integration` | 本机真实 PostgreSQL、独立 OS 进程与真实事务/竞争测试 | 生产数据库、高可用、真实身份提供方或 provider 能力 |
| `real-online` | 记录的端点、模型标识、请求参数和时间下的在线观察 | 浮动模型别名未来行为不变 |
| `raw-replay` | 解析、状态机和评分逻辑对已保存原始响应的行为 | 重新调用模型的能力 |
| `synthetic-fixture` | 离线控制流与故障分支 | 真实数据分布或模型质量 |
| `official-documentation-review` | 固定版本官方资料明确规定的接口行为 | 本地兼容端点一定实现正确 |
| `raw-observation-review` | 保留观察的算术、口径与适用范围 | 原始观察未记录的因果解释 |

回放与合成 fixture 不得计入真实模型能力结果。PostgreSQL 集成需单独标为 `postgres-integration`。官方文档支持、数据库集成、本地 fixture 和 provider 在线观察分别记录，即使两者都通过也不能合并成无范围的“已验证”。

## 登记约定

- `experiments/registry.json` 记录问题、lesson、代码围栏位置与 SHA-256、数据/评分版本、运行方式、预期不变量和结果路径。代码 hash 对应完整围栏内容，不含围栏标记。
- `experiments/results/<id>/result.json` 保存脱敏结果、方法、日期和限制。真实在线结果还需增加 provider、协议、endpoint（移除凭据）、请求/响应模型 id、参数、usage、结束原因、运行耗时与重复次数。
- `experiments/claims.json` 为高风险正文论断记录原文片段、文本 hash、适用条件、来源、实验、勘误和复核状态。source id 必须来自 `resources.ts`。
- `result.schema.json` 的顶层字段是结果记录白名单；`tests/evidence-registry.test.ts` 对 `observations` 递归执行字段 allowlist 和高置信度敏感值扫描。添加新观测字段须先审查并显式更新 allowlist，不得把日志或原始 transcript 整体写入结果。
- 新结果先以 `needs-review` 登记；首个人工复核完成前不得作为可发布证据或把状态改为 `verified`。`reviewedAt` 记录首次人工复核日期，尚未完成复核时必须为 `null`；登记/运行日期放在 result 记录中。该日期不能代替对方法、脱敏、限制和证据分类的人工判断。
- `experiments/errata.json` 与 `docs/ERRATA.md` 使用相同稳定勘误编号；勘误处于 investigating 时，关联记录不得标记为已关闭。
- 改动正文或示例后，受影响 claim/experiment 应转为需复核并更新 hash。不可只刷新日期来保留旧验证状态。

## 当前边界

`pnpm verify:evidence` 检查当前登记的 lesson、source、实验、勘误引用，claim 原文和 hash，以及代码围栏 hash 与结果文件链接。`pnpm verify:examples` 只运行 `examples/manifest.json` 中显式登记的条目，校验入口 hash，使用临时目录、固定 30 秒上限和不继承 API Key 的环境；它不执行 MDX 中任意围栏。`tests/evidence-registry.test.ts` 使用 Ajv 2020 对 claims、experiments 和全部 result 文件分别执行对应 JSON Schema；同时校验 lesson/source/errata/experiment 关系、正文文本 hash、围栏/脚本 hash 和结果关联。当前登记仍只是高风险样本，不代表全书证据已齐。
