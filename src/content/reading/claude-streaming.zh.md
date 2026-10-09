. Python SDK 同时支持 sync 和 async stream。详情请参见各 SDK 的文档。
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

```
client
=
anthropic.Anthropic()
with
client.messages.stream(
max_tokens
=
1024
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
"Hello"
}],
model
=
"claude-opus-5-5"
,
)
as
stream:
for
text
in
stream.text_stream:
print
(text,
end
=
""
,
flush
=
True
)
```

## 获取最终 message 而不处理事件

如果你不需要在文本到达时对其进行处理，SDK 提供了一种方式：在内部使用 streaming，同时返回完整的 Message 对象，与 client.messages.create() 返回的对象完全相同。这在对 max_tokens 值较大的请求中尤其有用，此时 SDK 要求使用 streaming 以避免 HTTP 超时。
CLI
Python
TypeScript
C#
Go
Java
PHP
Ruby

```
client
=
anthropic.Anthropic()
with
client.messages.stream(
max_tokens
=
128000
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
"Write a detailed analysis..."
}],
model
=
"claude-opus-5-5"
,
)
as
stream:
message
=
stream.get_final_message()
for
block
in
message.content:
if
block.type
==
"text"
:
print
(block.text)
```

.stream() 调用通过 server-sent events 保持 HTTP 连接存活，随后 SDK 的 message 累积辅助函数 stream.get_final_message() 会将所有事件收集为完整的 Message 对象。

## 事件类型

每个 server-sent event 都包含一个具名的事件类型及关联的 JSON 数据。每个事件使用 SSE 事件名（例如 event: message_stop），并在其 data 中包含匹配的事件 type。

每个 stream 使用以下事件流程：

message_start：包含一个 content 为空的 Message 对象。在 thinking-binding-controls-2026-08-01 beta header 下，该 Message 对象还携带 input_transformations 数组。在流中途发生 server-side fallback 之后，最后的 message_delta 事件会再次携带该数组，其中包含 serving model 的条目。

一系列 content block，每个都有一个 content_block_start，一个或多个
`content_block_delta` events，以及一个 `content_block_stop` event。每个 content block 都有一个 `index`，它与该 block 在最终 Message `content` 数组中的索引相对应。有一个例外：在 server-side fallback 响应期间，每个 model 边界处会以一个 `content_block_start` 和 `content_block_stop` 对的形式到达一个 `fallback` content block，两者之间没有 delta。

一个或多个 `message_delta` events，表示最终 `Message` 对象在顶层发生的变化。

最后一个 `message_stop` event。

### Ping 事件

事件流中也可能包含任意数量的 `ping` events。

### 错误事件

API 偶尔会在事件流中发送 `errors`。例如，在使用高峰期，你可能会收到一个 `overloaded_error`，在非流式场景下，它通常对应 HTTP 529：

错误示例

```
event: error
data: {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}
```

### 其他事件

根据 versioning policy，可能会新增事件类型，你的代码应当优雅地处理未知的事件类型。

## Content block delta 类型

每个 `content_block_delta` event 都包含一个 `delta`，其类型用于更新给定 `index` 处的 `content` block。

### 文本 delta

`text` content block delta 的样子如下：

文本 delta

```
event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "ello frien"}}
```

### 输入 JSON delta

`tool_use` content blocks 的 deltas 对应于该 block 的 `input` 字段的更新。为了支持最大程度的粒度，这些 deltas 是 partial JSON strings，而最终的 `tool_use.input` 始终是一个 `object`。

你可以累积这些字符串 deltas，并在收到 `content_block_stop` event 后解析 JSON——使用像 Pydantic 这样的库来做部分 JSON 解析，或使用 SDK 的 streaming helpers。在 Python 和 TypeScript SDK 中，这些 helpers 还能让你随着 `input` 的流式传输增量获取解析后的 `input`。

一个 `tool_use`
content block delta 看起来像这样：
Input JSON delta

