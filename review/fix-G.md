# 深度修复报告 G：sandboxing / agent-security / cost-and-latency

> 修复依据：[docs/CONTENT-DEPTH.md](../docs/CONTENT-DEPTH.md) 五要素标准 + [review/depth-G.md](depth-G.md) 逐节审计。
> 范围：仅 `src/content/chapters/` 下 sandboxing / agent-security / cost-and-latency 的 15 个 `.mdx`。未触碰 meta.ts、其他章、`src` 其他文件。
> 日期：2026-10-12。所有新增实测数据均为本次真跑（标注 2026-10-12）；构造出的示例均就地标注「（示例：构造数据，未实跑）」。

## 一、验收输出（实跑）

```text
$ node scripts/depth-check.mjs --chapter=sandboxing
## 术语首现无解释（0/1）
汇总：硬错误 0 条，建议项 0 条
EXIT=0

$ node scripts/depth-check.mjs --chapter=agent-security
## 术语首现无解释（0/2）
汇总：硬错误 0 条，建议项 0 条
EXIT=0

$ node scripts/depth-check.mjs --chapter=cost-and-latency
## 术语首现无解释（0/4）
汇总：硬错误 0 条，建议项 0 条
EXIT=0
```

（三章 E1/E2/E3/E4 全为 0，W 也为 0。）

```text
$ node scripts/content-stats.mjs | grep -E "sandboxing|agent-security|cost-and-latency"
agent-security/01-injection-escalation           3480      6493   1   4  ✅
agent-security/02-tools-as-untrusted-input       3331      4779   1   9  ✅
agent-security/03-supply-chain                   2999      4357   1   9  ✅
agent-security/04-exfiltration                   2920      4274   1   7  ✅
agent-security/05-defense-in-depth               2839      4265   1   3  ✅
cost-and-latency/01-cost-model                   2523      4397   1   9  ✅
cost-and-latency/02-latency-sources              2625      4417   1   8  ✅
cost-and-latency/03-caching                      2903      4279   1   9  ✅
cost-and-latency/04-routing                      3112      4717   1   7  ✅
cost-and-latency/05-budget-guardrails            2666      4009   1   4  ✅
sandboxing/01-why-isolate                        2900      4128   1   3  ✅
sandboxing/02-isolation-levels                   3362      4901   1   6  ✅
sandboxing/03-least-privilege                    2657      4343   1   8  ✅
sandboxing/04-secrets                            3002      4246   1   9  ✅
sandboxing/05-execution-policy                   2492      3850   1  12  ✅
共 134 节，达标 134 节（标准：中文≥1500 且 说明文字≥3000）
```

对照修复前基线（全部上升，无下降）：

| 节 | 中文 前→后 | 说明 前→后 |
|---|---|---|
| sandboxing/01 | 2279 → 2900 | 3174 → 4128 |
| sandboxing/02 | 2211 → 3362 | 3108 → 4901 |
| sandboxing/03 | 1914 → 2657 | 3041 → 4343 |
| sandboxing/04 | 2335 → 3002 | 3125 → 4246 |
| sandboxing/05 | 2057 → 2492 | 3075 → 3850 |
| agent-security/01 | 2178 → 3480 | 3136 → 6493 |
| agent-security/02 | 2133 → 3331 | 3013 → 4779 |
| agent-security/03 | 2241 → 2999 | 3206 → 4357 |
| agent-security/04 | 2130 → 2920 | 3009 → 4274 |
| agent-security/05 | 2138 → 2839 | 3003 → 4265 |
| cost-and-latency/01 | 1954 → 2523 | 3196 → 4397 |
| cost-and-latency/02 | 1754 → 2625 | 3023 → 4417 |
| cost-and-latency/03 | 2303 → 2903 | 3257 → 4279 |
| cost-and-latency/04 | 2211 → 3112 | 3119 → 4717 |
| cost-and-latency/05 | 2149 → 2666 | 3080 → 4009 |

