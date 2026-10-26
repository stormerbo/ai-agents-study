# 正式盲测运行登记表

## 先判断你是否需要这张表

这里的“盲测”不是普通作业，也不是让每个读者先登记自己的答案。它指的是最终项目发布前的一次正式验收：候选系统拿不到标准答案，独立评分方在候选运行结束后才核对结果；题目、系统版本和评分规则都要提前冻结，避免看完结果再改规则。

| 使用场景                         | 怎么记录                                                                       | 是否需要登记服务                                                         |
| -------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| 个人学习、普通课程练习           | 本地 CSV/JSON 或笔记：输入版本、系统输出、标准答案、评分结果                   | 不需要；本表也不用填                                                     |
| 团队内部反复调试                 | 受控开发集与版本记录；不要把它称为“正式盲测”                                   | 通常不需要外部 registry                                                  |
| 最终发布验收的一次正式隐藏集测试 | 使用本表冻结角色、候选、题集版本、预算、停机条件和证据位置；由独立人员安排运行 | 需要受控服务记录一次性授权、预约与终态，防止重复使用隐藏集或事后改写记录 |

“登记服务”是一个受控的后台系统，负责保存不可随意改写的授权和运行记录；**它不是普通学习者要搭建的功能，也不是本地练习页的依赖**。如果你只是按教程学习，跳过下面的正式验收模板即可。只有负责人真的要执行最终发布验收时，才复制并填写本表；当前项目尚未接通这种外部服务，因此模板里的 `TODO` 不是可以直接执行的授权。

> 复制此空白模板，为每个正式 run 单独填写。它用于确认“谁批准、测哪个版本、花费上限、停机条件、证据存在哪里”，不能代替外部 registry 的授权事件或正式验收签名。填写后的记录含身份和运行元数据，必须存入受控 evidence store；不要把已填写副本提交到 Git、候选镜像或公开工单。未填完、身份未核验或任何 preflight 未通过时，状态必须保持 `not-authorized`，不得预约隐藏集。

## 1. 运行身份

| 字段                                                                 | 值      |
| -------------------------------------------------------------------- | ------- |
| holdout version                                                      | `TODO`  |
| 新 run id（不得复用失败 run）                                        | `TODO`  |
| 预生成 authorization event id                                        | `TODO`  |
| 计划开始时间（UTC）                                                  | `TODO`  |
| 最晚结束时间（UTC）                                                  | `TODO`  |
| 本登记表阶段（draft / preflight / authorized / reserved / terminal） | `draft` |
| 最近一次 registry 查询状态                                           | `TODO`  |

Registry 状态按事件事实填写：`not_found` 表示没有授权事件；`authorized` 表示授权存在但尚无 reservation；`reserved` 表示额度已被保留；`consumed`、`aborted`、`failed` 是不可逆终态；查询超时或响应不可信写 `unavailable`，不能据此推断为 `not_found`。`authorized` 还必须核对授权未过期、run/spec hash 完全匹配后才允许预约。

## 2. 负责人和职责

填写身份系统的稳定 subject ID，不写个人邮箱、姓名或访问凭据；每个参与人或服务身份单独一行，同一角色有多人时重复该角色行。owner、executor、recovery operator 必须是三个不同 subject。handoff reviewer 必须与 risk owner、candidate implementer、executor 和 scorer 不同；scorer 必须与 candidate implementer、executor 和 runtime operator 不同；human acceptance authority 与 release approver 都必须与 candidate implementer、executor、risk owner 和 handoff reviewer 不同，且二者必须互不相同。risk owner 与 candidate implementer、executor、append-authority administrator、签名密钥保管人默认必须分离；若冻结策略明确允许某项重叠，必须记录补偿控制并由无利益冲突的 reviewer 批准。其他角色重叠也只有在冻结策略明确允许、记录权限边界和补偿控制，并由无利益冲突的 reviewer 接受时才可进入 preflight；无法满足职责分离或独立复核时为 no-go。服务身份填 workload subject，不得代替任何 human signer。

