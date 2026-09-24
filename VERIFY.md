# 待验证内容清单

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

| 状态 | 字段 |
|---|---|
| 支持 | `x-api-key`、`max_tokens`、`stream`、`system`、`stop_sequences`、`temperature`、`thinking`（`budget_tokens` 被忽略） |
| **被忽略** | `container`、`mcp_servers`、`service_tier`、`top_k`、**`cache_control`** |

所以用方式 B 时：

- ✅ 能验证：消息结构、`system` 位置、流式事件、多轮对话、`max_tokens`
- ❌ 验证不了：prompt caching（`cache_control` 被忽略）、`effort`、adaptive thinking
- ⚠️ 注意：DeepSeek **支持** `temperature`，而 Claude 新模型**已移除**它 —— 同一份代码在两边行为不同，这正是多厂商适配的真实难点

---

## 第一章：LLM 基础与 API 调用

### 1. `01-tokens-and-context.mdx` — token 与上下文窗口

| # | 待验证 | 怎样算通过 |
|---|---|---|
| 1.1 | `count_tokens` 的调用方式与响应字段 | 能打印出 `input_tokens` 且为正整数 |
| 1.2 | 新旧分词器的 token 数差异 | 同一段文本分别用 `claude-sonnet-4-5` 与 `claude-sonnet-5` 计数，后者多约 30% |

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

### 2. `02-sampling-params.mdx` — 采样参数的消失

| # | 待验证 | 怎样算通过 |
|---|---|---|
| 2.1 | 传 `temperature` 是否报 400（Anthropic 新模型） | 报 400 即符合文档描述 |
| 2.2 | `output_config.effort` 的写法 | 请求成功，且 effort 影响输出长度 |

```bash
# 2.1 预期失败：Anthropic 新模型应返回 400
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-opus-5-5","max_tokens":64,"temperature":0.2,
       "messages":[{"role":"user","content":"hi"}]}' | head -c 400

# 2.2 预期成功
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

| # | 待验证 | 怎样算通过 |
|---|---|---|
| 3.1 | `system` 作为顶层字段可用 | 请求成功且模型遵循了 system 指令 |
| 3.2 | 流式事件序列 | 依次出现 `message_start` → `content_block_*` → `message_delta` → `message_stop` |
| 3.3 | **`input_json_delta` 只带 index、不带 id** | 在原始事件里确认这一点 |
| 3.4 | `message_delta` 的 usage 是累积值 | 对比多轮事件里的数值变化 |

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

| # | 待验证 | 怎样算通过 |
|---|---|---|
| 4.1 | 多轮对话的 token 增长是平方级的 | 连续几轮后，`input_tokens` 随轮次线性增长，累计消耗呈平方增长 |

这一节无需专门验证 —— 它是成本算术，用 4.1 的方式心算即可确认。

---

### 5. `05-prompt-caching.mdx` — prompt caching

| # | 待验证 | 怎样算通过 |
|---|---|---|
| 5.1 | 缓存写入后第二次请求命中 | 第二次的 `cache_read_input_tokens` > 0 |
| 5.2 | **低于最小 token 门槛时不缓存且不报错** | 用一个短 prompt 加 `cache_control`，两个缓存字段都是 0 |
| 5.3 | 改变前缀会让缓存失效 | 在断点之前插入一个字符，命中归零 |

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
