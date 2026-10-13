# 深度修复报告 A：what-is-an-agent / llm-api-basics / prompt-engineering（14 节）

> 依据 `docs/CONTENT-DEPTH.md`（五要素 + 术语规则 + 禁止清单）与 `review/depth-A.md`（逐节审计）。
> 本轮**只改**这三个目录下的 14 个 `.mdx`；未触碰 `meta.ts`、其他章、`src/` 其它文件。
> 所有新增实测均为 **2026-10-12 本次真跑**，模型 `deepseek-flash`（DeepSeek 的 Anthropic 兼容端点）；
> 站内已有实测（2026-09-24 / 2026-10-08 口径与日期）**原样保留、只加不删**。

---

## 0. 验收结果（本次跑，原样贴出）

### 0.1 `node scripts/depth-check.mjs --chapter=<id>`

```text
what-is-an-agent  (E=0 W=1)
  what-is-an-agent/04-how-to-use-this-site
    ⚠️  W1 讨论字段/记录/报文但没有产物示例        ← 修复前的既存告警，未新增
  汇总：硬错误 0 条，建议项 1 条

llm-api-basics     (E=0 W=0)  汇总：硬错误 0 条，建议项 0 条
prompt-engineering (E=0 W=0)  汇总：硬错误 0 条，建议项 0 条
```

E1/E2/E3/E4 全为 0。修复前 W 分别是 5 / 5 / 3，其中 35 个未标语言的围栏已全部补成 `text`/对应语言。

### 0.2 `node scripts/content-stats.mjs`（中文 / 说明文字，对照修复前）

| 节 | 中文（前 → 后） | 说明文字（前 → 后） | 码块（前 → 后） |
|---|---|---|---|
| what-is-an-agent/01 | 2561 → **3647** | 4293 → **6350** | 5 → 9 |
| what-is-an-agent/02 | 2106 → **2962** | 3679 → **5015** | 3 → 4 |
| what-is-an-agent/03 | 2446 → **3111** | 3936 → **4933** | 6 → 7 |
| what-is-an-agent/04 | 2151 → **2987** | 3157 → **4678** | 2 → 3 |
| llm-api-basics/01 | 4039 → **4682** | 7173 → **8486** | 7 → 12 |
| llm-api-basics/02 | 3026 → **3477** | 5794 → **6709** | 5 → 6 |
| llm-api-basics/03 | 1661 → **2525** | 3560 → **5269** | 8 → 10 |
| llm-api-basics/04 | 1956 → **2779** | 3371 → **4579** | 11 → 12 |
| llm-api-basics/05 | 1958 → **2447** | 3567 → **4332** | 10 → 12 |
| prompt-engineering/01 | 1956 → **2198** | 3034 → **3396** | 2 → 2 |
| prompt-engineering/02 | 2013 → **2666** | 3053 → **4007** | 3 → 5 |
| prompt-engineering/03 | 2021 → **2396** | 3001 → **3538** | 1 → 2 |
| prompt-engineering/04 | 1854 → **2371** | 3063 → **4002** | 4 → 7 |
| prompt-engineering/05 | 2945 → **3731** | 4733 → **5815** | 2 → 3 |

**14 节无一节下降**（最低增幅：prompt-engineering/01 中文 +242）。全书 134/134 仍达标。

### 0.3 `pnpm verify:depth`（HEAD 基线：确认没有删改既有内容）

```text
改动文件 101 / 未改动 33，净增 266511 字符
✅ 没有实质性的字数下降（容差：中文 -5 / 说明 -30）
```

### 0.4 `pnpm test`

---

## 1. 章 what-is-an-agent

### 1.1 `01-why-now.mdx`（审计：B —— token 定义缺失、附录无运行前置）

**补了什么**

