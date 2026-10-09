effort 参数让你可以控制 Claude 在响应请求时消耗多少 token。你可以在单个模型上权衡响应的详尽程度与 token 效率。顶层 effort 参数在所有受支持的模型上均可用，无需 beta header。
Per-message effort 处于 beta 阶段。

## 设置 effort 级别

在请求上设置
output_config.effort
。以下示例以
medium
effort 运行一个请求，并打印响应文本。
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

4096
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
"Analyze the trade-offs between microservices and monolithic architectures"
,
}
],
output_config
=

{
"effort"
:
"medium"
},
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

## effort 的工作方式

大多数 Claude 模型默认使用 high effort，会按需消耗尽可能多的 token 以取得出色的结果；Claude Opus 5.5 和 Claude Haiku 5.5 默认使用 medium。你可以将 effort 级别提升至
max
以获得绝对最高的能力，或将其调低以更保守地使用 token，在优化速度与成本的同时接受一定程度的性能下降。
effort 参数会影响响应中的
所有 token
，包括：
文本响应与解释
工具调用与函数参数
思考（在启用时）
由于 effort 作用于每一个输出 token，因此无论是否启用思考，它都会生效。较低的 effort 还意味着更少、更简洁的工具调用。

### Effort 级别

级别
描述
典型使用场景
max
绝对最高能力，对 token 消耗不设限制。在 Claude Fable 5.1、Claude Mythos 5.1、Claude Fable 5、Claude Mythos 5、Claude Mythos Preview、Claude Opus 5.5、Claude Opus 5、Claude Opus 4.8、Claude Opus 4.7、Claude Opus 4.6、Claude Sonnet 5.5、Claude Sonnet 5、Claude Sonnet 4.6 和 Claude Haiku 5.5 上可用。
需要尽可能深入推理和进行最全面分析的任务
xhigh
为长周期工作扩展的能力。适用于 Claude Fable 5.1、Claude Mythos 5.1、Claude Fable 5、Claude Mythos 5、Claude Opus 5.5、Claude Opus 5、Claude Opus 4.8、Claude Opus 4.7、Claude Sonnet 5.5、Claude Sonnet 5 和 Claude Haiku 5.5。
长时间运行的 agentic 和编码任务（超过 30 分钟），token 预算达到数百万
high
按任务需要花费尽可能多的 token，以获得优秀结果。除 Claude Opus 5.5 和 Claude Haiku 5.5 外，所有支持 effort 的模型都默认使用此级别。
复杂推理、困难的编码问题、agentic 任务
medium
平衡方案，带来适度的 token 节省。Claude Opus 5.5 和 Claude Haiku 5.5 的默认级别。
需要在速度、成本和性能之间取得平衡的 agentic 任务
low
最高效。显著节省 token，同时能力有一定下降。
需要最佳速度和最低成本的较简单任务，例如 subagents
并非每个支持
max
的模型都支持
xhigh
。
下面针对各模型的建议在与本表不一致时，以这些建议为准。

### Claude Fable 5.1 的推荐 effort 级别

Claude Fable 5.1 支持全部五种 effort 级别。
从
high
开始，这是默认级别。
对于对能力最敏感的 agentic 和编码工作，提升到
xhigh
或
max
；对于例行工作或对延迟敏感的工作，一旦你的 evals 表明质量仍能保持，就降到
medium
或
low
。在
high
及以上时，设置较大的
max_tokens
。这是对总输出（thinking 加 response 文本）的硬性限制。同样的建议也适用于 Claude Mythos 5.1。参见
Prompting Claude Fable 5.1
。
Claude Fable 5.1 还支持通过每条消息的
output_config
在对话中途更改 effort，这会保留 prompt cache。

### Claude Fable 5 的推荐 effort 级别

Effort 是在 Claude Fable 5 上权衡 intelligence、延迟和成本的主要控制手段。
对于大多数任务，从
high
开始，这是默认级别
，使用
xhigh
对于对能力最敏感的工作负载，而日常工作则下调到 `medium` 或 `low`。Claude Fable 5 上较低的 effort 设置仍然表现良好，且往往超过先前模型上的 `xhigh` 性能。在 `high` 和 `xhigh` 下，设置较大的 `max_tokens`。它是对总输出（thinking 加响应文本）的硬性限制。参见 Cost control。

如果任务能够完成但耗时超过必要，或者你希望获得更快、更具交互性的工作方式，就降低 effort。同样的建议也适用于 Claude Mythos 5。更完整的指导参见 Prompting Claude Fable 5。

