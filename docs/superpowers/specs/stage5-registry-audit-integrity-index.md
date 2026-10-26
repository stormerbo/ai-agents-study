# Stage 5 设计与合同索引

这份索引用于在协议说明、实施计划、机器可读 schema 和离线合同测试之间定位。它不增加新的运行时要求，也不表示对应服务已经部署。

## 先读什么

1. [课程可靠性总设计](./2026-10-19-curriculum-reliability-design.md)说明全书目标、阶段边界和验收口径。
2. [Stage 5 registry audit integrity 主规格](./2026-10-23-stage5-registry-audit-integrity.md)说明信任边界、事件/签名协议、身份授权、决策状态机、故障行为和生产验收矩阵。
3. [Stage 5 capstone 计划](../plans/2026-10-20-stage5-capstone.md)按工作包记录本地合同与未来生产验收的完成状态。计划中的复选框统计整个 Stage 5 交付，不是设计文档完成率。

主规格处于文档/协议设计阶段。JSON Schema 和离线合同测试只验证形状与部分纯函数语义；它们不证明真实服务身份、密钥保管、角色授权、外部日志持久性、隐藏数据隔离或正式 holdout 结果。身份认证和 IdP 集成按当前范围暂不实现。

2026-10-23 文档收口检查：索引覆盖本目录全部 36 份 JSON Schema，所有非 schema JSON 互操作/摘要向量也均有入口；实施计划中未勾选项经分类均为真实服务/生产接入、部署选择、在线运行或独立人工验收 gate。设计边界已在主规格和计划中说明，不把这些外部证据当作文档阶段的隐含完成条件。

## Envelope、事件与人工治理

| 合同                                                                              | 用途                                                                                   |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| [v7 evidence envelope](./official-blind-holdout-evidence-envelope-v7.schema.json) | 唯一承载官方 holdout、registry receipt chain 与 governance evidence 的外层包。         |
| [Governance object](./stage5-governance-object-v1.schema.json)                    | approval/review/revocation 引用、attestation、handoff core 与 identity decision refs。 |
| [Governance event payloads](./stage5-governance-event-payloads-v1.schema.json)    | 追加日志中的审批、审查与撤销事件 payload。                                             |
| [Governance attestation](./stage5-governance-attestation-v1.schema.json)          | 人类签署的精确审批或审查声明。                                                         |
| [Handoff core](./stage5-handoff-core-v1.schema.json)                              | 独立 reviewer 签名覆盖的稳定交接材料。                                                 |
| [Acceptance decision receipt](./stage5-acceptance-decision-v1.schema.json)        | verifier 派生的完整性、授权、holdout 与 readiness 结果。                               |

## 身份与 verifier trust state

| 合同                                                                                               | 用途                                                           |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [Identity decision](./stage5-identity-decision-v1.schema.json)                                     | 绑定主体、key、scope、角色和 preflight/record-time 检查结果。  |
| [Role-change event](./stage5-identity-role-change-v1.schema.json)                                  | 有序、签名、可审计的身份角色或密钥变更。                       |
| [Role-change policy](./stage5-identity-role-change-policy-v1.schema.json)                          | 角色管理的完整授权矩阵、职责分离与 bootstrap policy。          |
| [Policy transition](./stage5-identity-role-change-policy-transition-v1.schema.json)                | 由旧策略授权、且须经独立 verifier pin 更新的策略迁移。         |
| [Role history package](./stage5-identity-role-history-package-v1.schema.json)                      | 完整、查询绑定、带签名 head 的身份历史读取包。                 |
| [Bootstrap root update](./stage5-identity-bootstrap-root-pin-update-v1.schema.json)                | planned root rollover 与紧急恢复的分离授权合同。               |
| [Verifier pin-bundle commit](./stage5-verifier-pin-bundle-commit-v1.schema.json)                   | 原子绑定 policy/root/config revision 与更新记录的提交回执。    |
| [Verifier pin-bundle history](./stage5-verifier-pin-bundle-history-package-v1.schema.json)         | 防止配置存储 rollback 的 verifier-owned witness history。      |
| [Decision-consumer identity decision](./stage5-decision-consumer-identity-decision-v1.schema.json) | 下游 acceptance/release 服务对精确操作意图做出的身份授权决定。 |

## Candidate、隐藏数据与可信执行

