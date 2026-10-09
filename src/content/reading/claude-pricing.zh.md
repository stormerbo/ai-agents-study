本页提供 Anthropic 模型和功能的详细定价信息。所有价格均以 USD 计。
如需获取最新的定价信息，请访问
claude.com/pricing
。

## 模型定价

下表列出了所有 Claude 模型的定价：
模型
基础 token
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
/
MTok
$50
/ MTok
$12.50
/ MTok
$20
/ MTok
$0.25
/ MTok
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
Claude Haiku 5.5
适用于高吞吐量、延迟敏感的任务，例如分类、抽取和路由
$0.10
/ MTok
适用于最多 100,000 tokens 的 prompt
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
适用于超过 100,000 tokens 的 prompt
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

补充说明
所有其他模型使用标准的 0.1x 倍数。
Claude 4.7 及更高版本模型以及 Claude Mythos Preview 使用更新的 tokenizer，这有助于它们在各类任务上取得更佳表现。对于相同的文本，该 tokenizer 会产生大约多 30% 的 token。确切的增幅取决于内容和工作负载形态。Claude Sonnet 4.6 及更早的模型使用先前的 tokenizer。

## 云平台定价

本节涵盖由合作伙伴运营的云平台，账单由云服务提供商向你开具。关于通过 marketplace 计费、由 Anthropic 运营的云平台，请参阅
Claude Platform on AWS 定价
和
Claude in Microsoft Foundry 定价
。
Claude 模型可在
Amazon Bedrock
和
Google Cloud
上使用。官方定价请访问：
Amazon Bedrock 定价
Google Cloud 定价

## Claude Platform on AWS 定价

Claude Platform on AWS
通过 AWS Marketplace 使用 Claude Consumption Units (CCU) 计费。Anthropic 按标准的分模型、分功能费率以 USD 对你的 token 用量计价，应用任何协商折扣，将结果按 $0.01/CCU 转换为 CCU，并每小时向 AWS Marketplace 报告 CCU 数量。你的 AWS 账单显示单个 CCU 行项目。

| 概念                                                                                   | 详情                                                                         |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 计费单位                                                                               | Claude Consumption Unit (                                                    |
| CCU                                                                                    |
| )                                                                                      |
| CCU 价格                                                                               | $0.01 per CCU（固定；折扣在 token 到 CCU 的转换时应用，而非应用于 CCU 价格） |
| 转换                                                                                   | token 用量按标准的分模型、分功能费率以 USD 计价（与                          |
| Claude API 定价                                                                        |
| 相同），然后按 $0.01/CCU 转换为 CCU                                                    |
| 计费周期                                                                               | 每小时向 AWS Marketplace 计量；按月开具发票                                  |
| 付款模式                                                                               | 仅后付（postpaid）；无预付额度                                               |
| 折扣                                                                                   | 以计量的 CCU 数量减少的形式应用                                              |
| 税费                                                                                   | 税前计量；税费由 AWS Marketplace 处理                                        |
| 成本可见性                                                                             |                                                                              |
| Claude Console 中的实时明细（通过 AWS Console 访问）；AWS Cost Explorer 显示聚合的 CCU |

### 推理地理区域

对于 Claude 4.6 及更高版本的模型，使用
inference_geo: "us"
会应用 1.1 倍的定价乘数。
inference_geo: "global"
（默认）使用标准定价。详情请参阅
数据驻留
。

### 私有优惠

当你在 AWS Console
Claude Platform on AWS
服务页面注册时，AWS Console 会查找与你的账户关联的任何私有优惠，并提示你在 AWS Marketplace 中接受它。请联系你的 Anthropic 客户代表以获取私有优惠条款。

## Claude in Microsoft Foundry 定价

Claude in Microsoft Foundry
通过 Azure Marketplace 使用 Claude Consumption Units（CCU）计费。Anthropic 按标准的每模型、每功能费率以 USD 对你的 token 用量进行计价，应用任何协商折扣，将结果按每 CCU $0.01 转换为 CCU，并每小时向 Azure Marketplace 报告 CCU 数量。你的 Azure 账单会显示单个 CCU 行项目。
概念
详情
计费单位
Claude Consumption Unit（
CCU
）
CCU 价格
每 CCU $0.01（固定；折扣应用于 token 到 CCU 的转换，而非 CCU 价格）
转换
token 用量按标准的每模型、每功能费率以 USD 计价（与
Claude API pricing
相同），然后按每 CCU $0.01 转换为 CCU
计费节奏
每小时向 Azure Marketplace 计量；每月开具发票
付款模式
仅后付费（postpaid）；无预付额度
折扣
以计量的 CCU 更少的形式应用
税费
税前计量；Azure Marketplace 处理税费
成本可见性
Azure Cost Management 显示聚合的 CCU