### Claude Opus 5.5 推荐的 effort 级别

Claude Opus 5.5 支持全部五种 effort 级别，`medium` 是默认值（Claude Opus 5 及更早的 Opus 模型默认为 `high`，因此省略 `effort` 的请求会比它在 Claude Opus 5 上低一级运行）。自适应 thinking 始终开启且无法关闭，因此 effort 是控制模型推理量以及请求成本的主要手段。在你的自有 evals 上运行一次 effort sweep，而不是从更早的模型沿用设置；在更高的级别上设置较大的 `max_tokens`：它是对总输出（thinking 加响应文本）的硬性限制。设置 `thinking: {"type": "disabled"}` 的请求在每个 effort 级别都会返回 400 错误。Claude Opus 5.5 还支持通过逐条消息的 `output_config` 在对话中途更改 effort，这会保留 prompt cache。参见 Prompting Claude Opus 5.5。

### Claude Opus 5 推荐的 effort 级别

Claude Opus 5 支持全部五种 effort 级别。从默认的 `high` 开始，并根据你的 evals 进行调整：对于要求较高的编码和 agentic 工作上调到 `xhigh`，当任务值得不受约束的 token 消耗时上调到 `max`，并在你的 evals 显示质量保持的场合，大方地使用 `low` 和 `medium` 作为控制 token 成本和响应时间的主要手段。如果你从更早的模型沿用了 effort 设置，请在你的 evals 上重新运行一次 effort sweep，而不是复用它们。
Effort 控制的是思考量，而不是可见回复的长度：在 Claude Opus 5 上，更改 effort 并不能可靠地缩短回复，因此请改为通过 prompt 控制长度。

API 默认值为 high。若要使用其他级别，请显式设置 effort。你传入的值会覆盖默认值。

在 Claude Opus 5 上，thinking 无法在 xhigh 或 max effort 下禁用：在这些级别下设置 `thinking: {"type": "disabled"}` 的请求会返回 400 错误。请参阅 Effort with thinking。

在 xhigh 或 max effort 下运行 Claude Opus 5 时，请设置较大的 max_tokens，以便模型有空间跨 subagent 和 tool call 进行思考和行动。从 64k token 起步并在此基础上调整，是一个合理的默认值。

Claude Opus 5 还支持通过每条消息的 output_config 在对话中途更改 effort，这样可以保留 prompt cache。Amazon Bedrock 上的 Claude Opus 5 不支持按消息设置 effort。

### Claude Opus 4.8 的推荐 effort 级别

Claude Opus 4.7 的指南同样适用于 Claude Opus 4.8。

在编码和 agentic 用例中从 xhigh 开始，对大多数其他对智能敏感的工作负载使用 high，只有在你的 eval 中测得较低级别能够保持质量时，才降级到 medium 或 low。

API 默认值为 high。若要使用其他级别，请显式设置 effort。你传入的值会覆盖默认值。

在 xhigh 或 max effort 下运行 Claude Opus 4.8 时，请设置较大的 max_tokens，以便模型有空间跨 subagent 和 tool call 进行思考和行动。从 64k token 起步并在此基础上调整，是一个合理的默认值。

### Claude Opus 4.7 的推荐 effort 级别

在编码和 agentic 用例中从 xhigh 开始，并对大多数对智能敏感的工作负载将 high 作为最低级别。对成本敏感的工作负载可降级到 medium，只有在你的 eval 显示 xhigh 仍有可衡量的提升空间时，才升级到 max。

API 默认值为 high。若要使用 xhigh，请显式设置 effort。你传入的值会覆盖默认值。