| 合同                                                                     | 用途                                                                     |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| [Build provenance](./p5-build-provenance-v1.schema.json)                 | 将不可变源码、完整材料闭包、build workload 与 OCI 镜像 digest 绑定。     |
| [Runtime image admission](./p5-runtime-image-admission-v1.schema.json)   | 候选启动前绑定 run、镜像、平台与受信 supervisor 身份。                   |
| [Capability grant](./p5-holdout-capability-grant-v1.schema.json)         | 仅授权一次、短时、单 run 的隐藏题读取能力。                              |
| [Session-open request](./p5-holdout-session-open-request-v1.schema.json) | 将 grant 兑换为唯一 custodian session 的请求。                           |
| [Custodian event](./p5-holdout-custodian-event-v1.schema.json)           | 记录 capability redemption、撤销、过期及 session 关闭。                  |
| [Runtime usage entry](./p5-runtime-usage-entry-v1.schema.json)           | 保留每个 provider operation 的不可变状态迁移与 usage 来源。              |
| [Runtime usage closure](./p5-runtime-usage-closure-v1.schema.json)       | 绑定可信 stop 状态、ledger head 与所有 provider operation 终态。         |
| [Runtime stop record](./p5-runtime-stop-record-v1.schema.json)           | supervisor 对进程终止、egress fence 和 stop-time ledger 状态的签名声明。 |
| [Output seal](./p5-holdout-output-seal-v1.schema.json)                   | 在 runtime 停止、usage closure 和 custodian session 关闭后封存输出。     |

## 人工验收、发布与变更挑战

| 合同                                                                                  | 用途                                                                                    |
| ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [Decision-consumption common](./stage5-decision-consumption-common-v1.schema.json)    | acceptance/release 共用的可信 source snapshot 与 append receipt。                       |
| [Decision-consumption policy](./stage5-decision-consumption-policy-v1.schema.json)    | 绑定身份角色、职责分离、source freshness 与 snapshot skew 的策略。                      |
| [Decision-consumption policy v2](./stage5-decision-consumption-policy-v2.schema.json) | 固定 monitor freshness TTL、检测 SLA、challenge event v2 与触发证据摘要 profile。       |
| [Human acceptance](./stage5-human-acceptance-v1.schema.json)                          | 对精确 verifier receipt 和 source snapshot 作出单独人工决定。                           |
| [Release authorization](./stage5-release-authorization-v1.schema.json)                | 对唯一 artifact/image、target environment 和 deployment operation 授权。                |
| [Deployment operation](./stage5-deployment-operation-v1.schema.json)                  | 对一次部署操作的 claim、执行、终态与 reconcile 记录。                                   |
| [Decision challenge events v1](./stage5-decision-challenge-events-v1.schema.json)     | 兼容结构样例；不绑定触发证据，不能用于正式 challenge。                                  |
| [Decision challenge events v2](./stage5-decision-challenge-events-v2.schema.json)     | 正式 challenge/resolution 形状；challenge 必须绑定触发证据摘要。                        |
| [Source outage episode](./stage5-source-outage-episode-v1.schema.json)                | 绑定连续 probe sequence 与起止时间；journal 完整性及 timeout/cadence 由 verifier 检查。 |
| [Source probe journal page](./stage5-source-probe-journal-page-v1.schema.json)        | nonce 绑定的 monitor journal 范围页与当前 head；signature、链连续性由 verifier 检查。   |

v2 schema 及离线结构/算术合同已加入；真实部署仍须用监测延迟、完整重扫和 target fanout 的实测最坏值填充具体 policy，并由风险负责人批准。v1 不能被用于声称 source-change monitor 有有界检测 SLA。

消费端集成顺序见[Acceptance/release consumer integration contract](./2026-10-23-stage5-registry-audit-integrity.md#acceptancerelease-consumer-integration-contract)；来源变化如何变成审计事件见[Source-change to challenge-event producer contract](./2026-10-23-stage5-registry-audit-integrity.md#source-change-to-challenge-event-producer-contract)。前者规定可信日志验证、fresh source 读取、challenge 派生、其他 gate 合并、CAS append、未知结果对账和部署副作用前复查的先后关系；后者规定监测、幂等追加、掉通知后的完整对账与检测窗口。它们是实现与 conformance 的设计合同，不代表现有本地 reducer 已具备这些服务能力。

## Parser 与跨语言互操作

| 合同                                                                       | 用途                                                                                                                                                    |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Verifier input limits](./stage5-verifier-input-limits-v1.schema.json)     | 冻结压缩/解压、JSON/JCS、CPU/内存和并发/排队资源边界。                                                                                                  |
| [Verifier protocol error](./stage5-verifier-protocol-error-v1.schema.json) | 约束无可信 decision receipt 时的有界协议错误响应。                                                                                                      |
| [JCS number-token vectors](./stage5-jcs-number-token-vectors-v1.json)      | 固定 binary64 转换前对原始十进制数字 token 的精确检查。                                                                                                 |
| [Identity signature vectors](./stage5-identity-signature-vectors-v1.json)  | 固定 identity profile 的 JCS bytes、SHA-256 和 Ed25519 测试向量；Node 与 Python 分别复核 canonical bytes、摘要、签名与篡改拒绝。                        |
| [Decision signature vector](./stage5-decision-signature-vectors-v1.json)   | 固定 detached decision profile 的 JCS bytes、SHA-256 和 Ed25519 公开测试向量；Node 与 Python 分别复核签名及篡改拒绝，不提供生产 signer。                |
| [v7 digest vectors](./stage5-v7-digest-vectors-v1.json)                    | 固定 report、handoff core/evidence 与 outer envelope 的 canonical preimage/hash，并验证四类内容变化的摘要隔离边界；合成输入不是 schema-valid evidence。 |

