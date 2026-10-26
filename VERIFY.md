# 待验证内容清单

> **2026-10-09 更新：第一轮验证已完成。** 结果见下方「已验证」一节 —— 过程中修掉了 3 个真实缺陷。

## 已验证（2026-10-09）

环境：`anthropic 0.39.0`（另用 `1.12.1` 交叉确认）+ DeepSeek 的 Anthropic 兼容端点，模型 `deepseek-flash`。
脚本：`verify-output/verify-ch1-5.py`（协议层）；正文章节里的 SDK 脚本逐个抽出实跑。

| 项                                             | 结果                  | 说明                                                                                                                    |
| ---------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 1.1 `count_tokens` 的调用方式与响应字段        | ✅ 通过               | 返回 `MessageTokensCount`，`input_tokens = 36`。**但方法位置随 SDK 版本变**（见下「修复 1」）                           |
| 1.1′ 五个样本的 token 数                       | ✅ 与正文表格逐行一致 | 7 字符→35、1050 字符→381（0.36/字符，正文说的区间下界）                                                                 |
| 3.1 `system` 作为顶层字段可用                  | ✅ 通过               | 请求成功且模型遵循了 system 指令                                                                                        |
| 3.2 流式事件序列                               | ✅ 通过               | 六类事件齐全且顺序正确（另有 `ping` 心跳）                                                                              |
| 3.3 **`input_json_delta` 只带 index、不带 id** | ✅ **确认**           | 9 个 delta，顶层键只有 `delta` / `index` / `type`。**在非 Anthropic 的实现上也成立** → 这是协议形状，不是某家的实现细节 |
| 3.4 `message_delta` 的 usage                   | ✅ 通过               | 带最终 `output_tokens`（累积终值）。⚠️ 但 DeepSeek 的 `message_start.usage` 是 `{}`，官方端点会带 usage                 |
| 4.1 多轮对话的 token 增长                      | ✅ 通过               | 40 → 55 → 70 → 85（每轮 +15），符合「线性增长、累计平方」                                                               |
| 跨厂商行为差异                                 | ✅ 新增实测           | 空模型名→400；**缺 `max_tokens`→200**；**传 `temperature`→200**。后两条与官方端点不同                                   |

### 验证时修掉的三个真实缺陷

**修复 1：`client.messages.count_tokens` 在旧 SDK 上不存在。**

```
anthropic 0.39.0  →  client.messages 上没有这个方法，它在 client.beta.messages 下
anthropic 1.12.1  →  client.messages.count_tokens 存在
```

原代码写死前者，在 0.39.0 上直接 `AttributeError`。**正文里那句「用 `getattr` 兼容返回类型差异」没能兜住它** ——
因为缺的是方法本身，不是返回类型的差异。现在改成 `getattr(client.messages, "count_tokens", None) or client.beta.messages.count_tokens`。
共 3 处（章 1 两处、章 4 一处）。

**修复 2：`client._client.post(...)` 永远 401。**

实测 `client._client` 的默认头是 `accept` / `accept-encoding` / `connection` / `user-agent` —— **没有认证字段**。
SDK 是在每次请求内部加 `x-api-key` 的，不在默认头上。所以直接 post 会一路 401「Authentication Fails」，
把三段错误探测的真实行为全遮住（这一点很危险：**它看起来像「错误行为就是这样」，其实是没通过认证**）。
现在改成自己带头的 httpx 客户端 —— 对照实验确认：同样请求带 `x-api-key` 则 200。

**修复 3：章 4 的脚本引用了两个从未定义的变量。**

`MY_SYSTEM_PROMPT` 与 `MY_TYPICAL_MESSAGES` 被引用但没有赋值，按「完整可运行代码」的标准印出来**跑不起来**。已补上定义。

### 无法用本环境验证的项

以下项目在 DeepSeek 兼容端点上**验不了**，原因在端点而不在内容：