| 角色                                            | 稳定 subject ID | 职责/系统权限                                      | 与其他角色重叠及理由 |
| ----------------------------------------------- | --------------- | -------------------------------------------------- | -------------------- |
| holdout owner / 授权人                          | `TODO`          | 冻结规格、生成 run/event id、授权一次运行          | `TODO`               |
| candidate implementer / 候选实现者              | `TODO`          | 实现并冻结候选代码、prompt 与工具策略              | `TODO`               |
| executor / 运行执行者                           | `TODO`          | 预约 run、启动冻结候选、产出脱敏结果               | `TODO`               |
| hidden-data custodian / 隐藏数据保管人          | `TODO`          | 保管题面与标签，按授权给 runtime/scorer 最小访问权 | `TODO`               |
| candidate runtime operator / 隔离运行环境操作人 | `TODO`          | 部署并限制冻结镜像、网络、进程、预算和输出         | `TODO`               |
| append-authority operator / 追加日志管理员       | `TODO`          | 运维权威追加日志、查询与恢复；不得签自己的治理审批 | `TODO`               |
| signing-key custodian / 签名密钥保管人          | `TODO`          | 管理密钥保管、轮换与撤销；不得代替审批人签署       | `TODO`               |
| identity-role administrator / 身份权限管理员    | `TODO`          | 管理治理角色授予/撤销；变更须双人控制且不得自我授予 | `TODO`              |
| scorer / 独立评分器身份                         | `TODO`          | 候选结束后读取标签并生成冻结格式的评分结果         | `TODO`               |
| recovery operator / 异常恢复人                  | `TODO`          | 候选未启动且 capability 已失效时执行 recover_abort；候选已启动时，须证明已停止、会话已撤销且在途调用已对账后才能 recover_finalize | `TODO`               |
| independent reviewer / 独立审阅人               | `TODO`          | 审查事件链、证据、偏差和质量结论                   | `TODO`               |
| human acceptance authority / 人工验收批准人     | `TODO`          | verifier-ready 后核验新鲜证据并签署接受或拒绝      | `TODO`               |
| release approver / 发布批准人                   | `TODO`          | 在人工验收通过后，针对精确 artifact/image 单独授权发布并确认回滚责任 | `TODO`               |

## 3. 冻结候选和评测材料

所有摘要均为 SHA-256；写入本表前先确认本地材料已冻结。隐藏题面与标签只记录受控 vault 的版本/引用，不复制到此文件、Git 或候选镜像。

| 组件                                                                                                       | 版本或受控引用 | SHA-256 / immutable digest |
| ---------------------------------------------------------------------------------------------------------- | -------------- | -------------------------- |
| source commit                                                                                              | `TODO`         | `TODO`                     |
| candidate OCI image                                                                                        | `TODO`         | `sha256:TODO`              |
| OCI target platform / selected platform-manifest digest                                                    | `TODO`         | `sha256:TODO`              |
| signed build-provenance attestation reference                                                              | `TODO`         | `sha256:TODO`              |
| approved builder identity / provenance profile                                                             | `TODO`         | `TODO`                     |
| canonical materials-closure manifest reference                                                             | `TODO`         | `sha256:TODO`              |
| build recipe / sanitized invocation digest                                                                 | `TODO`         | `sha256:TODO`              |
| prompt / agent instructions                                                                                | `TODO`         | `TODO`                     |
| tool schema / policy bundle                                                                                | `TODO`         | `TODO`                     |
| holdout dataset version（不含题面）                                                                        | `TODO`         | `TODO`                     |
| scorer source/version                                                                                      | `TODO`         | `TODO`                     |
| executor bundle source/version (`official_holdout.py` + `subprocess_candidate.py` + `canonicalization.py`) | `TODO`         | `TODO`                     |
| dependency lock / runtime image                                                                            | `TODO`         | `TODO`                     |
| canonical frozen spec                                                                                      | `TODO`         | `TODO`                     |
| frozen spec SHA-256                                                                                        | —              | `TODO`                     |

For this repository's reference executor, compute the bundle hash with
`executor_bundle_sha256()` from a clean checkout. It uses a fixed file order
and length-prefixes each relative filename and file content before hashing;
the release manifest additionally records each component's individual hash.

## 4. 单次运行预算和质量门槛

金额使用十进制字符串，例如 `"12.50"`，不可用 JSON 浮点数。每项必须有明确上限；没有经过负责人确认的值不可以留空或套用“默认值”。

| 限制                                     | 冻结值 |
| ---------------------------------------- | ------ |
| 最大总费用（USD 字符串）                 | `TODO` |
| 每任务最大费用（USD 字符串）             | `TODO` |
| 最大输入 token / 单请求                  | `TODO` |
| 最大输出 token / 单请求                  | `TODO` |
| 全 run 最大输入/输出 token               | `TODO` |
| 预声明样本数 / attempt 数                | `TODO` |
| 最低有效任务数                           | `TODO` |
| 最低通过率（整数 basis points，0–10000） | `TODO` |
| 是否要求每题全通过                       | `TODO` |
| candidate 输出最大字节                   | `TODO` |
| 单任务 deadline / 最大总时长             | `TODO` |
| provider 最大请求时长与强制终止方式      | `TODO` |
| 并发数                                   | `TODO` |

## 5. 触发即停条件

必须在授权前逐项确认；添加更严格条件可写在“其他”中。触发任意一项后立即停止，不补跑、不删失败项、不填造零 usage/cost，保留 `unknown` 并按协议对账。

- [ ] 费用或 token 预算将超限
- [ ] deadline 到期，或 runtime 无法强制终止超时进程
- [ ] 发生真实外部副作用或访问非合成目标
- [ ] 身份、租户或授权边界不符
- [ ] 题面、标签或隐藏 scorer 信息泄露给 candidate/provider/log
- [ ] 必需 evidence 缺失、hash 不符、事件链断裂或 registry 状态未知
- [ ] 单请求/总输出超限，或 runtime 在流式/IPC 边界未执行硬限制
- [ ] 观察到重复运行、重复 capability 兑换或未授权网络/文件访问
- [ ] 其他冻结停止条件：`TODO`