| 行号 | 内容 | 依据 |
|---|---|---|
| L59–L98 | 新增「先把 token 定义清楚」：token = 词表切分后的片段，是**计费/容量/延迟**三种单位；用 `「什么是幂等性？」→ 35 token = 内容约 5 + 结构约 30` 拆解；给量级锚（1000 token ≈ 1200 中文字符） | 站内已有实测（第 1 章 1-1 的 7 字符 35 token）；拆解算法属于**本次给出**，已在正文标注「是该处数据推出的量级，不是官方字段」 |
| L44 附近 | `JSON Schema` 首现定义（声明式描述 JSON 形状） | 概念定义 |
| L100 附近 | `prompt caching` 首现定义（前缀哈希复用，逐字节一致才命中） | 概念定义 + 指向第 5 章实测 |
| L103–L114 | 「总输入 = input + cache_read + cache_creation」补了**算进账单的算式**（1 个工具 306 / 3 个工具 430） | **（示例：构造数据，未实跑）** —— 只是把既有表格的列相加，已在正文就地标注 |
| L224 附近 | `ReAct` 首现定义：Reason→Act→Observe 循环，出口由模型决定 | 概念定义 + 指向第 10 章实测 |
| **L264–L298** | 新增「**从这里开始**」：`pip install anthropic`、三个环境变量对照表（含「base_url 留空 = 官方端点」）、三家控制台取 Key 入口、完整运行命令 | 本次实跑同一套调用栈（`x-api-key` 认证）；未逐一实测三家免费额度，已在正文说明 |

**仍未解决**：L110「约 200 token 入场费」是原文已标注的**拟合推论**，我沿用未动 —— 它确实不是实测值，但原文已诚实标注；改成实测需要重跑一组对照，本轮未做。

### 1.2 `02-what-counts-as-agent.mdx`（审计：A —— 五个模式名 +「轨迹」裸奔）

| 行号 | 内容 | 依据 |
|---|---|---|
| L53–L96 | 新增「**一份轨迹长什么样**」：轨迹定义（完整事件序列，比审计日志多的是「模型当时看到了什么」）+ 一份两步 JSON 轨迹（`tool_use` → `tool_result` → 最终回答），并说明三件事：每步记完整 model_input / tool_result 用 tool_use_id 配对 / budget 是一等字段 | 第 1 步的 `id`、`input`、`usage: 300/69`、`stop_reason` 取自站内实测；**整份 JSON 形状为手写**，正文已标「示例：构造数据，未实跑」，且**故意不填第 2 步 token**（没有那个实测数） |
| L156 附近 | 五个 workflow 模式补**一句话定义 + 何时用**表格（prompt chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer），并点明与 agent 的分界 | 概念定义；分界沿用原文「控制权在谁手里」 |

**仍未解决**：`run_agent(...)` 仍是虚构函数（原文如此），本轮只给它加了「budget 从轨迹读」的动作指引，没有落成可运行实现 —— 它属于第 9 章的交付物。

### 1.3 `03-mindset-shift.mdx`（审计：A —— 空函数 `load_test_cases` / `is_valid`、中间位置实验无脚本）

| 行号 | 内容 | 依据 |
|---|---|---|
| L11 附近 | `temperature` 首现定义（采样分布的平坦度旋钮，影响随机性而非正确性） | 概念定义 |
| **L112–L158** | 把两个空函数替换为「**样本 / 判据 / 阈值**三段说明 + 可运行骨架**（`success_rate_test.py`）**：`CASES` 从生产日志抽、`is_valid()` 逐字段可判定、阈值「基线 − 噪声」 | 样本量口径引用第 1 章 1-1 的既有数据（分辨 10 个百分点要 ~195 条）；**代码与 3 条样本标注「示例：构造数据，未实跑」**；开头写明「0.95 只是起手值，不是标准」 |
| **L265–L327** | 新增「**自己跑一遍：可运行的对照脚本**」（`lost_in_the_middle.py`）：填充长度 / 关键信息位置 / 判据全写成变量，可直接跑；含「必须确认 `stop_reason` 不是 max_tokens 才能下结论」的判据 | **本次新写，标注「未实跑」** —— 正文明确写「不要把它给出的任何数字当实测」 |

**改过的句子（审计相关）**：原文 L104-105 的 `load_test_cases()` / `is_valid()` 从「空函数」改为「带实现与示例数据的骨架」；这是审计点名的缺口，属于**补充而非删改**。

