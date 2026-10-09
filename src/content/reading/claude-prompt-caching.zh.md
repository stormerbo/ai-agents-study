prompt 缓存通过允许从你的 prompt 中的特定前缀恢复，优化你的 API 使用。这显著减少了重复性任务或具有一致元素的 prompt 的处理时间和成本。
启用 prompt 缓存有两种方式：
自动缓存
: 在你的请求的顶层添加一个单一的
cache_control
字段。系统自动将缓存断点应用于最后一个可缓存 block，并随着对话增长将其向前移动。最适合多轮对话，其中不断增长的消息历史应自动缓存。
显式缓存断点
: 将
cache_control
直接放在单个 content block 上，以精细控制具体缓存什么。
最简单的开始方式是使用自动缓存：
cURL
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

client
=

anthropic.Anthropic()
response
=

client.messages.create(
model
=

"claude-opus-5-5"
,
max_tokens
=

1024
,
cache_control
=

{
"type"
:
"ephemeral"
},
system
=

"You are an AI assistant tasked with analyzing literary works. Your goal is to provide insightful commentary on themes, characters, and writing style."
,
messages
=

[
{
"role"
:
"user"
,
"content"
:
"Analyze the major themes in 'Pride and Prejudice'."
,
}
],
)
print
(response.usage.model_dump_json())
使用自动缓存时，系统会缓存直到并包括最后一个可缓存 block 的所有内容。在具有相同前缀的后续请求中，缓存内容会自动重用。

## prompt 缓存如何工作 

当你发送启用了 prompt 缓存的请求时：
系统会检查直到指定缓存断点的 prompt 前缀是否已从最近的查询中缓存。
如果找到，它会使用缓存版本，从而减少处理时间和成本。
否则，它会处理完整 prompt，并在响应开始时缓存该前缀。
这对于以下情况特别有用：
具有许多示例的 prompt
大量上下文或背景信息
具有一致指令的重复性任务
长多轮对话

默认情况下，缓存的生命周期为 5 分钟。每次使用缓存内容时，缓存都会免费刷新。

生命周期从写入或读取缓存条目的请求开始时计算，而不是从其响应结束时计算。生成响应所花费的时间会计入该生命周期：如果响应流式传输需要 4 分钟，那么复用相同缓存前缀的后续请求必须在该响应完成后约 1 分钟内开始。

## 定价

Prompt caching 引入了新的定价结构。下表显示了每个受支持模型的每百万 tokens 价格：

模型
基础 tokens
Prompt caching
名称
输入
输出
5m 写入
1h 写入
命中与刷新
Claude Fable 5.1
适用于高要求的推理和长周期 agentic 工作
$10
/ MTok
$50
/ MTok
$12.50
/ MTok
$20
/ MTok
$0.25
/ MTok
1
Claude Opus 5.5
适用于长时间运行的 agentic 编码和知识工作
$4
/ MTok
$20
/ MTok
$5
/ MTok
$8
/ MTok
$0.20
/ MTok
2
Claude Sonnet 5.5
速度与智能的最佳组合
$2
/ MTok
$10
/ MTok
$2.50
/ MTok
$4
/ MTok
$0.10
/ MTok
2
Claude Haiku 5.5
适用于高吞吐量、对延迟敏感的任务，例如分类、提取和路由
$0.10
/ MTok
对于最多 100,000 tokens 的 prompts
$0.50
/ MTok
$0.125
/ MTok
$0.20
/ MTok
$0.01
/ MTok
$0.50
/ MTok
对于超过 100,000 tokens 的 prompts
$2.50
/ MTok
$0.625
/ MTok
$1
/ MTok
$0.05
/ MTok

其他模型
Claude Mythos 5.1
$10
/ MTok
$50
/ MTok
$12.50
/ MTok
$20
/ MTok
$0.25
/ MTok
1
Claude Fable 5
$10
/ MTok
$50
/ MTok
$12.50
/ MTok
$20
/ MTok
$1
/ MTok
Claude Mythos 5
$10
/ MTok
$50
/ MTok
$12.50
/ MTok
$20
/ MTok
$1
/ MTok
Claude Opus 5
$5
/ MTok
$25
/ MTok
$6.25
/ MTok
$10
/ MTok
$0.50
/ MTok
Claude Opus 4.8
$5
/ MTok
$25
/ MTok
$6.25
/ MTok
$10
/ MTok
$0.50
/ MTok
Claude Opus 4.7
$5
/ MTok
$25
/ MTok
$6.25
/ MTok
$10
/ MTok
$0.50
/ MTok
Claude Opus 4.6
$5
/ MTok
$25
/ MTok
$6.25
/ MTok
$10
/ MTok
$0.50
/ MTok
Claude Opus 4.5
$5
/ MTok
$25
/ MTok
$6.25
/ MTok
$10
/ MTok
$0.50
/ MTok
Claude Opus 4.1

$15
/ MTok
$75
/ MTok
$18.75
/ MTok
$30
/ MTok
$1.50
/ MTok
Claude Opus 4

$15
/ MTok
$75
/ MTok
$18.75
/ MTok
$30
/ MTok
$1.50
/ MTok
Claude Sonnet 5
$2
/ MTok
$10
/ MTok
$2.50
/ MTok
$4
/ MTok
$0.20
/ MTok
Claude Sonnet 4.6
$3
/ MTok
$15
/ MTok
$3.75
/ MTok
$6
/ MTok
$0.30
/ MTok
Claude Sonnet 4.5
$3
/ MTok
$15
/ MTok
$3.75
/ MTok
$6
/ MTok
$0.30
/ MTok
Claude Sonnet 4

$3
/ MTok
$15
/ MTok
$3.75
/ MTok
$6
/ MTok
$0.30
/ MTok
Claude Haiku 4.5
$1
/ MTok
$5
/ MTok
$1.25
/ MTok
$2
/ MTok
$0.10
/ MTok
Claude Haiku 3.5

$0.80
/ MTok
$4
/ MTok
$1
/ MTok
$1.60
/ MTok
$0.08
/ MTok
1
Claude Fable 5.1 和 Claude Mythos 5.1 上的 cache hit 与刷新按 base input price 的 0.025x 计价。
2
Claude Opus 5.5 和 Claude Sonnet 5.5 上的 cache hit 与刷新按 base input price 的 0.05x 计价。
所有其他模型均使用标准的 0.1x 乘数。

## 支持的模型

prompt caching（自动和显式）在所有
活跃的 Claude 模型
上均受支持。

## 自动缓存

自动缓存是启用 prompt caching 最简单的方式。无需在各个内容块上放置
cache_control
，只需在请求体的顶层添加一个
cache_control
字段。系统会自动将缓存断点应用到最后一个可缓存的块。
cURL
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

```python
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    cache_control={"type": "ephemeral"},
    system="You are a helpful assistant that remembers our conversation.",
    messages=[
        {
            "role": "user",
            "content": "My name is Alex. I work on machine learning."
        },
        {
            "role": "assistant",
            "content": "Nice to meet you, Alex! How can I help with your ML work today?",
        },
        {
            "role": "user",
            "content": "What did I say I work on?"
        },
    ],
)
print(response.usage.model_dump_json())
```