### 推理地理区域

托管在 Azure 上的部署可以使用 US Data Zone Standard 部署类型，这会将推理保留在美国境内。这相当于 Claude API 上的
inference_geo: "us"
，并应用相同的 1.1 倍定价乘数。详情请参阅
数据驻留
。

## 功能特定定价

### Prompt caching

Prompt caching 通过跨 API 调用复用 prompt 中此前已处理的部分，来降低成本与延迟。无需在每次请求时重新处理相同的大型 system prompt、文档或对话历史，API 会以标准输入价格的一小部分从缓存中读取。
启用 prompt caching 有两种方式：
自动缓存：
在请求的顶层添加单个
cache_control
字段。随着对话增长，系统会自动管理 cache breakpoints。对大多数用例而言，这是推荐的起点。
显式 cache breakpoints：
将
cache_control
直接放在各个内容块上，以便对具体缓存哪些内容进行细粒度控制。
Prompt caching 相对于基础输入 token 费率使用以下定价乘数：

| 缓存操作         | 乘数                                                                                                                          | 持续时间                     |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 5 分钟缓存写入   | 1.25x 基础输入价格                                                                                                            | 缓存有效期为 5 分钟          |
| 1 小时缓存写入   | 2x 基础输入价格                                                                                                               | 缓存有效期为 1 小时          |
| 缓存读取（命中） | 0.1x 基础输入价格（在 Claude Fable 5.1 和 Claude Mythos 5.1 上为 0.025x；在 Claude Opus 5.5 和 Claude Sonnet 5.5 上为 0.05x） | 与之前一次写入的持续时间相同 |

缓存写入 token 在内容首次存储时计费。缓存读取 token 在后续请求检索缓存内容时计费。一次缓存命中花费标准输入价格的 10%，这意味着对于 5 分钟持续时间（写入为 1.25x），一次缓存读取后即可回本；对于 1 小时持续时间（写入为 2x），两次缓存读取后即可回本。在 Claude Fable 5.1 和 Claude Mythos 5.1 上，一次缓存命中花费标准输入价格的 2.5%（每百万 token $0.25 USD）。
在 Claude Opus 5.5 和 Claude Sonnet 5.5 上，一次缓存命中花费标准输入价格的 5%（Claude Opus 5.5 上为每百万 token $0.20 USD，Claude Sonnet 5.5 上为 $0.10 USD）。
这些乘数会与其他定价调整项叠加，包括 Batch API 折扣和 data residency。
有关实现细节、支持的模型和代码示例，请参见
Prompt caching
。

### Data residency 定价

对于 Claude 4.6 及更高版本的模型，通过
inference_geo
参数指定仅限美国境内推理时，所有 token 定价类别都会产生 1.1 倍的乘数，包括 input tokens、output tokens、cache writes 和 cache reads。全球路由（默认）使用标准定价。

这适用于 Claude API（第一方）以及 Claude Platform on AWS。在 Claude in Microsoft Foundry 上，同样的 1.1 倍乘数适用于使用 US Data Zone Standard 部署类型的部署（参见
Inference geography
）。合作方运营的平台（Bedrock 和 Google Cloud）有各自独立的区域定价。详见
Bedrock
和
Google Cloud
。更早的模型不支持
inference_geo
参数，始终使用标准定价；在这些模型上包含该参数的请求会返回 400 错误。

更多信息，参见
Data residency
。

### Fast mode pricing 

Fast mode
处于研究预览阶段，为 Claude Opus 5.5、Claude Opus 5 和 Claude Opus 4.8 以溢价定价提供显著更快的输出。Fast mode 定价适用于整个上下文窗口，包括超过 200k input tokens 的请求。Fast mode 仅在 Claude API（第一方）上可用；在 Claude Platform on AWS 或合作方运营的云平台上不可用。