event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
: {
"type"
:
"input_json_delta"
,
"partial_json"
:
"{
\"
location
\"
:
\"
San Fra"
}}}
注意：当前模型一次只支持从
input
中输出一个完整的 key 和 value 属性。因此，在使用 tools 时，模型工作期间流式事件之间可能会有延迟。一旦一个
input
key 和 value 被累积完成，它们会以分块的 partial JSON 形式作为多个
content_block_delta
事件发出，这样该格式便能自动支持未来模型更细的粒度。

### Thinking delta 

在启用流式传输的情况下使用
thinking
时，你会通过
thinking_delta
事件接收 thinking 内容。这些 delta 对应于
thinking
content blocks 中的
thinking
字段。
对于 thinking 内容，会在
content_block_stop
事件之前发送一个特殊的
signature_delta
事件。此 signature 用于验证 thinking block 的完整性。
当 thinking 配置中设置了
display: "omitted"
时，不会流式传输任何 thinking 文本。thinking block 会打开，接收一个带有空
thinking
字符串的
thinking_delta
，然后接收一个单独的
signature_delta
，随后关闭。使用
display: "updates"
（beta）时，reasoning blocks 以相同方式流式传输，只有某些模型在 tool 调用之间写入的
progress updates
才会流式传输携带文本的
thinking_delta
事件。参见
Controlling thinking display
。
一个典型的 thinking delta 看起来像这样：
Thinking delta

event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
: {
"type"
:
"thinking_delta"
,
"thinking"
:
"I need to find the GCD of 1071 and 462 using the Euclidean algorithm.
\n\n
1071 = 2 × 462 + 147"
}}
signature delta 看起来像这样：
Signature delta

event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
: {
"type"
:
"signature_delta"
,
"signature"
:
"EqQBCgIYAhIM1gbcDa9GJwZA2b3hGgxBdjrkzLoky3dl1pkiMOYds..."
}}

## 完整的 HTTP 流式响应

使用流式模式时，请使用 client SDK。但是，如果你在构建直接的 API 集成，则需要自行处理这些事件。

一个流式响应由以下部分组成：

一个 `message_start` 事件

可能包含多个 content block，每个 block 包含：

一个 `content_block_start` 事件

可能包含多个 `content_block_delta` 事件

一个 `content_block_stop` 事件

一个或多个 `message_delta` 事件

一个 `message_stop` 事件

响应中还可能散布着 `ping` 事件。有关格式的更多细节，请参见事件类型。

### 基本的流式请求

cURL CLI Python TypeScript C# Go Java PHP Ruby

```python
client = anthropic.Anthropic()

with client.messages.stream(
    model="claude-opus-5-5",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=256,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

响应

```text
event: message_start
data: {"type": "message_start", "message": {"id": "msg_1nZdL29xx5MUA1yADyHTEsnR8uuvGzszyY", "type": "message", "role": "assistant", "content": [], "model": "claude-opus-5-5", "stop_reason": null, "stop_sequence": null, "usage": {"input_tokens": 25, "output_tokens": 1}}}

event: content_block_start
data: {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}

event: ping
data: {"type": "ping"}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "!"}}