## 6. 预约前 go / no-go

- [ ] 候选 commit、OCI digest、prompt、tool/policy、dataset、scorer、executor 与 lock 已冻结，且 hash 与发布清单相符。
- [ ] 独立验证 signed build provenance：builder identity/profile 在 verifier pin 中受信，source/material/build recipe/toolchain 与 frozen spec 一致，OCI index 与选定平台 manifest digest 对得上；没有该证据不得发放隐藏题 capability。
- [ ] 独立验证 runtime image admission：registry 按 `preflight_request_id` 幂等发短效 nonce；trusted supervisor 按冻结 OCI index 解析平台 manifest，并签署绑定 request/run/candidate/spec/runtime/nonce 的 digest；registry 原子消费 nonce、写 reservation 并一次性发 capability；custodian 只兑换该 capability。启动时 ledger digest 与 admission 完全一致。
- [ ] custodian 验证 registry capability grant 签名与当前 machine-key 状态、token hash、JCS scope、固定 audience 和实际 runtime workload identity；token 与 grant 不进入 candidate 或日志。
- [ ] custodian lifecycle event chain 的签名、每 capability 序号/前序 digest、当前 head/freshness 均已独立核验；no-start abort 使用已提交的 `capability-revoked` 事件，而不是 `not-redeemed` 查询结果。
- [ ] 隐藏输入和标签不在 candidate checkout、镜像、公开日志或开发者可读位置。
- [ ] candidate/runtime 在本次 run 的输出封存前无法读取标签；只有 runtime 已关闭、结果 hash 已封存后，独立 scorer 才能按授权读取该 run 标签。
- [ ] registry 服务级合同矩阵已通过，含并发预约、响应丢失、capability scope/replay、终态竞争、幂等、重启持久性和脱敏证据。
- [ ] runtime 对 provider 请求硬预算、流式输出字节上限、deadline、强制终止、网络出口和文件权限有可复核的实测证据。
- [ ] owner、executor、custodian、runtime operator、scorer、recovery operator、reviewer 与发布批准人身份已核验；owner/executor/recovery operator、scorer/候选实现者/executor/runtime operator、reviewer/候选实现者/executor/scorer 满足分离约束，其余重叠有补偿控制和独立复核。
- [ ] 预算、质量门槛、样本数、attempt 数、停止条件、截止时间与报告路径均已冻结。
- [ ] owner 先生成 authorization event id，再将其放入 frozen spec 并计算 spec hash；事件 ID 不可在 hash 之后由服务端补发。
- [ ] registry、artifact store、runtime audit 和 scorer 的读写权限已用当前身份实际验证。

**决定：** `no-go` / `go`（二选一，默认 no-go）

**Owner 签署身份与 UTC 时间：** `TODO`

**独立 reviewer 对 preflight 的签署与 UTC 时间：** `TODO`

## 7. 执行后记录

| 字段                                                                | 值     |
| ------------------------------------------------------------------- | ------ |
| 实际开始/结束 UTC                                                   | `TODO` |
| authorization / reservation / terminal event id                     | `TODO` |
| event chain 与 payload hash 校验 artifact                           | `TODO` |
| runner result artifact + SHA-256                                    | `TODO` |
| acceptance evidence envelope + SHA-256                              | `TODO` |
| runtime audit / scorer evidence references                          | `TODO` |
| custodian session event chain/head + capability revocation evidence | `TODO` |
| registry 终态（consumed / aborted / failed / 尚无终态事件）         | `TODO` |
| 执行观察状态（known / unknown）                                     | `TODO` |
| runtime 实际解析的 OCI index / 平台 manifest digest                 | `TODO` |
| 质量结论（passed / failed / insufficient-evidence / unknown）       | `TODO` |
| deviations / stop triggers / 未知值                                 | `TODO` |
| executor / reviewer 签署和 UTC 时间                                 | `TODO` |
| 发布决定（独立流程；不得由此表自动批准）                            | `TODO` |

如果 `reserve` 响应不确定，先按原 `preflight_request_id` / idempotency key reconcile。发现已预约却无法安全取得已绑定的 capability token 与 signed grant 时，不运行 candidate、不重发任一凭据；仅在 registry 从受信 runtime audit 确认 candidate 从未启动，并由 custodian 原子确认 capability 已撤销或到期后，由独立 recovery operator 追加 `aborted`。如果 `open_session` 响应丢失，只能用原 `redeem_request_id` 和完全相同 scope 重试以找回同一 session；换 id 不得新开 session。custodian 必须验证 registry machine-key 签名、当前 key 状态、token hash、完整 scope 和调用方 workload identity。若 redemption/revocation 或是否启动的权威状态未知，保持 `reserved` 并保留未知成本/尝试数，直到原操作完成对账。