Model
Input
Output
Claude Opus 5.5
$8 / MTok
$40 / MTok
Claude Opus 5 / Claude Opus 4.8
$10 / MTok
$50 / MTok

Fast mode 在 Claude Opus 4.7 上不可用（带有
speed: "fast"
的请求会返回错误），在 Claude Opus 4.6 上也不可用（请求以标准速度运行，并按标准费率计费）。参见
Fast mode
。

Fast mode 定价可与其他定价修饰项叠加：

Prompt caching multipliers
在 fast mode 定价之上应用
Data residency
乘数在 fast mode 定价之上应用

Fast mode 不能与
Batch API
一起使用。

更多信息，参见
Fast mode
。

### Batch processing 

Batch API 允许对大量请求进行异步处理，input 和 output tokens 均享受 50% 折扣。

Model
Batch tokens
名称
Input
Output
Claude Fable 5.1
适用于高要求的推理与长周期 agentic 工作
$5
/
MTok
$25
/ MTok
Claude Opus 5.5
适用于长时间运行的 agentic 编码与知识工作
$2
/ MTok
$10
/ MTok
Claude Sonnet 5.5
速度与智能的最佳组合
$1
/ MTok
$5
/ MTok
Claude Haiku 5.5
适用于高吞吐、延迟敏感的任务，如分类、抽取和路由
$0.05
/ MTok
适用于最多 100,000 tokens 的 prompts
$0.25
/ MTok
$0.25
/ MTok
适用于超过 100,000 tokens 的 prompts
$1.25
/ MTok

更多模型
Claude Mythos 5.1

$5
/ MTok
$25
/ MTok
Claude Fable 5
$5
/ MTok
$25
/ MTok
Claude Mythos 5

$5
/ MTok
$25
/ MTok
Claude Opus 5
$2.50
/ MTok
$12.50
/ MTok
Claude Opus 4.8
$2.50
/ MTok
$12.50
/ MTok
Claude Opus 4.7
$2.50
/ MTok
$12.50
/ MTok
Claude Opus 4.6
$2.50
/ MTok
$12.50
/ MTok
Claude Opus 4.5
$2.50
/ MTok
$12.50
/ MTok
Claude Opus 4.1

$7.50
/ MTok
$37.50
/ MTok
Claude Opus 4

$7.50
/ MTok
$37.50
/ MTok
Claude Sonnet 5
$1
/ MTok
$5
/ MTok
Claude Sonnet 4.6
$1.50
/ MTok
$7.50
/ MTok
Claude Sonnet 4.5
$1.50
/ MTok
$7.50
/ MTok
Claude Sonnet 4

$1.50
/ MTok
$7.50
/ MTok
Claude Haiku 4.5
$0.50
/ MTok
$2.50
/ MTok
Claude Haiku 3.5

$0.40
/ MTok
$2
/ MTok
有关 batch processing 的更多信息，请参阅
Batch processing
。

### 长上下文定价

Claude 4.6 及之后的模型（Claude Haiku 5.5 除外）以及
Claude Mythos Preview
在标准定价下提供完整的
1M token 上下文窗口
。（900k token 的请求与 9k token 的请求按相同的每 token 费率计费。）Prompt caching 和 batch processing 折扣在整个上下文窗口内均按标准费率适用。
Claude Haiku 5.5 按 prompt 长度定价：prompt 超过 100,000 tokens 的请求需支付更高的价格。请求的 prompt 长度会计入其所有 input tokens，包括 cache reads 和 cache writes。每个请求各自单独定价：即使请求的 prompt 中有一部分是 cache hit，只要超过该阈值，该请求仍需支付更高的价格，而更早的请求仍按原先计费的价格收费。

Model pricing
和
Batch processing
都列出了这两组价格。

### Tool use pricing

