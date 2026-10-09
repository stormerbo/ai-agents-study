# Letta

构建具备 memory 的 stateful agents，使其能够随时间学习和改进。

Letta（原名 MemGPT）正在积极开发中。当前源代码位于 [`letta-ai/letta-code`](https://github.com/letta-ai/letta-code)，其中包含 agent harness、交互式终端 UI、App Server、channels，以及桌面端和 Web 应用所使用的 runtime。

## 快速开始

从 npm 安装 Letta：

```bash
npm install -g @letta-ai/letta-code
```

启动交互式终端 UI：

```bash
letta
```

为本地或自托管 agents 运行 App Server：

```bash
letta server
```

你也可以通过以下方式使用 Letta：

- 适用于 macOS、Windows 和 Linux 的 [desktop app](https://docs.letta.com/letta-code/desktop-app)
- 在浏览器中访问 [chat.letta.com](https://chat.letta.com)，包括在移动端
- [Slack、Telegram、Discord 和自定义 channels](https://docs.letta.com/letta-code/channels)
- [Letta Agent SDK](https://docs.letta.com/letta-agent-sdk/overview)，用于将 agents 构建到 TypeScript 应用中
- [Letta Cloud](https://github.com/letta-ai/letta-code#letta-cloud)，用于让 agent memory、identity 和 conversations 在不同计算机之间保持可用

有关当前的安装、开发和部署说明，请参阅 [Letta 文档](https://docs.letta.com)。

## 历史源代码

[`archive`](https://github.com/letta-ai/letta/tree/archive) 分支包含已停用的 Letta V1 API server。现有 tags 和 releases 仍可用于复现，但活跃项目应使用[当前源代码](https://github.com/letta-ai/letta-code)。