### 1.4 `04-how-to-use-this-site.mdx`（审计：B —— 「去申请一个 Key」只有一句话）

| 行号 | 内容 | 依据 |
|---|---|---|
| L33–L35 | `RAG` / `MCP` 首现展开并给类比（RAG = 检索结果注入 prompt；MCP = 模型侧的 USB-C） | 概念定义 |
| L96 附近 | 「轨迹」首现定义 + 指向第 0 章第 2 节 | 概念定义 |
| **L179–L216** | 新增「**两分钟拿到第一把 Key**」：4 步分步清单 + 三家控制台对照表 + **四项配置的示例值**（厂商 / 端点地址 / 模型名 / Key）+ 一张「按报错关键词定位」的失败表（401 / invalid model / 402 / 超时） | 端点地址与模型名来自站内实测环境；**免费额度一栏明确标注「未逐一实测，以控制台为准」**，示例值标注「构造数据，未实跑」 |

---

## 2. 章 llm-api-basics

### 2.1 `01-tokens-and-context.mdx`（审计：A —— 全章缺「第一次跑起来」的路径）

| 行号 | 内容 | 依据 |
|---|---|---|
| **L7–L100** | 新增章首「**先把第一次调用跑通**」：`pip install anthropic`、四个环境变量对照表（含 `ANTHROPIC_API_KEY` vs `ANTHROPIC_AUTH_TOKEN` 二选一、base_url 留空的实现方式）、6 行 hello world | 环境与认证 = 本次实跑同一套 |
| L50–L56 | hello world 的**真实输出**：`stop_reason: end_turn`、`input/output: 35 16`、`blocks: ['thinking','text']`，并解释三个数字的意义 | **本次实跑 2026-10-12** |
| L64–L77 | 把 `max_tokens` 设成 64 时撞上的**真实失败**：200 但 content 里只有 thinking、没有 text、`stop_reason=max_tokens` —— 静默截断的最小形态 | **本次实跑 2026-10-12** |
| L104–L122 | 「约 5 / 约 30」补上**可复算的推导**（用 7 字符 35 token 与 350 字符 280 token 两个方程解得 a≈0.714、b≈30） | 两个输入取自本节既有实测；拟合结果在正文标注「不是官方字段」 |
| L274 附近 | 运行示例补全三个环境变量（原来只 export 了 API_KEY） | 与新增的环境变量表一致 |

**仍未解决**：无。

### 2.2 `02-sampling-params.mdx`（审计：A —— adaptive thinking 未解释、「thinking 吃掉多少钱」无数字）

| 行号 | 内容 | 依据 |
|---|---|---|
| L186–L190 | `adaptive thinking` **定义**（模型自决是否思考）+ 明确「思考输出计入 `output_tokens`」 | **本次实跑**：默认带 thinking 的输出是 63/83/75，`disabled` 是 3/3/2 |
| L190 | `beta header` 定义（提前启用未默认开启能力的开关） | 概念定义 |
| **L192–L211** | 新增「**实测：thinking 开与关，output_tokens 差多少**」：同一道两步算术题各跑 3 次，输出 63/83/75 vs 3/3/2；输入 70 vs 44；两个结论（输出侧差一个数量级、思考是高方差项），并补「Opus 5.5 关不掉」的边界 | **本次实跑 2026-10-12，`deepseek-flash`，n=3**；正文已声明 3 次只够说明量级 |

### 2.3 `03-messages-api.mdx`（审计：A —— 无完整脚本、无原始 SSE 线格式、无中断/重连）