### 自动缓存在多轮对话中的工作方式

使用自动缓存时，随着对话增长，缓存点会自动前移。每个新请求都会将直到最后一个可缓存块为止的所有内容写入缓存，而之前的内容则从缓存中读取。

| Request   | Content                                                                              | Cache behavior                                           |
| --------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| Request 1 | System + User(1) + Asst(1) + User(2) ◀ cache                                         | 全部写入缓存                                             |
| Request 2 | System + User(1) + Asst(1) + User(2) + Asst(2) + User(3) ◀ cache                     | System 到 User(2) 从缓存读取；Asst(2) + User(3) 写入缓存 |
| Request 3 | System + User(1) + Asst(1) + User(2) + Asst(2) + User(3) + Asst(3) + User(4) ◀ cache | System 到 User(3) 从缓存读取；Asst(3) + User(4) 写入缓存 |

缓存断点会自动移动到每个请求中最后一个可缓存块，因此随着对话增长，你无需更新任何 `cache_control` 标记。

### TTL 支持

默认情况下，自动缓存使用 5 分钟的 TTL。你可以指定 1 小时的 TTL，价格为基准 input token 价格的 2 倍：

```json
{
  "cache_control": {
    "type": "ephemeral",
    "ttl": "1h"
  }
}
```

### 与块级缓存结合使用

自动缓存与显式 cache 断点兼容。两者一起使用时，自动缓存断点会占用 4 个可用断点槽位中的一个。

