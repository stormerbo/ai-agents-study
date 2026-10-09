ADK 是开源的 agent 开发框架，让你能够以企业级规模构建、调试和部署可靠的 AI agents。提供 Python、TypeScript、Go、Java 和 Kotlin 版本。
开始构建
Python
TypeScript
Go
Java
Kotlin
from
google.adk
import
Agent
from
google.adk.tools
import
google_search

agent =
Agent
(
name=
"researcher"
,
model=
"gemini-flash-latest"
,
instruction=
"你帮助用户彻底研究主题。"
,
tools=[google_search],
)
import
{
LlmAgent, GOOGLE_SEARCH
}
from
'@google/adk'
;
const
agent =
new
LlmAgent
({
name:
'researcher'
,
model:
'gemini-flash-latest'
,
instruction:
'你帮助用户彻底研究主题。'
,
tools: [GOOGLE_SEARCH],
});
import
"google.golang.org/adk/v2/agent/llmagent"
model, _ := gemini.
NewModel
(context.
Background
(),
"gemini-flash-latest"
,
nil
)
a, _ := llmagent.
New
(llmagent.
Config
{
Name:
"researcher"
,
Model: model,
Instruction:
"你帮助用户彻底研究主题。"
,
Tools: []tool.Tool{geminitool.
GoogleSearch
{}},
})
import
com.google.adk.agents.
LlmAgent
;
import
com.google.adk.tools.
GoogleSearchTool
;

LlmAgent
agent =
LlmAgent
.builder()
.name(
"researcher"
)
.model(
"gemini-flash-latest"
)
.instruction(
"你帮助用户彻底研究主题。"
)
.tools(
new
GoogleSearchTool()
)
.build();
import
com.google.adk.kt.agents.
LlmAgent
import
com.google.adk.kt.tools.
GoogleSearchTool

val
agent =
LlmAgent
(
name =
"researcher"
,
model =
Gemini
(name =
"gemini-flash-latest"
),
instruction =
Instruction
(
"你帮助用户彻底研究主题。"
),
tools = listOf(
GoogleSearchTool
()),
)
pip install google-adk
📋
npm install @google/adk
📋
go get google.golang.org/adk/v2
📋
com.google.adk:google-adk
📋
com.google.adk:google-adk-kotlin-core
📋
Agents CLI

## 用 agents 构建 agents。

在几分钟内从想法变为编码好的 ADK agent。使用你喜爱的 AI 赋能开发环境，通过 Agents CLI 进行脚手架搭建、构建、测试、评估和部署。
了解更多
Graph Workflows

## 可靠的逻辑。智能推理。

将确定性代码与自适应 AI 推理交织在一起。通过结构化的、基于图的架构编排复杂任务，具有明确的执行路径和可预测的结果。ADK 2.0 中的新功能！
了解更多
框架

## 强大的简洁性。为规模而构建。

从使用 prompt 和工具调用构建 ADK agent 开始，然后扩展到多 agent 编排、基于图的工作流、性能评估，以及部署到世界级企业服务，以实现可扩展性、可靠性和吞吐量。
了解更多
生态系统

## 开放生态系统。连接一切。

ADK 的开放集成合作伙伴将你的 agent 与现有应用、广泛的 AI 模型连接起来，并扩展 agent 能力以访问数据、增加韧性并评估性能。
了解更多

## 准备好构建 agent 了吗？

我们认为最好的学习方式之一就是动手构建，因此我们创建了指南，帮助你设置开发环境并在几分钟内运行一个 ADK agent。
开始构建

## 开发者社区

与不断壮大的开发者社区一起构建下一代生产级 AI agent。无论你是想排查图工作流的问题、分享自定义 Agent Skill，还是塑造框架的未来，我们都希望你的参与。

### 社区电话会议

加入 ADK 核心工程团队，观看现场演示、技术深入探讨、路线图更新和 Q&A。
了解更多 →

### 开发者资源

通过全面的培训、视频和来自像你这样的社区成员的深入探讨，跳过学习曲线。
了解更多 →

## 常见问题解答

对 ADK 还有疑问？这里有一些答案：
我可以用 ADK vibe code agent 吗？
是的！ADK 设计为可由人类和 AI 共同编写。将你最喜欢的编码助手连接到我们的 ADK developer Skills 和 AI-aware developer resources，几秒钟内生成 agent。在我们的
Coding with AI
指南中了解有关 AI 驱动的 agent 编码的更多信息。
我可以将哪些 AI 模型与 ADK 一起使用？
ADK 可与几乎任何生成式 AI 模型配合使用。该框架提供了对 Gemini 以及其他领先模型的便捷访问，我们还提供了适配器，让你能够连接许多其他模型和模型提供方，包括本地运行的模型。对于企业，ADK 可以连接到托管服务上的模型，包括 Google Cloud——后者提供广泛的模型，并让你能够密切管理性能、可靠性、安全性、访问、安全防护和成本。

## 是什么让 ADK 与众不同？

借助 ADK，我们专注于构建一个开放的开发框架，让你能够构建专业级、生产级 agent，而无需堆砌大量代码即可上手。我们的目标是让你快速开始构建 agent，并让你按需添加功能和复杂度。ADK 为 agent 提供了一种易于构建的基础结构，并且该结构在设计上具有灵活性，让你能够扩展、延展并构建复杂、健壮、有用的 agentic 系统。我们投入了大量精力，为你提供用于与你构建的 agent 交互的开发工具，并提供使用 AI 驱动的工具来构建 ADK agent 的方式。我们也为我们处理 agent 上下文管理的方式感到相当自豪——我们管理上下文以保持其高效，同时也让你能够按需调整上下文管理。我们还可以继续讲下去，如果你有兴趣，可以在我们的
开发者文档
中找到更多细节。

## ADK 如何处理上下文管理？

与那些只是把字符串拼接在一起、直到上下文窗口溢出的工具不同，ADK
管理
你的 context。我们将 context 视为源代码——sessions、memory、tool outputs 和 artifacts 被组装成一个结构化视图，其中每个 token 都有其价值。ADK 会自动过滤无关事件、总结较早的对话轮次、延迟加载 artifacts，并跟踪 token 使用情况。这种方法默认让你的 agents 保持快速、高效和可靠，同时让你能够完全自定义复杂任务中 context 的管理方式。
ADK 如何部署到生产环境？
ADK 生来就具备
deploy anywhere
的灵活性。你可以将 ADK 容器化并运行在自己的基础设施上，也可以利用我们原生的、一条命令即可完成部署到 Google Cloud 的能力。通过 Agent Runtime（Agent Platform）、Cloud Run 或 GKE 部署到 Google Cloud 时，你的 agents 会立即继承托管基础设施、内置身份验证、Cloud Trace 可观测性以及企业级安全性——这一切都无需你改动 agent 代码中的任何一行。本地开发，全球扩展。
什么时候应该使用 agent framework 来处理生成式 AI？
AI 聊天对话可以完成许多任务，但当你需要完成复杂的多步骤流程时，agent framework 能让你创建一种受管理、可重复的任务结构，它可以在极少人工输入的情况下
hands-off
运行。像 ADK 这样的 agent framework 可以自动启动任务、发出多次迭代式 AI model 请求、管理 context、处理 tool calls、记录数据、运行并行任务、处理失败，并在任务停止后恢复它们。
Back to top