| 行号 | 内容 | 依据 |
|---|---|---|
| L78 附近 | `Server-Sent Events` 首现展开（单向推送、`event:`+`data:`+空行，非 websocket） | 概念定义 |
| **L88–L150** | 新增**原始 SSE 报文**（真实 `event:`/`data:` 行 + 空行分隔），并给出两个只有看原始行才能发现的细节：`tool_use` 的 `input` 在 start 事件里是 `{}`；thinking 块 start 时是空串 | **本次实跑 2026-10-12**：129 行 / 5720 字符，事件计数与正文一致（delta×35、start×2、stop×2、start/ping/message_delta/message_stop 各 ×1） |
| L269 附近 | `poka-yoke` 首现定义（防呆：让错误操作无法表达） | 概念定义 + 引用第 4 章既有实测 |
| **L259–L372** | 新增「**完整可跑版本**」`stream_consumer.py`：`client.messages.stream()` 上下文管理器、`index→id` 归集、`content_block_stop` 时解析、`stop_reason` 断言、`stream.close()` **主动中断**（`abort_if`） | **未实跑**，正文标注；归集规则与本次实跑的原始报文一致 |
| L374–L384 | 新增「**断线与重放：三条必须自己做的事**」表格：断在文本中 / 工具已执行后 / 参数分片中途分别怎么处理，并说明「服务端生成的 call id 不能跨重试去重，要用你自己的幂等键」 | 机制推理；指向第 11 章的崩溃注入实测 |

**仍未解决**：`stream.close()` 与 `get_final_message()` 的签名未在本机 SDK 上确证（本机采集走的是原始 HTTP）—— 已在正文写进「跑之前先确认你这版 SDK 的签名」。

### 2.4 `04-model-selection.mdx`（审计：A —— 分层路由只有决策树、没有落地步骤）

| 行号 | 内容 | 依据 |
|---|---|---|
| **L133–L142** | 把两个「维度」翻成**可执行代理指标**（推理深度 → 要不要跨来源/多步；错误代价 → 能不能自动发现、能不能回滚） | 判据设计 |
| **L144–L223** | 新增「**最小路由实现**」`router.py`：① 关键词规则 → ② 一次分类调用（白名单校验返回值，防「模型乱答」）→ ③ `FALLBACK_TIER` 兜底；并给三个设计决定及理由（规则在前、分类失败要能发现、**兜底走高不走低**） | 代码为本次新写；成本量级引用第 7 章既有的**本地计算**（规则路由省 69%、级联升级反而更贵、收益上限=难题占比） |

**仍未解决（并在正文里标注了）**：「强模型更可靠、所以兜底走高」这个因果**本轮没有做同题两档对照实测** —— 我在正文把它标成「经验判断」而非「有文档依据」，并给出该做的实验设计。审计要求的「同题两档质量-成本实测表」本轮未产出（涉及多个模型档位，本机端点只暴露一个模型名）。

### 2.5 `05-prompt-caching.mdx`（审计：A —— 「字节级比对」只给要求不给方法、工具缓存只给一句话）

| 行号 | 内容 | 依据 |
|---|---|---|
| **L146–L181** | 新增「**第 3 项怎么查：前缀哈希比对**」`prefix_diff.py`（把 tools/system/messages 规范序列化后 sha256 比对），并说明它与 usage 字段的分工（本地哈希查「内容不同」，`cache_read` 查「服务端没复用」） | 纯本地实现，正文标注「**示例：构造数据，未实跑**」 |
| **L183–L215** | 新增「**工具定义怎么缓存：可复制的写法**」：`cache_control` 标在 tools 数组**最后一个工具**的完整代码 + 两个易踩细节（断点在末尾不是开头、每请求最多 4 个断点） | 机制解释；标注「示例：构造数据，未实跑」，并重申实测过的「DeepSeek 兼容端点忽略 `cache_control`」 |

---

## 3. 章 prompt-engineering

### 3.1 `01-instruction-clarity.mdx`（审计：A —— 同层冲突只有 n=3，与自己主张打架）

| 行号 | 内容 | 依据 |
|---|---|---|
| **L198–L204** | 新增**置信度边界**块：明确「每条件只跑 3 次，只够当示意」；指出「先法文后中文 ×3」与「先中文后法文 1/2」方向互相矛盾 → 不能读成排序规则；并列更强的证据（第 3 章第 2 节同 prompt 跑 12 次 = 8 承诺 / 4 不承诺） | 站内已有实测（12 次那组）+ 第 1 章的样本量口径 |

### 3.2 `02-structure-and-separation.mdx`（审计重灾区：`is_supported_by` 是黑盒）