Tool use 请求的定价基于：
发送给模型的 input tokens 总数（包括
tools
参数中的）
生成的 output tokens 数量
对于 server-side tools，会有额外的基于用量的定价（例如，web search 按执行的搜索次数收费）
Client-side tools 的定价与其他任何 Claude API 请求相同，不过 server-side tools 可能会根据其具体用量产生额外费用。
Tool use 带来的额外 tokens 来自：
API 请求中的
tools
参数（tool 名称、描述和 schema）
API 请求和响应中的
tool_use
content blocks
API 请求中的
tool_result
content blocks
当你使用
tools
时，API 还会自动为模型加入一个特殊的 system prompt，以启用 tool use。每个模型所需的 tool use tokens 数量列在下表中（不包括前面列出的额外 tokens）。注意，该表假设至少提供了 1 个 tool。如果未提供
tools
，那么 tool choice 为
none
时使用 0 个额外 system prompt tokens。
Model
Tool use system prompt tokens
Name
Tool choice
Token count
Claude Opus 5.5
适用于长时间运行的 agentic coding 和知识工作
auto
,
none
286
tokens
Claude Sonnet 5.5
速度与智能的最佳组合
auto
,
none
286
tokens
Claude Haiku 5.5
适用于高吞吐量、对延迟敏感的任务，如分类、提取和路由
auto
,
none
286
tokens
any
,
tool
406
tokens

Additional models
Claude Opus 5
auto
,
none
286
tokens
any
,
tool
406
tokens
Claude Opus 4.8
auto
,
none
290
tokens
any
,
tool
410
tokens
Claude Opus 4.7
auto
,
none
675
tokens
any
,
tool
804
tokens
Claude Opus 4.6
auto
,
none
497
tokens
any
,
tool
589
tokens
Claude Opus 4.5
auto
,
none
496
tokens
any
,
tool
588
tokens
Claude Opus 4.1

auto
,
none
313
tokens
any
,
tool
315
tokens
Claude Opus 4

auto
,
none
313
tokens
any
,
tool
315
tokens
Claude Sonnet 5
auto
,
none
354
tokens
any
,
tool
474
tokens
Claude Sonnet 4.6
auto
,
none
497
tokens
any
,
tool
589
tokens
Claude Sonnet 4.5
auto
,
none
496
tokens
any
,
tool
588
tokens
Claude Sonnet 4

auto
,
none
313
tokens
any
,
tool
315
tokens
Claude Haiku 4.5
auto
,
none
496
tokens
any
,
tool
588
tokens
Claude Haiku 3.5

auto
,
none
264
tokens
any
,
tool
355
tokens
这些 token 数量会加到你的常规 input 和 output tokens 上，用于计算请求的总成本。
有关当前的各模型价格，请参阅
model pricing
一节。
有关 tool use 实现和最佳实践的更多信息，请参阅
Tool use
。

### 特定 tool 定价

#### Bash tool

bash tool 定义会向你的请求添加以下 input tokens。这还不包括只要存在任何 tool 就会生效的
按模型的 tool use system prompt
。
模型
额外 input tokens
Claude Opus 5、Claude Opus 4.8 和 Claude Opus 4.7
325 tokens
Claude Opus 4.6、Claude Sonnet 4.6 及更早版本
244 tokens
以下内容会消耗额外 token：
命令输出（stdout/stderr）
错误消息
大文件内容
有关完整的定价详情，请参阅
tool use pricing
。

#### Code execution tool

与 web search 或 web fetch 一起使用时，code execution 是免费的。
当你的 API 请求中包含
web_search_20260209
（或更高版本）或
web_fetch_20260209
（或更高版本）时，除了标准的 input 和 output token 成本外，code execution tool 调用不会产生额外费用。
在不使用这些工具时，code execution 按执行时间计费，与 token 用量分开统计：
执行时间最短为 5 分钟
每个组织每月获得
1,550 小时免费
使用时长
超出 1,550 小时的部分按
每容器每小时 $0.05 USD 计费
如果请求中包含文件，即使未调用该工具也会收取执行时间费用，因为文件已被预加载到容器上
代码执行使用量会在响应中跟踪：

```json
{
  "usage": {
    "input_tokens": 105,
    "output_tokens": 239,
    "server_tool_use": {
      "code_execution_requests": 1
    }
  }
}
```

#### Text editor tool

text editor tool 采用与 Claude 搭配使用的其他工具相同的定价结构。它根据你所使用的 Claude 模型，遵循标准的输入和输出 token 定价。
除基础 token 外，text editor tool 还需要以下额外的输入 token：