Effort
Claude Opus 4.7 的指南
low
高效，但最适合简短、范围明确的任务。如果你的任务包含多个部分，请将
low
与显式检查清单搭配使用。
medium
适用于普通工作流的开箱即用选择，既能获得良好结果，又能降低成本。
high
适用于仍需要兼顾智能水平与 token 消耗的高级用例。这通常是在质量与 token 效率之间取得的最佳平衡。
xhigh
推荐作为编码与 agentic 工作的起点，也适用于探索性任务，例如重复的 tool calling、详细的 web search 和 knowledge-base search。预计 token 用量会明显高于
high
。
max
保留给前沿问题。在大多数工作负载上，
max
会显著增加成本，而质量提升相对较小；在某些结构化输出或对智能水平不太敏感的任务上，它还可能导致过度思考。
Claude Opus 4.7 对 effort 级别的遵循也比 Claude Opus 4.6 更严格，尤其是在
low
和
medium
下。在较低的 effort 级别下，模型会把工作范围限定在所要求的内容内，而不会超出要求去做更多事情。如果你发现 Claude Opus 4.7 在复杂问题上推理较浅，应提高 effort，而不是通过 prompt 去绕开它。如果你为了延迟必须保持较低的 effort，请添加有针对性的指引，例如“This task involves multistep reasoning. Think carefully before responding.”
在以
xhigh
或
max
effort 运行 Claude Opus 4.7 时，请设置较大的
max_tokens
，以便模型有空间跨 subagents 和 tool calls 进行思考和行动。从 64k tokens 起步并在此基础上调优是一个合理的默认做法。

### Claude Sonnet 5.5 推荐的 effort 级别

Claude Sonnet 5.5 支持全部五个 effort 级别，并且在 Claude API 上默认为
high
。它的各级别经过重新校准，因此同一级别产生的思考量并不等同于 Claude Sonnet 5 上的同一级别。请在你的 evals 上重新做一次 effort 扫描，而不是沿用你在 Claude Sonnet 5 上使用的设置。除非你的工作负载是 agentic 或对延迟敏感，否则请从
high
开始。对于 agentic coding 和多步 tool use，请从
medium
用于定义明确的任务，对于更难或更长的任务则改用
high
。对于 chat 以及其他对延迟敏感的工作，从
medium
或
low
开始。仅在你的 eval 显示质量有提升的地方使用
xhigh
或
max
。设置
max_tokens
时要为 thinking 和回复留出空间。即使 thinking 内容不会被返回，thinking 也计入
max_tokens
。对于 agentic coding，将
max_tokens
设为 128,000，即模型的最大值，并
stream
响应。
要关闭 up-front thinking，请发送
thinking: {"type": "between_tools"}
而不是
"disabled"
。这是 Claude Sonnet 5.5 上最低的 thinking 设置，并且在
low
、
medium
和
high
effort 下都有效。在
xhigh
或
max
下，带该设置的请求会返回 400 错误，因此在这些级别下请使用 adaptive thinking：省略
thinking
字段或发送
thinking: {"type": "adaptive"}
。参见
Running without up-front thinking
。
Claude Sonnet 5.5 还支持通过 per-message
output_config
在对话中途更改 effort，这会保留 prompt cache。使用
between_tools
时，effort 无法在对话中途更改：per-message
output_config.effort
如果与当前生效的级别不同，会返回 400 错误。要按轮次变化 effort，请使用 adaptive thinking。参见
Prompting Claude Sonnet 5.5
。

### Claude Sonnet 5 推荐的 effort 级别

Claude Sonnet 5 在 Claude API 和 Claude Code 上默认使用
high
effort。
High effort（默认）：
适用于复杂推理、coding 和 agentic 任务，在这些任务中质量比速度或成本更重要。
Xhigh effort：
用于最难的 coding 和 agentic 任务。参见
Prompting Claude Sonnet 5
。
Medium effort：
从默认级别降档以节省成本。相当于 high effort 下的 Claude Sonnet 4.6。
Low effort：
适用于高并发量或对延迟敏感的工作负载。适合 chat 及非 coding 用例，这类场景优先考虑更快的周转速度。
Max effort：
适用于需要绝对最高能力、且对 token 花费没有限制的任务。

### Claude Sonnet 4.6 推荐的 effort 级别

Sonnet 4.6 默认使用
high
effort。使用 Sonnet 4.6 时显式设置 effort，以避免意外的延迟：

Medium effort
（推荐的默认值）：对大多数应用而言，在速度、成本和性能之间取得最佳平衡。适用于 agentic coding、工具密集型工作流和代码生成。

Low effort
：适用于高并发或对延迟敏感的工作负载。适用于优先考虑更快周转的 chat 和非编码用例。

High effort
：适用于复杂推理以及质量比速度或成本更重要的任务。

Max effort
：适用于需要绝对最高能力、且对 token 开销没有任何限制的任务。

### Claude Haiku 5.5 推荐的 effort 等级

Claude Haiku 5.5 支持全部五个 effort 等级，并且在 Claude API 和 Claude Code 中
medium
是默认值。Effort 是控制模型思考量的主要手段，同时也控制着质量、延迟和成本。