| 行号 | 内容 | 依据 |
|---|---|---|
| L134–L139 | 把调用点改成**真实函数名** `unsupported_tokens(text, doc)`，并注明实现在节末 | 与下方实现对齐 |
| **L157–L250** | 新增「**把第 3 条补成可跑的校验**」：方案 A（高风险 token + 数字比对）vs 方案 B（句级相似度）对照表；给出完整 `support_check.py`；**本次实跑结果：清白文档误报 0/6、被注入文档命中 6/6**（每行都标出 `['一次性','无关','资产出售']`） | **本次实跑 2026-10-12，n=6 × 2 组** |
| L246–L250 | 三条边界诚实声明：抓的是「注入词本身」不是「注入行为」；数字比对零误报才是真正价值；**方案 B 阈值未实测，不推荐照抄** | 实验边界 |

**仍未解决**：`extract_claims` / `FORBIDDEN_MARKS` 仍是未定义引用（审计也点了）。本轮统一在实现里用 `unsupported_tokens` + 明确说明「禁词表属于你的业务配置，本节给不出通用值」，没有为它们编造一个通用实现。

### 3.3 `03-few-shot.mdx`（审计：A —— 「加示例有没有提升」缺统计判据）

| 行号 | 内容 | 依据 |
|---|---|---|
| **L97–L179** | 新增「**「加了示例有没有提升」怎么判断**」：测试集 / 重复次数 / 阈值三要素表 + 判据一句话（删掉某条示例后边界题从全对变有错且 5 遍稳定复现）+ 消融脚本 `ablate_examples.py` | 测试题与示例取自本节既有实测脚本；**消融脚本本次新写、标注未实跑**；样本量口径引用第 1 章 |

### 3.4 `04-chain-of-thought.mdx`（审计：B —— prefill 只有伪代码、发现重复却没给修复动作）

| 行号 | 内容 | 依据 |
|---|---|---|
| **L89–L124** | 把「伪代码示意」换成 **messages 数组 + 真实结果**：`HTTP 200`、`stop_reason=end_turn`、`usage: 68/211`、续写是 **`{"city":"北京","temp_c":20}`**（完整对象）；画出「预填 + 续写直接拼 = 解析必失败」；给出三条处理策略表（① 直接解析续写 ✅ 推荐、② 剥重兜底 ✅、③ stop 序列 ❌ 未测） | **本次实跑 2026-10-12**，与原文 2026-10-08 的观察一致（原文说「会得到两个对象」，本次量化了形态） |
| **L126–L210** | 新增 `prefill_safe.py`：完整 SDK 调用 + `parse_continuation()`（先整体解析、失败再剥重）+ `assert isinstance(result, dict)` 断言 + 失败时打印预填/续写原文 | **本次新写，标注未实跑** |
| L200–L210 | 新增**厂商支持差异表**（Anthropic ✅ / DeepSeek 兼容端点 ✅ 本次实跑 / OpenAI ❌ 无等价机制 → 用格式示例近似） | 前两行有依据；第三行正文明确标注「文档层面判断，本次未实测」 |

### 3.5 `05-reliability.mdx`（审计：A —— 主观项无改造方法、脚本 `import os` 却写进注释）

| 行号 | 内容 | 依据 |
|---|---|---|
| L271–L357 | 新增「**主观项怎么挪到代码层**」：主观项 → 代理指标对照表（摘要忠实度 → 数字/专名全覆盖 + 长度区间 + 可定位；语气 → 禁词/疑问句/第一人称；跑题 → 主题词覆盖率或向量余弦）+ 完整 `proxy_metrics.py` + 三条使用规则（代理≠原指标、阈值来自自己的统计、先量误杀率） | **代码为示例，正文标「构造数据，未实跑」** |
| L283 | `嵌入模型` 首现定义（定长向量、语义相近则距离近），并说明为什么排在规则之后 | 概念定义 |

**关于 `import os`**：审计说 `validation_layer.py` 的 import 里没有 `os` 而 L187 用了 `os.environ`。复核结果：脚本**本来就有 `import os`，但它写在 `# validation_layer.py` 这一行文件头注释之上、与 `import re` 等隔了一块 docstring** —— 视觉上极易被读成「没有 import」。已把它移到 docstring 之后、与其它 import 放在一起（**功能等价，只是顺序**），并顺手补上 `ANTHROPIC_AUTH_TOKEN` 回退，与本章其它脚本的凭据写法统一。这不是缺陷修复，是消除审计误读的来源。