| 工具                              | 额外输入 token |
| --------------------------------- | -------------- |
| text_editor_20250429 (Claude 4.x) | 700 tokens     |
| 完整的定价详情请参见              |
| tool use pricing                  |
| 。                                |

#### Web search tool

web search 的使用费在 token 用量之外另行收取：

```json
{
  "usage": {
    "input_tokens": 105,
    "output_tokens": 6039,
    "cache_read_input_tokens": 7123,
    "cache_creation_input_tokens": 7345,
    "server_tool_use": {
      "web_search_requests": 1
    }
  }
}
```

Web search 在 Claude API 上的价格为
每 1,000 次搜索 $10
，外加搜索生成内容的标准 token 费用。整个对话过程中检索到的 web search 结果都会计入输入 token，包括在单轮中执行的搜索迭代以及后续的对话轮次。
无论返回多少条结果，每次 web search 都计为一次使用。如果 web search 期间发生错误，该次 web search 将不计费。

#### Web fetch tool

Web fetch 的使用除标准 token 费用外
没有额外收费
：

```json
{
  "usage": {
    "input_tokens": 25039,
    "output_tokens": 931,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
    "server_tool_use": {
      "web_fetch_requests": 1
    }
  }
}
```

Web fetch tool 可在 Claude API 上以
无额外费用。你只需为获取到的、成为你的对话上下文一部分的内容支付标准 token 费用。
为防止无意中获取会消耗过多 token 的大型内容，请使用
max_content_tokens
参数，根据你的用例和预算考量设置合适的限制。
典型内容的 token 用量示例：
平均网页（10 kB）：约 2,500 tokens
大型文档页面（100 kB）：约 25,000 tokens
研究论文 PDF（500 kB）：约 125,000 tokens

#### Computer use tool 

Computer use 遵循标准
tool use pricing
。使用 computer use tool 时：
Toolset 定义开销：
声明
computer_toolset_20260801
及其默认成员会向请求增加约 4,500 个输入 token（在 Claude Fable 5、Claude Mythos 5、Claude Opus 5 和 Claude Opus 4.8 上约为 4,520，在 Claude Sonnet 5 上约为 4,590），这涵盖成员 tool 定义和 tool use system prompt。通过
configs
禁用
zoom
会移除其中约 410 个 token。请求的精确数量会在响应
usage
中报告，你可以提前使用
token counting endpoint
估算。
更早的 tool 版本：
以下数字适用于
computer_20251124
和
computer_20250124
tool 版本，不适用于
computer_toolset_20260801
：
System prompt 开销：向 system prompt 增加 466–499 tokens
Tool 定义：每个 tool 定义约 735 个输入 token（使用
computer_20250124
测量）
额外的 token 消耗：
在 tool 结果中返回的 Screenshot 和 zoom 图像，按 image input 计费（参见
Vision pricing
）
返回给 Claude 的 tool 执行结果

#### Browser use tool 

Browser use 遵循标准
tool use pricing
。使用 browser use tool 时：
Toolset 定义开销：
声明
browser_toolset_20260801
及其默认成员会为每个请求增加约 6,600 个 input tokens（在 Claude Fable 5、Claude Mythos 5、Claude Opus 5 和 Claude Opus 4.8 上约为 6,610，在 Claude Sonnet 5 上约为 6,670），这涵盖了成员 tool 定义和 tool use system prompt。启用全部四个可选成员会增加约 880 个 tokens，而使用 configs 禁用成员则会减少该数量。请求的确切数量会在响应的 usage 中报告，你可以使用 token counting endpoint 提前估算。

额外的 token 消耗：

- tool 结果中返回的 screenshot 和 zoom 图像，按 image input 计费（参见 Vision pricing）
- 返回给 Claude 的文本 tool 结果，例如 accessibility trees、页面文本以及 console 或 network 条目

## Claude Managed Agents 定价

Claude Managed Agents 按两个维度计费：tokens 和 session runtime。

### Tokens

Claude Managed Agents session 消耗的所有 tokens 均按 Model pricing 中所示的费率计费。Prompt caching 乘数同样适用。在 session 内触发的 web search 按标准的每 1,000 次搜索 $10 计费。在 Claude Platform on AWS 上，session token 和 runtime 费用按标准费率转换为 Claude Consumption Units。当 agent 的 model.speed 设置为 `"fast"` 时，适用 Fast mode 溢价定价。data residency multiplier 同样适用：当 agent 的 model.inference_geo 固定为 `"us"` 时，运行该 agent 的 session 所消耗的 tokens 按标准费率的 1.1 倍计费，这与 Messages API 上仅限美国推理所适用的乘数相同。