## 本地参考实现

| 行为合同                  | 实现与测试                                                                                                                                                                                            | 能证明什么 / 不证明什么                                                                                                                                                                                                               |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Challenge 事件派生        | [`decision_challenges.py`](../../../examples/capstone-acceptance/decision_challenges.py) / [`test_decision_challenges.py`](../../../examples/capstone-acceptance/test_decision_challenges.py)         | 在调用方已验证完整 receipt prefix 和 fresh trigger snapshot 后，逐 challenge 配对 resolution；要求目标记录 digest 稳定，并精确匹配 resolution 引用的 decision id/receipt digest。它不验证签名、身份、source freshness 或外部 append。 |
| Challenge gate 投影       | 同上 `challenge_gate_for_target`                                                                                                                                                                      | 只返回精确目标的 `blocked` / `unverified` / `clear` challenge 状态；`clear` 不代表总体 release readiness。                                                                                                                            |
| v7 lifecycle 语义         | [`stage5-v7-lifecycle-conformance.mjs`](./stage5-v7-lifecycle-conformance.mjs) / [`test-stage5-v7-lifecycle-conformance.mjs`](./test-stage5-v7-lifecycle-conformance.mjs)                             | 检查已验证事件前缀中的审批、授权、预约、终态、审查顺序，以及 no-start、撤回、early-failure 和 incomplete 映射。它不解析或验签外部 receipt，也不查询身份/usage source。                                                                |
| v7 决策维度与组合         | [`stage5-v7-decision-conformance.mjs`](./stage5-v7-decision-conformance.mjs) / [`test-stage5-v7-decision-conformance.mjs`](./test-stage5-v7-decision-conformance.mjs)                                 | 组合 lifecycle 状态、预先验证的 integrity/governance/holdout 维度与 readiness 优先级；结构错误不产生 decision receipt。输入的来源可信性由调用方负责。                                                                                 |
| Detached decision receipt | [`stage5-v7-decision-receipt-conformance.mjs`](./stage5-v7-decision-receipt-conformance.mjs) / [`test-stage5-v7-decision-receipt-conformance.mjs`](./test-stage5-v7-decision-receipt-conformance.mjs) | 检查派生维度、证据绑定和最早 source expiry；不签署回执、不证明信任源真实、及时或独立。                                                                                                                                                |

运行本地课程合同：`pnpm verify:examples`。它会在锁定依赖环境运行 capstone-acceptance 单测，但 fake / synthetic receipt 与 snapshot 不能代替生产 verifier、append authority 或 release consumer。

## 离线验证入口

- `pnpm test:stage5-governance-contract`：运行 schema、精确数字边界、Node identity/decision signature 与 v7 digest vectors、identity reference，以及 v7 lifecycle/decision/receipt 合同；再使用 `examples/p4-durable-support/uv.lock` 中固定的 Python JCS/Ed25519 依赖复核签名及 digest vectors（环境缺失时由 `uv` 按 lockfile 创建）。当前 Node 119 项、Python canonicalization 13 项。
- `docs/superpowers/specs/test-governance-schemas.mjs`：strict schema 与基本结构/关系测试。
- [`stage5-governance-conformance.mjs`](./stage5-governance-conformance.mjs)：在调用方已验证 receipt chain 和新鲜 identity decisions 的前提下，检查 v7 identity refs 的精确覆盖、顺序与绑定。
- [`test-stage5-governance-conformance.mjs`](./test-stage5-governance-conformance.mjs)、[`test-identity-signature-vectors.mjs`](./test-identity-signature-vectors.mjs)、[`test-stage5-decision-signature-vectors.mjs`](./test-stage5-decision-signature-vectors.mjs)、[`test-stage5-v7-digest-vectors.mjs`](./test-stage5-v7-digest-vectors.mjs)、[`test_canonicalization.py`](../../../examples/p5-agent-delivery/evaluation/test_canonicalization.py) 与上述 v7 测试文件：覆盖离线 helper、跨语言 golden vectors 和决策组合边界。

这些入口是设计合同的回归检查，不是生产 verifier，也不替代外部 registry、identity authority、custodian、witness、scorer、真实 holdout 或独立 handoff 验收。