大多数工作都从
medium
开始，包括 agentic coding。将
low
——最便宜、最快的等级——用于 chat、简短的工具任务以及简单的高并发请求。在较长的 agent prompt 中，模型在
low
下更有可能跳过搜索、提前停止或跳过检查。将
high
用于知识工作、较长的 agent 任务以及严格的指令遵循。仅在你的 evals 显示质量提升时使用
xhigh
或
max
，并与 Claude Sonnet 5.5 在性能、成本和速度上进行比较。Thinking 默认开启，并计入
max_tokens
，所以要为它留出空间。参见
Prompting Claude Haiku 5.5
。

要减少思考，就降低 effort 等级。你也可以在
high
或以下等级发送
thinking: {"type": "disabled"}
。在
xhigh
或
max
下，它会返回 400 错误，因此在那里使用 adaptive thinking：省略
thinking
字段或发送
thinking: {"type": "adaptive"}
。

在 Claude API 和 Google Cloud 上，Claude Haiku 5.5 还支持通过每条消息的
output_config
在对话中途更改 effort，这会保留 prompt cache。使用
thinking: {"type": "disabled"}
时，effort 无法在对话中途更改：每条消息的
output_config.effort
与生效中的级别不同的值会返回 400 错误。要逐轮调整 effort，请使用 adaptive thinking。

## 使用工具时的 effort

使用工具时，effort 参数会影响工具调用周围的说明以及工具调用本身。较低的 effort 级别倾向于：
将多个操作合并为更少的工具调用
减少工具调用次数
不做铺垫，直接进入操作
完成后使用简洁的确认消息
较高的 effort 级别可能会：
进行更多工具调用
在采取行动前解释计划
提供详细的变更摘要
包含更全面的代码注释

## 与 thinking 一起使用时的 effort

thinking
参数控制 Claude 在回答前是否在
thinking blocks
中思考；
effort
参数控制 Claude 在整个响应中投入多少工作量，在 adaptive 模式下，这包括它思考的频率和深度。不要把
adaptive
作为
effort
值传入：
adaptive
是一种 thinking 模式，不是 effort 级别。
在较高的 effort 级别下，Claude 会更愿意思考，并且思考得更长。在工具使用循环中，仅处理工具结果的后续请求在任何级别下仍然可以跳过 thinking。在较低级别下，Claude 对更简单的问题可以完全跳过 thinking。关于这两个控制项如何协同工作的完整指导，请参见
Thinking and effort
。
在 Claude Opus 4.5 上——唯一支持 effort 的仅扩展思考模型——它与
budget_tokens
协同工作：为你的任务设置 effort 级别，然后根据任务需要多少推理深度来设置 thinking token 预算。
关于各模型的 thinking 可用性，请参见
per-model configuration table
。Effort 在有或没有 thinking 的情况下都可用。请参见
How effort works
。

## 在对话中途更改 effort

你可以在对话的后续轮次中以两种方式在不同的 effort 级别下运行。在 Claude Fable 5.1、Claude Mythos 5.1、Claude Opus 5.5、Claude Opus 5、Claude Sonnet 5.5 和 Claude Haiku 5.5 上，使用 per-message effort 变更，这会保留 prompt cache。在其他模型上，在下一个请求中设置一个新的顶层值，这会重新开始 cache。

### Per-message effort（beta）

Per-message effort 处于 beta 阶段。在 Claude API 和
Google Cloud
上，它可用于 Claude Fable 5.1、Claude Mythos 5.1、Claude Opus 5.5、Claude Opus 5、Claude Sonnet 5.5 和 Claude Haiku 5.5。在
Amazon Bedrock
上，它可用于 Claude Fable 5.1、Claude Mythos 5.1 和 Claude Opus 5.5。它需要
beta header
mid-conversation-output-config-2026-07-01
。使用 Amazon Bedrock
InvokeModel API
时，它可用于 Claude Fable 5.1 和 Claude Opus 5.5，并且你需要在请求体的
anthropic_beta
数组中发送该值。
如果没有 beta 值，per-message
output_config
会返回 400 错误：
messages.N.output_config: Extra inputs are not permitted
，其中
N
是
messages
中
system
消息的索引。有了 beta 值，不支持 per-message effort 的模型（包括 Claude Fable 5）会返回 400 错误：
output_config.effort requires a model that supports per-turn effort; this model does not
。在 Amazon Bedrock 上，这些模型和 Claude Opus 5 会改为返回
Extra inputs are not permitted
错误。在带有
thinking: {"type": "between_tools"}
的 Claude Sonnet 5.5 上，以及在带有
thinking: {"type": "disabled"}
的 Claude Haiku 5.5 上，effort 无法在对话中途更改：如果 per-message
output_config.effort
与当前生效的级别不同，会返回 400 错误。要按轮次改变 effort，请使用 adaptive thinking。
添加一条
role: "system"
消息，其
content
为空，并在
output_config.effort
中设置新级别。新级别从下一个
user
轮次开始生效，并一直保持，直到后续某条消息更改它。该消息之前的所有内容都保持不变，因此缓存的 prefix 仍然匹配。
以下示例从 high 开始，然后针对例行的后续跟进降到 low：

