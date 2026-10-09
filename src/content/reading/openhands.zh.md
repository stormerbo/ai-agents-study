<a name="readme-top"></a>

<div align="center">
  <img src="https://assets.openhands.dev/logo-whitebackground.png" alt="OpenHands logo" width="340">
  <h1 align="center" style="border-bottom: none">Agent Canvas</h1>
  <p align="center">
    <strong>面向 coding agents 和 automations 的自托管开发者控制中心。</strong>
  </p>
  <p align="center">
    在本地、远程和云端后端上运行 OpenHands、Claude Code、Codex、Gemini 或任何兼容 ACP 的 agent。
  </p>
</div>
<div align="center">
  <a href="https://github.com/OpenHands/incubator-program"><img src="https://img.shields.io/badge/status-beta-blue?style=for-the-badge" alt="Project status beta"></a>
  <a href="https://github.com/OpenHands/OpenHands/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/OpenHands/OpenHands/ci.yml?branch=main&style=for-the-badge" alt="CI status"></a>
  <a href="https://www.npmjs.com/package/@openhands/agent-canvas"><img src="https://img.shields.io/npm/v/%40openhands%2Fagent-canvas?style=for-the-badge&logo=npm" alt="npm version"></a>
  <a href="https://docs.openhands.dev/openhands/usage/agent-canvas/backends"><img src="https://img.shields.io/badge/Documentation-000?logo=googledocs&logoColor=FFE165&style=for-the-badge" alt="Documentation"></a>
  <a href="https://go.openhands.dev/slack"><img src="https://img.shields.io/badge/Slack-Join%20the%20community-611f69?logo=slack&logoColor=white&style=for-the-badge" alt="Join us on Slack"></a>
</div>
<div align="center">
  <a href="#quickstart">快速开始</a> |
  <a href="./docs/README.md">文档</a> |
  <a href="./docs/SELF_HOSTING.md">自托管</a> |
  <a href="https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents">ACP Agents</a> |
  <a href="https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt-automations">Automations</a> |
  <a href="https://go.openhands.dev/slack">Slack</a>
</div>
<p align="center">
<img src="https://assets.openhands.dev/screenshot/automation-preview.png" alt="Agent Canvas automation preview" width="100%">
</p>
<hr>

OpenHands Agent Canvas 将你的 coding agents 变成一个自托管、始终在线的工程团队。它是一个开发者控制中心，用于发起会话并将日常任务自动化——比如生成报告并发布到 Slack，或自动将 GitHub issues 拆解为 tasks。

默认情况下，它运行在你的本地机器上，但可以连接多个 “agent backends”，例如在 Docker 容器中、VM 上，或在你公司的基础设施内运行 agents。你也可以选择在 OpenHands Cloud 或 OpenHands Enterprise 基础设施上运行 agents。

Agent Canvas 开箱即用地运行开源的 OpenHands agent，但也可以使用任何第三方 agent，例如 Claude Code 和 Codex。