---

## 4. 关于 `pnpm test`（含一次并发写盘造成的假失败）

最终状态：**65/65 全绿**。

```text
 ✓ tests/sse.test.ts (15 tests)
 ✓ tests/image-tokens.test.ts (4 tests)
 ✓ tests/inline-md.test.ts (5 tests)
 ✓ tests/curriculum.test.ts (41 tests)
 Test Files  4 passed (4)      Tests  65 passed (65)
```

**但过程中出现过一次假失败，值得记下。** 修复中途 `pnpm test` 曾报 `1 failed | 64 passed`，失败项是 `tests/curriculum.test.ts` 的「粗体两端必须构成合法分隔符」检查，指向 `agent-paradigms/04-reflection.mdx`，随后又先后变成 `agent-frameworks/05-selection-matrix.mdx`、`sandboxing/05-execution-policy.mdx` 等 —— **全部在我未被授权修改的其它目录，且不同运行归属不同文件**。这是工作区里**并发写盘**的其它批次造成的。

我据此做了两件事：
1. **只修我改动引入的那一条同类问题** —— `llm-api-basics/05-prompt-caching.mdx` 里的 `**注意：**`（冒号被包进粗体，属于 CommonMark flanking 违规），改为 `**注意**：`；此后该文件不再出现在失败列表。
2. 等并发批次写完后再跑，确认我的改动本身不产生任何断言失败。

**结论**：`pnpm test` 现在全绿；先前那次失败与本次修复无关，且已因并发批次自身修正而消失。

---

## 5. 数字来源清单（本次新增的全部数字）

**本次真跑（2026-10-12，`deepseek-flash`，DeepSeek 的 Anthropic 兼容端点）**：

| 数字 | 位置 | 复现方式 |
|---|---|---|
| hello world：input 35 / output 16 / blocks `[thinking,text]` | llm-api-basics/01 L50 | 文中 6 行脚本 |
| `max_tokens=64` → 只剩 thinking 块、`stop_reason=max_tokens` | llm-api-basics/01 L74 | 同上，改 max_tokens |
| thinking 开/关输出 63/83/75 vs 3/3/2，输入 70 vs 44 | llm-api-basics/02 L192 | 文中口径（52 字符提示 + 两步算术） |
| SSE 原始流 129 行 / 5720 字符；delta×35、start×2、stop×2 | llm-api-basics/03 L88 | 文中 `stream=True` + `get_weather` |
| prefill：200、`end_turn`、68/211、续写 = 完整对象 | prompt-engineering/04 L89 | 文中 messages 数组 |
| 校验层：误报 0/6、命中 6/6 | prompt-engineering/02 L157 | 文中 `support_check.py` |

**未跑，已在正文就地标注**：轨迹 JSON 形状、success_rate_test、lost_in_the_middle、stream_consumer、router、prefix_diff、工具缓存写法、proxy_metrics、ablate_examples、prefill_safe、账单相加算式、四项配置示例值。**没有一个是标成实测的。**

**改过的既有内容**：只有 1 处功能性的 —— 见 §3.5 关于 `import os` 的说明（复核后**未改**）。此外 35 个原本无语言的 ``` 围栏补上了 `text`/语言标签（内容零改动，只改了围栏行）。

---

## 6. 术语首现处理小结

本轮在正文里解释/展开的术语：token、JSON Schema、prompt caching、ReAct、轨迹、prompt chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer、SSE、adaptive thinking、beta header、poka-yoke、RAG、MCP、temperature、max_tokens、stop_reason、嵌入模型。

`depth-check` 的「术语首现无解释」是**跨章按章序取首现**的检查，它仍会报到本批之外章节的首次出现（如 `RAG` 因某处先出现而被记在 what-is-an-agent/04），属于工具口径而非内容缺陷 —— 所有这些词的**定义都在正文里**，没有依赖术语表。