以下 Messages API 修饰符**不**适用于 Claude Managed Agents session：

| 修饰符                 | 不适用原因                                    |
| ---------------------- | --------------------------------------------- |
| Batch API discount     | Session 是有状态且交互式的。没有 batch mode。 |
| Cloud platform pricing | 在合作伙伴运营的 cloud 平台上不可用。         |

### Session runtime

| SKU                                          | 费率                  | 计量                 |
| -------------------------------------------- | --------------------- | -------------------- |
| Session runtime                              | $0.08 每 session-hour | running 状态持续时间 |
| runtime 以毫秒为单位计量，并且仅在会话状态为 |
| running                                      |
| 时累计。处于                                 |
| idle                                         |
| （等待你的下一条消息或某个 tool 确认）、     |
| rescheduling                                 |
| 或                                           |
| terminated                                   |
| 状态所花费的时间不计入 runtime。             |

### 计算示例

一个使用 Claude Opus 5 的一小时编码会话，消耗 50,000 个 input tokens 和 15,000 个 output tokens：
项目
计算
费用
Input tokens
50,000 × $5 / 1,000,000
$0.25
Output tokens
15,000 × $25 / 1,000,000
$0.375
会话 runtime
1.0 小时 × $0.08
$0.08
总计
$0.705
如果 prompt caching 处于启用状态，且其中 40,000 个 input tokens 为 cache reads：
项目
计算
费用
未缓存的 input tokens
10,000 × $5 / 1,000,000
$0.05
Cache read tokens
40,000 × $5 × 0.1 / 1,000,000
$0.02
Output tokens
15,000 × $25 / 1,000,000
$0.375
会话 runtime
1.0 小时 × $0.08
$0.08
总计
$0.525

## 其他定价考量

### 成本优化策略

使用 Claude 构建 agent 时：
选用合适的模型：
简单任务选择 Haiku，大多数生产工作负载选择 Sonnet，最复杂的推理选择 Opus
实施 prompt caching：
降低重复 context 的成本
批处理操作：
对时间不敏感的任务使用 Batch API
监控使用模式：
跟踪 token 消耗，以发现优化机会

### 速率限制

速率限制因 usage tier 而异，并影响你可以发起的请求数量：
Start tier：
用于起步的入门级限制
Build tier：
面向不断增长的应用的更高限制
Scale tier：
面向生产工作负载的最高标准限制
有关详细的速率限制信息，请参见
Rate limits
。
如需超出 Scale tier 的限制或定制定价方案，
请联系 sales 团队
。

### 批量折扣

对于高用量用户，可能提供批量折扣。此类折扣逐案协商确定。
标准 usage tier 使用
Model pricing
中所示的价格
企业客户可
联系 sales
获取定制定价
可能提供学术与研究折扣

### Enterprise pricing

面向有特定需求的企业客户：
自定义 rate limits
批量折扣
专属支持
自定义条款
请联系销售团队：
sales@anthropic.com
或通过
Claude Console
讨论企业定价方案。

## Billing and payment

计费基于每月实际使用量
所有付款均以美元（USD）结算
支持信用卡和发票两种方式
可在
Claude Console
中跟踪使用量

## Frequently asked questions

### token 使用量是如何计算的？

token 是模型处理的文本片段。粗略估计，在英文中 1 个 token 约等于 4 个字符或 0.75 个单词。确切数量因语言和内容类型而异。

### 是否有免费套餐或试用？

新用户会获得少量免费额度用于测试 API。
联系销售团队
可了解用于企业评估的延长试用信息。

### 折扣如何叠加？

Batch API 与 prompt caching 折扣可以叠加使用。例如，同时使用这两项功能相比标准 API 调用可显著节省成本。各项乘数如何相互作用，请参见
prompt caching 定价
。

### 接受哪些付款方式？

标准账户可使用主流信用卡。企业客户可安排发票及其他付款方式。
如对定价有其他疑问，请联系
support@anthropic.com
。
Was this page helpful?
Ask Docs