event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: message_delta
data: {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": null}, "usage": {"output_tokens": 15}}

event: message_stop
data: {"type": "message_stop"}
```

### 带 tool use 的流式请求

本请求要求 Claude 使用一个工具来报告天气。

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
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        },
    }
]
with client.messages.stream(
    model="claude-opus-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "any"},
    messages=[
        {
            "role": "user",
            "content": "What is the weather like in San Francisco?",
        }
    ],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

响应

```text
event: message_start
data: {"type":"message_start","message":{"id":"msg_014p7gG3wDgGV9EUtLvnow3U","type":"message","role":"assistant","model":"claude-opus-5","stop_sequence":null,"usage":{"input_tokens":472,"output_tokens":2},"content":[],"stop_reason":null}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: ping
data: {"type":"ping"}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Okay"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":","}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" let"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"'s"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" check"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{
```

"type"
:
"text_delta"
,
"text"
:
" the"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
" weather"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
" for"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
" San"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
" Francisco"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
","
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
" CA"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
":"
}}
event: content_block_stop
data: {
"type"
:
"content_block_stop"
,
"index"
:
0
}
event: content_block_start
data: {
"type"
:
"content_block_start"
,
"index"
:
1
,
"content_block"
:{
"type"
:
"tool_use"
,
"id"
:
"toolu_01T1x1fJ34qAmk2tNTrN7Up6"
,
"name"
:
"get_weather"
,
"input"
:{}}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
""
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
"{
\"
location
\"
:"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
"
\"
San"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
" Francisc"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
"input_json_delta"
,
"partial_json"
:
"o,"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
" CA
\"}"
}}
event: content_block_stop
data: {
"type"
:
"content_block_stop"
,
"index"
:
1
}
event: message_delta
data: {
"type"
:
"message_delta"
,
"delta"
:{
"stop_reason"
:
"tool_use"
,
"stop_sequence"
:
null
},
"usage"
:{
"output_tokens"
:
89
}}
event: message_stop
data: {
"type"
:
"message_stop"
}

### 带 thinking 的流式请求

该请求在流式传输时启用 thinking。display: "summarized" 设置流式输出的是 Claude 推理的浓缩摘要，而不是完整的 chain of thought。
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
with
client.messages.stream(
model
=

"claude-opus-5-5"
,
max_tokens
=

20000
,
thinking
=

{
"type"
:
"adaptive"
,
"display"
:
"summarized"
},
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
"What is the greatest common divisor of 1071 and 462?"
,
}
],
)
as
stream:
for
event
in
stream:
if
event.type
==

"content_block_delta"
:
delta
=

event.delta
match
delta.type:
case
"thinking_delta"
:
print
(delta.thinking,
end
=

""
,
flush
=

True
)
case
"text_delta"
:
print
(delta.text,
end
=

""
,
flush
=

True
)
Response
event: message_start
data: {
"type"
:
"message_start"
,
"message"
: {
"id"
:
"msg_01..."
,
"type"
:
"message"
,
"role"
:
"assistant"
,
"content"
: [],
"model"
:
"claude-opus-5-5"
,
"stop_reason"
:
null
,
"stop_sequence"
:
null
}}
event: content_block_start
data: {
"type"
:
"content_block_start"
,
"index"
:
0
,
"content_block"
: {
"type"
:
"thinking"
,
"thinking"
:
""
,
"signature"
:
""
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
: {
"type"
:
"thinking_delta"
,
"thinking"
:
"I need to find the GCD of 1071 and 462 using the Euclidean algorithm.
\n\n
1071 = 2 × 462 + 147"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,

### 使用 web search 工具的流式请求

该请求要求 Claude 通过搜索网页获取当前天气信息。

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
with
client.messages.stream(
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

[{
"type"
:
"web_search_20250305"
,
"name"
:
"web_search"
,
"max_uses"
:
5
}],
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
"What is the weather like in New York City today?"
}
],
)
as
stream:
for
text
in
stream.text_stream:
print
(text,
end
=

""
,
flush
=

True
)

Response

event: message_start
data: {
"type"
:
"message_start"
,
"message"
:{
"id"
:
"msg_01G..."
,
"type"
:
"message"
,
"role"
:
"assistant"
,
"model"
:
"claude-opus-5-5"
,
"content"
:[],
"stop_reason"
:
null
,
"stop_sequence"
:
null
,
"usage"
:{
"input_tokens"
:
2679
,
"cache_creation_input_tokens"
:
0
,
"cache_read_input_tokens"
:
0
,
"output_tokens"
:
3
}}}
event: content_block_start
data: {
"type"
:
"content_block_start"
,
"index"
:
0
,
"content_block"
:{
"type"
:
"text"
,
"text"
:
""
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
"我来查一下"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
"纽约市当前的天气"
}}
event: ping
data: {
"type"
:
"ping"
}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
0
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
"。"
}}
event: content_block_stop
data: {
"type"
:
"content_block_stop"
,
"index"
:
0
}
event: content_block_start
data: {
"type"
:
"content_block_start"
,
"index"
:
1
,
"content_block"
:{
"type"
:
"server_tool_use"
,
"id"
:
"srvtoolu_014hJH82Qum7Td6UV8gDXThB"
,
"name"
:
"web_search"
,
"input"
:{}}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
""
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
"{
\"
query"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
"
\"
:"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
"
\"
weather"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
" NY"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
"input_json_delta"
,
"partial_json"
:
"C to"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
1
,
"delta"
:{
"type"
:
"input_json_delta"
,
"partial_json"
:
"day
\"}"
}}
event: content_block_stop
data: {
"type"
:
"content_block_stop"
,
"index"
:
1
}
event: content_block_start
data: {
"type"
:
"content_block_start"
,
"index"
:
2
,
"content_block"
:{
"type"
:
"web_search_tool_result"
,
"tool_use_id"
:
"srvtoolu_014hJH82Qum7Td6UV8gDXThB"
,
"content"
:[{
"type"
:
"web_search_result"
,
"title"
:
"2025 年 5 月纽约市天气（纽约）—— 一个月详细天气预报"
,
"url"
:
"https://world-weather.info/forecast/usa/new_york/may-2025/"
,
"encrypted_content"
:
"Ev0DCioIAxgCIiQ3NmU4ZmI4OC1k..."
,
"page_age"
:
null
},
...
]}}
event: content_block_stop
data: {
"type"
:
"content_block_stop"
,
"index"
:
2
}
event: content_block_start
data: {
"type"
:
"content_block_start"
,
"index"
:
3
,
"content_block"
:{
"type"
:
"text"
,
"text"
:
""
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
3
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
"以下是纽约"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
3
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
"市的当前天气信息：
\n\n

# "

}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
3
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
"纽约市天气"
}}
event: content_block_delta
data: {
"type"
:
"content_block_delta"
,
"index"
:
3
,
"delta"
:{
"type"
:
"text_delta"
,
"text"
:
"
\n\n
"
}}
...
event: content_block_stop
data: {
"type"
:
"content_block_stop"
,
"index"
:
17
}
event: message_delta
data: {
"type"
:
"message_delta"
,
"delta"
:{
"stop_reason"
:
"end_turn"
,
"stop_sequence"
:
null
},
"usage"
:{
"input_tokens"
:
10682
,
"cache_creation_input_tokens"
:
0
,
"cache_read_input_tokens"
:
0
,
"output_tokens"
:
510
,
"server_tool_use"
:{
"web_search_requests"
:
1
}}}
event: message_stop
data: {
"type"
:
"message_stop"
}

## Error recovery

### Claude 4.5 and earlier

对于 Claude 4.5 模型及更早版本，你可以通过从流中断处继续，来恢复因网络问题、超时或其他错误而中断的 streaming 请求。这种方式可以避免重新处理整个响应。
基本的恢复策略包括：
捕获部分响应：
保存错误发生前已成功接收的所有内容。
构造继续请求：
创建一个新的 API 请求，将部分 assistant 响应作为新 assistant 消息的开头包含在内。
恢复 streaming：
从中断处继续接收响应的其余部分。

### Claude 4.6 and later

对于 Claude 4.6 及更高版本的模型，同样适用捕获并恢复的策略，但第 2 步有所变化：不要将部分响应放在 assistant 消息中，而是添加一条 user 消息，指示模型从上次中断处继续。
捕获部分响应：
保存错误发生前已成功接收的所有内容。
构造继续请求：
创建一个新的 API 请求，其中包含一条 user 消息，该消息带有部分响应以及继续指令，例如：
Sample prompt

Your previous response was interrupted and ended with [previous_response]. Continue from where you left off.
恢复 streaming：
从中断处继续接收响应的其余部分。

### Error recovery best practices

使用 SDK 功能：
利用 SDK 内置的消息累积和错误处理能力。
处理内容类型：
请注意，消息可以包含多个 content block（
text
、
tool_use
、
thinking
）。Tool use 和 extended thinking block 无法部分恢复。你可以从最近的 text block 继续 streaming。

## Next steps

Stop reasons and fallback
在流完成后处理每个
stop_reason
值。
细粒度工具流式传输
无需服务器端缓冲即可流式传输工具输入 JSON，从而降低延迟。

Thinking
使用
thinking_delta
和
signature_delta
事件流式传输 thinking 输出。

客户端 SDK
使用官方 SDK，它们会为你处理流式传输、累积和重连。

批处理
当你不需要实时响应时，异步处理大量请求。
这个页面有帮助吗？


询问 Docs