```text
$ pnpm test
 ✓ tests/sse.test.ts (15 tests)
 ✓ tests/image-tokens.test.ts (4 tests)
 ✓ tests/inline-md.test.ts (5 tests)
 ✓ tests/depth.test.ts (2 tests)
 ✓ tests/curriculum.test.ts (41 tests)
 Test Files  5 passed (5)
      Tests  67 passed (67)
EXIT=0

$ node scripts/verify-depth-fixes.mjs --chapter=sandboxing
改动文件 5 / 未改动 0，净增 20841 字符
✅ 没有实质性的字数下降
$ node scripts/verify-depth-fixes.mjs --chapter=agent-security
改动文件 5 / 未改动 0，净增 15262 字符 ✅
$ node scripts/verify-depth-fixes.mjs --chapter=cost-and-latency
改动文件 5 / 未改动 0，净增 15939 字符 ✅
```

## 二、逐节修复

### sandboxing/01 为什么必须隔离（A 级）
- **补了什么**：L247 新增「被拒调用长什么样：一行日志的字段」——一份拒绝日志 JSON（rule_id / raw_path / resolved_path / reason / decision / tool / ts）+ 字段判据表 + 落地四步（谁写 / 写哪里 / 怎么读回 / 怎么更新）+ 失败形态。
- L124 的演示代码改成**真的数出** 4/6：删掉死代码 `leak`/`if ...: pass`，改为 `leaks += 1`（判据：朴素放行且真实路径拒绝），并让 `safe_read` 往 `LOG` 追加记录；L226 贴出本次实跑输出（含 `朴素版放过 4/6` 与日志行）。
- 术语首现：L7 工具注册表、L17 指令注入、L57 路径规范化。
- **依据**：代码与输出为**本次真跑（2026-10-12）**，结论 4/6 与原文一致；日志样例字段为设计判据，示例 JSON 标注「构造数据，未实跑」。
- **未解决**：无。

### sandboxing/02 隔离的层级（B 级）
- **补了什么**：L218「L3 的实体：一段可复制的容器配置」——可复制的 `docker run` 配置（--read-only / --tmpfs / --network none / --user / --cap-drop ALL / no-new-privileges / pids / memory / cpus / 只读 bind），配「开关↔失效模式」表并说明容器共享内核的边界。
- L250「验证：把『我们用了容器』变成可复跑的结果」——5 项隔离探针脚本 + **配置正确 vs 配置错误两组实跑输出**（正确组 5 PASS；错误组 4 FAIL），并如实记录「用连 1.1.1.1 测网络在本机两次都不可分辨，改用 eth 网卡判据」这一未复现观测。
- L314「生命周期：谁创建、清理什么、怎么验证清理干净」——创建方（调度层）、五项清理清单、洁净探针三步验证、三种生命周期选择的判据。
- 术语：L21 命名空间与 capabilities 就地展开。
- **依据**：容器验证为**本次真跑（2026-10-12，Docker 29.3.1，python:3.12-alpine）**；容器配置本身是官方 flag 的用法，未把「预期结果」写成实测。
- **未解决（偏差）**：审计建议「在该配置下把第 3 节 6 种攻击重跑一遍」**未照做**。原因：那 6 种攻击打的是 Python 里那个前缀检查函数，**不是容器边界** —— 换个环境跑结果仍取决于函数实现，无法体现容器隔离。故改为「针对容器应保证的性质」的探针（只读根 / 无网卡 / 非 root / 宿主挂载点不可见 / tmpfs 可写），这才能真正暴露配置错误。

### sandboxing/03 文件系统与网络的最小权限（A 级）
- **补了什么**：L244「网络最小权限的实现：从 URL 到 IP 的完整判据」——可运行的 `urlparse` + `ipaddress` 实现（整数/十六进制 IP 还原、先二次拒绝再白名单、DEMO_DNS 保证离线复现）+ 15 条用例实跑输出（含 `api.example.com@169.254.169.254`、十进制 IP、以及白名单域名解析到内网的 rebind 用例）+ 三个绕过点为何被挡 + DNS 重绑定要 pin IP 的说明。
- L367「网络版与文件版并列」对照表（原始值 / 解析目标 / 白名单比较 / 二次拒绝 / 已知绕过 / 共同根因）。
- L378「能力式接口长什么样」给出「传句柄而非路径」的真实签名与调用侧。
- 术语：L89 SSRF 展开，L135 硬链接「不可写」补做法（独立文件系统 + fs.protected_hardlinks），L241 poka-yoke 展开。
- **依据**：网络代码与输出为**本次真跑（2026-10-12）**；表格对照为工程判据。
- **未解决**：无（DNS 重绑定只给判据与做法，未新跑真实重绑定实验——已在正文说明要 pin IP）。