| 项                              | 为什么验不了                                                                 |
| ------------------------------- | ---------------------------------------------------------------------------- |
| 5.1–5.3 prompt caching          | `cache_control` 被静默忽略 —— 看起来像「缓存一直不生效」，实际是字段没被处理 |
| 2.1 传 `temperature` 是否报 400 | DeepSeek **支持** `temperature`（实测 200），验不了 Anthropic 新模型的行为   |
| 2.2 `output_config.effort`      | 该字段在兼容端点上不被处理                                                   |
| 1.2 新旧分词器的 token 差异     | 需要同时访问 `claude-sonnet-4-5` 与 `claude-sonnet-5` 两个模型               |

> 这几项要等有 Anthropic 官方 Key 时再验。**但注意 2.1 的实测结果本身有价值**：
> 同一个参数在一家被接受、在另一家报 400 —— 这正是第 1 章「兼容不等于一致」那句话的现场证据。

---

这个文件存在的理由：本站的写作标准要求「代码必须实跑过」，但目前撰写这些章节时**没有可用的 API Key**，所以代码只做了语法检查，**行为未经真实执行验证**。

与其在每节末尾写一句免责声明了事，不如把待验证项集中列在这里 —— 这样你手上有 Key 时可以一次性验完，而不是逐页去找。

验证通过后，请把对应章节正文里的「实跑状态」标注删掉，并在 `meta.ts` 里更新 `verifiedAt`。

---

## 验证前：两种调用方式

本站正文以 Anthropic 官方 API 为准（文档最权威），但**DeepSeek 提供了 Anthropic 兼容端点**，所以没有 Anthropic Key 也能验证相当一部分内容。

**方式 A：Anthropic 官方 API**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**方式 B：DeepSeek 的 Anthropic 兼容端点**

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="<你的 DeepSeek Key>"
```

⚠️ **但"兼容"不等于"一致"** —— DeepSeek 明确列出了一些被忽略的字段：

| 状态       | 字段                                                                                                                 |
| ---------- | -------------------------------------------------------------------------------------------------------------------- |
| 支持       | `x-api-key`、`max_tokens`、`stream`、`system`、`stop_sequences`、`temperature`、`thinking`（`budget_tokens` 被忽略） |
| **被忽略** | `container`、`mcp_servers`、`service_tier`、`top_k`、**`cache_control`**                                             |

所以用方式 B 时：

- ✅ 能验证：消息结构、`system` 位置、流式事件、多轮对话、`max_tokens`
- ❌ 验证不了：prompt caching（`cache_control` 被忽略）、`effort`、adaptive thinking
- ⚠️ 注意：当前 DeepSeek Anthropic-compatible 文档按字段与 model/mode 列出不同语义；Anthropic API 的采样参数弃用也按模型范围描述。迁移时要分开测试 SDK 方法签名、endpoint 字段处理和 model 行为，不能用“Claude 新模型”作一刀切结论。

---

## 第一章：LLM 基础与 API 调用

### 1. `01-tokens-and-context.mdx` — token 与上下文窗口

| #   | 待验证                              | 怎样算通过                                                                   |
| --- | ----------------------------------- | ---------------------------------------------------------------------------- |
| 1.1 | `count_tokens` 的调用方式与响应字段 | 能打印出 `input_tokens` 且为正整数                                           |
| 1.2 | 新旧分词器的 token 数差异           | 同一段文本分别用 `claude-sonnet-4-5` 与 `claude-sonnet-5` 计数，后者多约 30% |

```bash
python3 - <<'PY'
import anthropic
client = anthropic.Anthropic()
count = client.messages.count_tokens(
    model="claude-sonnet-5",
    messages=[{"role": "user", "content": "用一句话解释什么是 token。"}],
)
print(count)
PY
```

**预期**：输出含 `input_tokens`。若报错说对象没有该属性，说明 SDK 版本的返回类型与文档示例不同 —— 请以实际输出为准并反馈。

---

### 2. `02-sampling-params.mdx` — 采样参数与模型/SDK 契约

| #   | 待验证 | 怎样算通过 |
| --- | --- | --- |
| 2.1 | 在锁定的目标 model 上传非默认 `temperature` 的 API 行为 | 与该 model 的官方弃用说明一致；记录 API model ID、endpoint、请求 ID 和响应类型，不能推广到其他模型 |
| 2.2 | Anthropic Python SDK 1.x 的方法签名 | 直接传 `temperature=` 应在本地抛 `TypeError`，不会发 HTTP 请求；旧 model 如确需设置，另按 SDK 官方迁移指南验证 `extra_body` 与服务端支持 |
| 2.3 | `output_config.effort` 的端点和模型支持 | 请求成功只证明配置被接受；比较行为要用固定任务集与预设判据，不能用单次响应长度证明 effort 生效或质量变化 |

```bash
# 2.1 仅在当前 model 文档仍规定非默认 sampling 返回 400 时运行；支持范围随 model 变化
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-opus-5-5","max_tokens":64,"temperature":0.2,
       "messages":[{"role":"user","content":"hi"}]}' | head -c 400

