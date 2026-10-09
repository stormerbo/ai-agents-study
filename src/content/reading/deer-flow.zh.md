# 🦌 DeerFlow - 2.0

English | [中文](./README_zh.md) | [日本語](./README_ja.md) | [Français](./README_fr.md) | [Русский](./README_ru.md) | [Português](./README_pt.md)

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](./backend/pyproject.toml)
[![Node.js](https://img.shields.io/badge/Node.js-22%2B-339933?logo=node.js&logoColor=white)](./Makefile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

<a href="https://trendshift.io/repositories/14699" target="_blank"><img src="https://trendshift.io/api/badge/repositories/14699" alt="bytedance%2Fdeer-flow | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

> 2026 年 2 月 28 日，随着 2.0 版本的发布，DeerFlow 登上了 GitHub Trending 的 🏆 #1 宝座。万分感谢我们了不起的社区——是你们成就了这一切！💪🔥

DeerFlow（**D**eep **E**xploration and **E**fficient **R**esearch **Flow**）是一个开源的 **super agent harness**，它编排 **sub-agents**、**memory** 和 **sandboxes** 来完成几乎任何事情——由 **extensible skills** 驱动。

https://github.com/user-attachments/assets/a8bcadc4-e040-4cf2-8fda-dd768b999c18

> [!NOTE]
> **DeerFlow 2.0 是一次从零开始的重写。** 它与 v1 不共享任何代码。如果你在寻找最初的 Deep Research 框架，它维护在 [`1.x` 分支](https://github.com/bytedance/deer-flow/tree/main-1.x)上——仍然欢迎向那里贡献。活跃开发已转移到 2.0。

## 官方网站

在我们的[**官方网站**](https://deerflow.tech)上了解更多并查看**真实演示**。
落地页案例研究以允许列表、只读展示的形式打开，无需登录。

## 姊妹项目

<img width="446" height="280" alt="image" align="middle" src="https://github.com/user-attachments/assets/077edef4-d560-41af-bb0d-d0a5f14fcc20" />
- [**LLM Space**](https://github.com/deer-flow/llm-space) - 认识一下 DeerFlow 背后的秘密武器 —— 一款桌面工具，可用来快速原型化 agent 想法、检查每个 harness 步骤、回放失败案例，并对性能进行基准测试。

## 字节跳动火山引擎 Coding Plan

- 我们强烈建议使用 Doubao-Seed-2.0-Code、DeepSeek v3.2 和 Kimi 2.5 来运行 DeerFlow
- [了解更多](https://www.byteplus.com/en/activity/codingplan?utm_campaign=deer_flow&utm_content=deer_flow&utm_medium=devrel&utm_source=OWO&utm_term=deer_flow)
- [中国大陆地区的开发者请点击这里](https://www.volcengine.com/activity/codingplan?utm_campaign=deer_flow&utm_content=deer_flow&utm_medium=devrel&utm_source=OWO&utm_term=deer_flow)

## InfoQuest

InfoQuest 的 reader、web search 和 image search 使用 30 秒的 HTTP 连接/读取空闲超时。爬取的 `timeout` 与 `navigation_timeout` 设置仍是独立的服务端选项；它们不控制本地 HTTP 超时。

DeerFlow 新集成了 BytePlus 独立开发的智能搜索与爬取工具集 —— [InfoQuest（支持免费在线体验）](https://docs.byteplus.com/en/docs/InfoQuest/What_is_Info_Quest)

<a href="https://docs.byteplus.com/en/docs/InfoQuest/What_is_Info_Quest" target="_blank">
  <img
    src="https://sf16-sg.tiktokcdn.com/obj/eden-sg/hubseh7bsbps/20251208-160108.png"   alt="InfoQuest_banner"
  />
</a>

---

## 目录

- [🦌 DeerFlow - 2.0](#-deerflow---20)
  - [官方网站](#official-website)
  - [姊妹项目](#sister-projects)
  - [字节跳动火山引擎 Coding Plan](#coding-plan-from-bytedance-volcengine)
  - [InfoQuest](#infoquest)
  - [目录](#table-of-contents)
  - [一行式 agent 设置](#one-line-agent-setup)
  - [快速开始](#quick-start)
    - [配置](#configuration)
    - [运行应用](#running-the-application)
      - [部署规模](#deployment-sizing)
      - [选项 1：Docker（推荐）](#option-1-docker-recommended)
      - [升级现有 checkout](#upgrading-an-existing-checkout)
      - [选项 2：本地开发](#option-2-local-development)
      - [启动模式](#startup-modes)
      - [LangGraph Studio（可选）](#langgraph-studio-optional)
      - [Docker 生产部署](#docker-production-deployment)
    - [高级](#advanced)
      - [Sandbox 模式](#sandbox-mode)
      - [MCP Server](#mcp-server)
      - [IM 渠道](#im-channels)
      - [请求 Trace 关联](#request-trace-correlation)
      - [LangSmith Tracing](#langsmith-tracing)
      - [Langfuse Tracing](#langfuse-tracing)
      - [Monocle Tracing](#monocle-tracing)
      - [使用多个 Provider](#using-multiple-providers)
      - [Existing-Run 流操作](#existing-run-stream-actions)
      - [Personal Access Token](#personal-access-tokens)
  - [从 Deep Research 到 Super Agent Harness](#from-deep-research-to-super-agent-harness)
  - [核心特性](#core-features)
    - [Skills \& Tools](#skills--tools)
      - [导出自定义 Skills](#exporting-custom-skills)
      - [Claude Code 集成](#claude-code-integration)
    - [私有知识检索（RAGFlow）](#private-knowledge-retrieval-ragflow)
    - [聊天归档](#chat-archive)
    - [会话目标](#session-goals)
    - [手动上下文压缩](#manual-context-compaction)
    - [Sub-Agent](#sub-agents)
    - [Sandbox 与文件系统](#sandbox--file-system)
    - [Agentic 浏览器控制](#agentic-browser-control)
    - [上下文工程](#context-engineering)
    - [阅读被引用的对话](#reading-a-referenced-conversation)
    - [当前任务笔记](#current-task-notes)
    - [长期记忆](#long-term-memory)
  - [推荐模型](#recommended-models)
  - [内嵌 Python Client](#embedded-python-client)
  - [项目](#projects)
    - [项目说明](#project-instructions)
    - [文档架](#document-shelf)
    - [归档读取语义](#archive-read-semantics)
- [Trash](#trash)
  - [Scheduled Tasks](#scheduled-tasks)
    - [Preview cron occurrences through the API](#preview-cron-occurrences-through-the-api)
    - [Upgrade Notes](#upgrade-notes)
  - [Terminal Workbench (TUI)](#terminal-workbench-tui)
  - [Documentation](#documentation)
  - [⚠️ Security Notice](#️-security-notice)
    - [Improper Deployment May Introduce Security Risks](#improper-deployment-may-introduce-security-risks)
    - [Gateway Admin Is Equivalent to Code Execution](#gateway-admin-is-equivalent-to-code-execution)
    - [External Chat Message Roles](#external-chat-message-roles)
    - [Deployment Defaults](#deployment-defaults)
    - [Security Recommendations](#security-recommendations)
  - [Contributing](#contributing)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)
    - [Key Contributors](#key-contributors)
  - [Star History](#star-history)

## 一行命令设置 Agent

如果你使用 Claude Code、Codex、Cursor、Windsurf 或其他 coding agent，可以用一句话把设置说明交给它：

```text
Help me clone DeerFlow if needed, then bootstrap it for local development by following https://raw.githubusercontent.com/bytedance/deer-flow/main/Install.md
```

该 prompt 面向 coding agent。它告诉 agent 如有需要则 clone 仓库，在可用时选择 Docker，并在结束时给出确切的下一步命令以及用户仍需提供的任何缺失配置。

## 快速开始

### Configuration

运维人员可以通过字面量的 prepend/append 配置扩展 lead-agent、subagent 和 DeerMem 抽取 prompt，而无需编辑源模板。参见 [prompt overlays](backend/docs/CONFIGURATION.md#prompt-overlays)。

可选的按模型 [`request_admission`](backend/docs/CONFIGURATION.md#model-request-admission) 会对请求进行限速，以帮助保持在 provider 的每分钟请求限制内。它默认禁用；参见链接指南以启用它。

对于 Google 官方的 Gemini OpenAI-compatible endpoint，请使用
[Gemini reasoning profile](backend/docs/CONFIGURATION.md#gemini-via-googles-openai-compatible-endpoint)。

关于 MindIE XML tool calls，请参阅
[argument parsing and newline compatibility guide](backend/docs/CONFIGURATION.md#mindie-xml-tool-arguments)。
同步流和异步流均保留这一兼容性：启用 tool 的流会模拟来自非流式响应的 chunks，而未启用 tool 的流则保持原生方式。

1. **克隆 DeerFlow 仓库**

   ```bash
   git clone https://github.com/bytedance/deer-flow.git
   cd deer-flow
   ```

2. **运行 setup 向导**

   在项目根目录（`deer-flow/`）下运行：

   ```bash
   make setup
   ```

   这会启动一个交互式向导，引导你选择 LLM provider、可选的 web search，以及执行/安全相关偏好设置，例如 sandbox mode、bash access 和 file-write tools。它会生成一个最小的 `config.yaml`，并将你的 keys 写入 `.env`。大约需要 2 分钟。

   该向导还允许你配置可选的 web search provider，或者暂时跳过。

   Jina、Browserless 和 InfoQuest 的 web fetch 会使用所请求的页面 URL（或可用的 HTML base URL）来解析相对链接和图片源，因此返回的 Markdown 包含完整的目标地址。链接解析会保留周围的 HTML 源码，包括格式错误页面的格式。

   Jina fetch 支持通过 tool 配置中的 `max_retries`（默认 `0`）和 `retry_budget_seconds`（默认 `30`）选择启用有界重试。有效的 `Retry-After` 提示会为 HTTP 429/503 设置最小等待时间；429 若没有有效提示则保持终止状态。无法适配剩余预算的提示会停止重试。本地 backoff 仍为随机化。重试可能增加上游请求量与成本；参见 [Jina fetch retries](backend/docs/CONFIGURATION.md#jina-fetch-retries)。
   Jina 还接受一个需主动启用的 `max_response_bytes` 工具设置（正整数；省略/null 会禁用它）。它会在提取前停止过大的已解码响应，不会出现部分成功或重试。这使 4096 字符的输出上限保持不变，并且不会限制 HTTPX 解压器的分配或链路带宽；参见 [响应预算](backend/docs/CONFIGURATION.md#jina-response-byte-budget)。

随时运行 `make doctor` 来验证你的设置并获取可操作的修复提示。如果你要就本地设置或运行时问题提交 GitHub issue，请运行 `make support-bundle`。该命令会打印报告者的后续步骤，写入一个 `*-issue-summary.md` 文件以便粘贴到 issue 中，写入一个用于 AI 辅助提交 issue 的 `*-issue-draft.md` 文件，并在 `.deer-flow/support-bundles/` 下生成一个可选的证据 zip。如果由 AI 助手提交该 issue，请从草稿开始，并替换每个 REQUIRED 占位符，而不是编造缺失的事实。仅当维护者要求，或仅凭摘要不够时，才附加该 zip。维护者和 AI triage 工具可以从 `triage.json` 开始；该 bundle 仅包含已脱敏的诊断信息和文件清单，不包括 `.env`、原始对话消息或用户文件内容。子进程诊断信息以 UTF-8 捕获，Python 辅助程序即使在非 UTF-8 主机上也会输出 UTF-8，并转义无法编码的字符。线程清单遵循本地启动器的运行时路径：checkout 的 `.env` 值会覆盖 shell 导出，而仅设置项目根目录覆盖时仍会优先使用 `backend/.deer-flow`。像 `DEER_FLOW_HOME="$PWD/backend/.deer-flow"` 这样的简单变量引用会将 checkout 用作 `PWD`；单引号引用保持字面量。对于使用 `backend/.env` 或 `DEER_FLOW_ENV_FILE` 的独立 Gateway 启动，在收集 bundle 时导出有效的 `DEER_FLOW_HOME`，并确保 checkout 的 `.env` 不会覆盖它。
Doctor 的内部工具探测同样会以替换方式解码 UTF-8 中的无效字节，以便其余诊断输出仍可获取。

当请求 thread manifest 时，非空的 `DEER_FLOW_HOME` 会选择运行时数据目录，而不是过期的 checkout 数据。外部数据路径在报告中显示为 `{DEER_FLOW_HOME}`；文件内容仍被排除在外。运行时路径设置同样来自 checkout 的 `.env`，其中 shell 导出具有更高优先级。相对路径按 checkout 解析，与 `make dev` 中一致。若未显式指定 home，则已配置的 `DEER_FLOW_PROJECT_ROOT` 会选择其 `.deer-flow` 目录；外部路径在报告中使用该变量名。

> **高级 / 手动配置**：如果你更倾向于直接编辑 `config.yaml`，请改为运行 `make config` 来复制完整模板。可选的依赖自动检测接受带或不带字节顺序标记（BOM）的 UTF-8 配置文件。完整参考请见 `config.example.yaml`，其中包括 CLI 支持的 provider（Codex CLI、Claude Code OAuth）、OpenRouter、Responses API、subagent 运行时上限（如 `subagents.max_total_per_run`）等。

可选的按模型定价必须在所有已定价模型中使用同一种货币。当货币混用时，DeerFlow 会禁用 Console 成本估算，而不是呈现无效的汇总结果。

管理员还可以打开 **Settings → Models**，在不编辑 `config.yaml` 的情况下添加、编辑、测试以及启用/禁用共享的 OpenAI 兼容 Chat Completions 模型。输入唯一名称、base URL、model ID 以及可选的 API key；保存后会刷新 chat model 列表。连接测试会发送一个简短的流式 tool-call 请求，可能会产生 provider 费用。它不会保存草稿，也不会验证图像支持；请根据 provider 文档设置图像支持和 token 限制。位于 `https://api.deepseek.com` 的官方 DeepSeek 模型，或
`https://api.deepseek.com/v1`（默认 HTTPS 端口）会自动使用 DeerFlow 的 DeepSeek adapter，在工具调用之间保留 reasoning content，并遵守 output token 限制。Chat 使用所选的 thinking mode；连接测试会临时禁用 thinking，因为 DeepSeek 在 thinking mode 下拒绝强制工具选择。该测试检查的是 streaming tool 连通性，而非每一个 agent workflow 或 thinking-mode 行为。已有的已保存 DeepSeek profile 无需重新输入凭据即可获得此 adapter。针对第三方 proxy 的 DeepSeek 专属设置、其他 native adapter 以及高级 reasoning 设置仍通过 YAML 配置。

DeepSeek 回归测试随常规 backend 套件离线运行。要显式验证真实 provider，请在环境中设置 `DEEPSEEK_TEST_API_KEY`，并从 `backend/` 运行：

```bash
DEER_FLOW_RUN_LIVE_TESTS=1 uv run --no-sync pytest tests/test_managed_deepseek_live.py -q
```

这些选择性启用的测试会向 DeepSeek 发送短请求，可能产生费用；它们使用临时状态，绝不将凭据保存到部署 catalog，并且在 CI 中会被跳过。`DEEPSEEK_TEST_MODEL` 可选择不同的 DeepSeek model ID（默认：`deepseek-flash`）。同样的测试可在未修复和已修复的修订版本上运行；成功始终是预期结果。

YAML model 在此页面中保持只读，并在名称冲突时优先。Managed model 追加在 YAML model 之后；编辑应用于新的配置快照，而正在运行的 run 保留其现有快照。禁用某个 model 会将其从未来的选择/解析中移除，因此请在禁用前更新任何显式引用它的 custom-agent 或 scheduled task 定义。Managed model 由部署共享，而非个人 API-key profile，并且仍受现有 model authorization policy 约束。

加密 catalog 和生成的本地加密密钥存储在
`$DEER_FLOW_HOME/managed-models/`（默认 `.deer-flow/managed-models/`）。持久化并备份**整个目录**，限制文件系统访问，并在应使用同一 catalog 的 Gateway workers/replicas 之间共享它。本地 key 受文件系统权限保护；加密无法防止能同时读取这两个文件的人。丢失 key 需要恢复备份。如果 catalog 无法解密，读取和写入会失败，而不是替换它。此存储独立于 SQL backend，并可与只读 YAML mounts 一起工作。

当配置了多个模型时，打开任一模型选择器，并使用模型旁的星标将其收藏。收藏会首先出现在主聊天和 Side Chat 选择器中，而不会更改任一聊天已选或默认的模型。它们会为已登录用户存储在当前浏览器中，因此不会同步到另一浏览器或设备，也不需要启动设置。紧凑收藏选择器有意省略搜索，仅在两行模型列表中添加收藏排序。

<details>
<summary>手动模型配置示例</summary>

```yaml
models:
  - name: gpt-4o
    display_name: GPT-4o
    use: langchain_openai:ChatOpenAI
    model: gpt-4o
    api_key: $OPENAI_API_KEY

  - name: openrouter-gemini-2.5-flash
    display_name: Gemini 2.5 Flash (OpenRouter)
    use: langchain_openai:ChatOpenAI
    model: google/gemini-2.5-flash-preview
    api_key: $OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1

  - name: opper-claude-sonnet-4-6
    display_name: Claude Sonnet 4.6 (Opper)
    use: langchain_openai:ChatOpenAI
    model: claude-sonnet-4-6
    api_key: $OPPER_API_KEY
    base_url: https://api.opper.ai/v3/compat

  - name: gpt-5-responses
    display_name: GPT-5 (Responses API)
    use: langchain_openai:ChatOpenAI
    model: gpt-5
       api_key: $OPENAI_API_KEY
       use_responses_api: true
       output_version: responses/v1

     - name: qwen3-32b-vllm
       display_name: Qwen3 32B (vLLM)
       use: deerflow.models.vllm_provider:VllmChatModel
       model: Qwen/Qwen3-32B
       api_key: $VLLM_API_KEY
       base_url: http://localhost:8000/v1
       supports_thinking: true
       when_thinking_enabled:
         extra_body:
           chat_template_kwargs:
             enable_thinking: true
```

OpenRouter 以及类似的 OpenAI 兼容网关应使用 `langchain_openai:ChatOpenAI` 并配合 `base_url` 进行配置。如果你更偏好特定 provider 的环境变量名，请将 `api_key` 显式指向该变量（例如 `api_key: $OPENROUTER_API_KEY`）。

`write_file` 工具的 output-budget 提示使用当前活动模型的有效 `max_tokens`。缺失或不可用的限制，包括 YAML `.inf`、`-.inf`、`.nan`，以及对于字符估算而言过大的值，会省略此提示，而不会导致工具组装失败；特定 provider 的模型验证仍然适用。

若要通过 `/v1/responses` 路由 OpenAI 模型，请继续使用 `langchain_openai:ChatOpenAI`，并将 `use_responses_api: true` 与 `output_version: responses/v1` 一起设置。
对于 provider 契约与 DeerFlow 通用 thinking/effort 假设不同的模型，可以声明一个按模型配置、取值为映射的 `reasoning:` 块（thinking 为 `unsupported`/`optional`/`required`，可接受的 effort 取值及其别名与默认值，payload 方言，以及推理历史要求）。设置向导中的 Z.AI GLM-5.3-Flash profile 就使用了它：每次前台和后台调用都保持开启 thinking，effort 选择器则提供该模型自己的 `low`/`high`/`max` 级别。Ollama 现有的布尔型 `reasoning: true` 仍然是原生 provider 设置，并会被转发给 ChatOllama。将 profile 迁移到自定义 effort `path` 时，要从 profile 和 thinking 模板中移除所有旧的 `reasoning_effort` 设置；配置校验会拒绝这个残留的 key。切换到不声明该 effort 的 legacy 模型时，聊天 UI 会丢弃已记住的 provider 专属 effort。不带该块的 profile 保持其现有的 provider 行为。结构形式及等价的手动配置参见 `config.example.yaml`。
对于 vLLM 0.19.0，使用 `deerflow.models.vllm_provider:VllmChatModel`。对于 Qwen 风格的 reasoning 模型，DeerFlow 通过 `extra_body.chat_template_kwargs.enable_thinking` 来切换 reasoning，并在多轮 tool-call 对话中保留 vLLM 非标准的 `reasoning` 字段。旧式的 `thinking` 配置会自动规范化以保持向后兼容，且不会修改模型默认值或调用方拥有的 `extra_body` 字典；被复用的字典可能会在请求之间改变旧式开关。如果 endpoint 在每个 streaming chunk 上都报告累计 usage 快照，请设置 `cumulative_stream_usage: true`，这样 DeerFlow 会将这些快照转换为每个 chunk 的增量；该选项默认禁用，并且在无法获得稳定的 completion id 时不会改变 usage。Reasoning 模型还可能要求服务端以 `--reasoning-parser ...` 启动。如果你的本地 vLLM 部署接受任意非空 API key，你仍然可以将 `VLLM_API_KEY` 设置为一个占位值。

当为使用
`deerflow.models.claude_provider:ClaudeChatModel` 配置的模型启用 prompt caching 时，DeerFlow 会保留 thinking
和 redacted-thinking 历史记录，而不会将 cache breakpoints 直接放在
这些块上。Extended-thinking 的 tool follow-up 可以继续使用 prompt caching。

基于 CLI 的 provider 示例：

```yaml
models:
  - name: gpt-5.4
    display_name: GPT-5.4 (Codex CLI)
    use: deerflow.models.openai_codex_provider:CodexChatModel
    model: gpt-5.4
    supports_thinking: true
    supports_reasoning_effort: true

  - name: claude-sonnet-4.6
    display_name: Claude Sonnet 4.6 (Claude Code OAuth)
    use: deerflow.models.claude_provider:ClaudeChatModel
    model: claude-sonnet-4-6
    max_tokens: 4096
    supports_thinking: true
```

`ClaudeChatModel` 在 `auto_thinking_budget: true`（默认值）时会对手动 extended-thinking 预算进行规范化。省略或为 null 的 budget 会获得 `max_tokens` 的 80%，最小为 1024 tokens。显式指定的 budget 必须是至少为 1024 的整数，并且对于普通 thinking，必须严格小于 `max_tokens`；输出限制为 1024 或更小时会在本地失败。对于受支持的手动 interleaved thinking，请配置 tools 和 `betas: ["interleaved-thinking-2025-05-14"]`：thinking budget 可以等于或超过正的输出限制。受支持的模型见 [Anthropic 的 interleaved-thinking 规则](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#interleaved-thinking-in-manual-mode)。`auto_thinking_budget: false` 会绕过此规范化和验证；disabled thinking 和 adaptive thinking 保持不变。

- Codex CLI 读取 `~/.codex/auth.json`
- Codex function tools 在包装或扁平字典定义中保留显式的 `strict: true` 或 `strict: false`。缺失或为 null 的设置则保持 provider 默认值。`bind_tools` 对字典和 `BaseTool` schema 应用相同的转换。
- 当 token usage 为 null、省略或为空时，已完成的 Codex responses 仍然返回其文本和 tool calls；usage 元数据仍不可用。
- Codex model provider 返回已完成的 responses，而不等待 SSE 连接关闭。失败或不完整的 responses 会报告 provider 的 error 或 reason；部分输出不会作为成功答案返回。非对象类型的 error 详情会以文本形式报告。
- Claude Code 接受 `CLAUDE_CODE_OAUTH_TOKEN`、`ANTHROPIC_AUTH_TOKEN`、`CLAUDE_CODE_CREDENTIALS_PATH` 或 `~/.claude/.credentials.json`
- `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR` 接受 UTF-8 token 传递，并在同一进程内的后续 model 实例中复用它。无法解码的传递会被跳过，以便 Claude Code 仍能尝试其 override 或默认 credentials 文件。
- CLI 凭证 JSON 文件接受带或不带 BOM 的 UTF-8 编码，与主机 locale 无关。`make doctor` 在检查 CLI 认证时接受相同的文件。无效的文本编码被视为不可读的来源；在无效覆盖后，Claude Code 仍可尝试其默认文件。
- ACP agent 条目与模型提供商分开——如果你配置 `acp_agents.codex`，请将其指向一个 Codex ACP 适配器，例如 `npx -y @zed-industries/codex-acp`
- 每个 ACP agent 的 `timeout_seconds`（默认值：1800）是一个共享预算，用于初始化、会话创建和 prompt，从子进程启动后开始计时。超时后，DeerFlow 会中止调用并在返回错误之前关闭子进程。工作区/MCP 准备和子进程清理不在此预算内。SDK 在此截止时间到期前引发的 `TimeoutError` 保留其自身的错误消息。
- MiniMax Code 直接支持 ACP。安装并认证它，然后将其添加为 ACP agent：

```bash
npm install --global @minimax-ai/code
mcode login
```

```yaml
acp_agents:
  mcode:
    command: mcode
    args: ['acp']
    description: MiniMax Code for implementation, refactoring, debugging, and repository tasks
    auto_approve_permissions: false
```

`mcode` 必须在 Gateway 进程的 `PATH` 上；仅在 Docker 主机上安装它不会使其在 Gateway 容器内可用。DeerFlow 通过 `invoke_acp_agent` 在每线程 ACP 工作区中调用它，并转发已启用的 MCP 服务器。对于不受信任的任务，保持 `auto_approve_permissions: false`；仅当 mcode 必须编辑文件或运行命令且你信任该任务时才启用它。

- 在 macOS 上，如果需要，显式导出 Claude Code 认证：

```bash
eval "$(python3 scripts/export_claude_code_oauth.py --print-export)"
```

exporter 在打印 token、发出 shell export 或写入 credentials 文件之前，会拒绝格式错误的 credential 容器以及非字符串或空白的 access token。有效的 token 会原样导出，而文件导出会保留完整的 credential 容器。

API key 也可以在 `.env` 中手动设置（推荐），或在你的 shell 中导出：

```bash
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
```

   </details>

若要显式指定后端的 dotenv 文件，请在启动前导出 `DEER_FLOW_ENV_FILE`，如有需要可同时导出 `DEER_FLOW_CONFIG_PATH`。例如，在 `backend/` 目录下执行：

```bash
DEER_FLOW_ENV_FILE=/srv/deer-flow/stage.env DEER_FLOW_CONFIG_PATH=/srv/deer-flow/stage.yaml make gateway
```

相对的 dotenv 路径以后端进程的工作目录为基准；绝对路径则不受该目录影响。已存在的进程变量优先。未设置该选择器时，保留默认的 dotenv 发现机制；若指定的路径为空、不存在、不是文件或不可读，则启动失败。当 `PYTHON_DOTENV_DISABLED` 禁用 dotenv 加载时，显式选择同样会失败。更改文件后需重启。此选项仅选择后端的 dotenv 输入：shell 启动器、Docker Compose 和前端各自保留自己的环境加载方式。它们已经导出的值优先。它不会选择 `ENV` profile，也不会隔离数据库、存储或租户。参见 [backend dotenv selection](backend/docs/CONFIGURATION.md#backend-dotenv-selection)。

### 运行应用程序

#### 部署规格选型

在选择如何运行 DeerFlow 时，可将下表作为实用的起点：

| 部署目标                                 | 起点配置                          | 推荐配置           | 说明                                                                                         |
| ---------------------------------------- | --------------------------------- | ------------------ | -------------------------------------------------------------------------------------------- |
| 本地评估 / `make dev`                    | 4 vCPU、8 GB RAM、20 GB 可用 SSD  | 8 vCPU、16 GB RAM  | 适合一名开发者或一个使用托管模型 API 的轻量会话。`2 vCPU / 4 GB` 通常不够用。                |
| Docker development / `make docker-start` | 4 vCPU, 8 GB RAM, 25 GB free SSD  | 8 vCPU, 16 GB RAM  | Image builds, bind mounts, and sandbox containers need more headroom than pure local dev.    |
| Long-running server / `make up`          | 8 vCPU, 16 GB RAM, 40 GB free SSD | 16 vCPU, 32 GB RAM | Preferred for shared use, multi-agent runs, report generation, or heavier sandbox workloads. |

- 这些数字仅涵盖 DeerFlow 本身。如果你还托管本地 LLM，请单独为该服务规划规格。
- Linux 加 Docker 是持久化服务器的推荐部署目标。macOS 和 Windows 最好作为开发或评估环境使用。
- 如果 CPU 或内存使用率持续处于高位，先减少并发运行数，再升级到下一个规格档位。

#### 选项 1：Docker（推荐）

需要 Docker Desktop / Docker Engine 以及 **Docker Compose v2.24+**
（`docker compose version`）。较旧的 Compose 客户端无法解析
`docker/docker-compose.yaml` 和 `docker/docker-compose-dev.yaml` 中可选的
`env_file` 语法。

**开发环境**（热重载、源码挂载）：

```bash
make docker-init    # 拉取 sandbox 镜像（仅需一次，或镜像更新时执行）
make docker-start   # 启动服务（从 config.yaml 自动检测 sandbox 模式）
make docker-logs    # 查看日志
```

只有当 `config.yaml` 使用 provisioner 模式（`sandbox.use: deerflow.community.aio_sandbox:AioSandboxProvider` 且配置了 `provisioner_url`）时，`make docker-start` 才会启动 `provisioner`。

Docker 构建默认使用上游 `uv` registry。如果你在受限网络中需要更快的镜像源，请在运行 `make docker-init` 或 `make docker-start` 之前导出 `UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple` 和 `NPM_REGISTRY=https://registry.npmmirror.com`。

本地 AIO sandbox 控制流量始终直连：loopback/私有地址、
单标签集群主机名以及 Docker/Podman 内部主机名不会继承
`HTTP_PROXY` 或 `HTTPS_PROXY`。外部 sandbox FQDN 和公网 IP 仍然
遵循环境代理设置。
后端进程在下次访问配置时会自动获取 `config.yaml` 的更改，因此在开发期间，模型元数据更新不需要手动重启。

Gateway 运行在 API 请求未提供 `recursion_limit` 时使用 `config.yaml` 中的顶层 `recursion_limit`。默认值为 `100`；有效的按请求值优先，并且 `max_recursion_limit`（默认 `1000`）对两者设上限。更改会在下一次运行时生效，无需重启 Gateway。此顶层设置适用于 Gateway API 运行；IM 通道和嵌入式 `DeerFlowClient` 运行保留它们自己的默认值和按调用覆盖路径。
checkpoint 存储设置 `database.checkpoint_channel_mode` 和 `database.checkpoint_delta.snapshot_frequency`（默认 `10`）是例外：两者在进程首次构建 agent 时冻结（包括通过 `DeerFlowClient`），并且需要重启进程才能安全更改。

可选的 `database.checkpoint_cache` 部分（仅 delta channel 模式）缓存物化的 checkpoint 历史：`type` 为 `memory`（默认）或 `redis`，且 `max_entries: 0` 禁用缓存。`redis` 后端仅限 Gateway/异步；同步 TUI/嵌入式路径仅支持 `memory`。缓存仅用于性能——禁用它时结果相同——因此它永远不会被冻结，并且共享同一个 checkpoint 数据库的 worker 可以安全地运行不同的缓存设置。

> [!TIP]
> 在 Linux 上，如果基于 Docker 的命令失败并显示 `permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock`，请将你的用户添加到 `docker` 组，并在重试前重新登录。完整修复方法请参阅 [CONTRIBUTING.md](CONTRIBUTING.md#linux-docker-daemon-permission-denied)。

**Production**（本地构建镜像，挂载运行时配置和数据）：

```bash
make up     # 构建镜像并启动所有生产服务
make down   # 停止并移除容器
```

访问：http://localhost:2026

`make up` 在报告成功之前会等待 Gateway 的 `/health` 端点。
如果 Gateway 在 startup window 内未变为健康状态，部署会以非零状态退出，并打印容器状态以及最近的 Gateway 日志。生产镜像从其已构建的环境中启动，并且绝不在容器启动时解析或安装 Python 依赖。

如果 `make up` 在 `make docker-start` 之后报告 runtime home 不可写或持久化的 secret 不可读，请运行打印出的 `sudo chown -R <uid>:<gid> '<home>'` 恢复命令并重试。该检查会遵循来自 shell 或 `.env` 的 secret 覆盖，接受可读的只读 secret 文件，并保持 `make down` 可用，而无需读取或生成 secret。

对于持久化部署，将 `database.backend` 配置为 `sqlite` 或 `postgres`。所选的 backend 由 LangGraph checkpointer、LangGraph Store 和 DeerFlow 应用程序数据共享。已弃用的 `checkpointer` 部分（如果存在）会为了向后兼容而覆盖前两项。

Gateway 启动会自动修复影响某些现有数据库的缺失的 run-change schema (#5516)。该修复会保留 run 历史和现有的 change 位置；将修复降级到其前身也会保留该版本所需的 schema 和位置。

对于轻量级单进程事件持久化，`run_events.backend: jsonl` 会保持 Unicode 消息内容完整，包括行分隔符和段落分隔符。现有的有效 JSONL 记录保持可读，无需重写文件。

对于每次调用的 usage 审计，带有已填充 usage 的即时 LLM 响应 replay 会同时更新嵌套 usage 和顶层 token 计数器，即使初始 usage 缺失或为零。原始请求、模型和状态元数据保持不变；已刷新的事件不会被重写。请参阅 [run event contract](contracts/run_event_stream_contract.json)。
统一 nginx endpoint 默认同源，且不会发出浏览器 CORS 头。如果你运行的是分离源（split-origin）或端口转发的浏览器客户端，请将 `GATEWAY_CORS_ORIGINS` 设置为以逗号分隔的精确 origin，例如 `http://localhost:3000`；此后 Gateway 会应用 CORS allowlist 以及相匹配的 CSRF origin 检查。

启用细粒度授权后，Live Browser 连接除要求拥有该 thread 之外，还要求具备 `threads:write` 权限，即使只是查看帧也是如此：同一条连接可以控制浏览器。权限检查在连接时执行。升级后请重启 Gateway，以断开由旧代码准入的会话。

浏览器登录使用 `HttpOnly` session cookie。登录页面提供 "keep me signed in" 选项，当请求为 HTTPS（包括可信的 `X-Forwarded-Proto: https`）或 localhost HTTP 时，该选项会延长浏览器会话。localhost 例外使用直接请求的 `Host`，并忽略转发的 host 头。公开 HTTP 部署（包括许多临时 sandbox URL）默认回退为 session cookie。DeerFlow 从不在浏览器存储中保存密码；UI 可能仅记住 email 地址。

DeerFlow 仍使用 `Forwarded` / `X-Forwarded-*` 头来还原代理背后面向浏览器的 scheme 和 origin。捆绑的 nginx 会设置 `X-Forwarded-Proto`，但会保留上游的 HTTPS 值，并且不会覆盖每一个转发的头。请配置外层可信代理，在流量到达 DeerFlow 之前替换或剥离客户端提供的转发头。

> [!IMPORTANT]
> Gateway 仍在进程内持有活跃的 run 任务，因此生产环境默认使用单个 Gateway worker（`GATEWAY_WORKERS=1`）。多 worker 部署需要 Postgres、Redis stream bridge（`stream_bridge.type: redis`）、`run_ownership.heartbeat_enabled: true` 以及 `run_events.backend: db`；进程本地内存/JSONL 事件存储无法跨 worker 强制实现单例送达回执。Kubernetes 副本每个 Pod 运行一个 worker，而 worker 数量无法感知这一点：通过 `deployment.multi_instance: true`（或 `DEER_FLOW_MULTI_INSTANCE=1`，部署工具如 Helm chart 可根据其副本数设置该变量）来声明，使启动门禁强制执行相同的前置条件，而不是保持惰性。该 bridge 在多个 worker 之间共享 SSE 送达以及有界的 `Last-Event-ID` 重放。当有效的重连游标已被修剪，或者一个已建立空流等待的订阅者在其首次送达之前落后时，Memory 和 Redis 会发出机器可读的 SSE `gap` 事件，而不是静默返回部分重放；Web UI 会重新加载持久化的 thread/event 状态，并从保留的尾部恢复。租约协调会将来自已死亡 worker 的 run 标记为错误，持久化其送达回执，发布终止流标记，安排保留流清理，并更新受影响的 thread 状态。SSE、`/wait` 和内部流消费者使用 `stream_bridge.heartbeat_interval_seconds`（默认 `15`）进行空闲存活检查；更改它需要重启 Gateway。格式错误的 Redis 重连 ID 会实时跟随新事件，而不是重放保留缓冲区，滚动保留缓冲 TTL（`stream_ttl_seconds`）仍然是清理安全网，而不是 run 超时。`POST /api/v1/auth/login/local` 的登录失败计数器和锁定（`auth.local.max_login_attempts` / `lockout_seconds`）在应用数据库为 SQLite 或 Postgres 时保存在共享的 `login_throttle` 表中（`auth.local.throttle_storage: auto`，默认值），因此每个副本都对每个客户端 IP 强制执行一次锁定；`memory` 保留历史上的每进程计数器，在 N 个副本下这会给予攻击者 N × `max_login_attempts` 次猜测，并记录启动警告。IM 通道状态和其他进程本地服务仍然需要它们自己的多 worker 协调。
> 在单进程 JSONL 部署中，取消一个已受理的 event-store mutation 会等待其后台文件 I/O、回滚和簿记工作完成，然后才释放线程写锁。这可以防止较早的已取消写入重新创建已删除记录，或回滚较晚的成功写入。因此，取消可能等待慢速存储；它不会停止正在进行的 filesystem 操作。仍在等待获取锁的调用方可以取消，而无需启动 mutation。跨多个线程的批次在传播取消之前，会先清空其当前线程组；后续线程组不会启动。
>
> 在一次 run 发布其 terminal stream marker 后，其进程本地的 `RunRecord` 在清理前的现有五分钟宽限期内仍然可用；持久化 run 历史仍可通过 `RunStore` 获取，而 stream bridge 按其单独的清理计划保留其 delivery tail。
>
> Run 取消可能落到任意 Gateway worker 上。非拥有者 worker 现在会为活跃拥有者持久化 interrupt 或 rollback 请求，拥有者在 lease renewal 期间观察到该请求并执行正常的取消流程；仅靠负载均衡器路由不再产生 409。第一个被接受的操作获胜，即使重试落到拥有者上也是如此，并且被接受的取消会与拥有者完成操作进行原子竞争。死亡拥有者仍遵循 lease takeover 和 orphan recovery。因此，取消延迟受 lease heartbeat interval 限制。

> 取消 model recovery probe（包括在其排队或等待重试时）会让下一次调用检查 provider 是否已恢复。取消不会计为 provider failure，也不会释放另一次调用的 active recovery probe。
> 模型重试会遵循 provider 的有效 `Retry-After` 提示，最长可达 24 小时，包括长于本地 backoff 上限的等待。格式错误、非有限或超出限制的提示则改用常规 backoff。这适用于 LLM 错误处理中的数值/日期提示，以及 Claude 重试路径中的整数秒提示。
>
> 启用 lease heartbeat 后，暂时的 RunStore 续期错误只会重试到最后一个已确认的 lease 过期为止；随后这个 stale worker 会取消本地执行，并抑制 checkpoint、completion-hook、delivery-receipt 与 thread-status 的 finalization。已经在进行中的远程 tool 副作用可能仍处于本地取消范围之外。
>
> 协调使用一个原子的 takeover claim，它会在候选选择之后重新检查 lease，因此 owner 续期成功会优先于孤儿恢复，并且只有一个协调器能将某个 run 报告为已恢复。当多个 Gateway worker 共享 Docker/AIO 或 E2B sandbox 后端时，还需配置 `sandbox.ownership.type: redis`；E2B 会在后台启动和周期性协调期间使用这些 lease，因此重复/孤儿清理不会终止仍在运行的 peer 的 sandbox。

有关详细的 Docker 开发指南，请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

#### 升级现有 checkout

保留 `config.yaml`、`.env` 和 `extensions_config.json`。停止你当前使用的服务，运行 `git pull --ff-only`，然后再次以相同模式启动。常规源代码升级不要再次运行 `make config` 或 `make docker-init`。如果新版本需要更改配置，请在重启前运行 `make config-upgrade`。各模式的命令请参阅 [Operations and Troubleshooting](frontend/src/content/en/application/operations-and-troubleshooting.mdx#upgrading-an-existing-checkout)。

在多个 Gateway worker 或 Pod 上滚动发布 resume-command 幂等性修复时，请将**所有带 key 的 resume 提交与重试**（带 `Idempotency-Key` 的 `command.resume`，作用于 thread 范围的 `/runs`、`/runs/stream` 或 `/runs/wait`）路由
仅向已升级的 worker 放行，直到服务这些 endpoint 的每个 worker 都已升级。
较旧的 worker 会忽略 private resume identity，只比较 `input`：当 `input: null` 时，重试 `deny` 可能会错误地复用先前的 `approve` run。
如果 load balancer 无法隔离已升级的 worker，请在 rollout 完成前暂停 keyed resume 流量，或者在以新版本重启之前停止所有旧 worker。增量式数据库 migration 可保持旧的 run-history reader 兼容；它并不会让旧 worker 对 resume admission 变得安全。当重试没有 identity 的 legacy resume run 时，已升级的 worker 会返回 409，即使决策相同也是如此；在决定提交新 action 之前，请检查该 run 和当前 thread 状态。参见 [run API contract](backend/docs/API.md#create-run)。

#### 选项 2：本地开发

如果你更愿意在本地运行服务：

前置条件：先完成上面的“Configuration”步骤（`make setup`）。`make dev` 需要项目根目录下有一个有效的 `config.yaml`。设置 `DEER_FLOW_PROJECT_ROOT` 以显式定义该根目录，或设置 `DEER_FLOW_CONFIG_PATH` 以指向特定的配置文件。运行时状态默认位于项目根目录下的 `.deer-flow`，可通过 `DEER_FLOW_HOME` 移动；skills 默认位于项目根目录下的 `skills/`，可通过 `DEER_FLOW_SKILLS_PATH` 移动。启动前运行 `make doctor` 以验证你的设置。

配置检查和 agent-storage migration 通过从 repository 根目录执行 `uv run --no-sync --project backend` 来使用已安装的 backend 环境。这保留了相对运行时路径和已安装的可选依赖；参见 [setup checks](backend/docs/SETUP.md#steps) 和 [agent-storage migration](backend/docs/CONFIGURATION.md#agent-storage)。
在 Windows 上，请从 Git Bash 运行本地开发流程。基于 bash 的服务脚本不支持原生 `cmd.exe` 和 PowerShell shell，并且不保证 WSL 可用，因为某些脚本依赖 Git for Windows 的实用工具，例如 `cygpath`。

文档中记录的根目录 `make` 命令会通过 Bash 显式调用仓库中的 `.sh` 文件。
因此，它们仍可在不保留 POSIX 可执行位的源码归档或文件系统中正常工作。当从此类检出目录中直接调用脚本时，请使用 `bash ./scripts/<name>.sh ...`。

1. **检查前置条件**：

   ```bash
   make check  # 验证 Node.js 22+、pnpm、uv、nginx
   ```

   当可用时，本地 `make check`、`make install`、`make dev` 和 `make start` 入口点会使用直接的 `pnpm` 可执行文件，否则回退到 `corepack pnpm`。在原生 Windows Python 下，共享 runner 会在通用 `pnpm` 查找之前检查 `pnpm.cmd`，后者遵循 `PATH`/`PATHEXT`，并可能在同一目录或更早的 PATH 目录中选择 `.exe` 或 `.bat`。Corepack 回退同样会在 `corepack` 之前检查 `corepack.cmd`。POSIX Python 则优先保留通用名称，包括在 MSYS/Cygwin 下运行时。runner 和诊断程序以绝对路径解析仓库路径，因此无论调用者的当前目录是什么，这些检查都能正常工作。Corepack 从 `frontend/` 运行，因此它会遵循 `frontend/package.json` 中固定的 `packageManager` 版本；无需启用全局 pnpm shim。

   `make check` 将工具诊断输出按 UTF-8 解码，并在非 UTF-8 主机上保留 Unicode pnpm
   错误。无效的输出字节会被替换，以便检查器能够报告依赖失败，而不是在解码输出时中止。

2. **安装依赖**：

   ```bash
   make install  # 安装后端 + 前端依赖 + pre-commit hooks
   ```

   Hook 设置通过 uv 调用 pre-commit，因此 uv 的工具目录不必位于 `PATH` 中。

3. **（可选）预拉取沙箱镜像**：

   ```bash
   # 如果使用 Docker/Container 沙箱，推荐执行
   make setup-sandbox
   ```

   从 UTF-8 编码的 `config.yaml` 中读取已配置的 sandbox image，无论是否带有前导 BOM，使用 LF 或 CRLF 行尾。
   在 macOS 上，只要 Apple Container 拉取成功，即使未安装 Docker，此步骤也算完成。如果 Docker 可用，其 image 也会被拉取。

4. **启动服务**：

   ```bash
   make dev
   ```

5. **访问**：http://localhost:2026

6. **（可选）加载示例 memory 数据以供本地审阅**：打开 `Settings > Memory`，点击 **Import memory**，然后选择 `backend/docs/memory-settings-sample.json`。浏览器会将其导入到当前登录用户的 memory 中。

   若要为一次性审阅环境中的每个已注册用户替换 memory：

   ```bash
   cd backend
   uv run python ../scripts/load_memory_sample.py --all-users
   ```

   批量模式支持 SQLite/PostgreSQL 用户注册表，会在 `.deer-flow/memory-sample-backups/` 下创建带时间戳的备份，并拒绝非持久化的 `database.backend: memory` 模式。完整审阅流程请参见 [backend/docs/MEMORY_SETTINGS_REVIEW.md](backend/docs/MEMORY_SETTINGS_REVIEW.md)。

本地服务始终使用其内部端口（`8001`、`3000` 和 `2026`）。
根目录 `.env` 变量 `PORT` 仅配置对外发布的 Docker ingress；
它不会改变 `make dev` 使用的 Next.js 端口。

#### 启动模式

DeerFlow 在 Gateway API 内运行 agent runtime。开发模式启用 hot-reload；生产模式使用预构建的前端。

|             | **Local Foreground**                         | **Local Daemon**                                             | **Docker Dev**                                      | **Docker Prod**                     |
| ----------- | -------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------- | ----------------------------------- |
| **Dev**     | `./scripts/serve.sh --dev`<br/>`make dev`    | `./scripts/serve.sh --dev --daemon`<br/>`make dev-daemon`    | `./scripts/docker.sh start`<br/>`make docker-start` | —                                   |
| **Prod**    | `./scripts/serve.sh --prod`<br/>`make start` | `./scripts/serve.sh --prod --daemon`<br/>`make start-daemon` | —                                                   | `./scripts/deploy.sh`<br/>`make up` |
| Action      | Local                                        | Docker Dev                                                   | Docker Prod                                         |
| ---         | ---                                          | ---                                                          | ---                                                 |
| **Stop**    | `./scripts/serve.sh --stop`<br/>`make stop`  | `./scripts/docker.sh stop`<br/>`make docker-stop`            | `./scripts/deploy.sh down`<br/>`make down`          |
| **Restart** | `./scripts/serve.sh --restart [flags]`       | `./scripts/docker.sh restart`                                | —                                                   |

`make start` 和 `make start-daemon` 每次运行都会用 `next build` 重新构建 frontend。若要改为复用上一次的构建，请传入 `SKIP_FRONTEND_BUILD=1`（或者直接调用 `./scripts/serve.sh --prod` 时加上 `--skip-frontend-build`）。这是可选启用的行为：当 `frontend/.next` 中没有已完成的构建时，它会快速失败。

Gateway 拥有 `/api/langgraph/*`，并将这些公开的 LangGraph 兼容路径转换为 nginx 背后其原生的 `/api/*` 路由。

run 创建期间的冷 agent 导入使用专用的 worker pool，从而在 agent stack 加载时保持不相关的 Gateway 请求仍能及时响应。factory 导入失败会导致该 run 不被接纳。

若要在没有 Gateway 的情况下运行只读 demo，请在 `frontend/` 中运行 `make build-static`，然后在同一目录下运行 `HOSTNAME=127.0.0.1 PORT=3000 node --env-file=.env .next/standalone/server.js`。该构建包含公开的 demo 资源，并在本地解析受支持的 demo API 读取；写入不可用。若要显示首页的 GitHub star 数，请在启动 Node 之前于 `frontend/.env` 中设置 `GITHUB_OAUTH_TOKEN`。该 token 保留在服务器上；凭据缺失或 GitHub 失败都会隐藏计数。更改 token 后需重启 Node；无需重新构建。

#### LangGraph Studio（可选）

默认的 `make dev` 拓扑使用 DeerFlow 的 Gateway 内嵌 runtime，不需要 LangGraph Studio。若要使用独立的开发服务器来检查和测试已注册的 lead-agent graph，请在 `backend/` 中运行该命令，以便 CLI 发现 `langgraph.json`：

```bash
cd backend
uv run langgraph dev --allow-blocking
```

该命令会打印本地 API 和 Studio UI 的 URL。这个内存中的服务器是
仅用于开发和测试。该 flag 允许 DeerFlow 在本地 Studio 请求期间进行同步配置和 graph-factory 设置；不得将其视为生产服务器设置。本地 Studio 身份验证会自动处理，因此连接不需要自定义 headers。对于生产工作负载，请使用 DeerFlow 文档中记录的生产启动模式或受支持的 LangSmith 部署。此 standalone 模式下的 assistant 所有权和来源由服务器拥有：Studio 可以发现已注册的 graphs 以及它创建的 assistants，并且正常的 assistant-version 选择仍然可用。在锁定的本地 runtime 加载其持久化开发存储之前，DeerFlow 会修复旧版 assistant 行和版本历史，这样历史客户端 metadata 就无法恢复服务器权限，也不会被 runtime 的启动清理丢弃。使用 `uv sync` 保持后端依赖同步；此兼容路径需要声明的 LangGraph runtime 版本，并且如果持久化存储契约不再匹配其预期，会记录一条警告。文档中记录的命令使用 LangGraph 的基于文件的 custom-app loader，这也直接由 DeerFlow 的回归测试覆盖。

使用 `if_not_exists="create"` 的 standalone 运行会在新创建的 thread 上保留 config 和 run metadata，包括可搜索的 tags；对于重复的键，run metadata 优先。Thread 所有权和 MCP incarnation 仍然由服务器拥有，后续运行不会替换 thread 的创建 metadata。

对于通过 LangGraph Studio 或直接通过 LangGraph Server 调用 `backend/langgraph.json` 的工作流，DeerFlow 会消费该 runtime 发布的经过身份验证的身份，并将其用于 custom-agent 配置/SOUL、用户 skills 和 skill policy、uploads、thread 数据以及 memory 读/写。这使经过身份验证的运行不会进入共享的 `default` filesystem bucket，并且服务器拥有的身份优先于普通客户端提供的 `user_id`
值。诸如 email 地址之类的外部身份，在访问 DeerFlow 存储之前会被映射为稳定、抗碰撞、目录安全的 user ID。默认的 DeerFlow 服务拓扑仍是上文所述的 Gateway 内嵌运行时。

Gateway run 会自动对在 `/mnt/user-data/outputs` 下创建或修改的 artifact 强制执行原生交付：`present_files` 必须至少呈现一个由当前 run 产生的 output，并且终态的 `run.delivery` receipt 必须被持久记录。虚拟 artifact 路径会在验证输出目录边界之前，先在产生该 output 的同一已认证 user 和 thread 作用域内完成解析。不产生 output artifact 的 run 保持普通的对话行为。

以 `status: error` 结束的 thread 作用域 `runs.wait()` 调用会报告当前 run 的错误，而不是更早的 answer。异步 Python LangGraph SDK 默认会抛出异常；传入 `raise_error=False` 可检查返回的 status 和 error。

DeerFlow 内置的 custom event 可通过两种 LangGraph streaming 接口获取：原生客户端可以继续订阅 `stream_mode="custom"`，而基于 callback 的集成则可以从 `astream_events(version="v2")` 中以 `on_custom_event` 记录的形式消费相同的 payload。callback 事件名称与 payload 的 `type` 字段一致。

#### Docker 生产部署

`./scripts/deploy.sh` 支持分别构建和启动：

```bash
# 一步完成（build + start）
./scripts/deploy.sh

# 两步完成（先 build 一次，稍后 start）
./scripts/deploy.sh build       # 构建所有 image
./scripts/deploy.sh start       # 启动已构建的 image

# 停止
./scripts/deploy.sh down
```

### 高级

#### Sandbox 模式

DeerFlow 支持多种 sandbox 执行模式：

- **本地执行**（直接在宿主机上运行 sandbox 代码）
- **Docker 执行**（在隔离的 Docker container 中运行 sandbox 代码）
- **Docker Execution with Kubernetes**（通过 provisioner service 在 Kubernetes pods 中运行 sandbox 代码）

conversation state 中的 Sandbox references 由服务器拥有。外部 run 和 thread-state APIs 拒绝调用方提供的 `sandbox` 值；恢复 checkpoint 时，runtime 会在 tool 能复用它之前，针对已认证的 user 和 thread 解析该引用。即使被引用的 sandbox 已缓存，缺失的 runtime thread ID 也会引发错误。

当为 Local Execution 启用 host Bash 时，DeerFlow 使用 `uname -s` 启动 OS 检测，然后在 Darwin 上使用 `sw_vers`。在 Linux 上，仅当活动的 sandbox policy 允许时，它才读取诸如 `/etc/os-release` 之类的 host system 文件。Host filesystem path 检查仍然适用；在路径被阻止后，agent 会被引导使用允许的 command-only probe 或 virtual path，而不是重复被拒绝的命令。

对于 Docker 开发，服务启动遵循 `config.yaml` sandbox mode。在 Local/Docker 模式下，`provisioner` 不会启动。

Local AIO sandbox 端口分配在 TCP port 65535 停止。如果从配置的起始端口开始的剩余端口已被占用，分配会报告没有可用端口，而不是尝试进行越界绑定。

参见 [Sandbox Configuration Guide](backend/docs/CONFIGURATION.md#sandbox) 以配置你偏好的模式。

Remote directory listings 将遍历失败（例如，不可读的目录）报告为 incomplete results，即使未返回任何条目。缺失的起始路径会单独报告为“Directory not found.”

可选的 [Tenki cloud sandbox provider](backend/packages/harness/deerflow/community/tenki/README.md) 使用 Tenki SDK 1.4.0 或更新版本。超时命令会保留部分输出并报告 `Exit Code: 124`；不成功的 health checks 无法回收 warm sandbox。Health probes 容忍 `ok` 行周围的 login-shell 输出，并且失败时会在替换 sandbox 之前记录 sandbox ID 和 probe output。
BoxLite shutdown 拒绝迟到的 VM 注册，并在进行中的获取完成时保持其 SDK 循环打开。如果它们无法在五秒内排空，shutdown 会失败，资源仍被持有，并且可以重试。

#### MCP Server

在 chat UI 中，启用 **Token Usage → Debug** 以检查 generic/MCP tool calls。每个 **Tool details** 面板初始为折叠状态，并显示 tool name、call ID、input 以及收到的 result 或显式 error。大型预览会被截断；名称超出剩余预览预算的字段会被省略，而不是重命名。结构化预览保留完整的 JSON 语法，包括转义字符串和闭合分隔符。当文本预算无法显示另一个元素时，数组预览会停止；字面量省略号值会被保留。数组末尾的连续生成标记共享一个省略号，表示省略的后缀；位于后续值之前的标记保留其位置。文本结果保留其原始表示，包括大型数字 ID 和重复的 JSON 键，而不重新解析。超出限制的文本显示为前缀并带有截断通知；结构化对象和数组分别格式化。复制操作仅复制显示的预览。这是浏览器已接收数据的前端视图，没有额外的机密信息脱敏层。

在 plan mode 中，格式错误的 TODO 状态返回正常的 tool-validation 错误，而不会中止 token 归属，因此 agent 可以纠正该调用。
Tool 生成的路径和 URL 可以在 context compaction 期间保留为短 artifact handle（`config.yaml` 中的 `tool_artifacts`）。Handle 区分不同的 tool 结果出现，即使 provider 重用 call ID。检测到的文件 URL 保留其 query string 和 fragment。当启用 PII redaction 时，模型可见的 artifact label 遵循该策略；内部引用保持完整，以便进行 tool argument 解析。配置的 registry limit 保留最新的 artifact，而 checkpointed 处理标识防止被驱逐的结果在重启后被重新捕获。解析在授权和 write-safety 检查之前运行；未知或过期的 handle 返回错误，而不执行 tool。小的未知结构化结果可以作为完整 JSON 保留，最多 4096 UTF-8 字节；空或过大的 payload 会被跳过。Handle 是 agent 本地的：task argument 将 parent handle 解析为具体引用，委托的报告必须返回具体引用，而不是 child-local handle。截断的模型投影报告省略了多少个 handle。

DeerFlow 支持可配置的 MCP server 和 skill 来扩展其能力。
对于 HTTP/SSE MCP server，支持 OAuth token 流程（`client_credentials`、`refresh_token`）。
缺失、格式错误或超出范围的 token 响应 `expires_in` 值使用一小时的默认生命周期。这包括无法在不导致 expiry timestamp 溢出的情况下添加到当前时间的生命周期。
持久的 HTTP/SSE 任务状态和取消调用使用持久化的任务所有者来选择配置的 `user_auth` 凭据，包括重启之后；按请求的 secret 不会为后台调用保留。如果请求作用域的凭据覆盖提交身份验证，则两个凭据都必须授权访问同一个远程任务。
对于 stdio MCP server，可以使用 `tool_call_timeout` 配置单个 tool 调用的超时；对于 HTTP/SSE server，持久化的后台任务调用也遵循相同的设置。
对于 stdio 文件输出，裸文件名会链接到该调用创建或更改的唯一匹配文件。嵌入在无关路径中的文件名（包括 Windows 反斜杠路径）会保持原样。
对于 HTTP/SSE 后台任务调用，`session_init_timeout` 单独约束连接建立（包括 SSE endpoint 事件）和 MCP 初始化的总时长；一旦 tool 调用开始，它就不再适用。初始化截止时间错误会标识 server 和配置的时间限制。
普通的 `task` subagent 会为 MCP 调用保留父 run 捕获的 thread incarnation，包括 legacy thread，因此委派会保持相同的生命周期范围。
MCP tool 名称默认会加上 `<server_name>_` 前缀，以防止跨 server 冲突。如果某个 server 已经为自己的 tool 加了命名空间，可在 `extensions_config.json` 中为该 server 设置 `tool_name_prefix: false` 以保留原始名称。仅当生成后的名称在所有已启用的 server 中仍然唯一时，才应禁用前缀。
已登录用户的 notification 开关、默认 model、conversation mode 和 reasoning effort 会保存到其账户，并在其他浏览器或清除浏览器存储后恢复。浏览器 notification 权限仍需在每个设备上授予。更改在 network 失败后会重试；未发送的更改在同一 tab 中刷新后仍会保留。对不同字段的并发编辑会被保留；对于同一字段，以最后一次 server 写入为准。现有的未绑定作用域的浏览器偏好设置不会自动上传，因为它们没有账户归属；升级后请重新选择这些设置一次。静态 demo 和禁用 auth 的开发环境保留浏览器本地设置。thread 特定的 model override 和其他显示偏好设置仍保留在本地。

在新的 chat 中，提交的问题保持在其流式 reasoning 之上，
工具步骤，同时服务器创建会话并确认消息。

Capability Center 按办公协作、文档与知识、搜索与研究、业务与数据以及开发与运维对插件进行分组。目录包含设置参考以及现有的 MCP 配置和 Lark。推荐的集成和内置支持不意味着已安装或已验证的连接；Installed 筛选器仅显示已配置的 MCP 条目和已安装的 Lark。

在 Web 界面中配置的个人 MCP 连接按用户持久保存。部署工具保持共享。管理员可以在 **Platform provided** 下添加、编辑、启用、禁用和删除共享 MCP 服务器；普通用户只能查看其状态而无控制权。个人插件开关仅影响已登录用户的连接。请参阅[连接所有权](docs/capability-center.md#personal-and-deployment-mcp-configuration)。

有关插件清单、适配器注册和 Agent 能力选择，请参阅 [Capability Center 集成契约](docs/capability-center.md)。

DingTalk 和 WeCom 群通知以及 HubSpot CRM 是捆绑的可配置插件。管理员提供机器人凭证或 HubSpot 私有应用 token；然后 Agents 可以发送请求的群通知、列出公司或创建联系人。保存配置不会执行任何外部写入。这些插件复用现有的 MCP 生命周期，不需要单独的插件服务。有关必填字段、scopes 和功能边界，请参见上文的集成契约。

插件品牌图标在本地捆绑。添加或编辑一个个人 MCP 插件时，用户可以上传 PNG、JPG 或 WebP 图像（最大 2 MB），预览图像，或恢复默认图标。更改仅在保存后生效；自定义图标会跨浏览器持久保存为服务器条目中仅用于显示的 `presentation.icon` 元数据内的标准化 128px PNG。它们不会发送到 MCP transport。
能力中心 > 插件通过定向变更一次添加、替换和删除一个 MCP 服务器，这些变更会保留并发的同级更改；删除使用无 body 的 URL 寻址请求。某个服务器上的无效 stdio 命令不再阻止切换另一个服务器，而启用该无效服务器仍受命令允许列表保护，并在 UI 中显示后端验证消息。
定向更新同时接受 DeerFlow 的 `type` 字段和 MCP 规范中用于 SSE/HTTP 服务器的 `transport` 字段。
运行时 MCP 和技能更新原子地替换 `extensions_config.json`，因此中断的写入不会使共享配置被截断或部分写入。每个读取同一文件的 Gateway worker 或实例会在下次读取时获取新的修订版本（缓存检查文件的内容签名），因此通过一个副本所做的 MCP 和技能更改会应用到其他副本，而无需重启；缺失、截断或无效的修订版本会保留之前的配置，直到一个完整的修订版本落地，包括在重新加载期间文件消失的情况。
管理员 MCP 缓存重置会推进可写配置目录中的一个持久化 generation 标记。每个挂载同一目录的 Gateway worker 会在下一次查找之前淘汰自己的缓存工具和池化会话；具有独立文件系统的副本不会被隐式覆盖。如果无可用的配置路径，API 则报告进程本地重置。
解析后的扩展配置及其记录的内容摘要来自同一次读取，因此并发的编辑随后进行保留时间戳的备份恢复，不会导致一个不同的修订版本被无限期缓存。

`extensions_config.json` 接受带或不带前导字节顺序标记 (BOM) 的 UTF-8，包括由编辑器保存为带 BOM 的 UTF-8 的文件。
MCP routing hints 也可以为匹配的请求优先选择某个特定的 MCP tool，而不会禁止其他 tools。当 `tool_search` 推迟 MCP schemas 时，匹配的 routing metadata 可以在模型调用前自动提升最多 `tool_search.auto_promote_top_k` 个 deferred schemas。

OpenViking 用户可以使用 owner-bound USER API key 在 `/mcp` 注册官方 Streamable HTTP endpoint。原生 `forget` tool 被暴露出来以实现能力对等；删除不可逆，因此只应在用户明确确认后调用。DeerFlow 不强制执行该确认。这条显式的、由模型选择的 MCP tool 路径可以与独立的自动 OpenViking memory backend 并行运行；它不会替代自动 turn capture 或 recall。参见 [OpenViking MCP tools configuration](backend/docs/MCP_SERVER.md#openviking-mcp-tools)。
Gateway 可以将 MCP server 的普通 `submit` / `status` / `cancel` 工具适配为持久化的后台任务。Agent 只能看到配置的 submit 工具和一个 DeerFlow 本地 task ID；remote ID 会在 submit 调用返回之前持久化，而 status 和 cancel 保持为 runtime 内部使用。轮询使用跨 worker 租约、指数退避重试、限定作用域的 MCP session、有界结果存储以及重启恢复。status 工具的 `isError` 会作为有界诊断信息保留并重试；server 通过带有 `status: "failed"` 的普通结构化结果来报告永久性的 remote-task 结果。远程轮询提示是有限正数，上限为 24 小时，artifact-reference JSON 限制为 64 KiB，task/server 标识符在持久化前会按其持久化 SQL 列限制进行校验。需要输入（input-required）和终态更新会通过幂等的 Agent run 唤醒当前 chat，而 `list_background_tasks` 和 `cancel_background_task` 让 Agent 能够管理任务，无需向用户询问 remote handle。当前 thread 的任务可通过 `GET /api/threads/{thread_id}/mcp-tasks`、其详情端点以及 `POST /api/threads/{thread_id}/mcp-tasks/{task_id}/cancel` 获取；当 task runtime 实际启动时，Web UI 会从 chat header 暴露相同的安全本地视图，支持实时状态刷新、取消，以及按需查看 result、artifact、input-request、status-error 和取消重试详情。默认禁用以及使用 memory backend 的部署会隐藏该 UI，并且不会轮询 task 端点。失败的远程取消会以退避方式保持排队，其最新的有界错误和尝试次数会在展开的 task card 中保持可见。在 `config.yaml` 中启用 `mcp_tasks`，在 `extensions_config.json` 中用精确的原始工具名配置 `task_toolsets`，并使用 SQL database backend（`sqlite` 或 `postgres`）。启用 task 的 server 连接、authentication、interceptor、timeout 或 binding 变更需要重启 Gateway，以确保 Agent 工具发现和后台调用不会使用不同版本的配置。`input_required` 目前仅用于通知：DeerFlow 可以显示该请求，但尚不能将用户的回答提交回远程任务。
对于具有 `task_toolsets` 的 deployment-level HTTP/SSE 服务器，discovery、ordinary
tools 和后台任务调用在一个 Gateway
进程内共享 OAuth token 状态，包括跨 tool-cache 重置的情况。轮换后的 refresh token 保留在
内存中；它们不会写回配置，也不会跨进程共享。
重启后，配置的 refresh token 必须仍然有效。

通知启动和失败的 Agent-run 投递使用有上限的 exponential backoff，并带有可见的尝试次数，在五次失败尝试后停止。当一个有界的 ordinary release 超过其 drain deadline 时，服务保留所有权直到它稳定。一个永久被拒绝的目标（例如已删除的聊天）会立即被 dead-lettered，而不是永远重试或重新创建。取消 endpoint 在持久记录请求后返回；后台服务拥有可能缓慢的远程 MCP 调用及其重试计划。

通知运行将其受信任的投递指令与带框架的、不受信任的远程事件 payload 分开。进程启动时的 task runtime——而不是热配置读取——控制任务管理工具是否暴露，因此更改 `mcp_tasks` 需要重启 Gateway。当 skill 的 `allowed-tools` 策略处于活动状态时，`list_background_tasks` 和 `cancel_background_task` 必须像其他业务工具一样显式声明。
有关详细说明，请参阅 [MCP Server 指南](backend/docs/MCP_SERVER.md)。

安全：仅通过 `config.context.secrets` 传递 per-request MCP credentials；credentials 绝不能放在任一 run metadata surface（`metadata.auth_token` 或 `config.metadata.auth_token`）中。有关支持的 interceptor flow 以及从 legacy metadata credentials 迁移时所需的轮换和保留副本清理，请参阅 [MCP credential 迁移和清理](backend/docs/MCP_SERVER.md#migrating-legacy-mcp-credentials)。

#### IM 渠道

DeerFlow 支持从消息应用接收任务。Channel 在配置后自动启动 — 它们中任何一个都不需要公网 IP。

取消 channel 重启会丢弃其待处理的配置重载，保留之后应用的较新运行时设置。

DeerFlow 还可以在工作区 UI 中暴露用户拥有的 IM channel 连接。当启用 `channel_connections` 时，已登录用户可以从侧边栏 / Settings > Channels 绑定 Telegram、Slack、Discord、Feishu/Lark、DingTalk、WeChat、WeCom、QQ 或 Buzz。它复用现有的出站 `channels.*` transports，因此不需要公网 IP 或提供商回调 URL。传入的 IM 消息随后在连接的 DeerFlow 用户账户下运行。有关设置和安全说明，请参阅 [IM Channel Connections](backend/docs/IM_CHANNEL_CONNECTIONS.md)。

| Channel       | Transport                                                        | 难度 |
| ------------- | ---------------------------------------------------------------- | ---- |
| Telegram      | Bot API (long-polling)                                           | 简单 |
| Slack         | Socket Mode                                                      | 中等 |
| Feishu / Lark | WebSocket                                                        | 中等 |
| WeChat        | Tencent iLink (long-polling)                                     | 中等 |
| WeCom         | WebSocket                                                        | 中等 |
| QQ            | WebSocket (仅文本 C2C 和群组 @mentions；每个来源四/五条被动回复) | 中等 |
| DingTalk      | Stream Push (WebSocket)                                          | 中等 |
| Buzz          | Nostr relay (WebSocket, NIP-42)                                  | 中等 |

**`config.yaml` 中的配置：**

Discord 的 `channels.discord.allowed_guilds` 接受一个正数 guild ID（带引号或不带引号）或一个 YAML 列表。未设置、`null`、`[]` 或空字符串允许所有 guild。无效条目会被忽略并发出警告；任何其他配置值若未产生有效 ID，则拒绝所有 guild 并记录错误。`allowed_channels` 接受一个 channel ID（带引号或不带引号）或一个 YAML 列表，其中的 ID 在允许的 guild 内豁免 `mention_only`。空值不提供任何豁免，因此启用时 `mention_only` 适用于所有地方。

```yaml
channels:
  # 兼容 LangGraph 的 Gateway API 基础 URL（默认：http://localhost:8001/api）
```

```yaml
langgraph_url: http://localhost:8001/api
# Gateway API URL（默认：http://localhost:8001）
gateway_url: http://localhost:8001

# 排队中或由 provider 预留的入站消息的最大数量（默认：1000）
inbound_queue_maxsize: 1000
# 长期存活的入站 handler worker 的固定数量（默认：5）
max_concurrency: 5
# 在取消活跃 handler 之前，用于排空已接受工作的秒数（默认：3）
shutdown_grace_period_seconds: 3

# 可选：所有移动端渠道的全局 session 默认值
session:
  assistant_id: lead_agent # 或自定义 agent 名称；自定义 agent 通过 lead_agent + agent_name 进行路由
  config:
    recursion_limit: 100
  context:
    thinking_enabled: true
    is_plan_mode: false
    subagent_enabled: false

feishu:
  enabled: true
  app_id: $FEISHU_APP_ID
  app_secret: $FEISHU_APP_SECRET
  # domain: https://open.feishu.cn       # 中国（默认）
  # domain: https://open.larksuite.com   # 国际

qq:
  enabled: true
  app_id: $QQ_APP_ID
  client_secret: $QQ_CLIENT_SECRET
  allowed_users: [] # QQ OpenID，而非 QQ 账号

wecom:
  enabled: true
  bot_id: $WECOM_BOT_ID
  bot_secret: $WECOM_BOT_SECRET
  # 可选：除内置的 qq.com 系列和 WeCom 官方 COS 媒体 host
  # （ww-aibot-img-1258476243.<region>.myqcloud.com）之外，入站媒体下载
  # 可能来自的额外 host 后缀；如果 WeCom 轮换到新的 COS 账号，
  # 或媒体经由代理传输，可在此添加
  allowed_media_hosts: []

slack:
  enabled: true
  bot_token: $SLACK_BOT_TOKEN # xoxb-...
  app_token: $SLACK_APP_TOKEN # xapp-...（Socket Mode）
  allowed_users: [] # 空 = 允许所有

telegram:
  enabled: true
  bot_token: $TELEGRAM_BOT_TOKEN
  # 可选：将最终的 Markdown 回复渲染为 Telegram Rich Messages。
  rich_messages: false
  allowed_users: [] # 数字 user ID，而非 @usernames；空 = 允许所有

wechat:
```

    enabled: false
    bot_token: $WECHAT_BOT_TOKEN
    ilink_bot_id: $WECHAT_ILINK_BOT_ID
    qrcode_login_enabled: true      # 可选：当 bot_token 缺失时，允许首次通过二维码引导登录
    allowed_users: []               # iLink 用户 ID；为空表示允许所有用户；一个 ID 占一个条目
    polling_timeout: 35             # 时间值必须为正的有限秒数
    polling_retry_delay: 5
    qrcode_poll_interval: 2
    qrcode_poll_timeout: 180
    state_dir: ./.deer-flow/wechat/state
    max_inbound_image_bytes: 20971520
    max_outbound_image_bytes: 20971520
    max_inbound_file_bytes: 52428800
    max_outbound_file_bytes: 52428800
    # 入站媒体下载按上述上限进行流式传输，并限制为
    # 以下主机后缀（默认还包括 *.qq.com 以及 cdn_base_url 的主机）
    allowed_media_hosts: []

    # 可选：按渠道 / 按用户的 session 设置
    session:
      assistant_id: mobile-agent  # 此处也支持自定义 agent 名称
      context:
        thinking_enabled: false
      users:
        "123456789":
          assistant_id: vip-agent
          config:
            recursion_limit: 150
          context:
            thinking_enabled: true
            subagent_enabled: true

dingtalk:
enabled: true
client_id: $DINGTALK_CLIENT_ID # 你的钉钉应用的 Client ID
client_secret: $DINGTALK_CLIENT_SECRET # 你的钉钉应用的 Client Secret
allowed_users: [] # 为空 = 允许所有用户
card_template_id: "" # 可选：用于流式打字机效果的 AI 卡片模板 ID

````

Notes：
- `assistant_id: lead_agent` 会直接调用默认的 LangGraph assistant。
- 如果 `assistant_id` 被设置为自定义 agent 名称，DeerFlow 仍会通过 `lead_agent` 进行路由，并将该值作为 `agent_name` 注入，因此该自定义 agent 的 SOUL/config 会对 IM 渠道生效。
- IM channel worker 会在内部调用 Gateway 的 LangGraph-compatible API，并自动附加进程本地的内部认证，以及创建 thread 和 run 所需的 CSRF cookie/header 对。
- 入站工作受限于 `inbound_queue_maxsize` 条待处理消息加上 `max_concurrency` 个活跃 worker。当容量耗尽时，socket/polling provider 会在发送 DeerFlow 的 working acknowledgment 之前丢弃新消息，并发出限速警告。Buzz 保持其 replay cursor 不变，并为 relay replay 重新连接；GitHub webhook 返回 `503`，将该 delivery 标记为失败，以便手动/API 重新投递。关闭流程会立即关闭准入，在已接受消息最多 `shutdown_grace_period_seconds` 内排空期间保持 channel transports 可用，然后取消并等待活跃 handler，之后才关闭 provider resources；Gateway 的外层超时可以取消未完成的 shutdown，而不会分离这些 resources。
- Feishu/Lark 现在会按映射的 DeerFlow `thread_id` 将快速跟进消息排队，而不是立即显示通用 busy 回复，并且 topic 回复会在 queued/running/final patch 期间保留带紧凑源消息预览的逐消息卡片。
- 流式 IM channel 会将后端 `error` 事件视为 transport failure，并遵循相同的回复和重试路径。channel 会记录错误类型和消息以便诊断。

在 `.env` 文件中设置对应的 API key：

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

# Feishu / Lark
FEISHU_APP_ID=cli_xxxx
FEISHU_APP_SECRET=your_app_secret

# WeChat iLink
WECHAT_BOT_TOKEN=your_ilink_bot_token
WECHAT_ILINK_BOT_ID=your_ilink_bot_id

# WeCom
WECOM_BOT_ID=your_bot_id
WECOM_BOT_SECRET=your_bot_secret

# DingTalk
DINGTALK_CLIENT_ID=your_client_id
DINGTALK_CLIENT_SECRET=your_client_secret
````

**Telegram 设置**

1. 与 [@BotFather](https://t.me/BotFather) 聊天，发送 `/newbot`，然后复制 HTTP API token。
2. 在 `.env` 中设置 `TELEGRAM_BOT_TOKEN`，并在 `config.yaml` 中启用该 channel。
3. 该 bot 接受入站文本、照片和文档（带或不带 caption）。托管 Bot API 的下载限制为每个附件 20 MB。

**Slack 设置**

1. 在 [api.slack.com/apps](https://api.slack.com/apps) 创建 Slack App → Create New App → From scratch。
2. 在 **OAuth & Permissions** 下添加 Bot Token Scopes：`app_mentions:read`、`chat:write`、`im:history`、`im:read`、`im:write`、`files:write`。
3. 启用 **Socket Mode** → 生成具有 `connections:write` scope 的 App-Level Token（`xapp-…`）。
4. 在 **Event Subscriptions** 下订阅 bot events：`app_mention`、`message.im`。
5. 在 `.env` 中设置 `SLACK_BOT_TOKEN` 和 `SLACK_APP_TOKEN`，并在 `config.yaml` 中启用该 channel。

**Feishu / Lark 设置**

1. 在 [Feishu Open Platform](https://open.feishu.cn/) 创建应用 → 启用 **Bot** capability。
2. 添加权限：`im:message`、`im:message.p2p_msg:readonly`、`im:resource`。
3. 在 **Events** 下订阅 `im.message.receive_v1` 并选择 **Long Connection** 模式。
4. 复制 App ID 和 App Secret。在 `.env` 中设置 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`，并在 `config.yaml` 中启用该 channel。
5. 该 bot 支持入站文本、图片和文件消息。入站附件下载限制为每个附件 20 MB。

**WeChat 设置**

1. 在 `config.yaml` 中启用 `wechat` channel。
2. 要么在 `.env` 中设置 `WECHAT_BOT_TOKEN`，要么设置 `qrcode_login_enabled: true` 以进行首次 QR 引导。
3. 当 `bot_token` 缺失且启用了 QR 引导时，观察 backend logs 中 iLink 返回的 QR 内容并完成绑定流程。
4. QR 流程成功后，DeerFlow 会将获取到的 token 持久化到 `state_dir` 下，供后续重启使用。
5. 对于 Docker Compose 部署，请将 `state_dir` 放在持久化 volume 上，以便 `get_updates_buf` 游标和保存的 auth state 在重启后仍然保留。
6. 出站图片/文件在读取时强制执行 `max_outbound_image_bytes` / `max_outbound_file_bytes`（默认 20 MiB / 50 MiB），包括在解析之后发生增长的文件。超限读取会在加密/上传之前被拒绝，而不是发送被截断的前缀。非正数限制会禁用对应的上限。

7. `allowed_users` 接受 iLink user ID。未设置、`null`、`[]` 或空字符串表示允许所有人。单个 ID 是一个条目，而不是一串字符，未加引号的整数值数字会以其整数的文本形式存储。包含逗号或内部空白的标量字符串会记录一条警告，但仍作为单个字面 ID；多个 ID 请使用 YAML 列表。无效条目会被忽略并记录警告；任何其他配置值如果无法产生有效 ID，则会拒绝所有用户并记录错误。`/connect` 在该检查之前仍会被接受，被拒绝的发送者会在入站媒体下载之前被丢弃。

8. 关闭时会等待进行中的 cursor 写入。在 token 过期时，DeerFlow 会持久化 cursor 重置，并在完成 poller 取消之前移除已保存的 token。

**WeCom Setup**

1. 在 WeCom AI Bot 平台上创建一个 bot，并获取 `bot_id` 和 `bot_secret`。
2. 在 `config.yaml` 中启用 `channels.wecom`，并填写 `bot_id` / `bot_secret`。
3. 在 `.env` 中设置 `WECOM_BOT_ID` 和 `WECOM_BOT_SECRET`。
4. 确保后端依赖包含 `wecom-aibot-python-sdk`。该 channel 使用 WebSocket 长连接，不需要公网 callback URL。
5. 当前集成支持入站文本、图片和文件消息。agent 生成的最终图片/文件也会被发送回 WeCom 会话。

**DingTalk Setup**

1. 在 [DingTalk Developer Console](https://open.dingtalk.com/) 中创建一个 DingTalk 应用，并启用 **Robot** 能力。
2. 在 robot 配置页面中，将消息接收模式设置为 **Stream Mode**。
3. 复制 `Client ID` 和 `Client Secret`，在 `.env` 中设置 `DINGTALK_CLIENT_ID` 和 `DINGTALK_CLIENT_SECRET`，并在 `config.yaml` 中启用该 channel。
4. _（可选）_ 如需启用流式 AI Card 回复（打字机效果），请在 [DingTalk Card Platform](https://open.dingtalk.com/document/dingstart/typewriter-effect-streaming-ai-card) 上创建一个 **AI Card** 模板，然后将 `config.yaml` 中的 `card_template_id` 设置为该模板 ID。你还需要申请 `Card.Streaming.Write` 和 `Card.Instance.Write` 权限。

当 DeerFlow 在 Docker Compose 中运行时，IM channels 在 `gateway` 容器内执行。在这种情况下，不要将 `channels.langgraph_url` 或 `channels.gateway_url` 指向 `localhost`；请使用容器服务名，例如 `http://gateway:8001/api` 和 `http://gateway:8001`，或设置 `DEER_FLOW_CHANNELS_LANGGRAPH_URL` 和 `DEER_FLOW_CHANNELS_GATEWAY_URL`。

**Commands**

channel 连接后，你可以直接在聊天中与 DeerFlow 交互：

| Command             | Description                  |
| ------------------- | ---------------------------- |
| `/new`              | 开始新对话                   |
| `/status`           | 显示当前 thread 信息         |
| `/models`           | 列出可用模型                 |
| `/memory`           | 查看 memory                  |
| `/agent list`       | 列出你的 Custom Agents       |
| `/agent use <name>` | 使用 Custom Agent 开始新对话 |
| `/help`             | 显示帮助                     |

> 不带命令前缀的消息会被视为普通聊天——DeerFlow 会创建一个 thread 并以对话方式回复。

Agent 选择的作用域是对话：`/agent use <name>` 会开始一个新对话，并在 thread metadata 中固定该 Custom Agent。已有对话绝不会中途切换 agent，该选择在 Gateway 重启后仍然保留，并且在 Web UI 中打开由 IM 创建的 thread 时仍会继续使用同一个 Custom Agent。
使用 `/agent use lead_agent` 可在新对话中恢复为默认 agent。

#### Request Trace Correlation

每个 Gateway HTTP 响应都带有一个 `X-Trace-Id` header。该 id 继承
来自入站的 `X-Trace-Id`（当调用方发送一个时），否则会生成一个，因此代理或上游服务可以跨服务固定一个 id。它无需配置，且无法关闭。

同一个 id 会继续附着在比 HTTP 响应存活更久的工作上：分离的 run task、它委派的任何 subagents，以及后台 memory-update 线程。它会作为 `deerflow_trace_id` 记录在 run record 上（在 runs API 中可见）、线程的 checkpoint metadata 中，以及 Langfuse traces 中。Scheduled tasks、MCP task notification runs 和 IM channel messages 在 HTTP 之外启动，并每次发生时生成自己的 id。

仅当 enhanced logging 开启时，日志记录才会携带该 id：

```yaml
logging:
  enhance:
    enabled: true # print trace_id into log records
    format: text # or json
```

它默认关闭，因为开启它会改变日志格式。`logging` 需要重启才能生效，因此请编辑 `config.yaml` 并重启 Gateway。该设置只影响日志输出——id、响应头和 run metadata 不受影响。

`deerflow_trace_id` 是一个 DeerFlow correlation id：它不是 run id，也不是提供方的原生 trace id。它也不是查找键——没有任何东西用它解析 thread 或 run；用它来关联日志行。在 run 请求的 `metadata` 或 `config.context` 中发送的 `deerflow_trace_id` 会被忽略并覆盖，因此响应头、日志和持久化的 run 永远不会不一致。要固定一个 correlation id，请发送 `X-Trace-Id` 头。

Gateway run history 还会为每个 run 记录一个终态 `run.delivery` 回执，包括零输出和崩溃恢复的 run。在正常执行期间，回执会在持久化的终态 run 状态之前被持久化。孤儿恢复首先原子性地认领一个过期的 lease，然后幂等地回填该回执，因此过期的恢复扫描不会覆盖活跃 run 的详细 delivery 事实。在 event-store 中断期间，回执持久化仍保持 best-effort。那些 run
fail checkpoint preflight（或在等待先前 finalization 时被取消）会保留现有的 completion-data 行为：它们会收到 zero-delivery receipt，但不会用空快照覆盖 RunStore 的 completion 字段。

当 `tool_progress.enabled` 为 true 时，同一 run event history 也会记录 result-quality guard 的阶段变化。它会记录循环检测决策以及针对 lead agent 和普通 task subagents 的延迟 MCP tool 提升。Promotion
事件会标明新提升的 deferred-tool 名称，以及是 routing metadata 还是
`tool_search` 选中了它们，而不会将搜索查询、routing 关键词、schemas、arguments、results 或 catalog hash 复制到 promotion 事件本身中。

#### LangSmith Tracing

DeerFlow 内置了 [LangSmith](https://smith.langchain.com) 集成用于可观测性。启用后，所有 LLM 调用、agent 运行和 tool 执行都会被追踪，并可在 LangSmith dashboard 中查看。

将以下内容添加到你的 `.env` 文件中：

```bash
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxx
LANGSMITH_PROJECT=xxx
```

#### Langfuse Tracing

DeerFlow 还支持 [Langfuse](https://langfuse.com) 可观测性，用于 LangChain 兼容的运行。

将以下内容添加到你的 `.env` 文件中：

```bash
LANGFUSE_TRACING=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxxxxxx
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

如果你使用的是自托管的 Langfuse 实例，请将 `LANGFUSE_BASE_URL` 设置为你的部署 URL。

**Trace correlation 字段。** 每次 agent 运行都会标注 Langfuse 的 reserved trace attributes，以便 Sessions 和 Users 页面自动亮起：

- `session_id` = LangGraph `thread_id` — 将同一对话的每条 trace 分组在一起
- `user_id` = 来自 `get_effective_user_id()` 的有效用户（在 no-auth 模式下回退为 `default`）
- `trace_name` = assistant id（默认为 `lead-agent`）
- `tags` = `[env:<DEER_FLOW_ENV>, model:<model_name>]`（内置 Gateway lead-agent 与嵌入式客户端运行时，会在默认或回退解析之后为所选模型打标签；自定义 graph 工厂可能只提供所请求的模型；未设置环境时省略环境标签）
- `metadata.deerflow_trace_id` = DeerFlow 请求关联 id，当启用请求 trace 关联时，与 `X-Trace-Id` 一致

这些内容会在 graph 调用根处注入到 `RunnableConfig.metadata`，对 gateway 路径（`runtime/runs/worker.py::run_agent`）和嵌入式路径（`client.py::DeerFlowClient.stream`）都是如此，因此任何 LangChain 兼容的 callback 都能读取它们。设置 `DEER_FLOW_ENV`（或 `ENVIRONMENT`）即可按部署环境为 trace 打标签。

#### Monocle Tracing

DeerFlow 还支持 [Monocle](https://github.com/monocle2ai/monocle)，这是一个面向 agentic 应用的基于 OpenTelemetry 的 tracer。它会端到端记录每次运行：LLM 调用、agent 步骤，以及 tool 和 MCP 调用，包括它们的输入、输出、耗时和 token 数量。

将以下内容添加到你的 `.env` 文件：

```bash
MONOCLE_TRACING=true
MONOCLE_EXPORTERS=file          # file, console, okahu, s3, blob, gcs (default: file)
OKAHU_API_KEY=okh_xxxxxxxx      # required only for the `okahu` exporter
```

每次运行都会向 `.monocle/` 写入一个 trace 文件；在 [Monocle VS Code extension](https://marketplace.visualstudio.com/items?itemName=OkahuAI.monocle-apptrace) 中打开它，即可查看 span 时间线和 token 数量。连接到 [Okahu](https://www.okahu.ai)——一个 agent 可观测性平台——即可跨运行分析 trace，并运行基于 trace 的评估和 agentic 评估（通过 `okahu` exporter）。
Traces 会逐字记录 span 的输入和输出——prompts、tool arguments 和 model responses——以及 token usage 和 timings。`file` exporter 将它们保存在本地磁盘上，且从不轮转或清理，因此要定期清理 `.monocle/`；远程 exporters（`okahu`、`s3`、`blob`、`gcs`）会把同样的数据发送到本机之外，因此只启用你信任的目标。Monocle 在 Gateway 启动时初始化一次：配置错误（未知 exporter、缺少 `OKAHU_API_KEY`）会在那里被记录，并且 tracing 会保持关闭，直到 Gateway 重启。

#### 使用多个 Providers

LangSmith 和 Langfuse 作为 LangChain callbacks 挂载，因此你可以同时启用两者，DeerFlow 会把每次 run 报告给两者。如果已启用的 provider 缺少必需的 credentials 或初始化失败，DeerFlow 会快速失败并指出是哪一个。Monocle 使用全局 OpenTelemetry provider 而不是 callback；Langfuse 共享该 provider，因此三者可以一起运行。由于两个 span processors 都位于同一个共享 provider 上，当两者都启用时，Monocle 的 exporters 也会看到 Langfuse 的 spans。

对于 Docker 部署，tracing 默认禁用。在你的 `.env` 中设置 `LANGSMITH_TRACING=true` 和 `LANGSMITH_API_KEY` 以启用它。

#### Existing-Run Stream Actions

Existing-run SSE joins 在 `GET` 上仅用于观察：提供
`action=interrupt|rollback` 会返回 `405`。此 stream route 上的取消操作
仅支持 `POST`，并且需要 `runs:cancel` 权限。相应地，OpenAPI
contract 仅在 `POST` 上暴露 `action` 和 `wait`；`GET` 操作仅暴露
其 path parameters。

#### Personal Access Tokens

非交互式客户端（CI pipelines、scripts、server-to-server integrations）
可以使用 **personal access token (PAT)** 而不是浏览器会话来调用 Gateway API。在登录状态下通过 `POST /api/v1/auth/pats` 创建一个——原始 `dfp_...` 值只显示一次；仅存储其 SHA-256 digest——然后将其作为 Bearer credential 发送：

```http
POST /api/threads/search
Authorization: Bearer dfp_...
Content-Type: application/json

{}
```

每个 token 以其所归属用户的身份运行（owner 过滤与 per-user memory 保持正常工作），携带一组只能收窄该用户权限的 scope，并且只被允许访问 thread/run 生命周期相关路由——其他所有路由对 PAT 调用者一律返回 `403`，且 PAT 永远不具备 admin 能力。Token 可以随时列出和撤销；撤销立即生效。PAT 需要数据库后端（SQLite/PostgreSQL）。完整参考：[API Reference — Personal Access Tokens](backend/docs/API.md#personal-access-tokens)。

## 从 Deep Research 到 Super Agent Harness

DeerFlow 最初是一个 Deep Research 框架——社区把它带得很远。自发布以来，开发者们已经将它推向了远超研究范畴的用途：构建数据管道、生成 slide deck、搭建 dashboard、自动化内容工作流。这些都是我们从未预料到的。

这告诉我们一件重要的事：DeerFlow 不只是一个研究工具。它是一个 **harness**——一个为 agent 提供基础设施、让它们真正把工作做完的 runtime。

于是我们从头重建了它。

DeerFlow 2.0 不再是一个需要你自己拼装的框架。它是一个 super agent harness——开箱即用，完全可扩展。它构建在 LangGraph 和 LangChain 之上，内置了 agent 所需的一切：文件系统、memory、skills、感知 sandbox 的执行能力，以及为复杂的多步任务进行规划并派生子 agent 的能力。

直接使用它。或者把它拆开，改造成你自己的。

## 核心特性

### Skills 与 Tools

从工作区侧边栏打开 **Capability Center**，管理 **Plugins**（MCP server 与 Lark/Feishu 集成）和 **Skills**。两个目录都支持搜索；skill 卡片显示简要描述，完整描述在详情视图中查看。内置 skill 与用户创建/导入的 skill 分开列出。Community 标签页支持将 `.skill` 归档导入到 My skills。通用偏好设置仍在 Settings 中。
Skills 让 DeerFlow 能够 _几乎做任何事_。

一个标准 Agent Skill 是一个结构化的能力模块——一个 Markdown 文件，它定义工作流、最佳实践以及对支持资源的引用。DeerFlow 自带用于研究、报告生成、幻灯片创建、网页、图像和视频生成等的内置 skills。但真正的强大之处在于可扩展性：添加你自己的 skills，替换内置 skills，或将它们组合成复合工作流。

Skills 是逐步加载的——仅在任务需要它们时加载，而不是一次性全部加载。这使上下文窗口保持精简，并让 DeerFlow 即使在 token 敏感的模型上也能良好工作。

当启用延迟 skill 发现时，`describe_skill` 会按照有界的、Unicode 规范化的意图词项在名称和描述中的覆盖度对已安装 skills 进行排名。因此，自然的多词项请求可以找到相关的 skill，而不需要精确匹配某一个短语，同时精确的 `select:` 和必需名称的 `+prefix` 查找仍然可用。排名搜索最多使用 256 个字符，并最多返回五个结果；精确的 `select:` 列表不会被截断，并返回所有请求的 catalog 匹配项。

一个 skill 目录是一个包边界：一旦 DeerFlow 找到其 `SKILL.md`，该包下的嵌套 `SKILL.md` 文件（例如评估 fixtures）仍作为支持数据，而不会被注册为运行时 skills。这适用于托管的集成包以及公共和自定义 skills。没有自己的 `SKILL.md` 的命名空间目录仍然可以对嵌套 skills 进行分组。

发现过程会遵循操作员管理的目录符号链接，但会跳过指回祖先目录的链接，这样循环命名空间就不会重复重新扫描同一棵树。指向同一外部 skill 树的独立链接仍然受支持。

Skill Markdown 和捆绑的文本资源使用 UTF-8。Skill-creator CLI 和审查工具显式地以 UTF-8 读写文本，以便本地化的 skills 在不同操作系统上行为一致。
用户可以通过以 `/skill-name` 开头发起请求，为单个 turn 显式激活一个已启用的 skill，例如 `/data-analysis analyze uploads/foo.csv`。DeerFlow 会将该 skill 的 `SKILL.md` 作为隐藏的当前 turn 上下文加载，同时让 base prompt 仍仅限于 skill metadata。斜杠激活会遵循已禁用的 skills、custom-agent skill 白名单，以及诸如 `/new` 和 `/help` 之类的现有 channel 命令。

在某个 answer 加载了 skills 之后，其 toolbar 会包含 **Skills used**。悬停或点击该图标可查看 skills 及其来源；悬停在某个 skill 名称上会为其加下划线。选择一个 skill 可在可调整大小的 side panel（移动端为 drawer）中查看其 `SKILL.md`。该视图使用在成功执行已配置的 read-tool 加载或显式斜杠激活期间捕获的 snapshot，因此之后对某个 skill 的编辑或删除不会重写其历史记录。重复加载在每次 run 中只出现一次，按首次加载顺序排列。范围读取和有界 snapshot 会被标记为 partial；没有捕获证据的较早对话不会显示此菜单。Copy 会返回捕获的 Markdown，包括 YAML frontmatter。Package-relative 链接和图片仍作为可读引用保留，而不会导航离开该对话。通过其他工具（例如 shell 命令）执行的 skill 加载，不会从 answer 文本中推断。
已启用 skill 的 `allowed-tools` 策略仅在该 skill 被显式 slash-activated 或经过 `read_file` 加载后被捕获到 agent 的 active skill context 中之后才适用。仅仅在 custom agent 或 subagent 的 `skills` allowlist 中启用、通告或列出某个 skill，并不会缩减该 agent 的正常工具集；subagent 使用与 lead agent 相同的渐进式发现与激活策略。在一次 slash-activated 运行期间，该显式 skill 的策略是权威的：读取另一个 `SKILL.md` 可以提供指令，但不能扩大 slash skill 的工具。没有 slash activation 时，实际加载到 active context 中的 skill 的策略保持其并集语义。一旦激活，该策略会同时过滤模型可见的工具 schema 和工具执行。框架发现工具（`tool_search` 和 `describe_skill`）保持可用，因此被允许的 deferred tool 或已安装的 skill 仍可被发现，但发现与提升绝不会授予执行从 `allowed-tools` 中省略的业务工具的权限。`task` 并非框架豁免项；一个限制性 skill 必须显式列出它，才能委托给 subagent。每步策略决策是内部运行时上下文，并从可观察或持久化的上下文副本中移除。Registry 失败以及没有剩余有效 skill 的 active set 会 fail closed 到框架安全工具；只有当另一个有效 active skill 仍然存在时，个别陈旧路径才被忽略。这是尽力而为的行为作用域，而不是硬安全边界：通过另一个工具加载 skill 指令不会被捕获，并且 active-skill 条目可能会从有界上下文中被逐出。
当你通过 Gateway 安装 `.skill` 归档时，DeerFlow 接受标准的以空格分隔的 `allowed-tools`、可选的 frontmatter 元数据以及 Claude 兼容的 `argument-hint` 字段，而不是拒绝原本有效的外部 skills。`allowed-tools` 仍支持 YAML 列表，并保留精确的运行时名称。诸如 `WebFetch`、`WebSearch`、`Glob`、`Grep` 和 `Read` 这样的精确可移植拼写会映射到 DeerFlow 的 `web_fetch`、`web_search`、`glob`、`grep` 和 `read_file` 工具；小写或其他未知的标量名称保持不变，以便自定义工具和 MCP 工具保留其精确的运行时拼写。类似 `Bash(tvly *)` 的带括号条目会被 token 化为一个字母条目，包括空格、带引号的文本和转义括号，但仍保持不生效，因为 DeerFlow 不会检查工具参数；仅当 skill 可能使用完整的 Bash 工具时才声明 `bash`。

禁用 skill 还会将其从沙箱文件系统视图中移除，因此 shell 命令和结构化文件工具遵循相同的启用状态。本地、Docker/AIO、hostPath provisioner 以及新建的 E2B 沙箱从仅包含已启用项的投影中获取 `/mnt/skills`，这些投影会在公共、自定义、legacy 或托管的集成 skills 被切换、编辑、创建、删除或安装时更新。结构化的 `read_file` 调用（包括行范围和 read-before-write 检查）使用沙箱 provider 的挂载映射，因此在获取沙箱时捕获的用户身份仍然是权威的。托管的集成包保持共享，而它们投影出的文件系统可见性遵循每个用户的启用状态。多 worker 的 Gateway 在重建用户投影时会重新读取磁盘上的启用状态，因此由一个 worker 处理的切换会被另一个 worker 的下一次沙箱获取所遵循。现有 E2B 沙箱会保留其创建时的快照，直到它们被重新创建。由 PVC 支持的 provisioner skills 目前会保留其配置的 PVC 快照/布局；动态 PVC 物化会单独跟踪。

```
# sandbox 容器内部的路径
/mnt/skills/public
├── research/SKILL.md
├── report-generation/SKILL.md
├── slide-creation/SKILL.md
├── web-page/SKILL.md
└── image-generation/SKILL.md

/mnt/skills/custom
└── your-custom-skill/SKILL.md      ← 你自己的

/mnt/skills/integrations
└── lark-cli/lark-doc/SKILL.md      ← 受管理，只读
```

内置的 `image-generation` skill 支持 Gemini、MiniMax 以及兼容 OpenAI 的
Images API。使用 `IMAGE_GENERATION_PROVIDER=openai` 选择后者，然后配置
`IMAGE_GENERATION_API_KEY`、`IMAGE_GENERATION_BASE_URL` 和
`IMAGE_GENERATION_MODEL`。对于容器化的 sandbox 或显式启用的本地主机
shell，通过 `sandbox.environment` 暴露这些变量；sandbox 命令有意不
从 Gateway 进程继承 API key。
本地 provider 原样使用解析后的配置值，且 request 作用域的 secret 会覆盖
operator 值。本地 bash 输出和命令错误会遮蔽 credential 值，同时保留
模型名和 base URL 等无害设置的可读性。

对于 `LocalSandboxProvider`，这是一条受管理的 tool 路径边界，而非主机
文件系统隔离。显式的 per-Agent skill 策略仅在主机 bash 被禁用（默认
情况）时才被接受，因为主机子进程可以不使用 provider 的虚拟路径映射
而直接访问规范化路径。当文件系统边界必须与 shell 访问同时保持可执行
时，请使用 Docker/AIO、Kubernetes provisioner 或 E2B。

受管理的 integration 会安装共享的只读 skill 包，而不会将它们混入
custom skill。Lark/Feishu CLI integration 位于
`Capability Center → Plugins → Lark / Feishu` 下；管理员在
`{DEER_FLOW_HOME}/integrations/skills/lark-cli` 下一次性安装或升级官方
`lark-*` 包，每个用户都会发现同一个包，并各自拥有独立的启用状态。
每个用户的应用配置和 OAuth 数据保持隔离，位于
`{DEER_FLOW_HOME}/users/{user_id}/integrations/lark-cli/{config,data}`。这些密钥目录的权限被限制为 `0700`，普通凭据文件被限制为 `0600`，并且会拒绝符号链接。

安装完成后，用户可以点击 **Connect Lark** 打开浏览器授权链接；无需进行终端授权。同一个 UI 可以请求额外的权限域，例如 Calendar、Docs 或 Drive，也可以请求 `lark-cli` 报告的特定 OAuth scope。低成本的状态刷新只检查本地凭据树，因此在显式完成浏览器流程执行实时 token 验证之前，UI 会报告 **Credentials configured (not live-verified)**。此后该操作仍保持为 **Reconnect Lark**，以便用户可以替换或扩展授权。如果 agent 在对话过程中遇到缺少 Lark 授权的情况，托管的 `lark-shared` 指引会通过 `/workspace/capabilities?tab=plugins&plugin=lark` 将用户引导回同一个 plugin 配置。

配置完成后，**Change Lark app** 允许用户在不重新安装的情况下，将其 DeerFlow 账号指向另一个 Lark/Feishu app——既可以粘贴现有 app 的 App ID / App Secret，也可以在浏览器中重新注册一个 app。切换是按用户进行的（绝不会触碰其他用户的凭据），它会先通过官方 CLI 的实时 tenant-token 探测验证新凭据，然后才替换当前生效的 app，并撤销/移除先前 app 的 OAuth token。被拒绝的凭据变更不会取代正在进行中的设置或授权流程。在 CLI 存储替换用的 app 之前，先前的 OAuth 数据会被清除，因此新的基于文件的 keychain secret 在重新连接期间仍然可用。随后 DeerFlow 会立即为新绑定的 app 打开浏览器授权，因此切换最终会得到一个可用的连接。

安装 Lark skill pack 时会从 GitHub 解析最新的官方 `larksuite/cli` release，并在安装时下载该版本的 skills，因此
Gateway 需要出站互联网访问以执行该步骤（如果发布版本查找失败，它会回退到保底的固定版本）。设置页面显示已安装的版本，并在可用时显示最新发布的版本，以便管理员可以通过重新安装来升级。气隙部署可以预置归档文件，并将 `DEER_FLOW_LARK_CLI_SKILLS_ARCHIVE` 指向本地文件。完整性不依赖于固定的归档字节哈希（GitHub 不保证源归档字节的稳定性）；相反，下载被限制在官方 GitHub 主机上，每个归档成员都通过结构安全检查，并且记录有效安装的技能树（包括 DeerFlow 注入的共享指南）的内容哈希，以便在重新安装时内容变化可审计。

当 `sandbox.use` 选择 AIO 提供程序时，同一次安装还会下载官方 Linux amd64 和 arm64 CLI 发布归档，验证其发布的 SHA-256 校验和，安全地提取每个架构的一个可执行文件，并将生成的运行时以只读方式挂载到 `/mnt/integrations/lark-cli/runtime`。该挂载中的架构选择启动器使 `lark-cli` 在沙箱 `PATH` 中可用。气隙 AIO 部署可以预置一个无符号链接的运行时树，其中包含 `bin/lark-cli` 以及 `linux-{amd64,arm64}/lark-cli` 两个文件，并将 `DEER_FLOW_LARK_CLI_SANDBOX_RUNTIME_DIR` 设置为该目录。

> **沙箱信任边界：** 浏览器永远不会接收 Lark 应用密钥，但 agent 对话在沙箱内运行 `lark-cli`，因此每用户凭证目录被挂载到其中：`config`（保存长期有效的 `appSecret`）以**只读**方式挂载，其原本为空的 `config/locks` 子目录被以可写方式覆盖挂载，用于 `lark-cli` 协调文件，而 `data`（可刷新的 OAuth token）是可写的。带有凭证的 config 和 data 挂载对于 agent 在那里运行的任何进程仍然是*可读的*，因此代码
> 通过 tool result 中的 prompt injection 到达的（攻击者）可以读取它们。在 sidecar
> credential-broker 后续工作将这些 mount 从 sandbox 执行中移除之前，请将
> sandbox 视为处于 Lark credential 信任边界之内。

对于远程/Kubernetes 部署（provisioner 后端），sandbox 的
`lark-cli` runtime 可以改由一个可选的 init container 提供，该容器将二进制文件复制到
共享的 `emptyDir` 中——无需在安装时从 GitHub 下载，也无需 hostPath/PVC runtime
mount。在 [`docker/lark-cli-init`](docker/lark-cli-init/README.md) 下发布该镜像，并在
provisioner 上设置 `LARK_CLI_INIT_IMAGE`（使用 Helm chart 时，为
`provisioner.larkCliInitImage` / `provisioner.larkCliBrokerImage`）；未设置时保持关闭
（沿用旧行为）。Lark 集成状态
（`GET /api/integrations/lark/status`）会报告 `sandbox_runtime_mode`、
`sandbox_runtime_probed` 和 `sandbox_runtime_ready`。
`sandbox_runtime_probed` 标记 runtime 就绪状态是否实际被评估过；来自较旧后端的响应
可能会省略该标志，在这种情况下，Settings 变更缓存会保留上次探测到的 runtime 字段，
而不是用未评估的 fallback 覆盖它们——因此 Settings UI 会显示在聊天时 `lark-cli`
是否实际存在于 sandbox 中，而不是用一个绿色状态掩盖之后出现的 `command not found`。

在 Lark broker 模式下，AIO 新启动的 Bash 会关闭继承的管道 stdin。持久终端命令保留其
输入；shim 忽略终端 stdin。显式 pipeline、heredoc 和文件重定向仍正常提供输入，shim
仅在 EOF 之后转发该输入。stdin 空闲超时会中止执行而不运行命令，broker 执行日志会省略
参数值。有关超时设置和镜像重建要求，请参阅
[broker 镜像指南](docker/lark-cli-broker/README.md)。
如果受信任的操作员通过 MinIO、NFS 或 CSI 等外部挂载来管理已配置的 skills 目录，那么管理员可以在更改文件后调用 `POST /api/skills/reload`。这会使处理请求的 Gateway 进程中的 skill prompt 缓存失效，最多等待有界刷新超时，然后在可写配置目录中推进一个持久化重置标记（`.extensions_config.json.skills-cache-reset.json`）。挂载该目录的每个 Gateway worker 或 Pod 会在其下一次 prompt 构建后约一秒内注意到该标记，并重新扫描最新文件，因此一次调用就能到达共享该卷的每个副本；响应会报告 `scope: shared_config`，或者在没有可用的 extensions config 路径时报告 `scope: process`。正在运行的任务保持不变。通过 API 进行的 skill 安装、编辑、删除、回滚以及启用/禁用切换会发布相同的标记，因此在一个副本上所做的更改无需重启即可在其他副本上生效。loader 级别的文件系统故障会返回通用服务器错误，并保留最后一次成功加载的进程缓存，而不是发布空的 catalog。具有独立文件系统的副本不在覆盖范围内。直接挂载写入会绕过 DeerFlow 的 install/edit API 所应用的验证、SkillScan 和历史记录，因此只有由操作员控制的系统才应具有写访问权限。
Skill 安装和 agent 管理的 skill 编辑会先经过 **SkillScan**——一个原生确定性安全扫描器，然后才进入基于 LLM 的 skill 扫描器。Phase 1 离线运行，不依赖 Semgrep/OpenGrep，会阻断高置信度的 `CRITICAL` 发现（如私钥或 shell 执行），并将警告类发现传递给 LLM 扫描器进行上下文审查。代码文件（`scripts/` 下的任何内容、带 `.py`、`.sh` 或 `.js` 等脚本后缀的文件，或以 `#!` 开头的无扩展名文件）如果不是无 NUL 的 UTF-8 文本，会产生警告，并且仍会通过有损解码进行分析，因此单个杂散字节无法将其从 `CRITICAL` 检查中隐藏。审核适配器在解析所需的 JSON 决策之前，会先规范化纯文本模型响应和 LangChain Responses API 文本块。Python 实例客户端外传检查遵循最小同作用域证据链：绑定到已知客户端构造器的简单名称、可选的名称到名称别名，以及由该构造器支持的实际上传出方法或上下文管理器使用。构造器根必须是已被证明的导入；仅看起来像规范名称的裸名称不会被推断为模块。嵌套作用域不继承客户端句柄，仅继承在外层作用域中从未被重新绑定的构造器导入别名。推导式、带 walrus 的语句、注解、复杂绑定目标、不支持的操作以及有歧义的分支流不会从该信号产生发现；被跳过的构造会保守地使其可能绑定的每个名称失效，因此陈旧的客户端状态无法产生发现。此尽力而为分析达到的确定性工作预算或递归限制不会丢弃已为该文件收集到的发现。在 `config.yaml` 中设置 `skill_scan.enabled: false` 只会禁用确定性分析器；安全归档提取和 LLM 扫描器仍会运行。
Windows 脚本（`.bat`、`.cmd`、`.ps1`、`.psm1`、`.js`、`.jse`、`.vbs`、`.vbe`、`.wsf`）、HTML 应用程序（`.hta`）以及 scriptlet（`.sct`）即使在 `scripts/` 之外也算作代码，无论文件名大小写如何。它们同时接受 SkillScan 分析和安装程序的可执行代码策略。
SkillScan 会对管道传入常见 shell 的远程下载发出警告，包括 `env` launcher、sudo、interpreter 路径以及 shell 行续接符。它能将环境变量转储与 `env` 命令区分开来，包括赋值和 GNU 拆分字符串转义。Shell 解析和拆分展开是有界的；达到限制时会保留已检测到的关键发现。管道传入 `jq` 和 `tee` 等非 shell 工具不会触发此警告。

SkillScan 以大小写不敏感的方式处理 HTTP/HTTPS scheme 拼写和 HTTP hostname，并将方括号形式的 IPv6
loopback（`[::1]`）URL 识别为本地。外部 IPv6 endpoint 仍会触发网络发现，
且 cloud-metadata hostname 检测是大小写不敏感的。

对于 Python credential 映射，SkillScan 检查字面值，同时将普通字典键视为标签。诸如 `tokens = {"access_token": os.getenv("ACCESS_TOKEN")}` 这样的映射不会报告 hardcoded credential。匹配已识别 cloud 或 API token 格式的键仍会作为 embedded credential 进行检查。

SkillScan 会阻止嵌入的传统和现代 `sk-` API token，包括 OpenAI project、service-account 和 admin key 以及 Anthropic key，即使在未进行 secret 赋值的 Bearer header 中也是如此。Token 主体可包含 `-` 和 `_`；查找证据会被完全脱敏。占位符示例不会抑制对同一文件中后续 credential 的检测。计划任务通知摘要也会在发送到外部 IM 平台之前对这些 key 格式进行脱敏。
DeerFlow 还随附了 **skill-reviewer**，一个用于只读 skill 质量审查的公共 skill。它使用内置的 `review_skill_package` 工具检查已安装的 skills、本地包、归档或粘贴的 `SKILL.md` 内容，而不会激活目标 skill、绑定其 secrets、执行其脚本或安装它。该工具向 model context 返回一个紧凑的、tag 中和化的 JSON payload，并将完整的原始审查 payload 保留在 tool artifact 中，供程序化消费者使用。确定性的审查核心复用 DeerFlow 解析和 SkillScan 事实，在 `contracts/skill_review/` 下生成带版本的 JSON contracts，并且可以从 backend CLI 运行：

```bash
cd backend
uv run python -m deerflow.skills.review.cli ../skills/public/data-analysis --format text --fail-on error --fail-on-incomplete
```

公共 skill 的 CI waivers 是 `.github/skill-review-waivers.v1.json` 中精确的、会过期的例外。因为只有受信任的 base manifest 才能抑制 finding，所以通过先合并一个仅 manifest 变更来安全地预授权一个更改文件的 pull request，该变更在 `preapproved_file_sha256s` 中列出经审查的未来完整文件 SHA-256；然后文件更改可以在后续 pull request 中落地。

Tools 遵循相同的理念。DeerFlow 自带一个核心 toolset —— web search、web fetch、rendered web capture、file operations、bash execution —— 并通过 MCP servers 和 Python 函数支持自定义 tools。捆绑的 DDG、Brave、Tavily、SearXNG 和 Serper search providers 接受可选的 `time_range`，取值为 `day`、`week`、`month` 或 `year`；省略它会保留现有的搜索行为。对于 DDG recency searches，DeerFlow 会排除忽略时间限制的 DDGS backends。替换任何东西。添加任何东西。
对于 DDG 网页搜索和 DDG 图片搜索，`config.yaml` 中的 `max_results` 可以是正整数或环境变量引用，例如 `max_results: $DDG_MAX_RESULTS` 并设置 `DDG_MAX_RESULTS=5`。配置的值优先于工具调用的 `max_results` 参数。无效值（例如 `abc`、空字符串或 `3.5`）、零和负数会产生警告，并回退到默认的 5 条结果。

Stdio MCP 服务器可以在 `extensions_config.json` 中设置 `cwd`，当它们的入口点或数据文件依赖于特定的工作目录时。该设置对发现和工具调用都适用；参见 [MCP 配置](backend/docs/MCP_SERVER.md#stdio-working-directory)。省略、`null` 或空值会保留默认工作目录。

Tavily `web_search` 还可以在其 `config.yaml` 工具条目中接受可选的 `include_domains` 和 `exclude_domains` 列表，以控制搜索来源。非空的 `include_domains` 使用 Tavily 的 `filter` 模式将结果限制到那些域名。这些是部署设置；模型仍然只提供 `query` 和可选的 `time_range`。省略过滤器会保留现有的 SDK 请求；显式空列表会被转发，并且不施加此类限制。参见[工具配置示例](backend/docs/CONFIGURATION.md#tools)。

Serper 网页搜索和图片搜索可以通过 `SERPER_BASE_URL` 和该提供商的 `SERPER_API_KEY` 使用另一个兼容 Serper 的提供商。每个工具可以改为在 `config.yaml` 中设置自己的 `base_url` 和 `api_key`；每个请求从一个配置快照中读取它们。使用带主机的绝对 HTTP(S) base URL，不带 `/search`、`/images`、查询字符串或片段。无效覆盖会在 HTTP 之前返回配置错误；空白环境变量值会保留 Serper 的默认值，除非工具覆盖它们。参见 [Serper 端点](backend/docs/CONFIGURATION.md#serper-endpoints) 了解优先级以及提供商如何接收 API key。
Serper `web_search` 也支持部署级的 `include_domains` 和
`exclude_domains`。它会检查返回的 URL host（包括子域），其中排除优先。过滤器可能返回更少的结果，包括零个；不会发起补充请求。这选择的是来源，而不是事实准确性或全局 URL 访问策略。model 参数和图像搜索保持不变。
有关校验和查询长度限制，请参阅 [Serper 配置](backend/docs/CONFIGURATION.md#serper-source-filters)。

当使用 Tavily 进行 `web_fetch` 时，提取出的无标题页面会使用其 URL 作为标题；其内容仍可供 agent 使用。
Chat 工具步骤标题接受页面第一个 H1 标题前的开头空行以及最多三个空格。缩进代码（包括混合使用空格和制表符）不会用作标题；该工具步骤会回退到 URL。
Tavily search 和 fetch 各自从 `config.yaml` 中各自的工具条目读取 `api_key`，省略时回退到 `TAVILY_API_KEY`。Fetch 不会复用 search 条目的 key，因此 search 可以使用不同的 provider。如果你之前只在 `web_search` 下配置了共享的 Tavily key，也请在 `web_fetch` 下设置它，或对两者都使用 `TAVILY_API_KEY`。

#### 导出自定义 Skills

管理员可以从 **Capability Center → Skills → My skills → View details → Export** 导出自己的自定义 Skills。查看文件列表和声明的环境要求，然后选择 **Download .skill**。该归档包含当前已保存的 skill，包括支持文件和空目录；已禁用的 Skills 也可以导出。如果 skill 在预览后发生变化，请在下载前刷新文件列表。使用 **Install .skill** 在另一个 DeerFlow 实例上导入该归档；现有名称冲突和常规安装安全检查仍然适用。
skill 文件夹之外的账户设置、对话和历史记录均被排除。该文件夹内的文件会原样保留，包括作者放置其中的任何 credentials;文件名通知仅供参考。请在目标端配置 dependencies 和 credentials。链接的文件夹/文件、硬链接、不受支持的可执行二进制文件、嵌套的 `SKILL.md` 文件以及不可移植的路径无法导出。导出功能支持具备 descriptor-relative no-follow 文件系统 API 的主机(Linux/macOS);不受支持的主机会显式失败。限制:4096 个 ZIP 条目、每个文件 64 MiB、内容/归档总计 100 MiB,以及 1 MiB frontmatter。不支持 YAML aliases 和过度复杂的声明。在 POSIX 导入时会保留普通脚本的可执行语义,但不会恢复特殊权限。参见[导出 API 契约](backend/docs/API.md#export-a-custom-skill)。

#### Claude Code 集成

`claude-to-deerflow` skill 让你可以直接从 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 与运行中的 DeerFlow 实例交互。发送研究任务、检查状态、管理 threads —— 全程无需离开终端。

**安装该 skill**:

```bash
npx skills add https://github.com/bytedance/deer-flow --skill claude-to-deerflow
```

然后确保 DeerFlow 正在运行(默认位于 `http://localhost:2026`),并在 Claude Code 中使用 `/claude-to-deerflow` 命令。

**你可以做什么**:

- 向 DeerFlow 发送消息并获取流式响应
- 选择执行模式:flash(快速)、standard、pro(规划)、ultra(sub-agents)
- 检查 DeerFlow 健康状况,列出 models/skills/agents
- 管理 threads 和对话历史
- 上传文件以供分析

**环境变量**(可选,用于自定义 endpoints):

```bash
DEERFLOW_URL=http://localhost:2026            # 统一 proxy 基础 URL
DEERFLOW_GATEWAY_URL=http://localhost:2026    # Gateway API
DEERFLOW_LANGGRAPH_URL=http://localhost:2026/api/langgraph  # LangGraph API
```

完整 API 参考请参见 [`skills/public/claude-to-deerflow/SKILL.md`](skills/public/claude-to-deerflow/SKILL.md)。

### 私有知识检索（RAGFlow）

回答可以引用检索到的 RAGFlow 证据，并带有可点击的知识引用。点击一条引用，或答案的知识来源列表中的条目，即可查看原始检索摘录、dataset 和 document 名称，以及 RAGFlow 提供时的页码。这些是随对话保留的检索时快照，包括由普通 `task` subagent 转发的来源；在重新加载对话后仍可查看。摘录不是完整 document 的实时副本：RAGFlow 中的更改不会重写过去的证据。缺失的来源记录会显示为不可用，而不是变成猜测的链接。来源快照不会增加知识管理页面，也不会暴露 RAGFlow API key。持久化批量导出和独立 Markdown 文件不包含这些交互式对话来源记录。Sources 部分中的普通 document 标题链接会打开与内联引用相同的证据。当工具输出预算生效时，只有能纳入的完整证据条目仍可引用；被省略的来源会被报告，而不是为被截断的摘录保留来源记录。

DeerFlow 可以选择性连接到租户范围的 RAGFlow 部署。`knowledge_search` Agent 工具会解析已配置的 dataset 范围，按 embedding model 对 dataset 分组，并并行检索这些分组，这样混合 embedding model 不会导致 provider error。Dataset ID 和 API key 绝不会暴露给 model。可选的 `list_knowledge_bases` 工具仅返回名称。

主聊天和 custom-agent 聊天可以选择性地在 mode control 旁边显示一个页面本地的、仅图标的 **Knowledge** 选择器。其持续高亮表示知识检索处于活动状态；中性状态表示检索关闭。在 `config.yaml` 中设置 `knowledge_base.scope_selection_enabled: true`
在使用内置 RAGFlow `knowledge_search` provider 来允许所有 permitted datasets、选定的 datasets/files，或某一 turn 不进行 retrieval 时。同一个 config flag 控制两种 chat types；当被禁用时，两个 composer 都不显示 selector 或提交 scope。当页面刷新或打开另一个 conversation 时，该选择会重置为 custom agent 保存的 default（或未绑定时为 all）；每条发送的 human message 都会保留一个不可变的 scope snapshot，用于 replay 和 history。Gateway 会验证每个 snapshot，将其与 operator 的 dataset allowlist 求交集，将 execution-only scope 传播到 native 和 durable subagents，并将其从 model inputs 和 external traces 中移除。Client-supplied 内部 runtime controls 和 credentials 也会在 execution 或 checkpoint persistence 之前从 run context 中剥离。Idempotent retries 同时接受 canonical snapshots 和 legacy raw run inputs，从而在 upgrades 之间保持 retry 兼容性。Custom agents 可以从 **Agents → Agent settings** 保存一个 **Default knowledge** 选择，包括可选的 file filters 或 retrieval off。选择所有 knowledge bases 会清除 binding。相同的 `knowledge_scope` field 在 agent create/update APIs 和 agent 的 stored configuration 中可用；省略的 updates 会保留它，而 `null` 会清除它。它是一个 default，而不是 authorization boundary：显式的 per-message selection 会覆盖它，而 operator 的 allowlist 在 retrieval time 仍然适用。没有 message scope 的 Gateway runs（包括 scheduled 和 channel turns）即使 composer selector 被隐藏，也会使用并 snapshot 保存的 default。Regenerate/resume 保留原始 turn 的 scope，包括 legacy unscoped turns，而不是采用后续的 configuration changes。Unknown 或 unavailable selections 永远不会扩大 retrieval。Idempotent retries 在添加、更改或清除 default 时保留原始 run 和 scope，包括在此 feature 之前接受的 unscoped runs。
此默认值适用于 Gateway 托管的 custom-agent 轮次；直接 harness/client 集成继续提供自己的 execution scope。

`knowledge_base` 块是 provider-neutral 的，仅控制 knowledge 能力与 selector 是否启用。RAGFlow 连接、dataset allowlist 和检索参数（`base_url`、`api_key`、`datasets`、`page_size`、thresholds 和 output limits）必须在 `tools[].name: knowledge_search` 条目上配置；它们绝不会从 `knowledge_base` 读取。
Custom-agent 聊天请求将所选 agent name 同时作为 `assistant_id` 和 `context.agent_name` 携带，因此 Gateway scope admission 和运行时 agent 加载使用同一身份。主聊天请求使用 `lead_agent`；仅当共享配置启用 RAGFlow provider 时，两种身份才被准入。
在回答待处理的 clarification 时，显式提交的当前 selector snapshot 优先；省略它的客户端继承上一轮已接受的 scope。Edit-and-regenerate 遵循相同的 fallback，并且只有在 dataset 从 all files 切换为 selected files 后，才会加载 file catalog。
此版本不会向 workspace sidebar 添加独立的 Knowledge 条目，也不会添加 DeerFlow knowledge-management 页面；请直接在 RAGFlow 中创建、上传、解析和删除 datasets 与 documents。

每条 message 仍然最多可选择 1000 个 documents。当从单个 dataset 中选择超过 100 个 documents 时，DeerFlow 会以最多 100 个为一批进行 validate，同时保留完整选择。如果任何批次包含不可访问或不可搜索的 document，则 retrieval 会被拒绝。
高级部署可以通过 `config.yaml` 中的 `authorization.enabled` 启用可插拔授权。已配置的 `AuthorizationProvider` 会在被拒绝的工具到达模型或延迟工具目录之前对其进行过滤，然后在每次业务工具执行之前，通过现有的 guardrail middleware 再次检查同一个 provider。Gateway `threads:*` 和 `runs:*` 路由权限源自同一个 provider，而现有的所有者检查和仅管理员的管理门控仍然有效。每个启动或启用未来 Agent run 的 HTTP 路由都需要 `runs:create`：这包括无状态的 `POST /api/runs/stream` 和 `POST /api/runs/wait` 端点，以及定时任务的创建、更新、恢复和手动触发变更。定时任务变更保留其现有的 `threads:write` 要求，并且当请求体中提供可选的 thread ID 时，无状态路由会单独强制执行所有权检查。生成的 `tool_search` 仅当它作为当前构建的已过滤延迟目录的前端时，才能绕过第二次工具检查。模型访问遵循相同的 provider：Gateway `models` 列表按 principal 过滤，`model:use` 在模型详情请求上强制执行，并在运行时解析 agent 的模型时再次强制执行；被拒绝的默认模型会回退到第一个同样通过 `model:use` 的剩余候选模型。内置的 RBAC provider 支持按角色的 `tools`、`routes`、`models`、`skills` 和 `sandbox` 允许/拒绝策略，并验证 `default_role` 命名了一个已配置的角色；授权默认禁用。在 provider 的 `roles` 映射中声明的自定义角色，通过 admin API（`GET /api/v1/admin/users`、`PATCH /api/v1/admin/users/{id}`；仅管理员，最后一个管理员的降级受到保护）将其分配给用户后即可访问——一个已声明但无人持有的角色不授予任何权限。参见 `config.example.yaml` 和 [authorization RFC](docs/plans/2026-07-10-pluggable-authorization-rfc.md)。
后续建议在调用所选模型之前也会检查 `model:use`，包括未提供名称时的默认模型。被拒绝的模型会返回 HTTP 403，且不发起 LLM 调用；authorization-provider 失败则遵循所配置的 `fail_closed` 策略。

对于支持 vision 的 agent，`view_image` 以及随后的模型上下文图像读取也需要 `sandbox:execute`。仅允许工具名称并不会授予图像文件访问权限；被拒绝 sandbox 执行的角色在其权限变更后无法重新读取此前记录的图像元数据。外部运行输入和 thread-state 更新不能设置 `viewed_images` 或 `thread_data`；当从宿主机副本读取已保存的图像时，其路径必须解析到当前用户的 thread 以及所记录的虚拟图像路径。
高级部署还可以通过在 `config.yaml` 或 `extensions_config.json` 中的 `extensions.middlewares` 下声明 `AgentMiddleware` 类来扩展 agent runtime 本身。每个条目要么是一个 `module.path:ClassName` 字符串（零参数构造函数），要么是一个对象 `{class, kwargs}`，其 `kwargs` 会传给构造函数。`kwargs` 的值必须是 JSON 类型（object、array、string、number、boolean 或 null）；YAML 的 date 和 timestamp 会被强制转换为 ISO 字符串，以便与 JSON 保持一致。DeerFlow 会把同一份配置列表加载进 lead-agent 和 subagent 流水线，位置在其内置 runtime middlewares 和 loop/token guards 之后，但在 terminal-response/safety/clarification 尾部之前，因此企业分支可以添加领域护栏、tool-call 治理或可观测性钩子，而无需修补内置的 middleware 构建器。缺失的包、无效的类、损坏的模块以及构造函数错误都会在 agent 创建时显式失败。请将 `config.yaml` 和 `extensions_config.json` 视为由操作者控制的可信文件：middleware 路径即代码执行，就像自定义 tool、model、sandbox、guardrail、MCP server 和 MCP interceptor 声明一样。Gateway 的 skill/MCP 开关端点会保留该字段，但不会为 `extensions.middlewares` 暴露 API 写入路径。目前尚不支持将 lead-only 与 subagent-only 的 middleware 列表分开配置。

对于可打包且可配置的 runtime 集成，请使用 DeerFlow 的 extension manager。
它接受 Python 包需求、公开的 HTTPS Git URL 或本地目录，将
包安装到后端专用的 `extensions` 依赖组中，更新
`backend/uv.lock`，并向 `config.yaml` 中仅在启动时使用的顶层 `plugins:` 列表
添加一条已启用的条目：

```bash
# PyPI — pin a version for a reproducible deployment
make extension-install SOURCE="deerflow-extension-acme==1.2.3"

# Public HTTPS Git — pin an immutable commit
make extension-install \
SOURCE="git+https://github.com/acme/deerflow-extension-acme.git@0123456789abcdef0123456789abcdef01234567"

# 本地包 — 使用绝对路径可避免 Make 后端相对工作目录的问题
make extension-install SOURCE="$PWD/examples/deerflow-extension-example"

make extension-list
make extension-upgrade SOURCE="$PWD/examples/deerflow-extension-example"
make extension-disable NAME=acme
make extension-enable NAME=acme
make extension-remove NAME=acme
```

安装是交互式的，因为包安装可能会执行 Python build hooks，而且加载后的 extension 之后会以 Gateway 权限运行。对于已经审查过的 source，自动化可以显式确认这一边界：`cd backend && uv run --frozen --no-group extensions deerflow extensions install <source> --yes`。
该 manager 要求 uv 0.8.0 或更新版本；所提供的 Docker images 固定使用 uv 0.11.1。
其他直接
命令包括 `deerflow extensions upgrade SOURCE`、`list`、`enable NAME`、`disable NAME` 和 `remove NAME`；
`NAME` 可以是 extension 名称、Python distribution 或 `module:install` 值。不要
把凭据放进 source URL —— 带有嵌入 userinfo 或看起来像凭据的
query parameter 的 URL 会在 uv 运行之前被拒绝。远程 Git source 必须使用公开 HTTPS；SSH
Git URL 会被拒绝，因为自带的 Docker builder 不会转发宿主机的 SSH
凭据。从 loopback URL 安装对本地工具链是允许的，但会发出警告，因为
记录在 lock 中的 `127.0.0.1` 在 Docker builder 内部代表的是另一台机器。

一个受管理的包恰好声明一个标准 PEP 621 entry point：

```toml
[project.entry-points."deerflow.extensions"]
acme = "acme_deerflow_extension:install"
```

该 callable 使用独立的 `deerflow-extension-api` contract，并且可以注册多种
contribution 类型：位于语义 lead/subagent model 或 tool 位置的隔离 middleware，
lead 和 subagent task-lifecycle hooks，针对 DeerFlow 所拥有的 model calls 的 observers，这些
不被 middleware 模型调用 hook 包装（目标、记忆、标题和摘要）、
Gateway 生命周期服务，以及 eager FastAPI HTTP 路由。contract 包不依赖
任何框架；扩展必须声明其导入的 FastAPI、LangChain、LangGraph 或其他
库。
[fetched-content screening 示例](examples/deerflow-extension-jev-screening/README.md)
在可见工具位置贡献了一个此类 middleware。操作员选择启用后，它会对远程工具结果向模型展示的
已清理文本进行分类，当启用 `pii_redaction` 时进行 PII 脱敏，并通过生命周期状态
更新添加建议性警告；它仅导入扩展 contract。

全栈贡献还可以通过
[插件 API](docs/full-stack-plugins.md) 提供浏览器页面、会话操作、
经过认证的后端操作和模型工具。独立的
[bookmarks 示例](examples/deerflow-extension-bookmarks/README.md) 演示了
一个带有持久化用户数据、独立侧边栏页面和只读搜索工具的包。
重新打开书签会通过宿主解析该会话当前的 agent，因此
自定义 agent 会话会保留其原始聊天入口点，包括较旧的书签。
独立的 [Agent teams 示例](examples/deerflow-extension-agent-teams/README.md)
让完整的 Custom Agents 通过原生 `@` 提及、共享消息和
异步对等请求进行协作，并带有独立的团队页面和持久化成员会话。
Capability Center 会在示例尚未安装时列出该示例，并提供本地化安装信息。
安装和激活仍由部署控制；Capability Center 显示插件
信息和状态。浏览器代码作为受信任的同源代码运行。
浏览器 API 和内联 `BrowserModule.code` 传输是实验性的。插件
指南描述了通往 manifest 和打包静态资源的增量路径。
DeerFlow 仅为中间件、生命周期或系统模型观测分配任务作用域的扩展存储。服务在 Gateway 持久化就绪后接收应用作用域的运行时依赖，并在活动运行排空后按相反顺序停止。可选的 `ExtensionRuntimeDeps.run_evidence_reader` 是一个稳定、只读的接口，供审计、评估、同步和可观测性服务使用：它使用不透明的可恢复游标发现已变更的运行，使用 `after_seq` 对已知运行的持久化事件分页，并将权威运行状态与事件证据分开读取。由数据库支持的运行存储使发现游标在 Gateway 重启后仍然有效；内存运行存储仅在当前进程生命周期内提供相同的顺序。事件元数据在此边界处会进行机密信息脱敏，但事件内容原样返回。两个载荷都是分离的快照，因此修改嵌套值不会更改宿主存储的证据。生产 Gateway 向受信任的操作员扩展提供应用作用域的跨用户读取器；嵌入式宿主可以将同一适配器绑定到一个用户。已变更运行的分页包含对保留行的创建和变更，而不是删除墓碑；需要协调删除的消费者必须轮询已知运行的状态，并将缺失结果视为不存在。扩展仍然以 Gateway 权限执行并保留遗留的 `session_factory`，因此该读取器是一个 API 稳定性和最小意外权限边界，而不是用于不受信任的 Python 包的沙箱。扩展 HTTP 路由器挂载在每个宿主路由之后；确定的遮蔽以及进入宿主认证豁免或 CSRF 豁免路径的路由会被拒绝，并附带归因诊断，而无关的路由器会继续加载。由于宿主的公共路径是一个扩展无法进入的保留前缀列表，**每个贡献的端点都需要经过认证的会话**——目前没有办法让扩展暴露一个
未认证的 route，因此入站 provider webhooks 和公共 status endpoints 不在本 release 的 scope 内。在此范围内，一个 extension 通过 `deerflow_extension_api.auth` 区分普通用户与 administrator：`resolve_principal(request)` 返回 caller，`require_admin(request)` 对任何其他人抛出 `PermissionError`，并在无法确定 identity 时 fail closed。Extensions 接收一个 projection——user id、admin flag、internal flag、roles——而从不接收 host 的 auth context。Router startup/shutdown hooks、custom lifespans、Mounts 和 WebSocket routes 不被接受；lifetime resources 属于 `ExtensionService`，而 WebSocket contributions 需要未来由 host 拥有的 authentication/Origin wrapper。Lifecycle 和 system-model callbacks 使用 Gateway 的 canonical notification loop，包括 isolated loops 上的 subagents。

面向用户的 extension routes 可以调用 `deerflow_extension_api.require_run_evidence_reader(request)`（extension API 0.2.2+）。Gateway 要求经过认证的 `runs:read` permission，并将 reader 的 scope 固定到该用户，包括 administrators 和 internal callers。Caller 提供的 IDs 不能改变该 scope。Invisible 和 missing runs 返回相同结果；changed-run cursors 不能直接跨用户重用。可选的 `resolve_run_evidence_reader(request)` 在 host 不支持该 capability 时返回 `None`；必需的 helper 则抛出 `NotImplementedError`。被拒绝的访问会抛出 `PermissionError`。Routes 应将这些异常分别映射到 HTTP 503 和 403；resolver 失败从不回退到 global service reader。

Extension services 可以选择性地接收一个 [host model invoker](backend/docs/extension-model-invocation.md)（extension API 0.2.4+）。Operators 在 `plugins[].host_access.model_invocation` 下显式映射允许的 logical roles；host 处理 credentials、concurrency、timeouts 和 schema-validated output。Admission 是有界的；timed-out provider work
保持其并发槽位直到完成，而 schema 验证在可终止的
子进程中运行。provider 自身的取消会变成 `ModelInvocationFailed`，
而调用方 extension 任务的取消仍正常传播。
没有授权时，capability 为 `None`。

插件顺序是确定性的，每个插件的配置会传给 `install()`，而
`required: true` 会使加载失败中止启动；否则失败会被报告并
跳过。`enabled: false` 会跳过解析和导入。manager 在切换 extension 时保留其
私有的 `config`，并为受管安装写入 `name`、`package`、`use`、`enabled` 和
`required` 元数据。安装记录为 `required: false`，这样后续
损坏的 extension 会被报告而不是阻止 Gateway 启动；当
包的缺失应中止启动时，改为传入 `extensions install <source> --required`。
插件在 Gateway 应用
构建时加载一次，因此 install、enable、disable、remove 以及手动 `plugins:` 编辑都
需要重启 Gateway。由于这会导入 Python 代码，`plugins:` 有意无法通过
API 可写的 `extensions_config.json` 使用。

管理命令在没有 extension 组的情况下通过
`uv run --frozen --no-group extensions` 引导 checkout 环境。Frozen 模式让 `disable` 和 `remove` 即使在
已安装 extension 的远程源或受管快照变得不可用时也能启动，
而全新 checkout 仍可以从现有 lock 创建非 extension 环境。
manager 自身负责后续加锁的依赖事务。
针对一个 checkout 的 mutation 通过进程锁串行化。
失败的 extension 操作会原子地恢复依赖文件和配置及其
原始文件权限，从而保留通过
组权限读取它们的 Gateway 的访问权限。
初始 manager 表面是 create/remove 而不是原地升级：要更改已
安装的源，请保存
其私有的 `plugins[].config`，将其删除，重新安装新的 pin，然后恢复该配置。

本地目录安装会被复制到
`backend/extensions/sources/<normalized-distribution>/`；记录在 lock 中的是这个可部署快照，
而不是原始目录。Git 元数据、虚拟环境、
字节码缓存、符号链接以及可能的凭据文件不会被接受为快照
内容。无论如何都要审查你安装的内容：过滤意外文件并不会对
扩展、其构建后端或其运行时代码进行沙箱隔离。

本地 `make dev`/`make start`、Docker 开发以及生产 Gateway 镜像都
使用相同的 `backend/pyproject.toml` 和 `backend/uv.lock`。本地和 Docker-dev
启动器在启动前执行 locked sync；生产镜像在其构建期间
执行该 sync，并将受管本地快照包含在构建上下文中。随后 Gateway 运行时
命令使用已创建的环境，而不会解析或安装包。
本地和 Docker 开发的启动前 sync 可能会下载缺失的锁定制品。生产部署
则仅在显式安装或镜像构建期间下载它们；启动生成的生产 Gateway
容器时绝不会从网络解析或安装扩展。本地 wheel 或 `file://` Git URL 会被拒绝，因为
它不会存在于 Docker 构建上下文中；请改为传入源目录以创建受管
快照。由于环境配置（例如 `UV_FIND_LINKS` wheelhouse）
仍可能将普通包名解析为本地 wheel，manager 会在启用扩展之前审计每个新 lock：
任何原版镜像构建无法复现的本地引用都会回滚整个安装或移除操作。
更改受管扩展集后，使用 `make up` 重新构建。有关完整示例，请参见
`config.example.yaml` 和
[reference extension](examples/deerflow-extension-example/)。
Gateway 生成的后续建议现在会在解析 JSON 数组响应之前，规范化纯字符串模型输出和块/列表样式的富内容，因此提供商特定的内容包装器不会静默丢弃建议。

后端响应清理会保留后续建议和润色草稿中无关的标签名，例如 `<think-tank>` 和 `<think:note>`；只有精确的 `<think>` 名称（可选后跟属性）才会启动推理块。自闭合的 `<think/>` 和 `<think />` 标签是空推理块，并且会保留后面的答案不变。引号属性内的分隔符，例如 `<think note=">"/>`，也会保留后面的答案不变。

Web UI 撰写器可以在发送前润色草稿输入。重写会作为一次简短的 Gateway LLM 请求运行，使用 `input_polish` 模型配置，保留诸如 `/data-analysis` 这样的斜杠技能前缀，并且仅在用户点击润色按钮后替换本地草稿；它不会创建线程运行或持久化消息。

当 agent 请求澄清时，Web UI 会显示结构化响应卡片，但保持常规撰写器可用。用户可以完成该卡片，或发送自由格式的聊天消息来绕过它；该消息会关闭最新的待处理澄清，并成为 agent 的下一个输入。随附的答案文本会留在执行步骤面板之外，并且在回答请求时，之前已完成的文本会保留在对话中，同时 agent 继续。

未发送的 Web UI 撰写器草稿在页面重新加载以及同一浏览器标签页内切换对话后仍会保留。草稿按用户、agent 和对话隔离，包含所选技能和显式对话引用，并在发送被接受后清除。已附加到线程的项目文档在重新加载后也会保留；浏览器本地上传和引用的消息摘录不会被持久化。
Web UI composer 支持在光标处或通过 `@` 按钮进行 `@` 引用。在分组选择器中搜索已启用的 skills、当前项目中的文档以及其他 conversations；所选的引用会内联显示在草稿文本旁边，并可通过常规编辑移除。一条消息中可以选择多个 skills（最多 16 个唯一 skills）；再次选择一个已勾选的 skill 会将其移除，每次选择都会根据当前用户 registry 和 agent allowlist 进行检查。项目文件仅在 ingestion 成功后才会附加；conversation 引用需要 `read_conversation` capability，并保留其每次运行的 limit。如果 capability discovery 失败，已保存的 conversation 引用将保持不变，发送会等待成功重试。当指令重新排序时，Polishing 会保留完整的引用标签。文件组还提供本地上传。`/goal`、`/compact` 以及旧版 `/skill-name` 输入仍然受支持。

Web UI composer 还支持基于浏览器的语音听写，前提是浏览器暴露了 Web Speech API。麦克风按钮仅将语音转写为本地草稿；DeerFlow 仅接收转写后的文本，而音频处理则根据该环境的策略委托给浏览器或操作系统语音识别服务。用户可以在发送前查看或编辑文本。当浏览器修剪 transcript 片段时，听写会保持单词分隔，保留中文和日文的连接，并在附加前导标点和百分号时不添加空格。

Web UI 在 standard 和 custom-agent 会话中，在 composer 下方显示本地化的 AI 生成内容免责声明，提醒用户核实重要信息。

中断的首轮运行仍会持久化一个回退 conversation 标题，因此停止流式响应不会在刷新后使线程保持为“Untitled”。
流式 Markdown 响应只对新到达的单词播放动画；当后续 chunk 扩展同一个 block 时，已经可见的文本不会被淡出并重放。
在 Web UI 中，已完成的 assistant 轮次可以分支到一个新的主对话。自动继承的分支标题使用下一个可用的语言中立数字后缀（`Title (2)`，然后对于另一个同级或编号对话的分支使用 `Title (3)`），以便生成同级标题保持不同，而无需持久化特定于区域设置的标签；匹配的显式或重命名的同级标题也保留其显示的后缀，即使它们不携带生成的序列元数据。显式的 API 标题会被保留。重命名分支会清除其生成的序列，因此其下一个自动分支从重命名后的标题开始，位于 `(2)`。最近聊天还会将已加载的分支直接分组在已加载的父级下方，并使用细微的树形连接线。缺失的父级、格式错误或循环的谱系，以及处于不同固定状态的分支会保持在顶层可见，而不是被隐藏或跨固定边界移动。新线程从该轮次的 checkpoint 开始，并保留之前的 replay checkpoint，因此分支的响应可以立即重新生成。最新的响应也可以在中断后重新生成，即使其流式部分文本从未到达 checkpoint。重新生成最新响应会保留线程的当前标题，包括你在原始响应后手动重命名的标题。没有 checkpoint 父链接的遗留或导入历史记录使用有界的时间顺序回退；如果不存在更早的 replay checkpoint，分支仍然以遗留的单 checkpoint 形状成功，而对该继承的响应，重新生成仍不可用。现有的单 checkpoint 分支保持不变，而不是尝试不安全的 checkpoint 复制。由于工作区文件不会被 checkpoint，当你从最新轮次分支时，分支只会收到当前工作区的尽力而为副本；从较旧轮次分支仅保留恢复的消息历史记录，因此分支永远不会继承在对话后续部分创建的文件。
Web UI 每次运行会报告一次已完成任务时间。这是总 wall-clock time——包括模型推理、工具调用和等待——而不是每步的或仅模型的思考时长。推理内容仍可通过其自身单独的展开区域查看。

当响应流式传输时，仅包含推理的消息会留在处理面板中，包括 Anthropic thinking blocks。一旦答案内容与推理一同到达，它就会出现在 assistant 气泡中。

围栏代码、缩进代码或行内代码中的字面 `<think>` 标签仍是答案及其复制文本的一部分，而不会被移入推理展开区域。这包括在列表项行上打开的围栏：代码之后的真实推理仍会被提取。未完成的行内代码 span 在段落内流式传输期间会被保留，但会在空行或中断性的标题、列表、主题分隔线或围栏处结束。缩进的段落延续不会启动代码块。

在 Web UI 中，最新完成的用户轮次也可以从消息工具栏中编辑并重新运行。DeerFlow 会恢复该用户消息之前的对话 checkpoint，将编辑后的文本作为新的用户消息提交，并在重放进行中或成功后隐藏被取代的轮次。这仅是对话状态重放：文件、memory 更新和外部工具副作用不会被撤销。

Web UI 聊天链接在将自定义 thread 标识符放入路由段之前会对其进行百分号编码，因此诸如 `#` 和 `?` 这类保留 URL 字符不会改变所打开的对话。

### 聊天归档

从侧边栏删除聊天需要显示其标题的确认。删除会移除该对话及其文件，且无法撤销。
在最近聊天的侧边栏菜单中使用 **Archive chat**，可以隐藏已完成的工作，同时保留其消息、文件和原始链接。成功提示会提供 **Undo**。打开 **Chats → Archived** 可找到已归档的对话并逐一恢复；打开已归档的对话时，其标题栏中也会显示恢复按钮。搜索会过滤已加载对话的标题，对于更早的条目可使用 **Load more**。

归档和恢复会保留聊天的活动时间和置顶状态。归档不会停止正在运行的任务，也不会暂停其 schedules，并且新的活动不会自动恢复该对话。当你打算删除某个对话及其文件时，请使用现有的 Delete 操作。

### Session Goals

使用 `/goal <completion condition>` 为当前 thread 附加一个活动的完成条件。该 goal 是 thread 作用域的状态，而不是 skill 激活，因此它会跨轮次保持活动，直到 DeerFlow 判定其已满足或你将其清除。agent 在每次模型调用时都能看到活动的 goal，因此在 context compaction 移除声明该 goal 的消息后，它仍会继续朝着该目标工作。

支持的命令：

```text
/goal finish the implementation and make all tests pass
/goal              # show the active goal
/goal clear        # clear it
```

在每次 Gateway-backed run 之后，DeerFlow 会使用 non-thinking evaluator model，针对 active goal 评估可见对话，包括 assistant 的 tool calls 和缩短后的 tool results。仅凭成功的 tool result 并不能满足 goal，并且当 assistant 不得不猜测缺失或含糊的信息时，evaluator 会报告 `needs_user_input`。evaluator 必须返回一个 typed blocker（`missing_evidence`、`needs_user_input`、`run_failed`、`external_wait` 或 `goal_not_met_yet`）以及 visible evidence。仅当最新的 assistant turn 已持久化 checkpoint、blocker 为 `goal_not_met_yet`、thread 在评估期间未发生变化，并且 no-progress breaker 未触发时，DeerFlow 才会注入 hidden continuation。safety cap 默认是 8 个 hidden continuation，并且重复的相同 non-progress 评估在 2 次尝试后停止。`/goal clear` 和任何 user-authored 新输入优先于排队的 continuation。当 evaluator 认为 goal 已满足时，DeerFlow 会在 run 成功 finalize 并发布更新后的 thread state 后清除它。如果所需的 artifact delivery 或其 receipt persistence 失败，run 会报告错误，且 goal 保持 active 以便稍后重试；这不会启动另一个 hidden continuation。

Web UI 会在 composer 上方显示 active goal。同一命令可在 TUI 和支持的 IM channels 中使用。在 Web UI 和支持的 IM channels 中，设置 `/goal <completion condition>` 还会以该 condition 作为 task 启动一个 run；status 和 clear 命令只管理 goal state。当该 thread 有 run in flight（包括由另一个 Gateway worker 拥有的 run）时，设置或清除 goal 会被拒绝，因此 goal checkpoint 不能从 active run 的 checkpoint lineage 分叉出去。
当你的角色缺少 `runs:create` 时，Web UI 会在准备 thread 或保存 goal 之前拒绝新任务或 `/goal <completion condition>`，并保留你的草稿以供重试。Goal 状态、goal 清除和 `/compact` 仍由其各自的端点权限控制。

### 手动上下文压缩

当启用 `task_continuity.enabled` 时，`history_search` 搜索当前任务的活动历史和已压缩历史。其可选的 `role` 接受 `user`、`assistant` 或 `tool`，并在八个结果上限之前进行过滤；省略它或传入 `null` 会保留跨所有角色的搜索。使用 `history_read` 验证原始来源；历史用户消息不会授予当前授权。参见
[task continuity](docs/task-continuity.md)。

自动和手动压缩会将旧的 todo 提醒消息从摘要输入和保留上下文两者中排除。当前 todo 列表保留在 thread 状态中。在规划模式下，如果原始 `write_todos` 调用不再可见，DeerFlow 会在下一次模型调用之前使用最新任务状态添加提醒。跳过或失败的压缩会保持现有消息不变。

可选的 `pii_redaction.enabled` 会脱敏用户消息、远程工具结果、压缩输入、重新注入的摘要以及配置的 LLM 标题输入中检测到的标识符。记忆准入，包括压缩前刷新，也会脱敏受支持的 text/JSON 内容、已解析和无效的调用参数/错误文本、provider-raw/legacy 函数调用以及受支持的用户内容来源中检测到的标识符。它默认关闭；启用的部署会提供一个 secret，用于稳定、带键的由值派生的占位符。不会持久化 token 到原始值的映射。原始 thread 文本和本地回退标题仍可用于显示；记忆脱敏会复制消息，而不会更改调用方的历史或工具执行。
Web UI 在将 history 与实时更新合并时，会保留已持久化的消息顺序。在已加载的 history 中，围绕某个已持久化结果的 streaming 步骤会保持在一起，包括在该结果之后到达的步骤。当 history 尚未刷新且 UI 尚未渲染它们时，在 compaction 期间捕获的步骤也会在其已持久化结果之前保持可见。

Compaction 会保留当前用户请求，并总结较早的 assistant/tool 活动。当挽救该请求后只剩下一个仅含 assistant/tool 的摘要窗口时，输入裁剪会偏向其最新的内容。对于 user-message 锚点落在裁剪预算之外的混合 history，compaction 会保留现有的 final-message 回退机制。`summarization.trim_tokens_to_summarize`（默认 4000）控制对原始 summary 输入的裁剪；转义和 prompt 格式化会在该预算之外增加额外开销。将该选项设为 `null` 会禁用 summary 模型的输入裁剪；仅当模型能够接受被压缩的完整 history 时才选择该设置。

如果相同的已渲染 summary prompt 和模型候选再次出现，且第一个候选此前原样返回了该 summary，DeerFlow 会复用现有的 summary。未变更的 fallback 响应不会被缓存，因此复用无法阻止在调用失败后重试 primary model。缓存失败会回退到正常生成。关于 summary 结果和复用计数器，参见 [summarization telemetry](backend/docs/summarization.md#reuse-and-telemetry)。
在 Web UI composer 中使用 `/compact` 为当前 thread 总结较早的 context。DeerFlow 会让完整聊天保持可见，但后续模型调用使用压缩后的摘要加上近期消息。当没有足够历史可供压缩时，该命令会被忽略；当 thread 有进行中的 run 时，它会被阻止，包括该 run 由另一个 Gateway worker 拥有的情况。如果多 worker 预留丢失其 lease，DeerFlow 会在替换 run 继续之前取消 checkpoint writer，并在清理后返回可重试的 conflict。Thread 标题编辑通过相同的 state-write 边界串行化，并且在 run 活跃时显示 conflict 而不关闭重命名对话框。

聊天头部还会在所选模型配置了正数 `context_window` 时显示一个 context-window 仪表。它估算最新物化 checkpoint 的消息 token，并在数据重新获取时保持先前同一 thread 的百分比可见，与累计 token 用量设置无关。

当 `token_budget.enabled` 和 `token_usage.enabled` 都启用时，每个 lead-agent run 预算包含已完成的 subagent 用量，包括最后一批。隐藏的 goal continuation 共享该预算；新的用户 run 从头开始。

### Sub-Agents

当 sub-agent 以 `return_direct=True` 工具结束时，包括由 extension middleware 贡献的工具，其输出按 tool-call 顺序返回。失败的工具会将任务标记为失败，同时保留该批输出。

普通 `task` 调用接受 `context_mode="isolated"`（默认）或
`context_mode="snapshot"`。Isolated 任务像之前一样接收其委托的 prompt。Snapshot 任务还接收父级保留的对话和压缩摘要，在 dispatch 时捕获作为历史背景。这有助于依赖较早需求或失败方案的 handoff，代价是额外的输入 token。保留的文本、tool-call 描述/结果，以及
JSON 可序列化的 media input blocks 会被保留。二进制或其他不可序列化的 media blocks 会变成显式的省略提示；周边的对话仍然可用。父级 system prompts、隐藏的框架消息（例如注入的 memory 和 todo 提醒）、reasoning blocks、工具执行元数据以及待处理的 tool calls 会被排除。Tool-call descriptions 要求存在一条保留的匹配结果，包括与当前任务并行的 calls。有效的隐藏用户澄清响应仍属于对话的一部分。子级保留自己的 role、model、tools 和 skill 限制。父级 tool records 无法满足子级执行检查。此后父级和子级的历史独立演进；共享的 sandbox/filesystem 行为不变。Snapshot 模式不会恢复已 compacted 的消息，也不承诺 prompt cache 复用。持久化的 `batch_task` 项仍要求自包含的 prompts。

原生 document blocks 会保留在 snapshots 中。其文本内容、标题和上下文使用与其他历史文本相同的保留标签和输入边界中和处理；编码的 media 和 URL sources 会被保留而不解码。

关于对完整 handoffs 和 snapshots 进行手动、合成对比，参见
[context snapshot evaluation](backend/scripts/benchmark/context_snapshot/README.md)。

Custom Agents 支持可选的 Unicode 显示名称，包括中文和 emoji。打开某个 agent 的 **Agent settings → Display name** 进行设置（最多 100 个 Unicode 码点），或留空以显示现有标识符。控制字符和双向格式化控制字符会被拒绝；普通的多语言文本和 emoji 受支持。仅含不可见字符的名称以及诸如零宽空格之类的不可见格式化字符会被拒绝。较旧或手工编辑的存储中的无效显示名称在读取时会回退为 agent 标识符；并会给出警告指明受影响的 agent。
重新 bootstrap 会保留有效的显示名称。图库，
chat header 和 welcome page 使用此 label；URL 和 API 调用继续使用稳定的英文 `name`。API 调用方可以在 agent 创建或更新请求中传入 `display_name`；更新时省略该字段会保留它，而 `null` 会清除它。agent 的 `config.yaml` 中也支持同一个可选字段。

Custom Agents 也可以从 Agents gallery 在 DeerFlow 用户或部署之间移动。**Export Agent** 会下载一个带版本号的 `*.deerflow-agent.json` package，其中包含可移植定义和 `SOUL.md`；**Import Agent** 会验证该 package，并让接收方用户选择一个本地名称。无效的 package 会显示验证消息，以便你修正该 package 并重试。导入绝不会覆盖现有 agent。Package 会携带 model、tool/MCP、skill、knowledge、sub-agent、reasoning 和 memory-policy 设置，但有意排除 memory contents、conversations、credentials 以及 operator 拥有的 GitHub bindings。

Sub-agent 是一种优化，而不是对复杂请求的默认响应。

在 Stop 中断一个已委派任务、使其在返回回复前停止后，下一个用户轮次会在 agent 的 durable context 中将该较早任务标记为 cancelled，以便它可以重试。现有回复会被保留。没有 status metadata 的较旧回复可能仍会显示为进行中；它们的结果不会从其文本推断。Durable delegation ledger 通过 run 和 provider tool-call ID 区分调用，因此后续用户轮次可以复用一个 ID，而不会替换较早的工作，也不会丢失该轮次的 per-run delegation count。
lead agent 可以即时生成 sub-agent——每个都有自己作用域内的 context、tools 和终止条件——当委派能从真正的并行延迟、专家能力或 context 隔离中获得明确的净收益时。它让相互依赖的作用域和重叠的副作用不进入并行分发；当专家或 context 隔离的收益明显胜出时，有界的顺序链仍可在一个 sub-agent 中运行。lead 使用最少的有效 sub-agent，并重新评估后续批次，而不是仅仅因为任务很大或多步就展开。sub-agent 回报结构化结果，lead agent 验证并将它们合成为连贯的输出。确定性的 tool receipts 覆盖直接 tool 消息和更新状态的 `Command` 结果（例如委派的 `task` 响应）；当 receipt ledger 达到其 context 预算时，它保留最新的操作及其原始 receipt ID。操作员可以通过 `verification.receipts_enabled: false` 禁用此 provenance 层。它们配置的 skills 从与 lead agent 相同的用户作用域目录中解析，因此用户拥有的自定义 skills 保持可用，而不会暴露另一个用户的版本。它们的内部 AI 和 tool 消息保持在委派图的作用域内，而不是进入父级聊天流。重新加载的线程历史强制执行相同的边界：回调捕获的 sub-agent AI 响应仍可在 run-event 诊断中使用，但被排除在父级转录之外，而父级 `task` 结果仍附加到其 subtask 卡片。长时间运行的 sub-agent 在启用摘要时压缩较旧的历史，并在继续之前将摘要作为受保护的、隐藏的持久 context 重新注入，因此最近的 assistant/tool 活动仍扎根于任务。它们的系统指令（包括角色和报告契约）在压缩后保留；如果只有这些指令和当前请求会被摘要，则跳过压缩。Provider/model 请求失败被报告为失败的 sub-agent 任务，而不是成功的结果，因此 lead agent 和 Web UI 可以正确地对其作出反应。并发的父级运行也会收到独立的服务器端 sub-agent 执行 ID，因此重用 tool-call ID 的 provider 无法让一个运行轮询、取消或清理另一个运行的后台任务。折叠的 sub-agent 卡片显示有效模型，并且当 provider 返回使用元数据时，显示累积 token 总数，该总数在每次完成的 sub-agent LLM 调用后更新，并在重新加载后持续存在。当启用 token 使用跟踪时，已完成的 sub-agent 使用量会从该运行的终端 tool-message 元数据中归属回调度的分派步骤，而不是进程全局的 provider-ID 缓存。
已取消或超时的后台 sub-agent 执行会保留来自已完成模型调用的 provider 报告的 token 使用量，包括在其下一次进度更新之前收到的响应。向父运行最终交付的用量不会重复计算较早的进度快照。

对于 `tests_passed:go test ./...`，标记为 `[no test files]` 或 `[no tests to run]` 的包不会否决来自另一个包的通过摘要。仅包含零测试包摘要的运行仍为 `UNVERIFIED`；失败仍然优先。这会检查记录的执行证据，而非声明正确性。

对于文件验收标准，共享工作区中的一个空常规文件可以满足 `file:<path> exists` 和 `file_written:<path>`，包括在远程沙箱上。它会使 `file:<path> non-empty` 失败，并给出确定性的空文件结果。

要请求 JSON 语法验证，请显式地将 `task` 或 `batch_task` 项的 `acceptance_criteria` 设置为 `["file:../outputs/report.json json-valid"]`。检查仅覆盖共享工作区内完整的 UTF-8 JSON 文件，最大 **50,000 字节**。有效语法返回 `holds`；空文件、语法错误、非 UTF-8 内容或 `NaN`/`Infinity` 返回 `does not hold`。超大文件、不完整读取、超出范围的路径或解析器资源限制返回 `UNVERIFIED`。读取被限制为 50,001 字节以检测超大内容。远程结果会检查完成标记、读取退出代码和探测的大小。缺少所需探测工具的远程 provider 会将结果保留为未验证，而不是回退到全内容读取。相同大小的并发写入不会产生原子快照。本地检查在解析路径或探测元数据之前授权沙箱访问，并在读取内容之前重新检查；撤销的权限返回 `UNVERIFIED` 而不揭示存在性。远程探测仅在存在可搜索的祖先和范围内的规范路径时才报告缺失文件；
无法访问的目录保持 `UNVERIFIED`。UTF-8 BOMs 会被拒绝。顶层标量、重复键以及语法上有效的大数字可以通过，而无需验证 schemas、字段或业务语义。其他文件标准不变，且不会自动检查 `.json` 文件。该标准统一了判定、路径边界和读取限制，而不是要求临时的 bash/Python 检查，并明确说明证据不足。执行完成状态和自动重试策略不变。

无内容的 sub-agent 最终消息报告 `No response generated`，而不是字面文本 `None`。无内容的 provider-error 回退在可用时报告其结构化错误详情。

普通 `task` 还会收到分派运行当前上传的防御性快照。这使符合条件的 sub-agent 能使用 `list_uploaded_files` 查找先前轮次的文件，而不会将同一轮次的附件作为历史附件返回。延迟或恢复的 `batch_task` worker 会使此工具保持禁用，因为它们没有有效的轮次本地上传边界。

历史上传发现支持稳定续页：`list_uploaded_files` 默认每页 20 项、最多 100 项，
将返回的 `next_cursor` 作为下一次调用的 `cursor`，保留相同过滤条件，直到末页不再
返回游标。目录元数据或调用上下文变化时会明确要求重新枚举；详情见
[文件上传文档](backend/docs/FILE_UPLOAD.md)。

持久化的 `batch_task` worker 使用一个应用自有的插件快照进行工具组装和执行。恢复的任务在 Gateway 重启后采用新 worker 的插件快照；插件对象绝不存储在持久化任务记录中。
普通 `task` 委派与显式持久化的 `batch_task` 执行共享启动时作用域的 `subagent_runtime` 进程容量。批处理模式将大型独立条目集合保存在 SQL 中，具备独立的 total、live 和 running 限制、重启恢复、有界结果，以及 thread 作用域的 Web UI 面板。该面板按需对有界预览进行分页；批量存储的结果可通过 owner 作用域的 JSONL 导出获取，而内部执行与授权上下文绝不会进入面向 owner 的响应。如果批处理 worker 之后被停止或禁用，带有持久化批次的 thread 仍保留只读的条目查看和 JSONL 导出；执行控件保持禁用，直到 worker 再次运行。有关限制和恢复语义，请参阅 `config.example.yaml` 和[实现契约](docs/plans/2026-08-24-subagent-batch-capacity-implementation.md)。
虽然 durable batch 工具可用，但后续的 owner turn 可以显式使用 `read_batch_result(batch_id, position=0, offset=0, max_chars=4000)` 检查选定的结果。reader 仅限于当前 user 和 thread，包括在显式绑定的 SDK graphs 中。它返回 JSON 文档的一个 window，其中包含存储的 report、执行/错误状态以及单独的 acceptance criteria/verdict，而不会启动或等待 work。在解析之前拼接 `content` windows：传递 `next_offset` 和返回的 `revision` 作为 `expected_revision`，直到 `next_offset` 为 null。更改过的 item 会返回 `restart_required`；丢弃先前的 windows 并从零开始。使用 `next_position` 在 `batch_status.total_items` 中选择下一个 item。最大 window 为 8,192 个字符；metadata 共享 window budget，并且 JSON response framing 会增加额外开销。`result_truncated` 意味着 storage 已经截断 report；continuation 无法恢复被丢弃的内容。一个 succeeded item 并不等于 accepted task，并且未检查的 criteria 保持 UNVERIFIED。没有添加自动 result ingestion、等待循环或 UI 更改。

完整的 escaped response 也既在 10,000 个字符以内，也在绑定的 host 的正向 `tool_output` externalization/fallback 限制以内，因此正常的 budgeting 会保留 continuation JSON。更小的限制会缩短 window；`budget_too_small` 意味着 operator 必须提高 budget，而不是重试 zero-length page。即使对于该 error envelope 来说也过小的限制，无法提供可用的 structured response。带有自定义 output-budget middleware 的显式 SDK graphs 应通过 `SubagentRuntime` 提供相同的 `AppConfig`；默认 graphs 使用默认 reader limits。
离线验收：`cd backend && PYTHONPATH=. uv run --locked pytest tests/test_batch_result_reader.py -k 'real_submission_worker or sdk_factory_graph' -q`。这会演练真实提交、确定性的 worker 完成、数据库重新打开以及已注册 graph 的消费；外部模型执行由 fake model/executor 替代。

持久化的 knowledge-research 结果还会导出可为空的 `result_artifact.knowledge_sources` 快照。每个保留的来源都会将存储的报告中的引用 ID 与由 `knowledge_search` 或委派的 `task` 捕获的精确摘录配对，并且还包含其 RAGFlow dataset/document/chunk 定位符和页码。现有的已认证 `GET /api/threads/{thread_id}/subagent-batches/{batch_id}/results.jsonl` 仍是入口：在该行的 `sources` 中按 `id` 找到报告的 `#knowledge-<id>` 链接，以便在 Gateway 重启或 provider 变更后检查证据。紧凑的 item 查询和 batch 面板不包含这些快照；这不会为 batch 预览添加可点击的引用。
Snapshot 保留完整摘录，而不是新获取的 provider 内容。它们继承 100-source/1,000,000-text-character 转发限制；序列化的 snapshot 除了 report 现有的预算外，还有一个单独的字符预算，等于 `subagent_batches.max_result_chars`。`knowledge_sources.omitted_count` 报告因转发、snapshot 投影检查或 snapshot 预算而省略的引用记录；在候选选择之前过滤掉的格式错误或不支持的 producer artifact 不计入。Report 截断将选择限制为存储文本中的完整引用。旧/普通结果没有 snapshot（`null`）；不会重建历史证据。Gateway 启动时通过迁移 `0033_batch_result_artifact` 添加一个可空的 JSON 列。迁移前备份数据库；降级会丢弃证据 snapshot，同时保留 report 文本。取消、失败和过期的尝试不会发布证据，显式重试会清除之前的 snapshot。

显式启用的嵌套 `task` 委托在其捕获的 artifact 中传播省略的不透明 source ID。每个外层 report 会过滤并去重这些 ID，独立捕获的证据可以恢复一个省略的 source。持久化的 snapshot 只发布最终计数。不带省略 ID 的旧版 task artifact 无法重建早期的转发丢失；未知的散文引用不被视为捕获的证据。

如果某个 item 的最终租约在耗尽重试预算后到期，那么一旦所有 item 都进入终态，该 batch 就达到终态：当没有一个成功时为 `failed`，当至少有一个成功时为 `completed`。在这两种情况下，该 item 都保持 `failed`，以便部分结果保持可见。
直接 `create_deerflow_agent(...)` 集成可以显式地拥有相同的 boundary，而不是依赖 Gateway startup。构造一个 `SubagentRuntime` 并在该应用中的每个 graph 中共享它；它的 `max_running`、普通 per-run total、绑定的 `task` 工具以及可选的 durable-batch 工具随后使用同一个 caller-owned snapshot 和 execution controller。带有 batch repository 的 runtime 拥有一个 worker，并且必须在 graph 构建之前启动，并在应用 shutdown 期间停止：

```python
from deerflow.agents import RuntimeFeatures, create_deerflow_agent
from deerflow.subagents import SubagentRuntime

runtime = SubagentRuntime.from_app_config(app_config, batch_repository=batch_repository)
async with runtime:
    graph = create_deerflow_agent(
        model,
        features=RuntimeFeatures(subagent=True),
        subagent_runtime=runtime,
    )
    # 在 durable worker 运行时服务或调用 graph。
```

`SubagentRuntime.stop()` 会等待其拥有的 batch service 完成，然后再传播 caller cancellation，包括重复 cancellation。这个 drain 没有超时；repository 操作和 child cleanup 必须终止。如果 service shutdown 也失败或被取消，那么第一个 caller cancellation 会被保留，并以 service failure 作为其原因。

该 factory 仍然不加载 YAML 或创建 SQL 基础设施：调用方提供 config snapshot、repository 和 lifecycle。因为它接受 caller-owned `system_prompt`，所以直接集成也拥有任何关于这些限制的 model-visible 措辞；默认 middleware 无论如何都会强制执行 runtime 限制。该 factory 不会挂载 Gateway owner-scoped HTTP routes 或 Web UI，因此直接应用如果需要这些 surface，就必须暴露自己的 result API/UI。仅对于普通 delegation，`SubagentRuntime(...)` 不需要异步 startup。
管理员可以从 **Settings → Subagents** 添加、编辑、禁用和删除可复用的 worker 定义。内置定义和 `config.yaml` 定义在那里仍作为只读条目可见。默认 Lead Agent 可以使用每个已启用的 runtime sub-agent；每个页面创建的 Custom Agent 则可以允许全部、不允许或允许选定集合。该选择既在模型可见的目录中强制执行，也由服务器端 `task` tool 强制执行。托管定义在此版本中面向整个部署，并遵循 `agent_storage.backend`：本地部署使用原子文件，多实例使用共享应用数据库。

例如，当 wall-clock 节省超过重复的发现与综合成本时，独立的只读研究可以并发运行；而涉及共享文件和顺序测试反馈的仓库重构则仍由 lead agent 处理。当 `max_concurrent_subagents` 为 `1` 时，并行和多批次路由指导将被禁用；委托仅在具有实质性专家或上下文隔离收益时可用。

### Sandbox 与文件系统

主机外部化的 tool 输出使用 Gateway 正常的文件创建 umask。主机和 sandbox 输出使用确定性文件名，该文件名由原始 tool 调用 ID 和输出内容哈希得到。缺失、冲突或过大的 ID 不能覆盖不同的输出，也不能使文件名过长；相同的输出可以复用其路径。主机和远程 sandbox 持久化失败（包括文件名哈希期间的无效 Unicode）将使用配置的内联回退。`tool_output` 字符/计数预算（包括每个 tool 的覆盖值）要求非负整数；YAML 布尔值会被拒绝，而不会被当作 0 或 1。显式的每个 tool 零覆盖会禁用外部化，同时保留任何正的全局回退限制。结构化 JSON tool 结果遵循这些预算，包括与媒体混合的结果；外部化通过文件引用保持完整 JSON 可用。
MindIE 将 JSON tool results 渲染为转义文本，并保留已配置的 tool 豁免。已启用的 PII redaction 会在渲染前扫描嵌套的 JSON 键和值。以另一个 UID 运行的已挂载 sandbox 需要通过共享存储权限获得读取访问权限。非正常关闭可能会在 thread outputs 下的 `tool_output.storage_subdir`（默认 `.tool-results`）中留下 `.tool-output-*.tmp` 文件。在所有 Gateway writers 停止的情况下，或在删除相应的非活跃 thread 的数据时，于 thread 数据维护期间移除残留文件。

`E2BSandboxProvider` 使用 `wait` 作为其默认 overflow policy。它会等待 `acquire_timeout`，然后使 agent turn 失败。DeerFlow 不会自动重试该 turn。客户端可以使用结构化错误来安排重试。

将 `burst` 与 `burst_limit` 一起使用，以允许有界的额外 VM。`wait` 和 `reject` policy 仅使用 `replicas`。`reject` policy 在返回错误之前可以移除一个 warm VM。

在内存所有权模式下，`replicas` 限制单个 Gateway 进程。在 Redis 所有权模式下，E2B 在使用相同 `sandbox.ownership.key_prefix` 的 worker 之间共享一个 capacity Hash；此时 `replicas`（加上已配置的 burst）是整个部署范围的硬限制。每个部署使用一个唯一前缀和相同的有效限制。要更改限制，请停止其 Gateway，删除 capacity Hash，然后重启；不匹配的 worker 会 fail closed。

该 Hash 统计远程 VM 和进行中的 creates，根据 E2B metadata 修复中断的 creates，对过期的 inventory omissions 提供宽限保护，并在 Redis 或初始 inventory 不可用时阻止新的 creates。以持久化、非逐出内存和 HA 运行 Redis。

E2B reconciliation 会使用覆盖其配置节奏的正超时来续期活跃 VM，即使 `idle_timeout` 为零或短于该节奏也是如此。Warm VM 保留配置的 idle-timeout 行为。过期的本地 warm 条目不会直接释放共享 capacity：远程 inventory 必须
先通过现有的 grace period 确认消失。
Active renewal 在 release 设置 warm timeout 之前完成，因此并发的
maintenance pass 无法延长空闲 VM 的寿命。Warm-entry cleanup 也会
保留在 sweep 期间由新请求获取的 ownership。
Ownership heartbeat 保持独立于缓慢的 E2B timeout 请求，从而防止
control-plane 延迟导致 active sandbox lease 过期。

E2B 在 provider 启动时对 `skills.container_path` 进行快照，并将
canonical root 纳入其 thread identity、warm-pool seed 和 remote metadata。为
不同 root 创建的 VM 永远不会被收编；一旦没有存活的 peer 拥有它，
reconciliation 会在配置的 grace period 之后将其回收。更改 root 后重启 Gateway。

E2B acquisition 使用有界 executor。等待中的 acquisition 不使用
默认的 asyncio executor。

每次 E2B mount 上传 pass 最多接受 512 MiB 和 2,000 个文件。该 pass
还有一个协作式的 120 秒 deadline。Skill projection 和配置的
mount 共享这些限制。provider 在每次 mount 之前以及目录 preflight 期间检查
deadline。deadline 到期后会停止新的文件上传。
它不会中断正在进行中的 filesystem 或 E2B SDK 调用。

E2B VM 会一直保留其 slot，直到 E2B 确认销毁。此规则涵盖
create 和 reclaim 操作。Discovery 可以发现来自另一个 Gateway 的 VM。
Shutdown 会关闭无主的 discovery client，而不销毁其 VM。
当 VM 进入 warm pool 时，Release 停止计入 transition。
Shutdown race 会在瞬时 kill 失败后重试 remote cleanup。
Reset 会销毁已跟踪的 active 和 warm E2B VM。旧的 provider 实例
无法接受新的 acquisition。

DeerFlow 不只是*嘴上说说*要做事情。它有自己的计算机。
每个任务获得自己的执行环境，具有完整的文件系统视图——skills、workspace、uploads、outputs。agent 读取、写入和编辑文件。它可以查看图像，并且在安全配置时执行 shell 命令。

read-before-write gate 将每个 read mark 绑定到该 `read_file` 调用的结果，包括返回多消息 `Command` 更新的自定义工具。一个无关的结果不能在读取失败后授权写入，也不能隐藏一次成功的读取。

对同一文件的并发读取和写入在同步和异步工具调用之间共享一个 gate。等待该 gate 的异步调用者不会占用完成当前读取或写入所需的 worker 线程。取消等待中的调用会让当前操作继续运行；一个已经启动文件检查的调用仍会等待该工作完成，然后才释放其 gate。

内置 `grep` 工具搜索一个文本文件或某个目录下所有匹配的文本文件，因此 agent 可以直接搜索上传的文档，而无需先将请求扩大到整个 uploads 目录。

E2B 的 `glob` 过滤器在文件名模式中保留空格、引号和美元符号，而通配符匹配和根相对目录作用域保持不变。

远程 `ls` 在应用其 500 条目的列表限制之前排除被忽略的后代，因此依赖树和构建树不会挤占可见文件。显式列出被忽略的目录仍会列出其内容；正常的深度和输出限制仍然有效。

AIO 目录列表丢弃缺失的 shell 会话，以便下一个请求可以恢复。连接断开后，目录列表和持久 shell 命令报告未知结果，而不重放该操作；后续调用使用新的会话。

上传的 Markdown 大纲识别 ATX 标题语法，通过线性后缀扫描清理结束标记，并跳过 HTML 注释块以及围栏和缩进代码示例，因此 hashtags 和代码注释不会
挤出 agent 标题预览中的真实文档章节。缩进的粗体示例同样被排除；最多带三个前导空格的 PDF 风格粗体标题仍受支持。
拆分粗体数字表格行，包括带括号的年份、带符号的值以及带货币前缀的金额，当章节编号之后的任一块为数字列时会被排除，因此它们不会占用大纲的标题预算。
带或不带字节顺序标记（BOM）的 UTF-8 Markdown 文件生成相同的大纲和回退预览，并保留原始行号。
大纲标题限制为 200 个字符，回退预览限制为每个文件 2,000 个字符，并带有截断标记。完整的已上传文件仍可用于定向读取。

转换后的上传大纲和预览需要匹配的源版本，包括修改时间戳。检测到源版本变化会使之前的转换失效，包括等长编辑。没有源时间戳的旧所有权记录也会被拒绝；请使用 `uploads.auto_convert_documents: true` 重新上传源文件，以恢复由转换支持的大纲。文件仍然可用，未经验证的 Markdown 转换会在 agent 的历史列表中显示为独立文件。
在 Windows 上，`st_ctime_ns` 可能表示创建时间；一次恢复原始 `mtime` 的同尺寸重写可以规避验证。时间戳检查是保守的元数据验证，并不保证内容相等。

为 vision-model 调用加载的 image bytes 是瞬时的：DeerFlow 在模型消费后移除隐藏的 base64 message，因此后续 checkpoint 不会持续复制该 payload。
每次 run 后，DeerFlow 会为 run 拥有的 `workspace` 和 `outputs` 目录记录一份 workspace 变更摘要。Web UI 在 assistant 轮次上显示一个紧凑的 "files changed" 徽章；打开它会显示创建、修改和删除的文件，并在可以安全显示时提供文本 diff。上传内容被排除在外，因为它们是用户输入，而不是 agent 生成的变更；DeerFlow 拥有的 `.mcp/` 命名空间下的 stdio MCP 临时/调试文件也被排除，因为它们是进程内部状态（类似 `.git/` 和 `node_modules/`，任何名为 `.mcp` 的目录在任何深度都会被排除）。大型、二进制或看似敏感的文件仅显示为元数据。

通过 `present_files` 呈现的文件仍然是 thread 的 artifact 状态的一部分，并且 Web UI 会在页面刷新后恢复 artifact 面板和选中的文档。当一个已完成的响应成功呈现 2 到 50 个文件时，其最终文件卡片还会提供一个 ZIP 下载。归档成员资格来自终端投递回执，而不是浏览器提供的路径，并且 ZIP 包含当前文件版本，这些版本自响应以来可能已经发生变化。当 run 完成时，当前选中的正式 artifact 会刷新一次，因此无需手动重新加载即可看到编辑。在 Unix 和 Windows 上，当 thread 空闲时，`/mnt/user-data/outputs` 下现有的 UTF-8 文本 artifact 也可以从面板中编辑并显式保存；保存使用内容修订来防止覆盖 agent 变更。源代码预览还会根据文件名识别无扩展名的 `Dockerfile` 和 `Makefile` artifact。未知文件类型（包括 `constructor` 和 `__proto__` 这类名称）保留下载回退。

当一个输出文件被原子替换时，artifact 内容修订会刷新，即使其大小和修改时间保持不变。刷新预览后便会提供用于保存的新修订；较旧的预览仍然需要重新加载。
超过 2 MiB 编辑限制的常规文件为 range validators 使用文件标识和变更元数据，而无需对整个文件进行哈希。常规文件的条件字节范围需要匹配的 ETag；日期形式的 `If-Range` 请求会收到完整的当前文件。保存还会将现有文件的读取限制为 2 MiB 加一个检测字节，因此在大小检查后增长或被替换的文件会被拒绝，而无需将整个超大文件加载到内存中。

CSV 和 TSV artifact 会在 artifact 面板和单独窗口中作为表格打开。预览会保留文本值（包括前导零），支持可选表头行，并从初始样本中分页浏览最多 200 行和 50 列。长单元格或多行单元格可以完整打开并复制。切换到 source 以检查或编辑文件；下载和单独窗口使用已保存版本。

HTML artifact 预览会从 artifact 目录解析相对资源，除非文档包含真正的 `<base>` 元素。注释或脚本文本中的 base 标签示例不会改变该解析。

如果样本将 CRLF 行结束符截成两半，预览会保留靠前的完整行，并省略不完整的最后一条记录，包括当其最后一个字段被引号括起来时。

Text artifact 通过 HTTP 字节范围支持进行流式传输。Web UI 最初最多加载 1 MiB，当文件更大时显示预览大小，并等待显式的 **Load full file** 操作，然后才获取剩余部分或挂载完整的代码编辑器。完整文件加载后即可进行编辑；未保存更改检测使用完整内容，包括在还原编辑或删除超出初始预览的部分时。如果重新加载失败或仅返回预览，用户仍可以退出编辑，同时保留其未保存草稿。活动 HTML、XHTML 和 SVG artifact 在 Gateway 边界仍被强制下载。

Artifact 预览和下载会保留文件名中的字面百分号序列：
`report%20final.md` 和 `report final.md` 仍是不同的文件。Markdown 链接
继续接受 URL-encoded 路径。

`write_file` 指引反映当前活动模型的输出 token 上限，包括 custom-agent 和 thinking-mode 的覆盖值。对于较长的文档，agent 会被引导使用 `append=True` 分段写入；没有已知上限的模型不会收到数字形式的预算提示。

使用 `AioSandboxProvider` 时，shell 执行在隔离容器内运行。使用 `LocalSandboxProvider` 时，文件工具仍映射到宿主机上按线程划分的目录，但宿主机 `bash` 默认被禁用，因为它不是安全的隔离边界。只有在完全可信的本地工作流中才应重新启用宿主机 bash。宿主机 bash 命令有挂钟超时限制，长时间运行的进程应在后台启动并将输出重定向到工作区日志。在 Windows 上，Git Bash/MSYS 的参数转换排除项仅限于安全的非根虚拟路径前缀，因此宿主机原生 CLI 启动器保留其正常的 MSYS 兼容性。当本地 sandbox 回退到 PowerShell 时，它以 UTF-8 捕获输出，因此 CJK 文本不依赖 Gateway 宿主机的 locale。

Docker AIO sandboxes 默认沿用其现有的开放出站访问行为以保持
兼容性。运维人员可将 `sandbox.network.mode` 设为 `isolated` 或
`allowlist`；allowlist 模式支持运维人员定义的域名，以及用于临时或
sandbox 生命周期内 HTTP(S) 审批的交互式 Human Input 卡片。私有、
loopback、link-local、multicast 和 cloud metadata 地址始终不可审批。
被拒绝的 hostname 会在 DNS 解析之前被拒绝。
以 `scheduled`、`webhook` 或 `autonomous` 交互模式运行时会自动拒绝，
而不打开卡片。这些无人值守运行仅针对低风险、可逆的工作以最小假设继续
推进；缺乏充分授权的高风险或不可逆工作会返回结构化的 `BLOCKED` 结果，
并指明缺失的决策，即使模型尝试请求澄清也是如此。
可信 sidecar 使用专用的 per-sandbox egress bridge，而不是 Docker 的共享默认 bridge，并在转发前拒绝有歧义的 HTTP 字段名。运行时需求和完整策略模型参见 [Sandbox 配置](backend/docs/CONFIGURATION.md#sandbox-network-policy)。

`AioSandboxProvider` 通常从其 backend 检测 thread-data mounts：本地容器使用挂载的 gateway 目录，而 remote/provisioner sandboxes 通过显式同步接收上传的文件。如果部署中双方保证共享相同的 thread 用户数据目录，可以设置 `sandbox.thread_data_mounts: true` 来跳过每次上传时的 sandbox acquire 和 sync。将该字段留空以进行自动检测；设置不正确可能导致上传的文件在 sandbox 内不可用。

上传提交失败时，即使临时文件清理也失败（例如由于 Windows 共享冲突），仍会报告原始错误。一旦文件发布，临时文件清理失败会被记录日志，但不会导致上传失败；隐藏的暂存文件会留给启动时清扫。

上传、新的 skill 支持文件以及新的本地 sandbox 路径会在所有平台上拒绝 Windows 保留设备名，包括 `COM¹`、`LPT²`、控制台别名 `CONIN$` 和 `CONOUT$`，以及带扩展名的名称，例如 `com³.txt`。扩展名之前的 ASCII 空格不会使设备名变得可移植：`NUL .txt` 和 `COM1  .log` 也会被拒绝。普通名称（例如 `report .txt`）会保持不变。在创建或上传这些文件之前重命名它们，以便同一文件树在 Windows 上仍然可用。

匹配 `.upload-*.part` 的上传文件名会被拒绝，因为该模式保留给临时暂存文件。上传这类文件之前请先重命名。该限制在所有主机上都包括带尾部点号或空格的 Windows 别名以及大小写变体，例如 `.upload-notes.part.`、`.upload-notes.part ` 和 `.UPLOAD-NOTES.PART`。
HTTP check 在提取 basename 时，会把 `/` 和 `\` 都识别为路径分隔符，在 Linux 上也是如此。对于包含 reserved name 的批次，endpoint 会在发布任何文件之前返回 `400` 并附带 rename 提示，因此 chat 会报告上传错误，而不是在没有附件的情况下继续。SDK 会在复制任何文件之前校验整个批次的文件名。新的 project document 名称遵循同样的限制，无论其是来自源文件的默认值，还是在上传或提升到 shelf 时显式提供；带有 reserved name 的旧 shelf document 仍可下载，但不能直接附加。请将其下载、重命名，然后上传到 thread。此变更不会恢复或迁移那些已经匹配 staging pattern 的旧 thread 上传。

这就是拥有 tool 访问权限的 chatbot 与拥有真实执行环境的 agent 之间的区别。

```
# sandbox container 内的路径
/mnt/user-data/
├── uploads/          ← 你的文件
├── workspace/        ← agents 的工作目录
└── outputs/          ← 最终交付物
```

### Agentic 浏览器控制

Browser 依赖自动检测在单个 tool entry 中接受 `name`、`group` 和 `use` 以任意顺序出现，YAML 列表既可缩进也可不缩进。

读取一个页面与*使用*一个页面并不是一回事。除了只读的 `web_fetch` 和 `web_capture` tool 之外，DeerFlow 还提供一个可选的 agentic browser tool group，它会为每个 conversation 维持一个实时的 browser session，使 agent 能够真正操作页面——导航、读取交互元素、点击、输入、提交表单，并在 JavaScript 密集型站点上执行多步骤流程。
每次操作都会返回页面交互元素的全新快照，每个元素都由稳定的 `[ref]` 编号寻址，因此 agent 基于刚刚观察到的内容行动，而不是猜测选择器。出站 URL 默认经过 SSRF 筛查，且浏览器的 TCP 连接会经过本地代理，由代理将每条连接固定到已筛查的地址，因此检查之后发生变化的 DNS 应答无法把它们重定向到私有主机（WebRTC UDP 不在此覆盖范围内）。它由 Playwright 驱动，并作为可选 extra 发布，以便核心安装保持精简：

```bash
cd backend
uv sync --extra browser
uv run playwright install chromium
```

然后在 `config.yaml` 中取消注释 `group: browser` 工具条目（`browser_navigate`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_get_text`、`browser_back`、`browser_screenshot`、`browser_close`）。`make dev` / Docker 启动时会检测到已启用的 `browser_navigate` 工具，并在依赖同步时保留 `browser` extra。如果配置了浏览器控制但缺少 Playwright，Gateway 会启动失败；并且除非后端确实能提供该功能，否则 `/api/features` 会隐藏 Browser UI。除本地、可信的调试之外，请保持 `headless: true` 和 `allow_private_addresses: false`。使用 `cdp_url` 附加到现有 Chrome 时，无法强制执行 DeerFlow 的子资源/重定向 SSRF 防护，因此除非通过 `allow_unguarded_cdp: true` 明确承认该风险，否则会以失败关闭（fail closed）；仅在配合受信任的本地浏览器时使用它。浏览器会话是进程本地的；在该工具组启用期间，请将 Gateway 保持为单个 worker 进程，因为普通的 uvicorn worker 调度不提供线程亲和性。这意味着要设置 `GATEWAY_WORKERS=1`，并且在那些向 uvicorn 传递参数时不带任何 worker 数量的启动方式中（`backend/Dockerfile`、`scripts/serve.sh`），还要将 `WEB_CONCURRENCY` 设为未设置或 `1`，因为 uvicorn 会从它获取进程数量。
现有、非 mock 的 Custom Agent 聊天在 browser control 可用，且 agent 要么将 `tool_groups` 留为不受限制，要么包含 `browser` 组时，会暴露相同的 Browser Live 控件。显式 tool-group 允许列表不包含 `browser` 时，会保持这些控件隐藏。

工作区 Browser Live 客户端会协商二进制 JPEG WebSocket 帧，每次显示刷新仅保留最新的待处理帧，并撤销被替换的 object URL。Gateway 控制消息仍为 JSON，未请求二进制能力的客户端保留旧版 JSON/base64 帧协议。

### 上下文工程

**表格工具输出摘要**：CSV/TSV 行数反映逻辑记录，因此引号字段内的换行不会增加行数。如果解析失败或超过字段限制，摘要会报告不确定的计数。超过输入大小限制的输出仍会跳过结构化解析。

**隔离的 Sub-Agent 上下文**：每个 sub-agent 都在自己隔离的上下文中运行。这意味着 sub-agent 将无法看到 main agent 或其他 sub-agent 的上下文。这对于确保 sub-agent 能够专注于手头任务，而不被 main agent 或其他 sub-agent 的上下文分散注意力很重要。

**摘要**：在一个会话内，DeerFlow 会激进地管理上下文——总结已完成的子任务，将中间结果卸载到文件系统，压缩不再立即相关的内容。这使它在长时、多步骤任务中保持敏锐，而不会撑爆 context window。

**工具输出预览预算**：外部化结果的结构化摘要有一个字符预算。较长的 JSON 键和路径会用 `...` 缩短，过大的摘要正文会包含截断提示。原始 head/tail 样本、完整文件引用和 `read_file` 指引会保留；如需精确键或完整输出，请读取保存的文件。
**严格的 Tool-Call 恢复**：当 provider 或 middleware 中断 tool-call 循环时，DeerFlow 现在会在强制停止的 assistant 消息上剥离 provider 级别的原始 tool-call 元数据，并在下一次模型调用前为悬空的调用注入占位 tool 结果。这可以避免严格校验 `tool_call_id` 序列的 OpenAI 兼容推理模型因历史记录格式错误而失败。

**可见的 Tool-Run 完成**：对于交互式轮次，DeerFlow 会对工具调用后为空的最终响应重试一次，然后呈现一个可见错误，而不是报告一次静默成功的运行。

**运行历史**：仅包含图片的用户输入每次运行只记录一次，即使 agent 发起多次模型调用也是如此。其媒体内容保留在历史记录中，无需文本摘要。

### 读取被引用的会话

Gateway API 调用方可以选择启用 `read_conversation`，并随一次运行提交 `conversation_references` 列表。lead agent 随后可以分页读取这些归其所有的会话当前可见文本的有限内容。读取权限随运行结束而失效，旧消息中的文本不会授予访问权限。在访问权限失效或源被删除后，agent 已经读取的文本仍会保留在目标会话中。一条消息若长到一次读取不完，会带有 continuation，因此 agent 可以读取其余部分；只有在无法进行该读取时，它才会请求缺失的部分。

无法添加顶级请求字段的 SDK 客户端可以将同一列表作为 `context.conversation_references` 发送，`GET /api/features` 会报告该工具是否启用。启用时，Web composer 会在附件按钮旁显示一个 “Reference a conversation” 按钮：最多选择三个你最近的会话，它们仅附加到下一条消息，并在 composer 和转录记录中显示为 chip。没有自动的历史搜索。参见[配置](backend/docs/CONFIGURATION.md#reading-referenced-conversations)
以及 [request contract](backend/docs/API.md#referencing-a-previous-conversation)。

### 当前 Task Notes

通过 `task_continuity.enabled: true` 启用 [task notes 和 history recall](docs/task-continuity.md)。
一个 task 最多可以保留八个 note。超出剩余 slot 的并行新增会返回
`note_capacity`，并保留现有 note。当启用 artifact-handle resolution 时，
容量按解析后的 key 计数；同一 note 的 alias 共享一个 slot。
格式错误的非 dict 同级参数不会消耗 slot，也不会干扰有效的 note 调用。
key 无效、内容超过 750 个字符、source 多于四个或 source ID 格式错误的
note 同样不占用 slot。现有 key 仍可被替换或删除。由同级删除或运行时
失败（例如 source 不可用或策略拒绝）释放的 slot 会在下一批中变为可用，
此时被拒绝的新增可以重试。

### 长期记忆

可选的 [DeerMem scope-isolation benchmark](backend/scripts/benchmark/deermem_scope_isolation/README.md)
会检查 facts 和 summaries 之间的语义安全性，以及跨用户和 agent 的
fact routing。失败的提取尝试是可重试的执行错误，而不是安全通过。

对于 DeerMem，`memory.backend_config.storage_class: markdown` 会选择容错的
summary 读取，同时保留 JSON 写入和现有 UI。手动编辑的
`memory.json` 可以将其 JSON 对象放在带围栏的 `memory-json` 块内；
支持内嵌反引号和后续的围栏 note。无法解析的 summary
文本会被移到 `memory.json.corrupt-<timestamp>` 以便在重建前恢复。
`storage_path` 必须指向数据根目录，而不是现有的 JSON 文件。

Gateway shutdown 会在关闭 backend 之前排空 memory 更新，即使
shutdown 被取消也是如此。配置重新加载失败会被记录，而不会中止运行时
teardown。对于 Kubernetes，为所有 shutdown
hook、config/backend resolution、`memory.shutdown_flush_timeout_seconds` 以及
预算 `terminationGracePeriodSeconds`
backend close 加上安全裕量。flush 超时不会约束 `close()`：
custom backends 必须使 close 快速或有内部界限，否则 shutdown 可能等待
直到进程被强制终止。

大多数 agent 在对话结束的那一刻就忘记一切。DeerFlow 会记住。

DeerMem 可以选择性地抑制近重复的提取事实，通过
`memory.backend_config.fact_dedup_enabled: true` 和
`fact_dedup_similarity_threshold`（默认 `0.7`，范围 `0.5`–`1.0`）。
这种本地、确定性的 word/CJK-bigram 启发式仅在同一 user、agent 和 category 内
比较事实；它不是语义等价检测。
它保留现有 ID、text 和 creation time，将 confidence 提升到
最大值，并且仅在 confidence 增加时刷新 source。显式
纠正替换和提议删除的事实受到保护，不会被
近重复合并。合并不算作用户确认。该 gate
默认关闭，且不影响定向事实更新。

DeerFlow 还包括一个可选的 `openviking` memory backend。它使用
官方 `langchain-openviking` package 将完成的轮次捕获到稳定的
OpenViking Sessions 中，并为 prompt 注入召回记忆，同时将
DeerMem 保留为默认。初始集成在 `memory.mode: middleware` 中支持一个 DeerFlow user 使用
一个凭据绑定的 OpenViking USER API key，并且
不会从 `ovcli.conf` 继承任意 HTTP headers。
有关其配置、行为和当前边界，请参见 [OpenViking memory backend](docs/OPENVIKING.md)。

跨会话，DeerFlow 构建关于你的 profile、preferences 和 accumulated knowledge 的持久记忆。你使用得越多，它就越了解你——你的写作风格、技术栈、重复出现的工作流。记忆存储在本地，并始终由你掌控。

DeerMem 和 mem0 捕获用户输入和最终 assistant 回复。请求工具的 assistant
轮次，包括格式错误或 provider-raw 调用，是
即使它们包含可见文本，也会被排除在 memory extraction 之外。

DeerMem 仍是默认的 local backend。对于托管的 mem0 Platform API 或与 API 兼容的自托管服务器，还提供可选的 `mem0` backend。其携带 token 的 `base_url` 默认必须使用 HTTPS；明文 HTTP 需要显式选择加入本地开发模式。参见 [mem0 backend 指南](backend/packages/harness/deerflow/agents/memory/backends/mem0/README.md)。

对于自托管或托管的 Honcho（v3 API），提供可选的 `honcho` backend。它在 Honcho 的服务器端构建 user-model memory——长期偏好以及跨会话的工作表示——因此该 backend 在本地不进行任何 LLM 调用。每个用户都会获得一个由 `user_id` 派生的隔离 workspace；缺少 user id 时会 fail closed，而不是回退到共享 workspace。此 backend 不支持 fact CRUD 以及 Settings 页面的 fact 编辑。参见 [Honcho backend 指南](backend/packages/harness/deerflow/agents/memory/backends/honcho/README.md)。

Memory 更新现在会在 apply 时跳过重复的 fact 条目，因此重复的偏好和上下文不会跨会话无限累积。旧版 memory 文件在读取或导入时会被规范化，包括可恢复的 fact metadata，因此随着 schema 演进，较旧的本地数据仍可使用。前端和后端规范化在 confidence 缺失或无效时使用 `0.5`，将空白 source 默认为 `unknown`，并裁剪 fact 内容。
在默认的 DeerMem `middleware` 模式下，自动提取现在会按 scope、durability 和 authority 对每条提议的 fact 进行分类，然后由确定性的 write gate 决定是否接受。只有持久的、描述性的 user 级 fact 才会被存储；当前 thread 或 project 的约束以及一次性 action 权限则保留在 conversation state 中。user-global summary 要求同时具备 user scope 和 descriptive authority，contradiction removal 受 scope gate 约束，而依赖于 replacement 的 removal 仅在其 replacement 实际通过验证并完成存储时才会被应用。这些分类标签是仅用于提取的 metadata，不会增加额外的 LLM 调用，也不会写入 fact 文件。`memory.mode: tool` 中的显式 CRUD 工具仍然是一条独立的、由模型驱动的路径。通过 `memory.backend_config.prompts_dir` 覆盖内置 DeerMem prompt 的部署，必须将新的分类字段添加到其自定义模板中（`memory_update` 的 fact/summary/removal 格式以及 `consolidation` 的 consolidated-fact schema）：write gate 采用 fail-closed 策略，因此未迁移的模板会阻止所有由提取驱动的 fact、summary 和 removal 写入，仅通过 `rejected_by_scope_gate` 指标和高拒绝率警告暴露出来。
当 fact scope 达到 `max_facts` 时，DeerMem 默认仍使用历史沿用的仅 confidence 淘汰顺序。运维人员可以选择启用 `memory.backend_config.fact_eviction_policy: hybrid-v1`，它组合了有界 confidence（65%）、显式确认新鲜度（25%）和 query 驱动的访问热度（10%）。Hybrid signal 元数据仅在 hybrid-v1 或 shadow mode 启用时收集。显式确认由现有的 memory-update LLM 调用作为 `factsToReinforce` 返回，并且仅当确定性消息处理也检测到用户强化 signal 时才被接受；它还会重置该 fact 的陈旧度审查时钟。这个确定性门控是批次级的：它仅确定当前提取批次中最后六条过滤后的消息里有一条 human message 匹配了强化模式。LLM 选择的 `factsToReinforce` ID 提供 fact 绑定；DeerMem 不会独立验证 signal-to-fact 对应关系。重复提取或自动注入从不会确认一个 fact。自定义 `memory_update` prompt 应添加可选的 `factsToReinforce` 数组，以参与确认新鲜度。访问热度存储在一个单独的衰减 sidecar 中，并且仅当 `memory_search` 实际返回该 fact 时才会增加，因此读取不会重写规范 Markdown 或其 `updatedAt`。Hybrid mode 还会保留一个有界的最小修正槽位数（上限的 10%，最多 10 个；未使用的槽位返回正常竞争）。容量删除仍然是物理删除，但有界的仅元数据审计会记录 fact ID、类别、策略分数和原因，而不复制 fact 内容。`fact_eviction_shadow_enabled: true` 会与默认策略一起评估 hybrid-v1，而不改变实际保留。此功能不增加 LLM 调用，并且可以通过选择 `confidence` 回滚。
基于文件的内存现在将全局用户上下文与 agent facts 分开。每个用户有一个 `memory.json`，仅包含与项目无关的 `user` 和 `history` 摘要；每个 fact 是 `agents/{agent_name}/facts/` 下的一个规范 Markdown 文件。现有的 lead-agent 中间件、API、Settings、import/export 以及省略 `agent_name` 的嵌入式客户端调用，在 DeerMem 内部解析为保留的 `__default__` 桶。该桶在有效的自定义 agent 名称语法之外，因此名为 `lead-agent` 的真实自定义 agent 拥有一个单独的 fact 仓库，并且删除自定义 agent 不能删除没有 `config.yaml` 的仅内存目录。公开的 agent 标识符不区分大小写，并规范化为小写。Runtime/API 读取器仍然为选定的/默认的 agent 接收兼容的 `facts` 数组，因此前端不会从 `memory.json` 读取 agent facts；结构化的 Markdown `source` 元数据在 MemoryManager 边界处投影到历史字符串字段。无作用域的 Clear All 首先从未读的旧版 per-agent JSON 迁移 facts，而不采用其即将被清除的摘要，然后从每个 agent 桶中移除共享摘要和 facts，同时保留 agent 配置文件，因此后续读取无法复活被跳过的旧版 facts；显式指定 agent 作用域的清除仅移除该 agent 的 facts。在首次正常读取时，嵌入在用户 JSON 中的旧 facts 会自动迁移到 `__default__`；当该目录不是真实的自定义 agent 时，写入较早的隐式 `lead-agent` 桶的 facts 也会被移动。迁移和正常写入仅在持久存储锁释放后通知配置的检索适配器。DeerMem 默认使用作用域感知的 SQLite FTS5/BM25 适配器，仅将可重建的派生索引数据存储在 `.retrieval/` 下（或在设置时存储在 `memory.backend_config.retrieval_index_path` 下；相对值相对于 `storage_path` 解析），并在 Gateway 启动期间在后台重建，或在首次作用域搜索时惰性重建。损坏的派生索引会自动重新创建。当多个 Gateway 实例共享一个 `storage_path` 时，将 `retrieval_index_path` 指向实例本地磁盘：SQLite 的 WAL 模式在网络文件系统上不受支持，每个实例在对等方写入后的下一次搜索时重新同步用户的索引，并且声明的多实例部署（`deployment.multi_instance: true` / `DEER_FLOW_MULTI_INSTANCE=1`）若将索引留在内存根目录下，会在启动时记录警告。Helm chart 为其挂载一个 Pod 本地的 `emptyDir`。将 `memory.backend_config.retrieval_adapter` 设置为空字符串以禁用它并使用本地子字符串回退。中文分词是可选的；安装后端 `memory-zh` extra（`uv sync --extra memory-zh`）以进行 jieba 辅助的子短语搜索。日志写入、共享用户锁和乐观用户内存修订可防止静默丢失更新。
设置 `memory.backend_config.retrieval_relevance_enabled: true` 以启用确定性的 relevance/confidence 排序和 query-aware 注入。这会**在搜索时绕过 `retrieval_adapter`**，包括默认的 FTS5/BM25 和自定义 adapter；索引仍照常配置。`retrieval_relevance_weight` 控制混合比例，`retrieval_diversity_weight` 启用近重复惩罚（默认 0）。评分对每个 query/fact 最多使用前 4096 个字符和 128 个 token。搜索最多只多样化到 `top_k`；注入则对 guaranteed 和 regular facts 分别独立多样化，直到达到各自的 token 预算。将该功能保持禁用，即可保留现有的检索和注入行为。

词法相关性衡量的是不同 query term 的 IDF 加权覆盖率，因此重复的部分匹配无法仅仅通过让分数饱和就与完整匹配持平。前缀匹配要求一个完整 token 作为另一个 token 的前缀，而不仅仅是共享四个字符。对于上传内容，query-aware 注入使用保留的用户请求，而不是前置的文件描述；仅含附件的消息仍保留无 query 的注入。较旧的自定义 memory backend 可以保留其现有的 `get_context` 签名：prompt injection 和继承的 async wrapper 仅在该 callable 支持该关键字且 hint 不为 `None` 时才传递 `query`。对于同一 user/agent 候选范围，搜索和自动注入使用相同的 IDF 加权。按 category 过滤的搜索以及注入各自的 guaranteed/regular token 预算仍可能产生不同的最终选择。
memory 注入遵循配置的操作模式。在 `middleware` 模式下，DeerMem 会注入用户全局摘要和所选 agent 的 facts。Custom Agent 的 bootstrap 对话也会使用该 agent 的 fact bucket，因此设置细节不会泄漏到默认 agent 的 memory 中。在 `tool` 模式下，自动 `<memory>` 块仅包含全局 `user` 和 `history` 摘要；agent facts 通过 `memory_search` 显式检索，避免自动和 tool 返回的 fact 上下文重复。设置 `memory.injection_enabled: false` 在任一模式下仍会禁用整个块。当 fact ID 已知时，`memory_get(fact_id)` 会从当前用户和 agent 作用域返回该确切 fact，而无需按内容搜索。缺失或超出作用域的 ID 会返回 not-found 错误；不具备所需读取或 agent 作用域能力的后端会返回 unsupported 错误。

单个 Custom Agent 可以在不更改全局设置的情况下选择退出 memory。将 `memory_enabled: false` 添加到该 agent 的 `users/{user_id}/agents/{name}/config.yaml`。该 agent 仍会收到当前日期提醒，但 DeerFlow 不会注入召回的 memory，不会排队被动或摘要驱动的 memory 更新（包括手动 `/compact`），不会暴露 memory 工具，也不会为该 agent 添加 memory 工具指令。如果现有 agent 被关闭，则在下次模型调用前，其先前注入的 memory 块会从 checkpoint 状态中移除，而其日期提醒和对话会保留。省略该字段（或将其设置为 `true`）会保留现有的全局 `memory` 行为。
单条 fact 的 repository 操作是真正增量的：upsert/delete 只读取、记录 journal、写入并重新索引所寻址的 fact 文件，并返回显式的 incomplete delta，而不是依赖 cache 的伪造完整文档。摘要 change set 将传入的 `user`/`history` 子键合并到已持久化的 section 之上，因此部分更新不会擦除被省略的兄弟项；完整导入会在应用替换值之前，把两个 section 规范化为完整的 compatibility schema。导入会在改动已存储 memory 之前，以 HTTP 400 拒绝格式错误的 fact 列表或空白/非文本内容；可恢复的 legacy metadata 仍会获得默认值。显式的空 fact 列表仍然是有意为之的清空。Manager/API compatibility 方法仅在其公开响应契约要求时才物化一份全新的完整文档。fact 级别的点操作使用各自独立的 expected user-memory revision 和 fact revision，并且当所有被寻址的 fact 前置条件仍成立时，可以显式 rebase。由 snapshot 派生的操作（如 scoped clear、capped create、consolidation 和 trimming）绝不重放陈旧的 delete/trim 集合：manifest 冲突会重新加载完整文档并重新计算该操作，且带有有界重试。fact 路径使用 `SHA-256(fact_id)` 的前两个十六进制字符，从而使生成的 `fact_*` ID 分散到各个 shard 上。cache token 结合了共享 JSON 的纳秒级 mtime、大小和持久化 revision；这可以防止粗粒度 mtime、相同大小的写入返回陈旧数据，而无需扫描 fact 文件。直接带外编辑 Markdown 需要显式 reload。特定于 storage 的冲突与损坏会在 MemoryManager 边界处转换；Gateway 将冲突返回为 HTTP 409，将稳定且不敏感的 corruption 错误返回为 HTTP 500。全文档 `save()` 仍然是 compatibility API，并在写入前计算 diff；格式错误或缺失的 `facts` 不再会静默擦除 agent 的 Markdown 文件。legacy migration 会在删除 agent 的 `memory.json` 之前保留非空的 `user`/`history`；冲突的 summary 会保留 legacy 文件并显式报错，而不是择一胜出。
`memory.json` 中的 legacy facts 会在用户首次正常读取 memory 时自动迁移到保留的 `__default__` Markdown bucket 中。如果运维人员希望在开始承载流量之前先审计或完成迁移，可以从 `backend/` 运行这个可选的幂等 CLI：

```bash
PYTHONPATH=. python scripts/migrate_memory_markdown.py --all-users --dry-run
PYTHONPATH=. python scripts/migrate_memory_markdown.py --all-users
# A custom DeerMem root or original non-directory-safe identity can be explicit:
PYTHONPATH=. python scripts/migrate_memory_markdown.py --storage-path /path/to/deerflow-home --user-id 'test@example.com'
```

对于正在运行的应用程序来说，v1 到 v2 的存储迁移是单向的：pre-PR 代码不会读取 Markdown facts。在升级持久化部署之前，请停止 DeerFlow，并对已配置的 memory storage root 创建文件系统快照或完整备份。迁移还会在写入 v2 数据之前，将每个将被破坏性处理的 JSON 源文件持久保留在原路径旁，命名为 `{manifest_filename}.v1.bak`；如果已存在不匹配的备份，或备份写入失败，迁移会停止，且不会修改 v1 源文件。这个本地备份会保留迁移前的数据，但它不能替代完整快照，也不包含升级后创建的 facts。

`--user-id` 可以重复指定。`--all-users` 会发现所选 storage root 下已有的 directory-safe buckets；那些传入了包含 `@` 等字符的 raw IDs 的独立集成应使用原始值配合 `--user-id`。某个用户迁移失败时会被报告出来，但不会掩盖审计的其余部分；当任何用户失败时，命令会以非零状态退出。自动首次读取路径仍然启用，因此启动并不要求运行这个 CLI。

## Recommended Models

DeerFlow 与模型无关——它可用于任何实现 OpenAI-compatible API 的 LLM。话虽如此，它在支持以下特性的模型上表现最佳：

- **长上下文窗口**（100k+ tokens），用于深度研究和多步骤任务
- **推理能力**，用于自适应规划与复杂任务分解
- **多模态输入**，用于图像理解与视频理解
- **强大的 tool-use 能力**，用于可靠的 function calling 和结构化输出

MindIE XML tool-call arguments 支持带符号、小数和指数的 JSON 数字。如果某个数字溢出、下溢为零，或超出 Python 的整数位数上限，则整个 argument 保持为字符串，包括嵌套的 JSON 列表和对象，因此解析不会静默改变其值。

## 嵌入式 Python 客户端

对于 `DeerFlowClient(agent_name="researcher")`，所指定 agent 的 `mcp_plugins` 选择同时作用于 lead agent 及其 `task` / `batch_task` 委派：`null` 继承所有已启用的 MCP 插件，`[]` 表示不选择任何插件，而 installation ID 则仅选择这些插件。在编辑已保存的 agent 配置后，调用 `client.reset_agent()` 以刷新该选择。

`DeerFlowClient.stream()` 在每个 `values` 事件中都包含 `summary_text`。它是当前压缩后的上下文摘要，不存在时为 `None`。消费者无需读取 checkpoint 内部结构即可记录变化；重复的快照可能携带相同的摘要，而初始快照可能已经包含来自更早轮次的摘要。

DeerFlow 可作为嵌入式 Python 库使用，而无需运行完整的 HTTP 服务。`DeerFlowClient` 提供对所有 agent 和 Gateway 能力的进程内直接访问，返回与 HTTP Gateway API 相同的响应 schema。HTTP Gateway 还暴露了 `DELETE /api/threads/{thread_id}`，用于在 LangGraph thread 本身被删除后移除 DeerFlow 管理的本地 thread 数据：
对于由数据库支撑的 run 事件，删除某个 run 会保留其 thread 的 sequence watermark。当不再有任何事件残留时，删除 thread 会移除该 watermark，从而允许重新创建的 thread 从 sequence 1 重新开始。当另一个 owner 的事件仍然存在时，owner 作用域的删除会保留该 watermark。

Thread ID 可以由调用方提供，不必是 UUID。显式提供的 ID 必须包含 1–64 个 ASCII 字母、数字、连字符或下划线（`^[A-Za-z0-9_-]{1,64}$`）。只有当 `thread_id` 被省略或为 `None` 时，DeerFlow 才会生成 UUID；显式提供的空字符串是无效的。在更早、更宽松的规则下创建的现有可路由寻址的 thread 仍然可读、可删除，但不能启动新的 run，也不能创建新的文件系统或 sandbox 状态。当 ID 在规范契约下不安全时，legacy 删除会跳过本地路径清理。对于那些对话仅存在于 LangGraph checkpoint 中的规范 legacy thread，DeerFlow 会在首次新的 run 之前从该 checkpoint 播种一个空的 run-event feed，以便 `/messages/page` 同时保留旧轮次和新轮次。

```python
from deerflow.client import DeerFlowClient

client = DeerFlowClient()

# 聊天
response = client.chat("Analyze this paper for me", thread_id="my-thread")

# 流式输出（LangGraph SSE protocol：values、messages-tuple、end）
for event in client.stream("hello"):
    if event.type == "messages-tuple" and event.data.get("type") == "ai":
        print(event.data["content"])
    elif event.type == "messages-tuple" and event.data.get("type") == "tool" and "artifact" in event.data:
        # 结构化的 tool artifact（例如 ask_clarification 卡片）
        # 会在 ToolMessage 提供时被保留。
        print(event.data["artifact"])

# 配置与管理 —— 返回与 Gateway 对齐的 dict
models = client.list_models()        # {"models": [...]}
skills = client.list_skills()        # {"skills": [...]}
client.update_skill("web-search", enabled=True)
```

client.upload_files("thread-1", ["./report.pdf"]) # {"success": True, "files": [...]}
client.set_goal("thread-1", "finish the implementation and make all tests pass")
client.get_goal("thread-1") # {"goal": {...}} or {"goal": None}
client.clear_goal("thread-1")

````

续接一个 thread 时，`values` 仍包含完整的会话状态，而 `messages-tuple` 和 `end.usage` 只覆盖当前这一轮。

HTTP Gateway 接受 `values`、`messages-tuple`、`updates`、`debug`、`tasks`、`checkpoints` 和 `custom` 流模式。不受支持的模式（如 `messages` 和 `events`）、不受支持的非默认 run 选项（如 webhooks、延迟执行或 `multitask_strategy="enqueue"`），以及未声明的 SDK 选项（如 checkpoint 持久性覆盖），都会在执行前返回 `422`，而不会被静默忽略或降级。

所有返回 dict 的方法都会在 CI 中依据 Gateway Pydantic 响应模型进行校验（`TestGatewayConformance`），以确保内嵌 client 与 HTTP API schema 保持同步。完整的 API 文档见 `backend/packages/harness/deerflow/client.py`。

## 项目

项目将相关的会话归组到共享的名称、instructions 和文档架之下。

会话在创建时加入项目（即选中某个项目时），或稍后通过移动菜单加入。run 从不修改归属关系：提交消息不能分配或重新分配会话。将会话移出项目后，它会保持未分配状态，直到被显式地再次移动。

移动会话会刷新它的 header 归属以及项目列表，即使某个较早的 metadata 请求仍在进行中也是如此。

项目需要当前的数据库表和列。如果缺少项目 schema，那么由较早的基于 0018 的 rollout 标记为 `0019_thread_incarnations` 的数据库会在启动时被拒绝。请遵循[离线数据库恢复流程](docs/database-forward-revision-recovery.md)
在针对该数据库启动此构建之前。

### 项目指令

每个项目存储自由形式的指令——适用于项目中每次对话的背景、约定和约束——可在项目页面的指令标签页中编辑，并带有实时字节计数器。当在成员线程上启动一次运行时，Gateway 会固定项目的当前状态一次，并将指令渲染为一个有界的、请求作用域的 `<project>` 块，仅用于该次运行：该块永远不会进入 system prompt 或持久化历史记录，并且每次新的运行都会看到最新保存的指令。指令的上限为 `projects.instructions_max_bytes` UTF-8 字节（默认 8192，范围 256–262144）；多字节字符按其 UTF-8 字节长度计算。过大的指令在写入时会被拒绝并返回 `422`，且绝不会被静默截断。

### 文档架

每个项目都有一个文档架，用于存放整个项目共享的文件，可从项目页面的文档部分进行管理：

- **上传**文件（按钮或拖放，每个请求一个文件）。文档架大小限制复用 `uploads.max_file_size`（默认 50 MiB）；重新上传相同内容会返回现有条目，而不是创建重复条目。
- **列出**条目，包含名称、大小、修改时间和来源（上传 vs. 从对话保存），并可预览或下载任何条目。
- **保存到项目**（从线程文件）：文档架下方的只读对话文件浏览器列出成员线程的上传和输出，每个都有一个保存到项目操作。
- **附加到线程**：通过正常的摄入管道将文档架文件复制到线程的上传中，以便对话可以直接使用它。

新的文档架名称，包括显式上传 `name` 和提升 `shelf_name`，遵循普通上传文件名验证。包含 NUL、Windows 保留设备名（例如 `CON.txt`）或尾部点号的名称会在字节暂存之前被拒绝并返回 `400`。
在原生 Windows 上，document shelf 使用 extended-length 文件系统路径，因此深层 workspace 目录和长文件名可以上传、下载、恢复和清除，而无需启用系统级的 long-path 设置。针对单个路径组件的文件系统限制仍然适用。

在 member 线程上的运行还会收到一个有界的 `<documents>` 索引，该索引在每次运行时从固定的快照渲染（受 `projects.shelf_index_max_entries` 和 `projects.shelf_index_max_bytes` 限制），并且 agent 可以使用 `list_project_documents` 和 `read_project_document` 工具对 shelf 进行分页并读取文档。

文档字符计数使用一个有界的、线程安全的缓存；并发读取不会在其缓存锁后面串行化完整的文件扫描。

### 归档读取语义

归档项目会冻结写入，但保留读取。已归档项目中的线程仍会运行，并且仍会收到项目的 instructions 和 shelf 索引，shelf 也仍然完全可读：列表、预览/下载、conversation-files 浏览器以及 attach-to-thread 都继续正常工作。上传、save-to-project 以及将单个 shelf 文件移到 trash 需要项目处于活动状态，并且已移入 trash 的文档无法恢复到已归档的项目中。删除已归档项目仍然被允许，并会将其整个 shelf 移到 trash。

### Trash

删除 shelf 文档会将其移到 trash，而不是将其擦除：该条目会保留其字节以及其来源项目的快照，为期 `projects.trash_retention_days`（默认 30 天），之后 retention sweep 可能会将其永久清除。`/workspace/trash` 页面——可从项目页面的 Documents 部分和侧边栏的 Projects 标题处进入——会列出已移入 trash 的文档及其来源项目和剩余保留时间，并提供针对每个条目的 Restore 和 Delete permanently 操作，以及一个 Empty trash 操作，该操作会永久删除 trash 中的每个文档——立即删除，而不是在保留窗口之后；该窗口仅限制条目可以在那里停留多长时间
在 retention sweep 回收它之前。Restore 会将 document 返回其 origin project，或返回当 origin 已不存在或已归档时你选择的 project；如果目标已包含相同的 active file，则 entries 合并。删除 project 会在同一步骤中将其整个 shelf 移到 trash。

## 计划任务

DeerFlow 现在在工作区中包含一流的 scheduled-task MVP。

编辑一次性任务的标题或 prompt 会保留其原始执行时间，包括秒以及在夏令时时钟回拨期间选定的 occurrence。更改其日期、时间或时区会重新计算执行时间。编辑时切换任务会加载所选任务自己的标题、prompt 和 schedule。

当前 MVP 能力：

- 在 `/workspace/scheduled-tasks` 管理任务
- 一次性任务表单会拒绝夏令时转换期间被跳过的本地时间；请在创建或保存任务前选择另一个时间。
- 选择每个计划任务是重用 thread 及其对话历史，还是每次运行创建新的 thread
- 将每个任务固定到 `lead_agent`（默认）或所有者已有的自定义 agent；未知名称会被拒绝
- 在 scheduled-task PATCH 中发送 `assistant_id: null` 会将任务重置为 `lead_agent`；省略 `assistant_id` 会保留当前 agent，包括当该自定义 agent 此后已被删除时
- 将现有任务复制到创建表单中作为可编辑草稿，而不复制其运行历史
- 支持 `once`、`cron` 和 `interval` 计划
- 编辑或复制 interval 任务会保留其保存的 cadence，直到 interval 被显式更改，包括操作员的 scheduler 配置所允许的 sub-minute intervals
- 将后台计划执行作为非交互式 DeerFlow 运行来运行（那里不暴露 `ask_clarification`）
- 当其复用的 thread 或全局执行预算繁忙时，将到期的执行持久化为 `queued`，然后在容量可用时启动它；排队的 occurrence 在 Gateway 重启后仍然存在，并在 `scheduler.queue_timeout_seconds` 后失败
- 在任务所有者之间公平地共享执行 slot：一个所有者同时最多可以有 `scheduler.max_concurrent_runs_per_user` 个已调度的 run 处于启动或运行状态（默认为 2，绝不超过 `max_concurrent_runs`；`0` 会关闭每个所有者的上限），等待队列按所有者逐个排空，因此一个所有者的积压永远不会阻碍另一个所有者的 run。等待时间超过 `scheduler.queue_timeout_seconds` 的 run 会被跳过，其历史记录显示 "Skipped: it waited too long for a free slot"
- 当 occurrence 处于 `queued`、`launching` 或 `running` 状态时冻结任务的 definition，因此持久化的 occurrence 不会静默地获取不同的 prompt、thread 或 schedule；将任务转换为 paused 或删除它会取消现有的等待中的 occurrence，而 `launching`/`running` 的工作必须先完成，才能重试这些变更，并且显式的手动触发仍然可以等待并运行，而不会恢复已暂停的 schedule
- 暂停、恢复、触发、检查历史记录和删除任务
- 搜索任务标题或 prompt，结合状态/类型过滤器和当前 thread 范围。
- 通过正常的 DeerFlow run 生命周期执行已调度的工作
- 当 `channel_connections.enabled: true` 时，在支持主动推送的应用上将计划任务更新发送给任务所有者已连接的 IM 身份（outbox + delivery worker），目前是 WeCom；设置中会为每个应用显示是否在那里发送更新，其他应用则不会收到任何更新。每次触发最多发送一条消息：已完成、失败或未达成目标的运行，连续三次未达成目标后的自动暂停，agent 的暂停（其停止条件已满足），或任务完成（所有 `max_runs` 执行完毕，到达 `end_at`）；当多种情况同时适用时，暂停或完成优先，并且仍会说明上一次运行的情况。一次性任务只发送其运行的结果。消息在记录该结果的同一数据库事务中排队，因此崩溃或丢失 lease 后最终确定的运行只会通知一次。它自行读取，使用你的 Web UI 语言（否则使用 `channel_connections.notification_locale`）：任务标题、发生了什么、agent 回复时的一行结果，以及“打开 DeerFlow → 计划任务查看详情。”，不含 ID 和链接。单纯手动“立即运行”的试验和中断的运行保持静默，结束时没有已完成运行的触发也保持静默（启动错误、队列超时、被重启中断）。渠道/传输中断会将投递搁置而不耗尽重试次数，最长约一天；平台拒绝会重试大约 15 分钟，然后最终成为 `failed`。在投递等待期间你断开的身份永远不会被推送：该行会作为 `failed` 被丢弃。
- 以每页 50 条浏览执行历史；较旧的页面会暂停自动刷新，并提供显式返回到最新运行的入口。计数仅在成功读取后出现；加载中和读取失败不会报告为零次运行。
Derived run summaries 会省略截断文本前导的内联 `<think>` 推理，因此冗长的思考不会在 previews 或定时通知中取代实际答案。原始响应历史和答案中的字面标签保持不变；此前已存储的 run summaries 不会被重写。

**通过 API 过滤执行历史**

若要在不下载每个成功 occurrence 的情况下检查失败项，具备 `threads:read` 权限的已认证客户端可以为自有 task 请求 `GET /api/scheduled-tasks/{task_id}/runs?status=failed&limit=50&offset=0`。可选的 `status` 接受 `queued`、`launching`、`running`、`success`、`failed`、`skipped`、`interrupted` 或 `unmet`；这些是 occurrence 状态，因此诸如 `completed` 之类的 task 状态无效（422）。

过滤发生在分页之前。`limit`（1–200，默认 50）和 `offset`（非负，默认 0）作用于匹配的记录，按创建时间再按 ID 排序，均为降序。省略 `status` 会保留现有的混合历史数组响应；无匹配项时返回 `[]`。该 API 不会改变 task 执行，workspace 历史 UI 仍保持未过滤状态。

当前 MVP 限制：

- 无纯文本 notification jobs
- 无 channel 或 GitHub dispatch targets（上述 result push 不是 dispatch target）

通过 `config.yaml -> scheduler.enabled` 启用后台轮询。手动触发使用相同的 scheduled-task 资源和执行路径。

### 生命周期、安全上限与停止条件

- tasks 页面和 REST API（`POST` / `PATCH /api/scheduled-tasks`）接受与 conversation 相同的每次运行目标（`goal_objective`）、安全上限（`max_runs`、`end_at`）和停止条件（`stop_condition`）。在 PATCH 中发送 `null` 会清除这四项中的任意一项；不带 UTC 偏移的 `end_at` 是 task 时区中的墙上时钟时间。
- 停止条件就是用户的“当……时停止”规则。它存储在它自己的字段中（migration `0031`），从不放在任务 instructions 里。只有当一次 run 开始时，DeerFlow 才会把它追加到该 run 的 message 中，并要求该 run 在规则成立时调用 `stop_scheduled_task`。当 `scheduler.tool_enabled` 打开时，每个 scheduled run 都能停止自己的 schedule，无论该任务是由 chat 还是由 tasks 页面创建的；当它关闭时，run 会被要求报告规则已满足，而不是调用一个它没有的工具。
- 在 tasks 页面创建的 goal 任务现在会像 chat 创建的任务一样被评估，它们的 run 也会收到保存的 notes 和上一次 run 的引用。
- Resume 会从现在开始计算下一次 run，因此长时间的暂停绝不会导致一次 catch-up run。一次性任务如果时间已过，会返回 `422 once_time_passed`，并且需要一个新的时间。Resume 一个 active 任务不会改变任何东西；pause 一个 finished 任务会返回 `409 task_finished`。
- `max_runs` 是自动 run 在整个生命周期内的总数；trial run 从不计入。重新激活一个上限已用完的任务（Resume，或一个会重新启用 finished 任务 schedule 的 PATCH）会返回 `409 limits_exhausted`，除非同一个请求续订了已耗尽的限额：已用完的 run 限额需要更高的 `max_runs` 或 `null`，已过的结束时间需要更晚的 `end_at` 或 `null`（仅靠更晚的 `end_at` 并不能续订已用完的 `max_runs`）。`POST /api/scheduled-tasks/{task_id}/resume` 为此接受一个可选的 `{"max_runs": …, "end_at": …}` body（`null` 会清除上限；chat 创建的 sub-hourly 任务必须保留一个）。一个只更改 finished 任务上限的 PATCH 会保存它，并让该任务保持 finished。
- goal-check 失败（evaluator 失败，或对话在检查期间发生变化）既不计入三次未命中的自动暂停，也不会重置它。更改 goal、instructions 或停止条件，或者添加一条 note，都会重新开始计数；Resume 会保留它。
- 当该 Gateway 进程的 scheduler 未运行时，创建 task（包括 Duplicate）会返回 `409 scheduler_not_running`，因为该 task 永远不会按 schedule 运行。`GET /api/features` 会报告 `scheduled_tasks.available`、`running`、`tool_enabled` 和 `min_interval_seconds`。
- 来自 `/api/scheduled-tasks*` 的错误格式为 `{"detail": {"code", "message", "params"}}`；参见 [`backend/docs/API.md`](backend/docs/API.md#scheduled-tasks) 和 `contracts/scheduled_task_errors_contract.json`。

### 在对话中创建 schedule

同时设置 `scheduler.enabled: true` 和 `scheduler.tool_enabled: true`，然后重启
Gateway。经过授权的交互式 turn 可以使用 `schedule_task` 来创建、更新、
列出、暂停、恢复或删除 task、启动试运行，或保存 note。例如：
“每个工作日 9:00，检查 release-checklist.md 并告诉我还有哪些未勾选；
当全部勾选后停止。”在 web app 中，结果是一张实时卡片，包含 schedule、
停止条件和按钮，agent 会用一两句话回复；IM 及其他非 web 的 turn 则以纯文本
描述 schedule、下一次运行时间和停止条件。

- **对话管理哪些 task。** 在对话中创建的 task，以及在 run
  conversation（即某次 scheduled run 发布消息所在的聊天）中，该次 run 所属的
  task：“pause this”或“move it to 10:00”在那里同样有效。这仅适用于
  你发送的 turn。scheduled run 本身只能通过
  `stop_scheduled_task` 暂停它自己的 schedule。
- **编辑会保留 task。** 修改时间、instructions、goal、停止条件
  或 safety cap 都是对同一 task 的 `update`，因此其 ID 和运行历史会保留。
  `resume` 会重新启动已暂停或已完成的 task，且不会进行补跑。当
  cap 用尽时，agent 会询问如何续期已耗尽的限制（更高的
  `max_runs` 或无限；更晚的 `end_at` 或无）并将该信息随 resume 一起发送。
- **Timezone。** 你指定的时区优先。否则，新 task 会使用 browser
时区是 web app 随每条消息发送的（`context.client_timezone`，仅为此读取），结果会说明使用了哪个 zone。Interval 和带 UTC offset 的一次性时间不需要 zone；对于 cron schedule 或没有已知 zone 的本地一次性时间（例如来自 IM），agent 会询问。编辑会保留已保存的 zone；浏览器 zone 永远不会改变已有的 task。
- **结果出现的位置。** 每次 run 都会在其自己的新 chat 中发布结果，标题为“{task} · {local time}”；如果 task 在发起它的 chat 中运行，则发布在那里。当 schedule 被 agent 暂停、被自动暂停或完成时，发起它的 chat 会显示一行说明对话当时所处的位置，并附上指向该次 run 或该 task 的链接；不会再向它发布其他内容。这行内容在 task 被删除后仍然保留。run chat 会把 task instructions 显示为 run header 下方一个折叠的“Task instructions”块，而不是一条冗长的用户消息。
- **语言。** agent 用你的语言撰写标题、instructions 和 stop condition，scheduled runs 用 instructions 的语言作答。

New tasks 默认每次触发都使用一个新会话。配置的 `goal_objective` 只适用于该次触发：成功不会停止 recurring schedule。运行中的 agent 可以在你的 stop condition 已满足时，为自己的 schedule 请求 `stop_scheduled_task`；该请求在 terminal finalization 期间生效。`max_runs` 只统计自动启动次数，`end_at` 提供截止时间。任一结束条件都优先于 pause 请求。由 tool 创建的 sub-hourly schedules 需要有结束条件；每个 owner 最多可保留 20 个 live tool-created tasks，包括已暂停的 tasks。

未满足的 occurrence 会被记录为 `unmet`，与 execution failure 不同。三个符合条件的自动 unmet occurrences 会暂停一个 recurring task。被接受的 success 会重置 streak，包括依赖已披露假设的 success；
手动 trial、中断、执行失败、外部等待以及 goal-check 失败不会推进它。Resume 会保留 streak，因此另一个符合条件的未满足 occurrence 可以再次暂停任务。已连接的带有主动推送的 IM 应用通过同一个 durable outbox 对每个 occurrence 接收一条通知（goal missed、auto-paused、paused by the agent、finished）；普通手动 trial 保持静默。

你可以在管理该任务的对话中要求 agent 为未来运行保存一条显式 note（最多 10 条 note，每条 500 个字符）。新的 recurring 运行可以通过 opt-in `read_conversation` 读取上一个已执行的 occurrence，并经过相同的 owner 和读取权限检查。这提供的是源引用，而不是自动摘要，也不是回发到原始聊天。

对于 trial，直接请求，例如 “Run it now”、“OK, run it now” 或 “先跑一次吧”；在 web app 中，卡片的 **Run once now** 按钮作用相同。Host 接受来自当前 user turn 的一组有界英文/中文 direct-run 请求，可选地跟在简短确认之后，例如 “Sure,” 或 “好的，”。单独的 “yes” 或 “好”、任务提及，以及引用或条件请求不会启动付费运行。当运行已经在等待启动时，不会添加额外的 trial，并且 agent 会说明这一点。trial 不计入 `max_runs`。

一个 goal occurrence 最多可以使用九个 agent turn，每个之后都有一个 evaluator 请求。Evaluator 请求和 provider 报告的 token 计入 run 使用量；缺失使用量会使相应的成本估算未知。`token_budget` 限制主 graph，并在模型调用后检查；evaluator 使用量是额外的，因此它不是严格的 whole-run 或美元限制。

**Goal evaluation 升级：** 现有的 scheduled、webhook 和 autonomous goal 运行可以接受已披露的低风险、可逆假设，并在其 verdict 中记录 `relied_on_assumption`。Interactive goal evaluation 仍然
严格。该策略同样适用于 conversation schedule 工具被禁用时；它不授权敏感操作，也不能替代用户授权。


计划运行使用 `config.yaml` 中的 `scheduler.recursion_limit`（默认 `1000`，与 web UI 的交互式预算一致）。超过 `max_recursion_limit` 的值会被钳制。该字段在分发时读取，因此下一次计划运行会采用新值，无需重启 Gateway。

后台 scheduler 默认是单实例的。对于多 Pod 部署，请设置 `scheduler.multi_instance: true`，并使用共享 Postgres、`run_ownership.heartbeat_enabled: true` 和 `run_events.backend: db`；这样启动时和周期性恢复会保留存活的 peer runs，将过期的 launch claims 原子性地退回队列，只接管过期的 run leases，并对陈旧的 launch 写入进行隔离。`max_concurrent_runs` 是跨 Pod 对 `launching`/`running` 出现的共享全局上限；等待中的 `queued` 行不占用该上限。如果没有这些设置，请仅在一个 Gateway pod 上启用 scheduler。这些 scheduler 字段仅在启动时生效；更改它们时，请一起重启所有 Gateway Pod。

### 通过 API 预览 cron 出现时间

拥有 `threads:read` 权限的已认证客户端可以在创建任务前调用 `POST /api/scheduled-tasks/preview-cron`：

```json
{"cron":"0 9 * * 1-5","timezone":"Asia/Shanghai","count":3,"start_at":"2026-09-12T00:00:00Z"}
````

响应包含规范化后的 `cron`、`timezone`、生效的 UTC `start_at`，以及带有 UTC `run_at` 和带偏移的 `local_time` 的 `occurrences`。在此示例中，第一次出现时间是 `2026-09-14T01:00:00Z` / `2026-09-14T09:00:00+08:00`。
`count` 是从 1 到 10 的整数（默认 5）。`start_at` 必须包含时区；省略它则仅捕获一次服务器时间。Cron 表达式使用 scheduler 的五字段语法（最多 256 个字符）；时区名称最多 128 个字符。无效输入或没有所请求的未来发生次数的 schedule 会返回 422。Preview 与 scheduler 的 DST 行为一致，不会创建 task、thread 或 run，也不预留执行。这是一项 API 能力；workspace 表单尚未显示这些发生次数。

### 升级说明

- 发生次数排序适用于由升级后的 Gateway 实例接纳的行，这些实例仅将已排序的发生次数投影到父 task 上，并在任一 occurrence 仍处于 live 状态时推迟恢复，无论它是哪个实例接纳的；如果某个 task 的历史完全未排序，则在其首次排序接纳之前保持之前的时间戳排序。在滚动升级期间，由升级前实例接纳的行仍由这些实例自身投影，与升级前一样，一旦每个 Gateway writer 都运行升级后的版本，排序保证即会生效。现有历史不会被回填；升级不会重建过去的顺序，也不会修复历史计数。
- 在升级具有 `GATEWAY_WORKERS > 1` 且 `scheduler.enabled: true` 的部署之前，要么将 scheduler 保持在恰好一个 Gateway worker 上，要么配置 `scheduler.multi_instance: true`，并配合共享 Postgres、`run_ownership.heartbeat_enabled: true` 和 `run_events.backend: db`。升级后的 Gateway 会在启动时拒绝这种不安全的组合，而不是静默启动。
- 在多实例模式下，`scheduler.max_concurrent_runs` 是集群范围的执行上限，而不是每个 Pod 的上限。它包含 `launching` 和 `running` 的已调度发生次数，因此容量不会随副本数量成倍增加；持久等待行不计入该上限。
- `scheduler.multi_instance` 以及相关的 scheduler、ownership 和 run-event 设置都是仅启动时生效的。要应用变更，需协调重启所有 Gateway Pod；只修改 ConfigMap 不会激活 multi-instance recovery。

## 终端工作台（TUI）

`deerflow` 是面向常驻 shell 的用户的终端原生工作台。它通过 `DeerFlowClient` **嵌入式**运行 —— 无需 Gateway、前端、nginx 或 Docker —— 同时遵循与 DeerFlow 其他部分相同的 `config.yaml`、checkpointer、skills、memory、MCP 和 sandbox 设置。

并行的同步 stdio MCP 调用在各自的事件循环上使用独立的 session。它们不会取消彼此的连接，但也不共享服务端状态；复用 session 需要相同的 loop。详情参见
[MCP session notes](backend/docs/MCP_SERVER.md)。
手动管理的事件循环在关闭前必须排空待处理的 session owners；
常规的 `asyncio.run()` 路径会自动完成此操作。

![DeerFlow TUI](docs/tui/tui-preview.svg)

```bash
uv pip install 'deerflow-harness[tui]'        # 可选的 'textual' 依赖

deerflow                                      # 启动终端 UI（需要 TTY）
deerflow --tui-transparent                    # 使用终端默认背景
deerflow --continue                           # 恢复最近的 thread
deerflow --resume THREAD                      # 按 id 恢复 thread
deerflow --print "summarize this repo"        # headless 一次性回答输出到 stdout
deerflow --json  "hello"                       # headless 换行分隔的 StreamEvents；失败 -> 一条 {"type": "error"} 记录，退出码 1
deerflow --recursion-limit 250 --print "task" # 覆盖 headless agent-loop 上限
```

当运行失败时，headless 的 `--print` 和 `--json` 会以状态码 `1` 退出，包括以 fallback 消息形式返回的 provider 错误。`--print` 仍会将 fallback 文本写入 stdout；`--json` 会追加一条终止性的 error 记录。
一个键盘驱动的聊天界面，具有流式 transcript（Markdown 渲染的答案）、紧凑的 tool-activity 卡片、`/` 斜杠命令面板、仅显示的 `/clear`、`/goal` 目标管理、`/model` 和 `/threads` 选择器、输入历史、PageUp/PageDown transcript 导航，以及 `Esc` / `Ctrl+C` 中断。composer 会保留粘贴的代码、堆栈跟踪和多段落 prompt 中的换行和缩进；`Enter` 发送完整文档。transcript 刷新会在您向上滚动后保留您的阅读位置，并在您返回底部时恢复跟随新输出。`/clear` 从当前终端显示中移除行，而不删除 thread 或其持久化的对话；`/new` 和 `/clear` 在活跃运行期间会要求您等待，而不是重置进行中的显示状态。在 TUI 中打开的会话也会出现在 Web UI 侧边栏中——它在本地默认用户下写入共享的 thread 存储，因此终端和 Web 保持同步 **而无需运行 Gateway**。

在活跃运行期间，`/resume`、`/threads` 和 `/switch` 会要求您等待，然后再切换对话。无效的 `/resume` 引用会显示错误，而不会关闭 TUI 或更改当前对话。
中断后，前一次运行的延迟流操作无法更改下一次运行的显示或状态，即使两个 prompt 使用相同的对话。
已经进行中的 tool 调用仍会完成，因此在其完成之前，该对话中的新 prompt 会被暂缓并给出通知，而不是与之竞争；`/new` 和 `/resume` 保持可用。
如果运行无法启动，TUI 会报告错误并返回空闲状态，以便您可以重试。

在 composer 的最后一行，`Down` 会保持未发送的草稿不变，除非您正在浏览输入历史；在召回历史后，它会向前移动以恢复您保存的草稿。

在 composer 的第一行，当没有可用的输入历史时，`Up` 也会保持草稿、光标和撤销历史不变。
回忆完全相同的历史文本或已保存的草稿也会保留光标和撤销历史。

完整指南请参见 [backend/docs/TUI.md](backend/docs/TUI.md)。

## 文档

- [贡献指南](CONTRIBUTING.md) - 开发环境搭建与工作流程
- [配置指南](backend/docs/CONFIGURATION.md) - 安装与配置说明
- [架构概览](backend/CLAUDE.md) - 技术架构详情
- [后端架构](backend/README.md) - 后端架构与 API 参考

## ⚠️ 安全须知

### 部署不当可能引入安全风险

DeerFlow 具备关键的高权限能力，包括**系统命令执行、资源操作和业务逻辑调用**，并且默认设计为**部署在本地可信环境中（仅可通过 127.0.0.1 回环接口访问）**。如果你在不可信环境中部署该 agent——例如 LAN 网络、公有云服务器或其他多端点可访问的环境——且未采取严格的安全措施，可能会引入安全风险，包括：

- **未经授权的非法调用**：Agent 功能可能被未授权的第三方或恶意互联网扫描器发现，触发批量未授权请求，执行系统命令和文件读写等高风险操作，可能导致严重的安全后果。
- **合规与法律风险**：如果 agent 被非法调用以进行网络攻击、数据窃取或其他非法活动，可能导致法律责任和合规风险。

### Gateway Admin 等同于代码执行

admin 可以注册 stdio MCP servers，这些 servers 会在 Gateway 容器内运行命令。API 会将它们限制在 allowlist 范围内（默认是 `npx`、`uvx`，可通过 `DEER_FLOW_MCP_STDIO_COMMAND_ALLOWLIST` 扩展），并拒绝会执行任意代码的 arguments 和 environment variables。这是一种防御
深度，不是边界：这些 launchers 的存在是为了获取并运行远程 packages，因此**应将 Gateway admin 视为等同于在 host 上执行代码**，并据此授予权限。

### 外部 Chat Message 角色

Gateway run 请求和手动 thread-state 更新会以 HTTP 400 拒绝客户端提供的 `system` / `developer` messages，包括等效的序列化 message 形式。普通 chat、attachments 以及 assistant/tool 历史重放仍然支持。Session 或 PAT 认证不会授予 system-prompt authority；受信任的内部 run producers 保留该能力。

此检查可防止新的 role injection；它不会重写现有的 checkpoints。如果较旧版本接受了注入的 system message，请使用全新的 thread，或让 operator 审查并清理受影响的状态。重启服务不会移除已持久化的 instructions，而恢复较旧的 checkpoint 可能会将它们恢复。

对于本地验证，运行 `python backend/tests/poc_external_system_message_injection.py --help`。同一个 opt-in PoC 在隔离的旧 revision 上支持 `--expect vulnerable`，在修复后支持 `--expect blocked`。其帮助信息包括 PAT 创建、thread-ID 选择、浏览器 follow-up，以及 persistence 与 model obedience 之间的区别。每次运行都使用一个全新的、一次性的 thread；该测试会追加 messages。

在隔离的未修复 checkout 上，`--expect vulnerable` 仅在请求返回 200，并且精确注入的 message 在一次正常 follow-up 后仍以 `type=system` 保留在 checkpoint 中时，才证明被接受。web 答案中的 marker 取决于 model，其本身并不能证明该 role 被提升。应用修复后，使用 `--expect blocked` 运行同一脚本：它要求特定的 role-rejection 400、未更改的 checkpoint、成功的普通 follow-up，以及被拒绝的 message IDs 不存在。其他 400 响应以及 authentication、conflict 或 server 错误是不确定的，而非通过。
PoC 不会自动清理。验证完成后，使用 web sidebar 的删除操作删除一次性 chat，并在创建了短期 PAT 的情况下撤销该 PAT。重启服务不会移除已持久化的 injected instruction。

### 部署默认值

Docker stack 仅将入口端口发布在 `127.0.0.1` 上，与上文所述的本地可信环境模型一致。要从另一台机器访问它，请在 `.env` 中设置 `BIND_HOST`（例如 `BIND_HOST=0.0.0.0`）——并且只有在落实下述安全措施之后才这样做。

**在主机变为可达之前完成首次运行设置。** 全新的实例尚无任何账户，因此，在启动任何并非仅 loopback 的部署后，立即通过 `/setup` 创建 admin 账户。

### 安全建议

**注意：我们强烈建议在本地可信网络环境中部署 DeerFlow。** 如果你需要跨设备或跨网络部署，则必须实施严格的安全措施，例如：

- **IP 允许列表**：使用 `iptables`，或部署带访问控制列表（ACL）的硬件防火墙/交换机，以**配置 IP 允许列表规则**并拒绝所有其他 IP 地址的访问。
- **认证网关**：配置反向代理（例如 nginx）并**启用强预认证**，阻止任何未经认证的访问。
- **网络隔离**：在可能的情况下，将 agent 和受信任设备置于**同一专用 VLAN** 中，与其他网络设备隔离。
- **保持更新**：持续关注 DeerFlow 的安全功能更新。

## 贡献

我们欢迎贡献！有关开发环境设置、工作流程和指南，请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

后端 `make test` 并发运行四个时长均衡的 shard，并在任一 shard 失败时报告失败。使用 `make test TEST_JOBS=1` 顺序运行各 shard。它不包括实时的外部 API 和阻塞式 I/O 覆盖。
运行 `cd backend && make test-blocking-io` 进行严格的 blocking-I/O 检查。
维护者可以通过 `cd backend && make test-live` 运行真实的 `DeerFlowClient` 测试套件。
该命令需要有效的根 `config.yaml` 和 API 凭据。
它可能产生 API 费用，并创建本地 sandboxes、artifacts 或文件。
直接运行 pytest 还需要 `DEER_FLOW_RUN_LIVE_TESTS=1`。

回归测试覆盖包括 `backend/tests/` 中的 Docker sandbox 模式检测和 provisioner kubeconfig 路径处理测试。
后端 blocking-IO 诊断可从仓库根目录通过
`make detect-blocking-io` 使用：它会静态扫描后端业务代码中可能在后端 event loop 上运行的
blocking IO，打印简洁摘要，
并将完整的 JSON 结果写入 `.deer-flow/blocking-io-findings.json`。
该 JSON 包含精简的审查记录，字段为 `priority`、`location`、
`blocking_call`、`event_loop_exposure`、`reason` 和 `code`。
Gateway artifact 服务现在强制将活跃的 web 内容类型（`text/html` 以及 `.xml`、`.xhtml` 和 `.svg` 等 XML 文档）以附件形式下载，而非内联渲染，从而降低生成的 artifacts 的 XSS 风险。

前端路由资源预算可通过 `cd frontend && pnpm
perf:check` 检查。该命令从常规 production build 中测量 `/login`，然后
为基于 fixture 的 workspace 路由执行 production static-demo build。
它测量代表性路由所引用的唯一 JavaScript 和 CSS，
并将详细结果写入 `.next/performance-results.json`。

## 许可证

本项目为开源项目，基于 [MIT License](./LICENSE) 提供。

## 致谢

DeerFlow 建立在开源社区的卓越工作之上。我们深深感谢所有项目和贡献者，他们的努力使 DeerFlow 成为可能。诚然，我们站在巨人的肩膀上。

我们要向以下项目的宝贵贡献致以诚挚的感谢：

- **[LangChain](https://github.com/langchain-ai/langchain)**：他们卓越的框架为我们的 LLM 交互和链提供支持，实现了无缝集成与功能。
- **[LangGraph](https://github.com/langchain-ai/langgraph)**：他们在 multi-agent 编排方面的创新方法，对实现 DeerFlow 的复杂工作流起到了关键作用。

这些项目体现了开源协作的变革力量，我们为能在其基础之上构建而感到自豪。

### 主要贡献者

衷心感谢 `DeerFlow` 的核心作者，是他们的愿景、热情和奉献让这个项目得以实现：

- **[Daniel Walnut](https://github.com/hetaoBackend/)**
- **[Henry Li](https://github.com/magiccube/)**

你们坚定不移的投入和专业知识，是 DeerFlow 成功的驱动力量。我们很荣幸能由你们引领这段旅程。

## Star 历史

[![Star History Chart](https://star-history.dera.page/svg?repos=bytedance/deer-flow&type=Date)](https://star-history.dera.page/#bytedance/deer-flow&Date)