### sandboxing/04 凭据不该进入上下文（B 级）
- **补了什么**：L241「主防线的实现：schema 无凭据字段，值在边界解析」——运行前准备（两个环境变量怎么拿、纯标准库）+ 完整工具实现（schema 无凭据字段 → `os.environ` 取值 → 错误归一化为 `error_code+hint` → 细节只进日志并脱敏）+ **断言「序列化后的工具定义不含凭据值」** + 实跑输出；并解释「归一化前取不到凭据必须直接返回错误」。
- L335「可轮换的引用长什么样」——credential_ref / scope / rotated_at 三字段与轮换判据。
- 术语：L15 轨迹与 schema、L94 密钥服务。
- **依据**：代码与输出为**本次真跑（2026-10-12，假 token 注入环境变量）**；错信息与引用 JSON 为构造示例并标注。
- **未解决**：①审计提到的「日志系统访问控制要和业务系统一样严」仍是原则性表述，未补可执行机制（属基础设施配置，本站无对应代码）；②原文 L134-148 与 L234-240 是同一段推论重复两遍，按「只加不删」保留，未合并。

### sandboxing/05 执行策略与审计（A 级）
- **补了什么**：L280「把策略接进 agent 循环：唯一的执行入口」——修正版策略引擎（R1 换成 `path_under`：先 realpath 再比；条件类型做成 `CONDITIONS` 注册表）+ `dispatch()` 统一入口，并交代工具名来自 `tool_use.name`、在真正执行 handler 前过 check。
- L341「一条固定的攻击测试用例」——4 条 pytest（含 `/workspace/../../../etc/passwd` 必须 deny）+ 实跑 `4 passed in 0.01s`。
- L375「怎么加第三种条件」——`ip_in_cidrs` 示例 + 失败形态（否定逻辑会绕过默认拒绝）。
- **依据**：引擎与 pytest 为**本次真跑（2026-10-12，pytest 8.3.4）**；新条件示例为构造片段。
- **未解决**：无。

### agent-security/01 注入为什么在 agent 里升级了（B 级）
- **补了什么**：L38 前新增三个入口定义（直接 / 间接 / 供应链注入）。
- L283「运行前准备：三个环境变量与一个离线开关」——ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / VERIFY_MODEL 各自怎么拿、base_url 两种形态、核心只用标准库；并解释 `stop_reason` / `tool_use`。
- L307「离线回放开关」——`REPLAY_FILE` 分支代码 + `replay.jsonl` 示例 + **机制本次实跑通过**说明。
- L347「第三轮那份『合法动作清单』」——动作 / 正常目标 / 被改后的目标 / 在任务中的位置 四列表（示例构造），并把它变成攻击测试五步与防护落点判据。
- **依据**：环境变量与端点用法与 .env.local 实跑一致（本次真跑）；回放机制真跑；清单为构造示例（已标注）。
- **未解决**：审计设想「把实测的 7 次 API 响应存成 JSON 供回放」——**原始 7 次响应在仓库里没有机器可读留存**，无法复原；改为提供可用的回放机制 + 构造样例，读者自行录制即可。

### agent-security/02 工具描述与返回值都是输入（B 级）
- **补了什么**：L79「先定义清楚：格式操纵 vs 内容操纵」——两类定义 + 第 2 章原始注入文本 + 判别表 + 标签法在两类上的 6/6→2/6 与 6/6→6/6（引用站内已实测，2026-10-08）+ 「标签在你的场景是否有用」的实用判据。
- L110「标签法长什么样：messages 对照」——无标签 / 带 `<external_content>` + system 声明的两段完整 messages，并强调工具返回值也要由调用层统一包。
- L139「异常内容不该进历史：谁、何时、怎么判」——ingestion 时机、调度层归属、四条确定性判据、隔离而非删除的 stub 报文、误报率验证。
- **依据**：两类数字引用站内第 2 章实测；messages / stub 为构造示例并标注。
- **未解决**：无。

### agent-security/03 第三方工具就是第三方依赖（B 级）
- **补了什么**：L262「一个最小 MCP 工具定义长什么样」——tools/list 返回对象 JSON + 方法表 + 「实现不可见」判据；术语 MCP / tools/list 就地展开。
- L288「描述被篡改长什么样：一次 diff」——前后描述 diff + 变更风险分级表。
- L312「固定版本的三种写法」——npm 精确版本+integrity、容器 digest、远程 server 快照提交进仓库（含命令）。
- L334「两个通道的错误信息」——给模型的归一化 JSON 与给日志的完整 JSON 对照 + 判据。
- **依据**：MCP 报文形态为协议字段（示例构造）；错误样例构造并标注；命令为标准工具用法。
- **未解决**：无。

