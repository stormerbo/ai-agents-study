让你能够以轻量、易用、极少抽象的方式构建 agentic AI 应用。它是我们此前为 agents 所做的实验
Swarm
的生产级升级版。Agents SDK 只有非常少的一组原语：
Agents
，即配备 instructions 和 tools 的 LLM
Agents as tools / Handoffs
，允许 agent 将特定任务委派给其他 agent
Guardrails
，用于验证 agent 的输入和输出
结合 Python，这些原语强大到足以表达 tools 与 agents 之间的复杂关系，并让你无需经历陡峭的学习曲线就能构建真实世界的应用。此外，该 SDK 内置
tracing
，让你能够可视化和调试你的 agentic 流程，对其进行评估，甚至为你的应用微调模型。

## 为什么使用 Agents SDK

该 SDK 有两条核心设计原则：
功能够多，值得使用，但原语够少，便于快速上手。
开箱即用，同时你可以精确自定义所发生的一切。
以下是该 SDK 的主要特性：
Agents
：构建带有 instructions、tools、guardrails、handoffs 以及一个内置循环（持续运行直到任务完成）的 agents。
Sandbox agents
：在真实的隔离工作区内运行专家型 agent。Sandbox agents 支持 manifest 定义的文件、sandbox client 选择以及可恢复的 sandbox 会话。
Realtime agents
：使用
gpt-realtime-2.1
构建强大的语音 agents，具备自动中断检测、上下文管理、guardrails 等更多能力。
Voice agents
：构建结合 speech-to-text、agent 工作流和 text-to-speech 的语音流水线。
Python-first
：使用内置语言特性来编排和串联 agents，而无需学习新的抽象。
Agents as tools / Handoffs
：一种在多个 agents 之间协调和委派工作的强大机制。
Guardrails
：与 agent 执行并行地运行输入校验和安全检查，并在检查未通过时快速失败。
函数工具
：借助自动 schema 生成和 Pydantic 驱动的校验，把任意 Python 函数变为工具。
MCP server 工具调用
：内置集成，可将远程 MCP 工具与函数工具一并暴露给 agent。
会话
：一个持久化记忆层，用于在 agent loop 内维护工作上下文。
Human in the loop
：内置机制，用于在 agent 运行过程中引入人类参与。
追踪
：内置追踪，用于可视化、调试和监控工作流，并支持 OpenAI 的评估、微调和蒸馏工具套件。

## Agents SDK 还是 Responses API？

对于 OpenAI 模型，该 SDK 默认使用 Responses API，但它把模型调用包装在更高层的 runtime 中。
在以下情况直接使用 Responses API：
你希望自己掌控 loop、工具分发和状态处理
你的工作流是短时的，主要只是返回模型的响应
在以下情况使用 Agents SDK：
你希望由 runtime 管理轮次、工具执行、guardrails、handoff 或会话
你的 agent 需要产出 artifacts，或跨多个协同步骤运行
你需要真实的工作区，或通过
Sandbox agents
实现可恢复的执行
你无需在全局层面二选一。许多应用将 SDK 用于托管工作流，而对更底层的路径直接调用 Responses API。

## 安装

`pip install openai-agents`

## Hello world 示例

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant"
)
result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

（如果运行此示例，请确保设置了 `OPENAI_API_KEY` 环境变量）
`export OPENAI_API_KEY=sk-...`

## 从这里开始

使用 Quickstart 构建你的第一个基于文本的 agent。
然后决定你希望如何在
Running agents
中跨轮次携带状态。
如果任务依赖真实文件、repo 或按 agent 隔离的 workspace 状态，请阅读
Sandbox agents quickstart
。
如果你正在 handoffs 和 manager 风格的 orchestration 之间做决定，请阅读
Agent orchestration
。

## 选择你的路径

当你知道自己想完成的工作，但不确定哪一页对此进行说明时，请使用此表。
目标
从这里开始
构建第一个 text agent 并查看一次完整运行
Quickstart
添加 function tools、hosted tools 或 agents as tools
Tools
在真实的隔离 workspace 中运行 coding、review 或 document agent
Sandbox agents quickstart
和
Sandbox clients
在 handoffs 和 manager 风格的 orchestration 之间做决定
Agent orchestration
跨轮次保留 memory
Running agents
和
Sessions
使用 OpenAI models、websocket transport 或非 OpenAI providers
Models
查看 outputs、run items、interruptions 和 resume state
Results
使用
gpt-realtime-2.1
构建低延迟 voice agent
Realtime agents quickstart
和
Realtime transport
构建 speech-to-text / agent / text-to-speech pipeline
Voice pipeline quickstart
