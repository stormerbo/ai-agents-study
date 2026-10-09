用于高要求的推理和长周期 agentic 工作，或当你在更高 effort 下对 Claude Opus 5.5 的 evals 仍不达标时。当前所有模型都支持文本与图像输入、文本输出、多语言能力、vision 和 tool use。每个模型的页面都会列出其可用的平台。
Feature
Claude Fable 5.1
用于高要求的推理和长周期 agentic 工作
Claude Opus 5.5
用于长时间运行的 agentic coding 和知识工作
Claude Sonnet 5.5
速度与智能的最佳组合
Claude Haiku 5.5
用于高并发、对延迟敏感的任务，如分类、提取和路由
Comparative latency
较慢
中等
快
最快
Pricing
$10 / input MTok
$50 / output MTok
$4 / input MTok
$20 / output MTok
$2 / input MTok
$10 / output MTok
From $0.10 / input MTok
From $0.50 / output MTok
Claude API ID
claude-fable-5-1
claude-opus-5-5
claude-sonnet-5-5
claude-haiku-5-5
Capabilities
Thinking
Adaptive (always on)
Adaptive (always on)
Adaptive
Adaptive
Default effort
high
medium
high
medium
Context window
1M tokens
1M tokens
1M tokens
1M tokens
Max output
128K tokens
128K tokens
128K tokens
128K tokens
Reliable knowledge cutoff
Jun 2026
Jun 2026
Jun 2026
Jun 2026

Additional details
Training data cutoff
Jun 2026
Jun 2026
Jun 2026
Jun 2026
Retirement
Not sooner than September 1, 2027
Not sooner than September 22, 2027
Not sooner than September 28, 2027
Not sooner than October 7, 2027
Model IDs
Claude API alias
claude-fable-5-1
claude-opus-5-5
claude-sonnet-5-5
claude-haiku-5-5
Amazon Bedrock ID
anthropic.claude-fable-5-1
anthropic.claude-opus-5-5
anthropic.claude-sonnet-5-5
anthropic.claude-haiku-5-5
Google Cloud ID
claude-fable-5-1
claude-opus-5-5
claude-sonnet-5-5
claude-haiku-5-5
Microsoft Foundry ID
claude-fable-5-1
claude-opus-5-5
claude-sonnet-5-5
claude-haiku-5-5
Claude Platform on AWS ID
claude-fable-5-1
claude-opus-5-5
claude-sonnet-5-5
claude-haiku-5-5
选定模型后，
了解如何发起你的第一次 API 调用
要了解 model ID、alias 和 snapshot 的工作方式，请参阅
Model IDs and versioning
；关于每个模型背后的可靠知识与训练数据截止时间，请参阅
Anthropic's Transparency Hub
。

## 使用 Models API 

你可以通过
Models API
以编程方式查询模型能力和 token 限制。响应中会为每个可用模型包含
max_input_tokens
、
max_tokens
以及一个
capabilities
对象。
响应中的每个模型还有一个
line
字段，用于标明它所属的模型线。Claude Opus 4.5 和 Claude Opus 4.6 都报告
opus
。可以用
line
对模型进行分组，例如在模型选择器中。当模型不属于任何线时，
line
为
null
。请读取
line
，而不要从模型的
id
推断它。Anthropic 可能会添加更多线，因此不要把取值的集合视为固定的。
每个模型的
capabilities
对象都包含
thinking.types.disabled
，它报告该模型是否接受
thinking: {type: "disabled"}
，即
关闭 thinking
的设置。当模型以 400 错误拒绝
"disabled"
时，
supported
为
false
；而在不支持 thinking 的模型上则为
true
。即使
supported
为
true
，API 仍可能因其他原因拒绝
"disabled"
请求。其中一个原因是：在 thinking 关闭时，模型不允许的
effort
级别。
每个模型的
capabilities
对象还包含
server_tools
，它报告该模型是否接受
web search
和
code execution
工具。它不涵盖其他 server 工具，例如 web fetch。
当模型接受该工具至少一个版本（不一定是所有版本）时，
server_tools.web_search.supported
和
server_tools.code_execution.supported
为
true
。当模型接受这两个工具中的至少一个时，
server_tools.supported
为
true
。即使某个工具受支持，你所在组织的设置仍可能导致使用该工具的请求失败。例如，管理员可以
禁用 web search
。
顶层的
code_execution
capability 是另一项检查。它报告 Claude 在 code execution tool 中运行的代码是否可以调用请求中的其他工具，如
programmatic tool calling
中所述。例如，对于 Claude Haiku 4.5，Models API 报告
server_tools.code_execution.supported
为
true
，而
code_execution.supported
为
false
。

## Prompt 与输出性能 

当前的 Claude 模型在以下方面表现卓越：
性能：
在推理、编码、多语言任务、长上下文处理、诚实性和图像处理方面取得顶级结果。有关通用和特定于模型的提示指导，请参阅
Prompting best practices
。
引人入胜的响应：
Claude 模型非常适合需要丰富、类人交互的应用。如果你更喜欢简洁的响应，请调整你的 prompts，引导模型达到所需的输出长度。有关详细信息，请参阅
prompt engineering guides
。
输出质量：
从上一代模型迁移时，你可能会注意到整体性能有更大的提升。如果你使用的是 Claude Opus 5 或更早版本，请参阅
Claude Opus 5.5 migration guide
。

## Claude 入门 

如果你已准备好开始探索 Claude 能为你做什么，那就深入其中吧！无论你是希望将 Claude 集成到应用中的开发者，还是想亲身体验 AI 强大功能的用户，以下资源都可以提供帮助。

Intro to Claude
探索 Claude 的能力和开发流程。

Quickstart
了解如何在几分钟内完成你的第一次 API 调用。
Choosing a model
制定标准，并为你的用例选择正确的模型。
Pricing
完整的定价信息，包括批量折扣和 prompt caching 费率。

Model deprecations
每个模型的生命周期状态和退役承诺。

Claude Console
直接在浏览器中编写和测试 prompts。
想与 Claude 聊天？请访问
claude.ai
。如果你有疑问，请联系
support team
或
Discord community
。
此页面有帮助吗？


Ask Docs