这样你就可以组合使用两种方式。例如，使用显式断点缓存你的 system prompt，同时由自动缓存处理对话内容：

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 1024,
  "cache_control": {
    "type": "ephemeral"
  },
  "system": [
    {
      "type": "text",
      "text": "You are a helpful assistant.",
      "cache_control": {
        "type": "ephemeral"
      }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "What are the key terms?"
    }
  ]
}
```

### 保持不变的部分

自动缓存使用相同的底层缓存基础设施。定价、最小 token 阈值、上下文排序要求以及 20 块回溯窗口都与显式断点相同。

### 边界情况

如果最后一个块已经有显式的 `cache_control`
在 TTL 相同的情况下，自动缓存是 no-op。
如果最后一个 block 带有显式 `cache_control` 且 TTL 不同，API 会返回 400 error。
如果已经存在 4 个显式的 block 级 breakpoint，API 会返回 400 error（没有剩余槽位可用于自动缓存）。
如果最后一个 block 不符合作为自动缓存 breakpoint 目标的条件，系统会静默向前回溯，寻找最近的一个符合条件 block。如果找不到，则跳过缓存。

## 显式 cache breakpoint

为了更精细地控制缓存，你可以把 `cache_control` 直接放在各个内容 block 上。当你需要缓存变化频率不同的不同部分，或需要对具体缓存内容进行细粒度控制时，这很有用。

### 组织你的 prompt

把静态内容（tool 定义、system 指令、context、示例）放在 prompt 的开头。使用 `cache_control` 参数标记可复用内容中用于缓存的结束位置。
缓存前缀按以下顺序创建：`tools`、`system`，然后是 `messages`。这个顺序构成了一种层级结构，其中每一层都建立在前面各层之上。

#### 自动前缀检查的工作方式

你只需在静态内容的末尾使用一个 cache breakpoint，系统就会自动找出先前请求已经写入缓存的最长前缀。理解其工作方式有助于你优化缓存策略。
三个核心原则：
缓存写入只发生在你的 breakpoint 处。
用 `cache_control` 标记一个 block 只会写入一条缓存条目：截至该 block 的前缀的 hash。系统不会为任何更早的位置写入条目。由于该 hash 是累积的，覆盖到 breakpoint 为止（含 breakpoint）的所有内容，因此在下一个请求中，只要改动 breakpoint 处或之前的任何 block，就会产生不同的 hash。
缓存读取会向前回溯查找先前请求写入的条目。
每次请求时，系统会在你的 breakpoint 处计算 prefix hash，并检查是否有匹配的 cache entry。如果不存在，它会一次一个 block 地向后回溯，检查每个更早位置的 prefix hash 是否与 cache 中已有的内容匹配。它寻找的是先前的写入，而不是稳定的内容。
lookback window 是 20 个 block。
系统每个 breakpoint 最多检查 20 个位置，将 breakpoint 本身计为第一个。如果系统在该 window 内未找到匹配的 entry，检查停止（或从下一个显式 breakpoint 继续，如果有的话）。在 Claude API 上，连续的
tool_use
blocks 算作一个位置，连续的
tool_result
blocks 也是如此，因此一个包含许多并行 tool calls 的 turn 不会仅凭自身将前一个请求的 entry 推出 window。
示例：在增长的对话中进行 Lookback
你在每个 turn 追加新的 blocks，并在每个请求的最后一个 block 上设置
cache_control
：
Turn 1：
10 个 blocks，breakpoint 在 block 10。不存在先前的 cache entries。系统在 block 10 写入一个 entry。
Turn 2：
15 个 blocks，breakpoint 在 block 15。Block 15 没有 entry，因此系统回溯到 block 10 并找到 turn-1 的 entry。在 block 10 处 cache hit；系统仅全新处理 blocks 11 到 15，并在 block 15 写入一个新的 entry。
Turn 3：
35 个 blocks，breakpoint 在 block 35。系统检查 20 个位置（blocks 35 到 16）并未找到任何内容。位于 block 15 的 turn-2 entry 在 window 外一个位置，因此没有 cache hit。在 block 15 添加第二个 breakpoint 会在那里启动第二个 lookback window，从而找到 turn-2 entry。
常见错误：将 Breakpoint 设置在每次请求都会变化的内容上
你的 prompt 有一个很大的静态 system context（blocks 1 到 5），后面跟着一个包含时间戳和用户消息的 per-request block（block 6）。你在 block 6 上设置
cache_control
：
Request 1：
在 block 6 处 cache write。Hash 包含时间戳。
Request 2：
timestamp 不同，所以 block 6 处的 prefix hash 不同。lookback 会遍历 block 5、4、3、2 和 1，但系统从未在那些位置中的任何一个写入条目。没有 cache hit。你在每个请求上都要支付一次全新的 cache write，却永远得不到一次 read。
lookback 不会在你的 breakpoint 背后找到稳定内容并将其缓存。它找到的是先前请求已经写入的条目，而写入只发生在 breakpoints 处。将 cache_control 移到 block 5，即跨请求保持不变的最后一个 block，之后每个请求都会读取缓存的 prefix。
Automatic caching 会落入同一个陷阱：它把 breakpoint 放在最后一个可缓存的 block 上，而在这个结构中，这个 block 就是每个请求都会变化的那个，所以改为在 block 5 上使用显式 breakpoint。
关键要点：
将 cache_control 放在最后一个 block 上，其 prefix 在你希望共享 cache 的请求之间完全相同。在持续增长的对话中，只要每一轮新增的 blocks 少于 20 个，最后一个 block 就有效：较早的内容从不变化，因此下一个请求的 lookback 会找到先前的写入。对于带有变化后缀的 prompt（timestamps、per-request context、传入的消息），将 breakpoint 放在静态 prefix 的末尾，而不是放在变化的 block 上。

#### 何时使用多个 breakpoints 

如果你想做到以下事项，最多可以定义 4 个 cache breakpoints：
缓存以不同频率变化的不同 sections（例如，tools 很少变化，但 context 每天更新）
更精确地控制到底哪些内容会被缓存
在持续增长的对话将你的 breakpoint 推到最后一次 cache write 之后 20 个或更多 blocks 时，确保 cache hit

### 理解 cache breakpoint 成本 

Cache breakpoints 本身不会增加任何成本。
你只需为以下各项付费：
Cache writes：
当新内容被写入 cache 时（对于 5-minute TTL，比 base input tokens 多 25%）
Cache reads：
当使用 cached content 时（base input token 价格的 10%，在 Claude Fable 5.1 和 Claude Mythos 5.1 上为 2.5%，在 Claude Opus 5.5
和 Claude Sonnet 5.5 上为 5%
）
Regular input tokens：
适用于任何未缓存的内容
添加更多
cache_control
breakpoint 不会增加你的成本；你仍然根据实际被缓存和读取的内容支付相同金额。breakpoint 让你能够控制哪些部分可以被独立缓存。

## 缓存策略与注意事项

### 缓存限制

在 Claude API、
Claude Platform on AWS
、
Google Cloud
和 Microsoft Foundry 上，最小可缓存 prompt 长度为：
512 tokens，适用于 Claude Fable 5.1、
Claude Mythos 5.1
、Claude Opus 5.5、Claude Opus 5、Claude Sonnet 5.5、Claude Fable 5、
Claude Mythos 5
和 Claude Haiku 5.5
2,048 tokens，适用于
Claude Mythos Preview
和 Claude Opus 4.7
4,096 tokens，适用于 Claude Opus 4.6 和 Claude Opus 4.5
1,024 tokens，适用于 Claude Opus 4.8、Claude Sonnet 5、Claude Sonnet 4.6、Claude Sonnet 4.5（
deprecated
）、Claude Opus 4.1（
retired, except on Bedrock and Google Cloud
）、Claude Opus 4（
retired, except on Google Cloud
）和 Claude Sonnet 4（
retired, except on Bedrock and Google Cloud
）
4,096 tokens，适用于 Claude Haiku 4.5
2,048 tokens，适用于 Claude Haiku 3.5（
retired, except on Google Cloud
）
这些最小值适用于每个模型可用的所有平台。
较短的 prompt 无法被缓存，即使使用
cache_control
标记。任何请求缓存的 tokens 数少于此值的请求都将在不进行缓存的情况下被处理，且不会返回错误。要验证某个 prompt 是否被缓存，请检查
response usage fields
：如果
cache_creation_input_tokens
和
cache_read_input_tokens
均为 0，则该 prompt 未被缓存（很可能是因为它未满足最小长度要求）。
如果你的 prompt 刚好低于你的模型和平台的最低值，扩展缓存内容以达到该阈值通常值得。缓存读取的成本显著低于未缓存的 input tokens，因此达到最低值可以降低频繁复用的 prompt 的成本。
对于并发请求，请注意，缓存条目只有在第一个响应开始后才会变为可用。如果你需要并行请求的缓存命中，请在发送后续请求之前等待第一个响应。
目前，"ephemeral" 是唯一支持的缓存类型，默认具有 5 分钟生命周期。

### 哪些内容可以缓存 

请求中的大多数块都可以缓存。这包括：
工具：tools 数组中的工具定义
系统消息：system 数组中的内容块
文本消息：messages.content 数组中的内容块，适用于用户和 assistant 回合
图像和文档：messages.content 数组中的内容块，位于用户回合
工具使用和工具结果：messages.content 数组中的内容块，适用于用户和 assistant 回合
这些元素中的每一个都可以缓存，可以自动缓存，也可以通过使用 cache_control 标记它们来缓存。

### 哪些内容不能缓存 

虽然大多数请求块都可以缓存，但有一些例外：
Thinking 块不能直接使用 cache_control 缓存。但是，当 Thinking 块出现在之前的 assistant 回合中时，它们可以与其他内容一起被缓存。以这种方式缓存时，从缓存读取时它们确实会计入 input tokens。
子内容块（如 citations）本身不能直接缓存。相反，应缓存顶层块。
对于 citations，作为 citations 源材料的顶层文档内容块可以被缓存。这使你能够通过缓存 citations 将要引用的文档，来有效地将 prompt 缓存与 citations 一起使用。
空文本块不能缓存。

### 什么会使缓存失效 

对缓存内容的修改可能会使部分或全部缓存失效。
如
Structuring your prompt
中所述，缓存遵循层级结构：
tools
→
system
→
messages
。每一层的变更都会使其自身及之后所有层级的缓存失效。
下表显示了不同类型变更会导致缓存的哪些部分失效。✘ 表示缓存失效，✓ 表示缓存仍然有效。
变更内容
Tools 缓存
System 缓存
Messages 缓存
影响
Tool 定义
✘
✘
✘
修改 tool 定义（名称、描述、参数）会使整个缓存失效
Web search 开关
✓
✘
✘
启用/禁用 web search 会修改 system prompt
Citations 开关
✓
✘
✘
启用/禁用 citations 会修改 system prompt
Speed 设置
✓
✘
✘
在
speed: "fast"
与标准 speed 之间切换会使 system 和 message 缓存失效
Tool choice
✓
✓
✘
对
tool_choice
参数的更改仅影响 message 块
Images
✓
✓
✘
在 prompt 的任意位置添加/移除 images 都会影响 message 块
Thinking 参数
取决于模型
取决于模型
✘
thinking 配置（mode，以及 extended 模式下的
budget_tokens
）会被渲染进 prompt，因此更改它总是会使 message 块失效；在那些将配置渲染在其之前的模型上，tool 和 system 缓存也会失效。参见
Thinking and prompt caching
。
Effort 设置
取决于模型
取决于模型
✘
更改
output_config.effort
值总是会使 message 块失效，对 tool 和 system 缓存的影响与 thinking 参数一样取决于模型。将 effort 显式设置为模型的默认值等同于省略它，不会导致失效。在支持
per-message effort
的模型上，通过
messages
中
role: "system"
消息携带的 effort 变更不会破坏已缓存的 prefix。
传递给 extended thinking 请求的 Non-tool results
✓
✓
取决于模型
在 Opus 4.5+、Sonnet 4.6+ 和 Haiku 5.5 上，thinking blocks 默认会被保留，因此缓存保持有效（✓）。在更早的 Opus/Sonnet 模型以及直至 Claude Haiku 4.5 的 Haiku 模型上，所有先前缓存的 thinking blocks 都会从上下文中被剥离，并且任何跟随这些 thinking blocks 之后的消息都会从缓存中移除（✘）。更多详情，请参见
Caching with thinking blocks
。
Dropped thinking blocks
✓
✓
✘
当 API 丢弃一个在该请求中未被
preserved
的 Claude Fable 5.1、Claude Mythos 5.1、Claude Opus 5.5、Claude Sonnet 5.5 或 Claude Haiku 5.5 thinking block 时（例如，你将其重放给一个无法读取它的模型），在该请求上，缓存前缀会从该 block 所在位置起发生变化。接收模型能够读取、且原样传回的 blocks 会保持缓存完好。
在支持
mid-conversation tool changes
的模型上，
inline-tools-2026-09-15
beta header 允许你在对话中途添加一个 tool，或更改某个 tool 的定义，而无需编辑
tools
。将定义放入对话中途 system message 中的
tool_addition
block 中发送，并让
tools
保持与你最初发送时完全一致。缓存前缀仍然匹配，因此只有追加的 message 会作为新输入被处理。唯一的例外是一个不包含任何 non-deferred tool 的
tools
数组，此时以这种方式定义的第一个 tool 会在该请求上产生一次完整的 cache miss。参见
Define tools in a message
。

### 跟踪缓存性能

使用响应中的
usage
内（或
streaming
时的
message_start
事件中）这些 API 响应字段来监控缓存性能：
cache_creation_input_tokens
：创建新条目时写入缓存的 token 数量。
cache_read_input_tokens
：此请求从缓存中检索到的 token 数量。
input_tokens
：未从缓存读取或未用于创建缓存的输入 token 数量（即最后一个 cache breakpoint 之后的 token）。

### 使用 thinking blocks 进行缓存

当将
thinking
与 prompt caching 一起使用时，thinking blocks 具有特殊行为：
与其他内容一起自动缓存：
虽然 thinking blocks 无法用 cache_control 显式标记，但当你带着 tool results 进行后续 API 调用时，它们会作为请求内容的一部分被缓存。这通常发生在 tool use 期间，即你把 thinking blocks 传回去以继续对话时。
Input token 计数：
当 thinking blocks 从缓存中读取时，它们会在你的 usage 指标中计为 input tokens。这对成本计算和 token 预算很重要。
缓存失效模式：
仅当 tool results 作为 user messages 提供时，缓存保持有效
在 Opus 4.5+、Sonnet 4.6+ 和 Haiku 5.5 上，即使添加了非 tool result 的 user 内容，thinking blocks 也会默认保留，因此缓存保持有效
在更早的 Opus/Sonnet 模型以及直至 Claude Haiku 4.5 的 Haiku 模型上，当添加非 tool result 的 user 内容时缓存会失效，导致所有先前的 thinking blocks 被从 context 中剥离
即使没有显式的 cache_control 标记，这种缓存行为也会发生
有关缓存失效的更多细节，请参见 What invalidates the cache。
带 tool use 的示例：

```
Request 1: User: "What's the weather in Paris?"
Response: [thinking_block_1] + [tool_use block 1]
Request 2:
User: ["What's the weather in Paris?"],
Assistant: [thinking_block_1] + [tool_use block 1],
User: [tool_result_1, cache=True]
Response: [thinking_block_2] + [text block 2]
# 请求 2 缓存其请求内容（而非 response）
# 缓存包括：user message、thinking_block_1、tool_use block 1 和 tool_result_1
Request 3:
User: ["What's the weather in Paris?"],
Assistant: [thinking_block_1] + [tool_use block 1],
User: [tool_result_1, cache=True],
Assistant: [thinking_block_2] + [text block 2],
User: [Text response, cache=True]
# 取决于模型，这个非 tool result 的 user block 要么保留先前的 thinking blocks，要么将其剥离（见下一段）
```

在较早的 Opus/Sonnet 模型以及直至 Claude Haiku 4.5 的 Haiku 模型上，此时所有先前的 thinking blocks 都会从上下文中移除。在 Opus 4.5+、Sonnet 4.6+ 和 Haiku 5.5 上，先前的 thinking blocks 默认保留，并继续作为缓存前缀的一部分。
如需更详细的信息，请参阅
Thinking and prompt caching
。

### 缓存存储与共享

组织和工作区隔离：
缓存在组织之间相互隔离。不同组织永远不会共享缓存，即使它们使用完全相同的 prompt。在 Claude API、Claude Platform on AWS 和 Microsoft Foundry 上，缓存还会在同一组织内按工作区隔离；Bedrock 和 Google Cloud 仅使用组织级隔离。
精确匹配：
缓存命中要求 prompt 片段 100% 相同，包括直至并包含带有 cache control 标记的块在内的所有文本和图像。
输出 token 生成：
Prompt caching 对输出 token 生成没有影响。你收到的响应与不使用 prompt caching 时得到的响应完全相同。

### 有效缓存的最佳实践

要优化 prompt caching 性能：
对于多轮对话，从
automatic caching
开始。它会自动处理断点管理。
当你需要以不同变更频率缓存不同部分时，使用
explicit block-level breakpoints
。
缓存稳定、可复用的内容，例如系统指令、背景信息、大型上下文或频繁使用的工具定义。
将缓存内容放在 prompt 的开头以获得最佳性能。
有策略地使用 cache breakpoints 来分隔不同的可缓存前缀部分。
将断点放在跨请求保持相同的最后一个块上。对于具有静态前缀和变化后缀（时间戳、每请求上下文、传入消息）的 prompt，应放在前缀的末尾，而不是变化的块上。
定期分析缓存命中率，并根据需要调整你的策略。

### 针对不同用例进行优化

根据你的场景定制 prompt caching 策略：
对话式 agent：降低长对话的成本和延迟，尤其是那些包含长指令或上传文档的对话。
编码助手：通过在 prompt 中保留代码库的相关片段或摘要版本，改进自动补全和代码库 Q&A。
大型文档处理：在 prompt 中纳入完整的长篇材料（包括图像），同时不增加响应延迟。
详细的指令集：提供大量的指令、流程和示例列表，以微调 Claude 的响应。开发者通常会在 prompt 中包含一两个示例，但借助 prompt caching，你可以通过包含 20 个以上高质量答案的多样化示例来获得更好的效果。
Agentic 工具使用：提升涉及多次工具调用和迭代代码修改的场景的性能，这类场景中每一步通常都需要一次新的 API 调用。
与书籍、论文、文档、播客转录稿以及其他长篇内容对话：通过将整份文档 embedding 到 prompt 中，让任何知识库焕发生机，并让用户向其提问。

### 排查常见问题

如果遇到意外行为：
确保缓存的片段在多次调用之间完全一致。对于显式断点，请验证
cache_control
标记位于相同的位置
检查调用是否在缓存生命周期内发起（默认 5 分钟）
验证
tool_choice
、图像使用、thinking 配置以及
output_config.effort
在多次调用之间保持一致
确认你为你的模型和平台缓存了至少最低数量的 token（参见
缓存限制
）
确认你的断点位于一个在多次请求之间保持不变的 block 上。缓存写入只发生在断点处，如果该 block 发生变化（时间戳、每请求的上下文、传入的消息），前缀 hash 就永远不会匹配。lookback 不会在断点之后找到稳定的内容；它只会找到更早的请求在各自的断点处写入的条目
验证你的
tool_use
内容块中的键是否具有稳定的顺序，因为某些语言（例如 Swift、Go）会在 JSON 转换期间随机化键的顺序，从而破坏缓存
使用
缓存诊断
让 API 比较连续请求，并报告 prompt 的哪一部分发生了偏离

## 1 小时缓存时长 

如果你发现 5 分钟太短，Anthropic 还提供 1 小时的缓存时长
，需额外付费
。
要使用延长缓存，请在
cache_control
定义中包含
ttl
，如下所示：
"cache_control"
: {
"type"
:
"ephemeral"
,
"ttl"
:
"1h"
}

响应中会包含详细的缓存信息，如下所示：
输出

{
"usage"
: {
"input_tokens"
:
2048
,
"cache_read_input_tokens"
:
1800
,
"cache_creation_input_tokens"
:
248
,
"output_tokens"
:
503
,
"cache_creation"
: {
"ephemeral_5m_input_tokens"
:
148
,
"ephemeral_1h_input_tokens"
:
100
}
}
}
请注意，当前的
cache_creation_input_tokens
字段等于
cache_creation
对象中各值之和。
如果你在使用 web search 之类的 server tools 时看到并非由你请求的
ephemeral_5m_input_tokens
写入，请参阅
结合 prompt caching 使用 tool use
。

### 何时使用 1 小时缓存 

如果你的 prompt 以固定的节奏被使用（即 system prompt 的使用频率高于每 5 分钟一次），请继续使用 5 分钟缓存，因为它将继续免费刷新。
1 小时缓存最适合用于以下场景：
当你的 prompts 可能使用频率低于每 5 分钟一次，但高于每小时一次时。例如，当一个 agentic side-agent 需要超过 5 分钟时，或者当你存储与用户的长对话，并且你通常预期该用户可能不会在接下来的 5 分钟内回复时。
当延迟很重要，并且你的后续 prompts 可能会在超过 5 分钟后发送时。
当你想提高你的 rate limit 利用率时，因为 cache hits 不会从你的 rate limit 中扣除。

### 混合不同的 TTL

你可以在同一个请求中同时使用 1-hour 和 5-minute cache controls，但有一个重要限制：具有更长 TTL 的 cache entries 必须出现在更短 TTL 之前（也就是说，一个 1-hour cache entry 必须出现在任何 5-minute cache entries 之前）。
混合 TTL 时，API 会在你的 prompt 中确定三个计费位置：
Position
A
：最高 cache hit 处的 token 数量（如果没有命中则为 0）。
Position
B
：在
A
之后最高 1-hour
cache_control
block 处的 token 数量（如果不存在则等于
A
）。
Position
C
：最后一个
cache_control
block 处的 token 数量。
你将被收取以下费用：
A
的 cache read tokens。
(B - A)
的 1-hour cache write tokens。
(C - B)
的 5-minute cache write tokens。
这里有三个示例。这描绘了 3 个请求的输入 tokens，每个请求都有不同的 cache hits 和 cache misses。结果是，每个请求都有不同的计算定价，显示在彩色框中。

## 预热 cache

Cache pre-warming 让你可以在用户触发真实请求之前，将你的 system prompt 或 tool definitions 加载到 prompt cache 中。这消除了首次用户交互时的 cache-miss 延迟惩罚，为延迟敏感型应用减少了 time-to-first-token (TTFT)。

### 工作原理

在你的请求中设置
max_tokens: 0
。API 会将你的 prompt 读入模型，并在任何
cache_control
断点处写入 cache，然后立即返回，不生成任何输出。响应中有一个空的
content
数组，
`stop_reason: "max_tokens"`，以及一个完整填充的 `usage` block。

把 `cache_control` 断点放在与后续请求共享的最后一个 block 上（通常是你的 system prompt 或 tool definitions），而不是放在占位 user message 上。否则 cache entry 会以占位消息为键，后续请求就不会命中它。同时也要使用与后续请求相同的 thinking 配置和 `output_config.effort`：这些值会被渲染进 prompt（参见 What invalidates the cache），因此用不同配置做的 pre-warm 可能写入一个你的真实流量永远不会命中的 entry。这意味着要使用 explicit cache breakpoint，而不是 automatic caching，因为 automatic caching 会把断点放在最后一个 block 上，而这里的最后一个 block 就是占位消息。占位 user message 可以是任何包含非空白内容的字符串（这里的示例使用 `"warmup"`）；其内容会被读入模型，但永远不会被回答。

cURL
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

```python
client = anthropic.Anthropic()