|                                                                                                                      |                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [**按你的方式自托管**](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/vm)                     | 在本地、Docker 中、VM 上运行 agents，或在你能够运行 agent server backend 的任何地方运行                |
| [**在不同的 backends 之间切换**](https://docs.openhands.dev/openhands/usage/agent-canvas/backends)                   | 在 local、remote 和 cloud agents 之间切换，而不会分散注意力                                            |
| [**Create automations**](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt-automations)               | 创建与 Slack、GitHub、Linear 等集成的 automations 和 workflows。可按计划运行，或响应 webhook 事件      |
| [**Integrate with the tools you use**](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt-automations) | 将你的 automations 与 Slack、GitHub、Notion 等第三方服务连接，实现 workflow 自动化                     |
| [**Bring your own model**](https://docs.openhands.dev/openhands/usage/settings/llm-settings#llm-profiles)            | 可与任何 LLM 一起使用                                                                                  |
| [**Use with any agent**](https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents)                         | 可与 OpenHands、Claude Code、Codex、Gemini，或任何支持 Agent-Client Protocol (ACP) 的 agent 一起使用。 |

如果你有疑问或反馈，请提交 GitHub issue，或加入 [Slack 中的 #proj-agent-canvas channel](https://openhands.dev/joinslack)。

## Quickstart

你可以在任何机器上安装 OpenHands 来运行 agents：在你的笔记本上、在 Mac Mini 这样的专用电脑上，
或在云端的服务器上。

运行 OpenHands 最强大的方式是在云端的服务器上。这样即使你的笔记本关机，你的 agents 也能继续运行，
并且更容易通过 Slack、GitHub 和 Datadog 等第三方服务来触发你的 agents。详见 [SELF_HOSTING.md](docs/SELF_HOSTING.md)，尤其是关于安全加固的部分。

值得注意的是，你可以在_多个不同的环境_中运行后端，并从同一个 Agent Canvas 前端在它们之间切换。例如，你可以与团队共享一个 Agent Server，用于执行代码审查和依赖更新的 agents，同时让你个人的 agents 运行在你的笔记本上。

### 方案 1：不使用 Sandbox

> [!WARNING]
> 这会在你安装所在的机器上直接运行 agent-server —— agent 将拥有对你文件系统的完整访问权限！

**前置条件**：[Node.js](https://nodejs.org/) 24 或更高版本、`uv`

```sh
npm install -g @openhands/agent-canvas
agent-canvas
```

`agent-canvas` 命令默认会启动完整的本地 stack。当你希望分开运行各部分时，也可以将其拆分：

```sh
agent-canvas --frontend-only  # 仅 static frontend + ingress
agent-canvas --backend-only   # 仅 agent server + automation backend + ingress
```

### 方案 2：使用 Docker Sandbox

**前置条件**：

- Docker：macOS/Windows 上使用 Docker Desktop，Linux 上使用 Docker Engine/Docker Desktop。
- 一个用于 `PROJECTS_PATH` 的宿主机目录，其中包含你希望 agent 访问的项目文件夹。请在启动容器前创建它。

**macOS / Linux：**

```sh
export PROJECTS_PATH="$HOME/projects"  # 包含你的项目文件夹的目录
mkdir -p "$PROJECTS_PATH" "$HOME/.openhands"

docker run -it --rm \
  -p 127.0.0.1:8000:8000 \
  -e AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true \
  -v "$HOME/.openhands:/home/openhands/.openhands" \
  -v "${PROJECTS_PATH}:/projects" \
  ghcr.io/openhands/agent-canvas:1.26.0 # x-release-please-version
```

**Windows（PowerShell / Windows Terminal）：** 等效命令见 [README.windows.md](./README.windows.md)。

agent 将能够访问 `PROJECTS_PATH` 下的任何项目。

### 方案 3：使用多个 Docker Sandbox

让每个新对话都在自己的 Docker 容器中运行，拥有自己的 Agent Server 和工具。这对于并发运行多个 agent 很有用。Canvas 和外层 Agent Server 运行在你的宿主机上，并将对话请求路由到各个容器。

**前置条件**：Node.js 24 或更高版本、`uv`，以及正在运行的 Docker Desktop（macOS）或 Docker Engine/Desktop（Linux）。启动 Canvas 的用户必须能够运行 `docker` 命令。

**macOS / Linux：**

```sh
npm install -g @openhands/agent-canvas
OH_CONVERSATION_RUNTIME=docker agent-canvas
```

打开 [http://localhost:8000](http://localhost:8000) 并开始一个新对话。已有的本地对话不会被转换。每个容器都会挂载其对话的 workspace 和持久化状态，因此 workspace 文件和对话历史在容器被替换后仍然保留。使用相同宿主 workspace 的对话仍然会共享这些文件；请选择不同的目录或 worktree，以避免编辑冲突。

此设置隔离对话执行；它不会将整个 Canvas 或自动化服务移入沙箱。对于 Windows，请参阅 [README.windows.md](./README.windows.md#option-3-with-multiple-docker-sandboxes-wsl-2)。

### 选项 4：从源码运行

> [!WARNING]
> 这会在你安装所在的机器上直接运行 agent-server —— agent 将拥有对你文件系统的完全访问权限！

**前置条件**：[Node.js](https://nodejs.org/) 24 或更高版本、`npm`、`uv`（用于通过 `uvx` 运行 agent server）

```sh
git clone https://github.com/OpenHands/OpenHands.git
cd OpenHands
npm install
npm run dev
```

---

对于 npm/源码启动器，请通过 [http://localhost:8000](http://localhost:8000) 访问 UI；对于 Docker 镜像，请通过 [http://localhost:8000/canvas](http://localhost:8000/canvas) 访问。你可以直接从 UI 中添加额外的后端。

本地（`npx` / `npm run dev`）监听器仅绑定 **loopback**（`127.0.0.1`），因此自动注入的 session key 无法从网络上的其他机器访问。若要监听所有接口，请传入 `--host 0.0.0.0`（或设置 `OH_BIND_HOST`）；此时 session key **不会**被注入，UI 将使用与 `--public` 相同的 API-key 输入界面。
Docker 监听所有容器接口，因此端口发布可以正常工作，但默认不会将 session key 注入 HTML。上面的 quickstart 显式启用了注入，同时仅将主机端口发布到 `127.0.0.1`。如果你将 Docker 发布到 LAN 或公共接口，请省略 `AGENT_CANVAS_ALLOW_LAN_SESSION_KEY`，并在 UI 中输入 API key。将 `LOCAL_BACKEND_API_KEY` 设置为一个强值，或使用 `docker exec <container> sh -c 'cat "$STATE_DIR/api-key.txt"'` 获取生成的值。对于面向互联网的安装，请遵循 [self-hosting](./docs/SELF_HOSTING.md)。

# Architecture

Agent Canvas 由 [OpenHands Agent Server](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-agent-server/openhands/agent_server) 提供支持，这是一个用于在单台机器上运行多个 agent 的 REST API。每个 Agent Server 运行在单个 host/port 上；Agent Canvas 可以连接到多个 Agent Server，并在它们之间轻松切换。

你可以在任何地方运行 Agent Server：

- 直接在你的笔记本电脑上（小心！）
- 在专用机器上，例如 Mac Mini
- 在云中的虚拟机上
- 在 OpenHands Cloud 内（我们的商业产品）

Agent Server 通常与 [Automation Server](https://github.com/OpenHands/automation) 搭配使用，后者让你可以设置按计划运行或响应事件运行的 agent。

<img width="1456" height="1258" alt="image" src="https://github.com/user-attachments/assets/cb6de6f5-ac30-4d04-a76a-b5c259f0c163" />

### Repository boundaries

Agent Canvas 是多仓库 OpenHands 系统的一部分。更改应提交到拥有该行为的仓库：

| Repository                                                                        | Responsibility                                                                                        |
| --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| [`OpenHands/OpenHands`](https://github.com/OpenHands/OpenHands)                   | Agent Canvas 前端、面向用户的控制中心、backend 选择，以及 local-stack 编排。                          |
| [`OpenHands/software-agent-sdk`](https://github.com/OpenHands/software-agent-sdk) | Python SDK、Agent Server、agents、tools、conversations、workspaces、events，以及规范化的 server API。 |
| [`OpenHands/typescript-client`](https://github.com/OpenHands/typescript-client)   | 与浏览器兼容的 TypeScript client，用于 Agent Server API。                                             |
| [`OpenHands/automation`](https://github.com/OpenHands/automation)                 | Automation 定义、调度、webhooks、运行历史与分发。                                                     |

Agent Server API 由 SDK 实现，并由 Agent Canvas 通过 TypeScript client 使用。automation 服务决定工作在何时运行，并将 conversations 分发给 Agent Server/SDK，由后者决定运行什么。关于贡献者特定的边界以及所需的 custom code-review 指南，请参见 [`AGENTS.md`](./AGENTS.md)。

## 更多文档

- [文档索引](./docs/README.md)
- [架构概览](./docs/architecture.md)
- [开发指南](./docs/DEVELOPMENT.md)
- [自托管指南](./docs/SELF_HOSTING.md)
