agent 是一种应用程序，它通过自行规划步骤并调用可读取文件、运行命令或编辑代码的工具来完成任务。Agent SDK 为你提供与 Claude Code 相同的工具、agent loop 和上下文管理能力，并可用 Python 和 TypeScript 进行编程。

## ​ 将 Agent SDK 与其他 Claude 工具进行比较

Agent SDK、CLI、Client SDK 和 Managed Agents 在由谁运行 agent、内置了什么，以及你如何访问它方面有所不同。找到与你期望的构建和运行方式相匹配的那一行。
你想要
使用
你将获得
在你自行运行的进程中，将 Claude Code 的 agent 嵌入到你自己的 Python 或 TypeScript 应用程序中
Agent SDK
一个运行 Claude Code 二进制的库，具备 Claude Code 的
能力
，例如内置工具、权限、会话和 hooks。
在终端中进行交互式开发或运行一次性任务
Claude Code CLI
终端界面，专为日常交互式使用而构建。
直接从你自己的代码中调用 Claude API
Client SDK
从任意 Client SDK 语言直接访问 Claude API。工具循环由你自己编写，或让 Client SDK 的 beta 版
tool runner
来驱动它。
让 Anthropic 托管 agent，并通过 Claude API 进行配置
Managed Agents
一个托管的 agent harness，负责运行 agent loop，其会话位于 Anthropic 托管的云沙箱中，或位于你自己基础设施上的
self-hosted sandbox
中。可通过
适用于你的语言的 SDK
、
ant
CLI 或 REST API 使用它。
若要从 Python 或 TypeScript 之外的语言驱动同一个 agent loop，
请将该 CLI 作为子进程运行
，并使用
-p
标志和
--output-format json
。

## ​ 能力

以下 Claude Code 能力在 SDK 中可用：
能力
作用
了解更多
内置工具
读取、写入、编辑文件，运行命令，以及搜索网页
Tools reference
Hooks
在 agent 生命周期的关键节点运行自定义代码
Hooks
Subagents
为聚焦的子任务派生专门的 agent
Subagents
MCP
通过 Model Context Protocol 连接外部工具和数据源
MCP
权限
控制哪些工具自动运行，哪些需要审批
权限
会话
在多次交互中保持上下文，之后可恢复或分叉
会话
技能、命令和记忆
自动从你的项目的
.claude/
以及
~/.claude/
加载，与 Claude Code 相同
技能
、
命令
、
记忆
、
配置加载
插件
打包技能、agent、hooks 和 MCP servers，并通过本地路径加载它们
插件

## ​ 快速开始

按照
Quickstart
安装 SDK、设置你的 API key，并构建你的第一个 agent，一个能在现有代码中发现并修复 bug 的 agent。
除非事先获得批准，Anthropic 不允许第三方开发者为其产品提供 claude.ai 登录或速率限制，包括基于 Claude Agent SDK 构建的 agent。请改用
Quickstart
中描述的 API key 认证方法。

## ​ 更新日志

查看 SDK 更新、bug 修复和新功能的完整更新日志：
TypeScript SDK
：
查看 CHANGELOG.md
Python SDK
：
查看 CHANGELOG.md

## ​ 报告 bug

如果你在使用 Agent SDK 时遇到 bug 或问题：
TypeScript SDK
：
在 GitHub 上报告问题
Python SDK
：
在 GitHub 上报告问题

## ​ 品牌指南

对于集成 Claude Agent SDK 的合作伙伴，是否使用 Claude 品牌是可选的。在你的产品中提及 Claude 时：
允许：
“Claude Agent”，在 dropdown menus 中优先使用
“Claude”，当位于已标注为“Agents”的菜单中时
“{YourAgentName} Powered by Claude”，如果你已有现成的 agent 名称
不允许：
“Claude Code”或“Claude Code Agent”
模仿 Claude Code 的 Claude Code 品牌 ASCII art 或视觉元素
你的产品应保持自己的品牌，不应看起来像 Claude Code 或任何 Anthropic 产品。有关品牌合规的问题，请联系 Anthropic
销售团队
。

## ​ 许可证和条款

Claude Agent SDK 的使用受
Anthropic 商业服务条款
约束
，包括当你使用它为你自己的客户和最终用户提供的产品和服务提供支持时，除非某个特定组件或依赖项由其 LICENSE 文件中指明的不同许可证覆盖。

## ​ 后续步骤

这些资源涵盖了使用 Agent SDK 构建的更深入技术细节和示例项目。
快速开始
：构建你的第一个能够发现并修复 bug 的 agent
迁移指南
：从 Claude Code SDK 包迁移到 Agent SDK
Agent loop
：Claude 如何规划、调用工具，并决定任务何时完成
示例 agents
：用于本地开发的演示应用
TypeScript SDK
：完整的 TypeScript API 参考和示例
Python SDK
：完整的 Python API 参考和示例
Agent harness 设计
：Claude Code 团队如何使用动态工作流一次性编排多个 subagents
这个页面有帮助吗？
是
否