# 2.3 请求示例：成功不等于 effort 改变了输出长度或任务质量
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-opus-5-5","max_tokens":256,
       "output_config":{"effort":"low"},
       "messages":[{"role":"user","content":"用一句话解释 token"}]}' | head -c 400
```

---

### 3. `03-messages-api.mdx` — Messages API 与流式

| #   | 待验证                                     | 怎样算通过                                                                      |
| --- | ------------------------------------------ | ------------------------------------------------------------------------------- |
| 3.1 | `system` 作为顶层字段可用                  | 请求成功且模型遵循了 system 指令                                                |
| 3.2 | 流式事件序列                               | 依次出现 `message_start` → `content_block_*` → `message_delta` → `message_stop` |
| 3.3 | **`input_json_delta` 只带 index、不带 id** | 在原始事件里确认这一点                                                          |
| 3.4 | `message_delta` 的 usage 是累积值          | 对比多轮事件里的数值变化                                                        |

3.3 是最值得亲手验的一条 —— 它决定了流式工具调用解析代码怎么写：

```bash
curl -sN https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-opus-5-5","max_tokens":512,"stream":true,
       "tools":[{"name":"get_weather","description":"查询指定城市当前天气",
                 "input_schema":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}],
       "messages":[{"role":"user","content":"北京今天天气怎么样？"}]}' \
  | grep -E "^event:|partial_json" | head -30
```

**预期**：能看到 `content_block_start`（带 `tool_use` 的 id 与 name），随后的 `input_json_delta` 事件里**只有 `index` 与 `partial_json`，没有 `id`**。

---

### 4. `04-model-selection.mdx` — 模型选型与成本

| #   | 待验证                          | 怎样算通过                                                    |
| --- | ------------------------------- | ------------------------------------------------------------- |
| 4.1 | 多轮对话的 token 增长是平方级的 | 连续几轮后，`input_tokens` 随轮次线性增长，累计消耗呈平方增长 |

这一节无需专门验证 —— 它是成本算术，用 4.1 的方式心算即可确认。

---

### 5. `05-prompt-caching.mdx` — prompt caching

| #   | 待验证                                  | 怎样算通过                                             |
| --- | --------------------------------------- | ------------------------------------------------------ |
| 5.1 | 缓存写入后第二次请求命中                | 第二次的 `cache_read_input_tokens` > 0                 |
| 5.2 | **低于最小 token 门槛时不缓存且不报错** | 用一个短 prompt 加 `cache_control`，两个缓存字段都是 0 |
| 5.3 | 改变前缀会让缓存失效                    | 在断点之前插入一个字符，命中归零                       |

> ⚠️ 这一节**无法用 DeepSeek 兼容端点验证** —— `cache_control` 会被静默忽略，看起来像"缓存一直不生效"。这本身就是个值得记住的现象。

```bash
# 连发两次，看第二次的 cache_read_input_tokens
for i in 1 2; do
  curl -s https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model":"claude-opus-5-5","max_tokens":64,
         "system":[{"type":"text","text":"<在这里放一段足够长(>1024 token)且固定的文本>",
                    "cache_control":{"type":"ephemeral"}}],
         "messages":[{"role":"user","content":"hi"}]}' \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['usage'])"
done
```

**预期**：第一次 `cache_creation_input_tokens` > 0、`cache_read_input_tokens` 为 0；第二次反过来。

---

## 验证后要做的事

1. 删除对应正文里的 `> **实跑状态**：...` 引用块
2. 更新该章 `meta.ts` 的 `verifiedAt`
3. 若发现正文与实际情况不符 —— **以实际为准**，改正文而不是改标注
