) 不再随连接而变化。需要跨调用状态的服务器使用显式的、由服务器铸造的 handle，并作为普通工具参数传入（
SEP-2567
）。
让 MCP 无状态化：移除
initialize
/
notifications/initialized
握手。现在每个请求都在
_meta
中携带其协议版本和客户端能力（
io.modelcontextprotocol/protocolVersion
、
io.modelcontextprotocol/clientCapabilities
）。客户端 SHOULD 在每个请求中标识自身（
io.modelcontextprotocol/clientInfo
），服务器 SHOULD 在每个结果的
_meta
中标识自身（
io.modelcontextprotocol/serverInfo
）。版本不匹配会返回
UnsupportedProtocolVersionError
（
SEP-2575
）。
新增
server/discover
：服务器 MUST 实现此 RPC，以公布其支持的协议版本、能力和身份。客户端 MAY 在任何其他请求之前调用它，用于预先进行版本选择，或在 STDIO 上将其用作向后兼容性探测（
SEP-2575
）。
用
subscriptions/listen
替换 HTTP GET 端点以及
resources/subscribe
/
resources/unsubscribe
：一条单一的长生命周期 POST 响应流，用于已选择加入的服务器到客户端变更通知。客户端选择加入特定类型（
toolsListChanged
、
promptsListChanged
、
resourcesListChanged
、
resourceSubscriptions
）；服务器进行确认，并用
io.modelcontextprotocol/subscriptionId
标记通知。诸如
notifications/progress
和
notifications/message
这类请求作用域的通知，仍在其所属请求的响应流上流动，而不是在
subscriptions/listen
流上（
SEP-2575
）。
移除
ping
、
logging/setLevel
和
notifications/roots/list_changed
。现在日志级别通过
_meta
中的
io.modelcontextprotocol/logLevel
按请求设置；对于未包含此字段的请求，服务器 MUST NOT 发出
notifications/message
（
SEP-2575
）。
将实验性的 tasks 移出核心协议，移入官方扩展（
io.modelcontextprotocol/tasks
）。重新设计的扩展替换了阻塞式的
tasks/result
通过
tasks/get
进行轮询的方法，新增用于客户端到服务器输入的
tasks/update
，移除
tasks/list
，并允许服务器在无需逐请求 opt-in 的情况下主动返回 task handle（
SEP-2663
）。
引入了 Multi Round-Trip Requests (MRTR) 模式，它取代了此前发送服务器发起请求（例如
roots/list
、
sampling/createMessage
或
elicitation/create
）的方式。服务器返回一个
InputRequiredResult
（
resultType: "input_required"
），其
inputRequests
字段携带处理该请求所需的附加信息请求。客户端在重试原始请求时通过
inputResponses
提供所请求的信息作为响应。（
SEP-2322
）。
现在所有结果都带有一个必需的
resultType
字段：普通结果为
"complete"
，
multi round-trip request
的中间结果为
"input_required"
。客户端
MUST
将省略该字段的早期协议服务器返回的结果视为
"complete"
（
SEP-2322
）。
从 Streamable HTTP transport 中移除 SSE 流可恢复性和消息重投递（
Last-Event-ID
头和 SSE event ID）。中断的响应流会丢失进行中的请求；客户端
MUST
以新的 request ID 将其作为新请求重新发出（
SEP-2575
）。

## ​ Minor changes