### agent-security/04 数据外泄的三要素（B 级）
- **补了什么**：L188「拦住渲染层：CSP 加服务端 URL 白名单」——CSP 响应头示例、为何 CSP 只管浏览器、可运行的服务端 `safe_image_url` 白名单（host 白名单 + 内网/元数据/localhost 二次拒绝 + 代理改写）、以及「两道都要」的理由与失败形态。
- L234「投影式接口：真实签名与返回」——原始查询 vs 三种投影（布尔 / 聚合 / 检索片段）的真实函数签名 + 返回示例。
- L271「三问清单的数据模板」——可直接填的 JSON 模板与「填不出来即缺口」用法。
- 术语：L57 渲染层就地解释。
- **依据**：白名单逻辑与第 3 节同源（本次真跑的口径）；CSP/投影/模板为工程构造（模板已标注构造）。
- **未解决**：无。

### agent-security/05 纵深防御：分层且不可绕过（A 级）
- **补了什么**：L101 那张空表旁补**一行已填示例**（四层各自的实现 / 失效时表现 / 负责人）。
- L227「四层共同的载体：一条完整的 trace 记录」——一条同时含 input_layer / model_layer / exec_layer / audit_layer 的完整 JSON + 字段职责表 + 「一眼看出一层隔离了 1 条、模型照样请求、执行层 default 拒绝、审计通知值班」的读法 + 失败形态。
- **依据**：trace 记录为构造示例并标注「构造数据，未实跑」（它描述的是机制载体，不是某次跑出来的数据）。
- **未解决**：无。

### cost-and-latency/01 成本的四块来源（A 级）
- **补了什么**：L85 后解释三个 usage 字段语义与「三项之和」口径。
- L205「一条真实的调用记录长什么样」——4 行真实调用记录 JSONL（含 trace_id / turn_index / step_kind / model / input_tokens / cache_read / cache_create / output_tokens / stop_reason / latency_ms）+ 字段来源表。
- L233「从这批记录算 P90 轮数与工具定义占比」——可运行聚合代码（三项求和 / 最近秩百分位 / 按 step_kind 归因 / 工具定义占比）+ 实跑输出。
- 修掉 L191 残留的 `e["tools"] & 0xFFFFFFFF` 位运算。
- **依据**：记录与输出为**本次真跑（2026-10-12，一个 4 轮最小 agent 循环）**；工具定义 60 token/工具引用第 4 章实测。
- **未解决**：样本仅 4 条，P90 无统计意义（正文已注明它只演示算法口径）。

### cost-and-latency/02 延迟被什么主导（A 级）
- **补了什么**：L13 展开 TTFT / prefill / 前向计算 / 注意力状态。
- L222「输出长度怎么估：把那个 180 用起来」——「同一任务历史输出 P50 ÷ 180」的经验规则 + 可运行代码（输入为本次实跑 4 轮输出）+ 实跑输出 + 适用边界（换模型/换任务要重测）。
- L268「判断输入是否进入主导区：一个两步测量」——固定输出、输入翻倍、比较 TTFT 的测量表与判读；用第 2 节已有的 36→1238 实测量级说明「本项目仍处固定开销区」，并要求每组 3 次取中位数。
- L285「把估算式接到 UI 与超时阈值」——超时阈值取 P99 生成时间加余量、进度提示要暴露「已生成 N 字 / 预计 M 秒」。
- **依据**：180 token/秒与固定开销 0.6-0.9s 引用第 2 节实测；估算代码本次真跑；「输入翻倍看 TTFT」为测量步骤，本次未新跑（无新数字）。
- **未解决**：输入主导区的**加倍测量本身未新跑**（只给了步骤与已有量级的对照说明）。