cURL CLI Python TypeScript C# Go Java PHP Ruby

```python
client = anthropic.Anthropic()
response = client.beta.messages.create(
    model="claude-fable-5-1",
    max_tokens=4096,
    output_config={"effort": "high"},
    messages=[
        {
            "role": "user",
            "content": "Plan a migration from SQLite to PostgreSQL in three short steps.",
        },
        {
            "role": "assistant",
            "content": "1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts.",
        },
        # 仅含 effort 的 system message：新级别从下一个 user 轮次开始生效。
        {
            "role": "system",
            "content": [],
            "output_config": {"effort": "low"},
        },
        {
            "role": "user",
            "content": "Summarize the plan in one sentence.",
        },
    ],
    betas=["mid-conversation-output-config-2026-07-01"],
)
for block in response.content:
    if block.type == "text":
        print(block.text)
```

仅含 effort 的 system message 不携带任何文本，因此 mid-conversation system messages 的放置规则并不适用。它可以出现在 messages 中的任意位置，包括作为第一条条目，或位于 assistant 轮次与下一个 user 轮次之间。取值为级别名称（low、medium、high、xhigh 和 max）。

在 Claude Fable 5.1 上，相比在请求之间更改顶层值，更推荐使用这种形式。更改顶层值会重启缓存，并且对模型的引导也更不可靠：它先前的回复是在上一个级别下写出的，而模型倾向于与这些回复保持一致。

### 在下一个请求上设置顶层 effort

顶层 output_config.effort 作用于整个请求。若要以不同级别运行对话的后续部分，请在下一个请求上设置新值。由于顶层 effort 会影响渲染后的 prompt，在请求之间更改它不会保留先前轮次的缓存前缀。如果你依赖 prompt caching
在一个长会话中，如果你的模型不支持 per-message effort，那么在一开始就选定一个 effort 级别并保持不变。

## 最佳实践

显式设置 effort：
API 默认使用
high
（在 Claude Opus 5.5 和 Claude Haiku 5.5 上为
medium
），但合适的起点取决于你的模型和工作负载。
对速度敏感或简单的任务使用 low：
当延迟很重要或任务较直接时，low effort 可以显著降低响应时间和成本。
测试你的用例：
effort 级别的影响因任务类型而异。在部署前，先在你的具体用例上评估性能。
考虑动态 effort：
根据任务复杂度调整 effort。简单查询可能适合 low effort，而 agentic coding 和复杂推理则受益于 high effort。在同一个会话中变动 effort 之前，请先看下一项。
在缓存会话中保持顶层 effort 不变：
在请求之间更改顶层 effort 值会使
prompt caching
失效，因此应在不同工作负载之间变动，而不是在依赖缓存命中的会话内部变动。在支持该功能的模型上，改用
per-message effort change
，这样可以保留缓存。参见
Thinking 和 prompt caching
。

## 后续步骤

Task budgets
为完整的 agentic loop 给 Claude 一个建议性的 token budget，帮助模型在长 agentic 任务中进行自我调节。
Steering thinking
了解 adaptive thinking，即 Claude 决定何时思考以及思考多少，并通过 effort 和 prompting 来引导它。

Thinking
了解 thinking 的工作方式、Claude 默认何时思考，以及 thinking 如何与 effort 交互。

## 兼容性

支持的模型
Fable
5 和 5.1
Mythos
5、5.1 和 Preview
Opus
4.5、4.6、4.7、4.8、5 和 5.5
Sonnet
4.6、5 和 5.5
Haiku
5.5
支持的平台
Claude API
Claude Platform on AWS
Amazon Bedrock
Google Cloud
Microsoft Foundry
本页是否有帮助？

Ask Docs