为
ClientCapabilities
和
ServerCapabilities
添加
extensions
字段，以支持核心协议之外的可选
extensions
。
记录
_meta
键（
traceparent
、
tracestate
、
baggage
）的 OpenTelemetry trace context 传播约定（
SEP-414
）。
服务器
SHOULD
以确定性顺序从
tools/list
返回工具，以支持客户端缓存并提高 LLM prompt 缓存命中率。
要求 Streamable HTTP POST 请求携带标准 MCP 请求头（
Mcp-Method
、
Mcp-Name
），并通过
x-mcp-header
添加对来自工具参数的自定义头的支持（
SEP-2243
）。
通过新的
CacheableResult
要求
tools/list
、
prompts/list
、
resources/list
、
resources/read
和
resources/templates/list
返回的结果上提供
ttlMs
和
cacheScope
字段
接口。
ttlMs 是一个新鲜度提示（以毫秒为单位），允许客户端缓存响应并减少轮询；
cacheScope
（
"public"
或
"private"
）控制共享中间方是否可以缓存该响应。这两个字段补充了现有的
listChanged
通知（
SEP-2549
）。
将资源未找到错误码从
-32002
改为
-32602
（Invalid Params），以与 JSON-RPC 规范保持一致。
授权服务器
SHOULD
依据
RFC 9207
在授权响应中包含
iss
参数，并且 MCP 客户端在兑换授权码之前
MUST
将
存在的
iss
与记录的 issuer 进行校验
（
SEP-2468
）。
要求 MCP 客户端在 Dynamic Client
Registration 期间指定合适的
application_type
，以避免 OpenID Connect 重定向 URI 冲突
（
SEP-837
）。
明确客户端凭据绑定到签发它们的授权服务器：
客户端
MUST
按 issuer 标识符为持久化的凭据建立键，
MUST NOT
将其与不同的授权服务器
复用，并且当授权服务器
变更时
MUST
重新注册（
SEP-2352
）。
放宽
inputSchema
和
outputSchema
，允许任意 JSON Schema 2020-12 关键字；并放宽
structuredContent
，允许任意 JSON 值。新增
$ref
解析要求以及
组合关键字的资源边界
（
SEP-2106
）。
移除
notifications/elicitation/complete
通知以及 URL 模式 elicitation 请求的
elicitationId
字段，二者均于
2025-11-25
引入。在
Multi Round-Trip Requests
模式下，
客户端通过重试原始请求来获知带外交互的结果，因此由服务器发起的完成信号——以及用于
关联它的标识符——不再适合该协议。需要在多次重试之间关联 elicitation 的服务器可在
requestState
中编码自己的标识符。
定义
错误码分配策略
，划分 JSON-RPC 服务器错误范围：
-32000
到
-32019
仍为
implementation-defined（现有 SDK 用法予以保留），
-32020
到
-32099
为
为 MCP 规范保留。相应地对本草案中引入的错误码重新编号——
HeaderMismatch
-32001
→
-32020
，
MissingRequiredClientCapability
-32003
→
-32021
，
UnsupportedProtocolVersion
-32004
→
-32022
——并将
HeaderMismatchError
添加到 schema 中，此前它仅存在于 transport 的说明文字中。

## ​ 已弃用

此处列出的功能仍是规范的一部分，但已计划根据
功能生命周期与弃用政策
移除。新的实现不应采用它们。
已弃用功能注册表
跟踪当前处于 Deprecated 状态的每一项功能。
弃用 Roots、Sampling 和 Logging 功能
（
SEP-2577
）。
这些功能在弃用窗口期内仍完全可用，但新的
实现不应添加对它们的支持。建议的迁移方式：通过工具参数、资源 URI 或服务器
配置传递目录或文件，以替代 Roots；直接与 LLM 提供商 API 集成
以替代 Sampling；记录到
stderr
（stdio）或使用 OpenTelemetry 以替代
Logging。
将 HTTP+SSE transport（自协议版本
2025-03-26
起已弃用）根据功能生命周期政策
重新归类为 Deprecated
（
SEP-2596
）。
迁移到
Streamable HTTP
。
将
includeContext
值
"thisServer"
和
"allServers"
（自协议版本
2025-11-25
起软弃用）重新归类为 Deprecated
（
SEP-2596
）。
省略该字段或使用
"none"
；这些值最迟将随
Sampling 功能本身一并移除。
弃用 OAuth 2.0 Dynamic Client Registration Protocol
（
RFC7591
）作为客户端注册
机制，转而采用
Client ID Metadata Documents
（
PR #2858
）。
为与不支持 Client ID Metadata Documents 的授权服务器保持向后兼容，它仍然可用。

## ​ 其他 schema 变更

schema.json
现在正确地反映了 minimum/maximum/default 的 Typescript 定义是
number
而不只是
integer
。这是由使用
--defaultNumberType integer
运行生成器导致的（
PR#2710
).

## ​治理与流程更新

采用 specification feature lifecycle 与弃用策略，
定义 Active、Deprecated 和 Removed 功能状态、最短
十二个月的弃用窗口，以及
弃用功能注册表
(
SEP-2596
)。

## ​流程变更

将基于 PR 的 SEP 工作流正式化：markdown 文件位于
seps/
目录、由 PR 派生的编号、sponsor 职责，以及通过 PR labels 进行状态管理（
SEP-1850
）。

## ​完整变更日志

如需查看自上次协议修订以来所做全部变更的完整列表，
请参阅 GitHub
。
本页是否有帮助？
是
否