### cost-and-latency/03 缓存与复用（B 级）
- **补了什么**：L45「怎么把缓存打开：请求体里的断点」——带 `cache_control` 的完整请求体 JSON（断点打在稳定 system 块末尾）+ 三条要点（缓存顺序 tools→system→messages、断点后可随便变、门槛与断点上限以官方文档为准）。
- L69「打开前后的 usage 对照（本次实跑）」——7 组真实读数：冷启动 4693/0/0、完全相同 213/4480/0、只改断点后内容 213/4480/0、无断点两次 4537/0/0 → 185/4352/0、短前缀两次 221/0/0、改一个空格 4837/0/0。
- 如实记录两个端点级观测：该端点**不打断点也会命中**（自动前缀缓存）；`cache_creation_input_tokens` 始终为 0，冷启动全额计入 `input_tokens`。
- **依据**：全部为**本次真跑（2026-10-12，deepseek-flash）**。
- **未解决**：最小可缓存 token 门槛与断点数量上限是会变的参数，只给了本次观测（约 2.4k 命中 / 约 0.1k 不命中）并指向官方文档，未写死具体阈值。

### cost-and-latency/04 分级与路由（B 级）
- **补了什么**：L212「『不满意』判据：能由代码判的，就别用小模型」——三档确定性判据（max_tokens / 结构化校验 / 工具参数缺字段）的可运行实现 + 5 组实跑输出 + self-eval 失败形态。
- L286「一条带 route 字段的调用记录」——带 `route / route_step / route_reason` 的完整记录 JSON + 用途表 + 「与 turn_index 并存」说明。
- L304「一个请求走完六步」——四个请求逐列判定表（code_only / cheap / strong / strong）。
- 术语：L61 self-consistency 展开。
- **依据**：判据代码与输出为**本次真跑（2026-10-12）**；route 记录与六步表为构造示例并标注。
- **未解决**：无。

### cost-and-latency/05 预算闸门与熔断（A 级）
- **补了什么**：L198「把常量换成从 usage 累加」——用每轮响应 usage 累加的闸门（`billed_input` 三项求和、`max_tokens` 单独记一类）+ 三档预算实跑输出 + 与常量版的三处差别。
- L248「超限和熔断都要有告警出口」——两个计数器与「周同比翻倍告警」规则（而非绝对阈值）。
- **依据**：输入为第 1 节本次实跑的 4 条记录，输出**本次真跑（2026-10-12）**。
- **未解决**：无。

## 三、对既有内容的修改（非纯新增，逐条说明）

1. **sandboxing/01 演示代码**：删除死代码 `leak = 0` / `if ...: pass`（它不产生任何效果，导致 4/6 靠肉眼数），改为代码自行计数并打印日志。返回值字符串与 4/6 结论均未改，本次重跑确认仍是 4/6。
2. **cost-and-latency/01**：删掉 `e["tools"] & 0xFFFFFFFF` 这一与语义无关的位运算残留，改为直接打印 `e["tools"]`；输出数值不变（均为正整数）。
3. **sandboxing/02 容器配置块**：初稿把说明写成行尾 `#` 注释，而 `\` 续行后接注释是**无效 shell**；已改为无注释的命令，说明移到紧随其后的表格。未涉及任何实测数据。
4. **术语就地解释**（只加不删）：sandboxing L7/L17/L57/L21/L89/L135/L241、sandboxing/04 L15/L94、agent-security L7/L28/L57/L61、cost L13 等。
5. **重复段落**：sandboxing/04、sandboxing/05、sandboxing/02 各存在前后重复的小节（修复前既有），按「只加不删」保留未合并。

## 四、仍未解决 / 需后续处理

1. **sandboxing/02「6 种攻击在容器内重跑」未做**：如 §二 所述，那 6 种攻击测的是应用层前缀检查，不是容器边界；已用容器性质探针（本次真跑）替代，并说明理由。
2. **agent-security/01 回放样例非真实 7 次响应**：原实验响应未以机器可读形式留存，无法复原；已给可用回放机制 + 构造样例（已标注），机制本次跑通。
3. **sandboxing/04 日志访问控制**：仅有「与业务系统同级」的原则，无本站可承载的机制代码。
4. **sandboxing/04 重复小节**：未合并（只加不删）。
5. **cost-and-latency/02 输入主导区加倍测量未新跑**：只给了可执行步骤与已有量级对照，未产生新数字。
6. **cost-and-latency/01 P90 样本过小**：仅演示口径；正文已说明真实系统需按任务维度收集数百条。
7. **cost-and-latency/03 缓存门槛/断点上限**：属会变化的参数，仅给本次观测与官方文档指引。