# 在用户到来之前触发此请求，以预热共享的 system-prompt cache。
prewarm = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=0,
    system=[
        {
            "type": "text",
            "text": "You are an expert software engineer with deep knowledge of distributed systems...",
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": "warmup"}],
)
print(prewarm.stop_reason)
# "max_tokens"
print(prewarm.content)
# []
print(prewarm.usage)
```

API 返回一个空的 `content` 数组：

输出

```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "content": [],
  "model": "claude-opus-5-5",
  "stop_reason": "max_tokens",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 8,
    "cache_creation_input_tokens": 5120,
    "cache_read_input_tokens": 0,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 5120,
      "ephemeral_1h_input_tokens": 0
    },
    "iterations": [
      {
        "input_tokens": 8,
        "output_tokens": 0,
```

"cache_read_input_tokens"
:
0
,
"cache_creation_input_tokens"
:
5120
,
"cache_creation"
: {
"ephemeral_5m_input_tokens"
:
5120
,
"ephemeral_1h_input_tokens"
:
0
},
"type"
:
"message"
}
],
"output_tokens"
:
0
,
"service_tier"
:
"standard"
,
"inference_geo"
:
"global"
}
}

### 典型使用模式

在应用启动时（或按计划间隔）发起一个 pre-warm 请求，然后在 pre-warm 完成后发送真实的用户请求：
cURL
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

client
=

anthropic.Anthropic()
SYSTEM_PROMPT
=

[
{
"type"
:
"text"
,
"text"
:
"You are an expert software engineer with deep knowledge of distributed systems..."
,
"cache_control"
: {
"type"
:
"ephemeral"
},
}
]
def
prewarm_cache
() ->
None
:
"""在应用启动时或按计划间隔调用此函数。"""
client.messages.create(
model
=

"claude-opus-5-5"
,
max_tokens
=

0
,
system
=

SYSTEM_PROMPT
,
messages
=

[{
"role"
:
"user"
,
"content"
:
"warmup"
}],
)
def
respond
(
user_message
:
str
) -> anthropic.types.Message:
"""真实的用户请求；受益于已预热的缓存。"""
return
client.messages.create(
model
=

"claude-opus-5-5"
,
max_tokens
=

1024
,
system
=

SYSTEM_PROMPT
,
messages
=

[{
"role"
:
"user"
,
"content"
: user_message}],
)

# 在任何用户流量到来之前预热缓存。

prewarm_cache()

# 之后当用户提交消息时，system-prompt 前缀已经被缓存。

response
=

respond(
"How do I implement a binary search tree?"
)
for
block
in
response.content:
if
block.type
==

"text"
:
print
(block.text)
请记住，缓存 TTL 仍然适用。对于默认的 5 分钟缓存，至少每 5 分钟发送一次新的 pre-warm 请求，以保持缓存处于预热状态。如果用户请求之间的间隔较长，请改用
1 小时缓存时长
。

### 限制

如果设置了以下任意一项，带有
max_tokens: 0
的请求会被拒绝，并返回
invalid_request_error
，因为每一项都意味着会产生输出，而零 token 预算无法产生输出：
stream: true
Extended thinking
(
thinking.type: "enabled"
)
Structured outputs
(
output_config.format
)
tool_choice
of
{"type": "tool", ...}
or
{"type": "any"}
max_tokens: 0
在
Message Batches
请求中也会被拒绝。Pre-warming 针对的是 time-to-first-token，而这并不适用于批处理，并且在批处理期间写入的 cache entry 很可能在后续请求运行之前就过期了。

### 替代 max_tokens=1 变通方案

在
max_tokens: 0
可用之前，一些应用使用
max_tokens: 1
的预热调用来达到相同效果。首选
max_tokens: 0
方法：不会产生任何输出，因此没有需要丢弃的单 token 回复，不会计费 output tokens，并且请求的意图是明确的。

## Prompt caching 示例

为了帮助你开始使用 prompt caching，
prompt caching cookbook
提供了详细的示例和最佳实践。
以下代码片段展示了各种 prompt caching 模式。这些示例演示了如何在不同场景中实现 caching，帮助你理解此功能的实际应用：

### 大上下文 caching 示例

cURL
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby
client
=

anthropic.Anthropic()
response
=

client.messages.create(
model
=

"claude-opus-5-5"
,
max_tokens
=

1024
,
system
=

[
{
"type"
:
"text"
,
"text"
:
"You are an AI assistant tasked with analyzing legal documents."
,
},
{
"type"
:
"text"
,
"text"
:
"Here is the full text of a complex legal agreement: [Insert full text of a 50-page legal agreement here]"
,
"cache_control"
: {
"type"
:
"ephemeral"
},
},
],
messages
=

[
{
"role"
:
"user"
,
"content"
:
"What are the key terms and conditions in this agreement?"
,
}
],
)
print
(response.usage.model_dump_json())
此示例演示了基本的 prompt caching 用法，将法律协议的全文作为 prefix 进行 caching，同时让用户指令保持 uncached。
对于第一个请求：
input_tokens
：仅用户消息中的 tokens 数量
cache_creation_input_tokens
: 整个 system message 中的 token 数量，包括法律文件
cache_read_input_tokens
: 0（首次请求无缓存命中）
对于缓存生命周期内的后续请求：
input_tokens
: 仅 user message 中的 token 数量
cache_creation_input_tokens
: 0（未创建新缓存）
cache_read_input_tokens
: 整个已缓存 system message 中的 token 数量

### 缓存 tool definitions

Tool definitions 可以通过在你的
tools
数组中的最后一个 tool 上放置
cache_control
来缓存。该 tool 之前（含该 tool）定义的所有 tools 都会作为一个单一前缀被缓存。
{
"model"
:
"claude-opus-5-5"
,
"max_tokens"
:
1024
,
"tools"
: [
{
"name"
:
"get_weather"
,
"description"
:
"Get the current weather in a given location"
,
"input_schema"
: {
"type"
:
"object"
,
"properties"
: {
"location"
: {
"type"
:
"string"
} },
"required"
: [
"location"
]
}
},
{
"name"
:
"get_time"
,
"description"
:
"Get the current time in a given time zone"
,
"input_schema"
: {
"type"
:
"object"
,
"properties"
: {
"timezone"
: {
"type"
:
"string"
} },
"required"
: [
"timezone"
]
},
"cache_control"
: {
"type"
:
"ephemeral"
}
}
],
"messages"
: [{
"role"
:
"user"
,
"content"
:
"What is the weather and time in New York?"
}]
}

在首次请求时，
cache_creation_input_tokens
反映所有 tool definitions 的 token 数量。在缓存生命周期内的后续请求中，这些 token 会转而出现在
cache_read_input_tokens
下。
关于 tool definitions、
defer_loading
与缓存失效之间的详细交互，参见
Tool use with prompt caching
。

### 继续多轮对话

cURL
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

client
=

anthropic.Anthropic()
response
=

client.messages.create(
model
=

"claude-opus-5-5"
,
max_tokens
=

1024
,
system
=

[
{
"type"
:
"text"
,
"text"
:
"...long system prompt"
,
"cache_control"
: {
"type"
:
"ephemeral"
},
}
],
messages
=

[

# ...long conversation so far

{
"role"
:
"user"
,
"content"
: [
{
"type"
:
"text"
,
"text"
:
"Hello, can you tell me more about the solar system?"
,
}
],
},
{
"role"
:
"assistant"
,
"content"
:
"Certainly! The solar system is the collection of celestial bodies that orbit our Sun. It consists of eight planets, numerous moons, asteroids, comets, and other objects. The planets, in order from closest to farthest from the Sun, are: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune. Each planet has its own unique characteristics and features. Is there a specific aspect of the solar system you'd like to know more about?"
,
},
{
"role"
:
"user"
,
"content"
: [
{
"type"
:
"text"
,
"text"
:
"Good to know."
},
{
"type"
:
"text"
,
"text"
:
"Tell me more about Mars."
,
"cache_control"
: {
"type"
:
"ephemeral"
},
},
],
},
],
)
print
(response.usage.model_dump_json())
此示例演示了如何在多轮对话中使用 prompt 缓存。
在每一轮中，最终消息的最后一个块会被标记为
cache_control
，因此对话可以增量缓存。系统会自动查找并使用之前缓存的最长块序列来处理后续消息。也就是说，之前用
cache_control
块标记过的块，之后不再这样标记，但如果它们在 5 分钟内被命中，仍然会被视为缓存命中（同时也是缓存刷新！）。
此外，请注意
cache_control
参数被放在 system message 上。这是为了确保如果它从缓存中被逐出（超过 5 分钟未被使用之后），它会在下一次请求时被重新加回缓存。
这种方法有助于在持续进行的对话中维护上下文，而无需反复处理相同信息。
当正确设置后，你应该会在每个请求的 usage 响应中看到以下内容：
input_tokens
: 新用户消息中的 token 数（会是最少的）
cache_creation_input_tokens
: 新的 assistant 和 user 轮次中的 token 数
cache_read_input_tokens
：对话中截至上一轮的 token 数量

### 综合应用：多个缓存断点

cURL
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

client
=

anthropic.Anthropic()
response
=

client.messages.create(
model
=

"claude-opus-5-5"
,
max_tokens
=

1024
,
tools
=

[
{
"name"
:
"search_documents"
,
"description"
:
"Search through the knowledge base"
,
"input_schema"
: {
"type"
:
"object"
,
"properties"
: {
"query"
: {
"type"
:
"string"
,
"description"
:
"Search query"
}
},
"required"
: [
"query"
],
},
},
{
"name"
:
"get_document"
,
"description"
:
"Retrieve a specific document by ID"
,
"input_schema"
: {
"type"
:
"object"
,
"properties"
: {
"doc_id"
: {
"type"
:
"string"
,
"description"
:
"Document ID"
}
},
"required"
: [
"doc_id"
],
},
"cache_control"
: {
"type"
:
"ephemeral"
},
},
],
system
=

[
{
"type"
:
"text"
,
"text"
:
"You are a helpful research assistant with access to a document knowledge base.
\n\n

# Instructions

\n

- Always search for relevant documents before answering
  \n
- Provide citations for your sources
  \n
- Be objective and accurate in your responses
  \n
- If multiple documents contain relevant information, synthesize them
  \n
- Acknowledge when information is not available in the knowledge base"
  ,
  "cache_control"
  : {
  "type"
  :
  "ephemeral"
  },
  },
  {
  "type"
  :
  "text"
  ,
  "text"
  :
  "# Knowledge Base Context
  \n\n
  Here are the relevant documents for this conversation:
  \n\n

## Document 1: Solar System Overview

\n
The solar system consists of the Sun and all objects that orbit it...
\n\n

## Document 2: Planetary Characteristics

\n
Each planet has unique features. Mercury is the smallest planet...
\n\n

## Document 3: Mars Exploration

\n
Mars has been a target of exploration for decades...
\n\n
[Additional documents...]"
,
"cache_control"
: {
"type"
:
"ephemeral"
},
},
],
messages
=

[
{
"role"
:
"user"
,
"content"
:
"Can you search for information about Mars rovers?"
,
},
{
"role"
:
"assistant"
,
"content"
: [
{
"type"
:
"tool_use"
,
"id"
"tool_1"
,
"name"
:
"search_documents"
,
"input"
: {
"query"
:
"Mars rovers"
},
}
],
},
{
"role"
:
"user"
,
"content"
: [
{
"type"
:
"tool_result"
,
"tool_use_id"
:
"tool_1"
,
"content"
:
"Found 3 relevant documents: Document 3 (Mars Exploration), Document 7 (Rover Technology), Document 9 (Mission History)"
,
}
],
},
{
"role"
:
"assistant"
,
"content"
: [
{
"type"
:
"text"
,
"text"
:
"I found 3 relevant documents about Mars rovers. Let me get more details from the Mars Exploration document."
,
}
],
},
{
"role"
:
"user"
,
"content"
: [
{
"type"
:
"text"
,
"text"
:
"Yes, please tell me about the Perseverance rover specifically."
,
"cache_control"
: {
"type"
:
"ephemeral"
},
}
],
},
],
)
print
(response.usage.model_dump_json())
这个综合示例演示了如何使用全部 4 个可用的 cache breakpoint 来优化 prompt 的不同部分：
Tools cache
（cache breakpoint 1）：最后一个 tool 定义上的
cache_control
参数会缓存所有 tool 定义。
Reusable instructions cache
（cache breakpoint 2）：system prompt 中的静态 instructions 会被单独缓存。这些 instructions 在请求之间很少发生变化。
RAG context cache
（cache breakpoint 3）：知识库文档会被独立缓存，允许你更新 RAG 文档而不会使 tools 或 instructions 的缓存失效。
Conversation history cache
（cache breakpoint 4）：最后一条 user message 被标记为
cache_control
，以便随着对话推进实现增量缓存。
这种方法提供了最大的灵活性：
如果你向对话追加新的一轮而不更改先前的内容，则全部四个 cache 段都会被复用
如果你更新 RAG 文档但保持相同的 tools 和 instructions，则前两个 cache 段会被复用
如果你更改对话但保持相同的 tools、instructions 和 documents，则前三个段会被复用
任何 breakpoint 处的变更都会使该 segment 及其之后的所有内容失效，而更早的缓存 segment 仍然有效

对于第一个请求：

input_tokens
: 极少（final cache breakpoint 之后的 token，在本例中接近 0）

cache_creation_input_tokens
: 所有缓存 segment 中的 token（tools + instructions + RAG documents + conversation history）

cache_read_input_tokens
: 0（无 cache hit）

对于仅包含一条新 user message 的后续请求（且第四个 breakpoint 移到该新的最终 message 上，如示例所示）：

input_tokens
: 极少（final cache breakpoint 之后的 token，在本例中接近 0）

cache_creation_input_tokens
: 新 user message 和上一个 assistant turn 中的 token（正在被缓存的新 conversation segment）

cache_read_input_tokens
: 此前所有已缓存的 token（tools + instructions + RAG documents + previous conversation）

这种模式对以下场景尤其有效：

- 具有大型 document context 的 RAG 应用
- 使用多个 tools 的 agent 系统
- 需要维护 context 的长时运行 conversation
- 需要独立优化 prompt 不同部分的应用

## 数据保留

Prompt caching（自动和显式）均符合 ZDR 条件。Anthropic 不会存储你的 prompt 或 Claude 回复的原始文本。

KV（key-value）cache 表示以及缓存内容的加密哈希仅保存在内存中，不进行静态存储。缓存条目的最短生存时间为 5 分钟（standard）或 1 小时（extended），之后会被迅速（但并非立即）删除。缓存条目在 organization 之间相互隔离；在 Claude API、Claude Platform on AWS 和 Microsoft Foundry 上，还会在同一 organization 内的 workspace 之间隔离。

关于所有功能的 ZDR 适用条件，请参阅
API and data retention
。

## FAQ

### 我需要多个 cache breakpoint，还是末尾一个就足够？

在大多数情况下，在静态内容末尾设置单个 cache breakpoint 就足够了。
缓存写入只发生在你标记的那个 block 上。把它放在跨请求保持完全相同的最后一个 block 上，之后每个请求都会读取同一个条目。如果后面的某个 block 会随请求变化（比如时间戳、传入的消息），就把 breakpoint 放在它之前，即最后一个稳定的 block 上。

只有在以下情况下你才需要多个 breakpoint：

- 不断增长的对话会把你的 breakpoint 推到超过最后一次缓存写入 20 个或更多 block 的位置，使先前的条目落在 lookback window 之外
- 你想要独立缓存以不同频率更新的区段
- 为了成本优化，你需要显式控制哪些内容被缓存

示例：如果你有 system instructions（很少变化）和 RAG context（每天变化），你可以使用两个 breakpoint 来分别缓存它们。

### cache breakpoint 会增加额外成本吗？

不会，cache breakpoint 本身是免费的。你只需为以下内容付费：

- 将内容写入缓存（5 分钟 TTL 时比基础 input token 多 25%）
- 从缓存读取（基础 input token 价格的一小部分，见 Pricing）
- 未缓存内容的常规 input token

breakpoint 的数量不影响定价；只有被缓存和读取的内容量才有影响。

### 如何从 usage 字段计算总 input token？

usage 响应包含三个独立的 input token 字段，它们共同代表你的总输入：

```
total_input_tokens = cache_read_input_tokens + cache_creation_input_tokens + input_tokens
```

cache_read_input_tokens：从缓存中取回的 token（cache breakpoint 之前所有已被缓存的内容）
cache_creation_input_tokens：正在写入缓存的新 token（在 cache breakpoint 处）
input_tokens：最后一个 cache breakpoint 之后、未被缓存的 token

重要：input_tokens 并不代表全部 input token，只代表最后一个 cache breakpoint 之后的部分。如果你有已缓存的内容，input_tokens 通常会远小于你的总输入。

示例：缓存了一个 200k token 的文档，外加一个 50 token 的用户问题：
cache_read_input_tokens
: 200,000
cache_creation_input_tokens
: 0
input_tokens
: 50
Total:
200,050 tokens
这一明细对于理解你的成本和速率限制用量都至关重要。更多详情请参阅
Tracking cache performance
。

### 缓存的生命周期是多久？

缓存的默认最短生命周期（TTL）为 5 分钟。每次使用缓存内容时，该生命周期都会刷新。
如果你觉得 5 分钟太短，Anthropic 还提供
1-hour cache TTL
。

### 缓存生命周期从何时开始？

生命周期从写入或读取缓存条目的请求开始时计算，而不是从其响应结束时计算。生成响应所花费的时间计入生命周期，因此后续请求复用缓存的时间窗口为生命周期减去生成时间。
如果你的请求会产生较长的响应，而下一次请求可能要等到生命周期结束后才会开始，请使用
1-hour cache TTL
。

### 我可以使用多少个缓存断点？

你可以在 prompt 中定义最多 4 个缓存断点（使用
cache_control
参数）。

### 所有模型都支持 prompt caching 吗？

所有
active Claude models
都支持 prompt caching。

### prompt caching 与 thinking 如何配合工作？

更改 thinking 参数（切换模式，或在 extended 模式下更改预算）会使缓存的 message 前缀失效，也可能使缓存的 system prompt 和 tools 失效，因为 thinking 配置会被渲染进 prompt 中。
output_config.effort
值的行为也相同。
有关缓存失效的更多详情，请参阅
What invalidates the cache
。
有关 thinking 的更多内容，包括其与 tool use 和 prompt caching 的交互，请参阅
Thinking and prompt caching
。

### 如何启用 prompt caching？

最简单的方法是在请求 body 的顶层添加
"cache_control": {"type": "ephemeral"}
（
automatic caching
）。或者，在单个 content block 上包含至少一个
cache_control
断点（
显式缓存断点
）。

### 我可以将 prompt caching 与其他 API 功能一起使用吗？

可以，prompt caching 可以与工具使用和视觉能力等其他 API 功能一起使用。但是，更改 prompt 中是否包含图像或修改工具使用设置会破坏缓存。
有关缓存失效的更多详细信息，请参阅
什么会使缓存失效
。

### prompt caching 如何影响定价？

prompt caching 引入了新的定价结构：5 分钟缓存写入的费用比基础输入 token 高 25%，1 小时缓存写入的费用是基础输入 token 的 2 倍，而缓存命中的费用仅为基础输入 token 价格的一小部分（请参阅
定价
了解各模型的乘数）。

### 我可以手动清除缓存吗？

目前，无法手动清除缓存。缓存的前缀在至少 5 分钟无活动后会自动过期。

### 我如何跟踪缓存策略的有效性？

你可以使用 API 响应中的
cache_creation_input_tokens
和
cache_read_input_tokens
字段来监控缓存性能。

### 什么会破坏缓存？

有关缓存失效的更多详细信息，包括需要创建新缓存条目的更改列表，请参阅
什么会使缓存失效
。

### prompt caching 如何处理隐私和数据隔离？

prompt caching 在设计上具有强大的隐私和数据隔离措施：
缓存键是使用直到缓存控制点的 prompt 的加密哈希生成的。这意味着只有具有相同 prompt 的请求才能访问特定的缓存。
在 Claude API、Claude Platform on AWS 和 Microsoft Foundry 上，缓存按组织内的工作区隔离。在 Bedrock 和 Google Cloud 上，缓存按组织隔离。在任何情况下，缓存都不会跨组织共享，即使 prompt 完全相同也是如此。有关详细信息，请参阅
缓存存储与共享
。
缓存机制旨在维护每个唯一对话或上下文的完整性和隐私。
使用是安全的
cache_control 可以放在 prompts 中的任何位置。为了让缓存产生读取，请把断点放在稳定前缀的末尾：把它放在每次请求都会变化的块上（例如时间戳或用户的任意输入），每次都会写入一个新条目，永远不会命中。
这些措施确保 prompt caching 在提供性能优势的同时，维护数据隐私与安全。

### 我可以在 Batches API 中使用 prompt caching 吗？

可以，你可以在 Batches API 请求中使用 prompt caching。但是，由于异步批处理请求可能会并发地、以任意顺序被处理，缓存命中是基于尽力而为（best-effort）提供的。
1 小时缓存有助于提高缓存命中率。最具成本效益的使用方式如下：
收集一组共享相同前缀的 message 请求。
发送一个批处理请求，其中只包含一个请求，该请求带有这个共享前缀和一个 1 小时缓存块。这会把该前缀写入 1 小时缓存。
一旦完成，就提交其余的请求。你需要监控该 job 以了解它何时完成。
这通常比使用 5 分钟缓存更好，因为批处理请求通常需要 5 分钟到 1 小时才能完成。

### 为什么我在 Python 中看到错误 `AttributeError: 'Beta' object has no attribute 'prompt_caching'`？

这个错误通常出现在你升级了 SDK 或者使用了过时的代码示例时。Prompt caching 不再需要 beta 前缀。不要这样写：
Python

client.beta.prompt_caching.messages.create(
**
params)

而应使用：
Python

client.messages.create(
**
params)

### 为什么我看到 'TypeError: Cannot read properties of undefined (reading 'messages')'？

这个错误通常出现在你升级了 SDK 或者使用了过时的代码示例时。Prompt caching 不再需要 beta 前缀。不要这样写：
TypeScript

client
.
beta
.
promptCaching
.
messages
.
create
(
/* ... */
);

而应使用：
client
.
messages
.
create
(
/* ... */
);
本页对您有帮助吗？

Ask Docs
