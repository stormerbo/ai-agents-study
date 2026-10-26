# 🔬 Open Deep Research

<img width="1388" height="298" alt="full_diagram" src="https://github.com/user-attachments/assets/12a2371b-8be2-4219-9b48-90503eb43c69" />

Deep research 已成为最受欢迎的 agent 应用之一。这是一个简单、可配置、完全开源的 deep research agent，可跨多个模型提供商、搜索工具和 MCP server 工作。其性能与许多流行的 deep research agent 相当（[参见 Deep Research Bench leaderboard](https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard)）。

<img width="817" height="666" alt="Screenshot 2025-07-13 at 11 21 12 PM" src="https://github.com/user-attachments/assets/052f2ed3-c664-4a4f-8ec2-074349dcaa3f" />

### 🔥 最近更新

**2025 年 8 月 14 日**：查看我们的免费课程[此处](https://academy.langchain.com/courses/deep-research-with-langgraph)（以及课程仓库[此处](https://github.com/langchain-ai/deep_research_from_scratch)），了解如何构建 open deep research。

**2025 年 8 月 7 日**：新增 GPT-5，并更新了 Deep Research Bench 评估，加入 GPT-5 结果。

**2025 年 8 月 2 日**：在 [Deep Research Bench Leaderboard](https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard) 上取得第 6 名，总体得分为 0.4344。

**2025 年 7 月 30 日**：在我们的[博客文章](https://rlancemartin.github.io/2025/07/30/bitter_lesson/)中阅读从我们最初的实现到当前版本的演变过程。

**2025 年 7 月 16 日**：在我们的[博客](https://blog.langchain.com/open-deep-research/)中阅读更多内容，并观看我们的[视频](https://www.youtube.com/watch?v=agGiWUpxkhg)以快速了解概况。

### 🚀 快速开始

1. 克隆仓库并激活虚拟环境：

```bash
git clone https://github.com/langchain-ai/open_deep_research.git
cd open_deep_research
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. 安装依赖：

```bash
uv sync
# or
uv pip install -r pyproject.toml
```

3. 设置你的 `.env` 文件以自定义环境变量（用于模型选择、搜索工具和其他配置设置）：

```bash
cp .env.example .env
```

4. 在本地使用 LangGraph 服务器启动 agent：

```bash
# 安装依赖并启动 LangGraph 服务器
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
```

这将在你的浏览器中打开 LangGraph Studio UI。

```
- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs
```

在 `messages` 输入字段中提问，然后点击 `Submit`。在 "Manage Assistants" 选项卡中选择不同的配置。

### ⚙️ 配置

#### LLM :brain:

Open Deep Research 通过 [init_chat_model() API](https://python.langchain.com/docs/how_to/chat_models_universal_init/) 支持广泛的 LLM 提供商。它将 LLM 用于几个不同的任务。在 [configuration.py](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/configuration.py) 文件中查看下面的模型字段以了解更多详情。这可以通过 LangGraph Studio UI 访问。

- **Summarization** (默认: `openai:gpt-4.1-mini`): 总结搜索 API 结果
- **Research** (默认: `openai:gpt-4.1`): 为搜索 agent 提供支持
- **Compression** (默认: `openai:gpt-4.1`): 压缩研究结果
- **Final Report Model** (默认: `openai:gpt-4.1`): 撰写最终报告

> 注意：所选模型需要支持 [structured outputs](https://python.langchain.com/docs/integrations/chat/) 和 [tool calling](https://python.langchain.com/docs/how_to/tool_calling/)。

> 注意：对于 OpenRouter：遵循 [此指南](https://github.com/langchain-ai/open_deep_research/issues/75#issuecomment-2811472408)，对于通过 Ollama 使用的本地模型，参见 [设置说明](https://github.com/langchain-ai/open_deep_research/issues/65#issuecomment-2743586318)。

#### Search API :mag:

Open Deep Research 支持多种搜索工具。默认情况下，它使用 [Tavily](https://www.tavily.com/) 搜索 API。它完全兼容 MCP，并为 Anthropic 和 OpenAI 原生支持原生网页搜索。更多细节请参见 [configuration.py](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/configuration.py) 文件中的 `search_api` 和 `mcp_config` 字段。可以通过 LangGraph Studio UI 访问。

#### 其他

有关用于自定义 Open Deep Research 行为的各种其他设置，请参见 [configuration.py](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/configuration.py) 中的字段。

### 📊 评估

Open Deep Research 配置为使用 [Deep Research Bench](https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard) 进行评估。该 benchmark 包含 100 个博士级研究任务（50 个英文、50 个中文），由 22 个领域（例如科学与技术、商业与金融）的领域专家精心设计，以反映现实世界中的深度研究需求。它有 2 个评估指标，但排行榜基于 RACE 分数。它使用 LLM-as-a-judge（Gemini），依据专家汇编的 golden set 报告，按照一组指标来评估研究报告。

#### 用法

> 警告：跑完这 100 个示例的成本约为 $20-$100，具体取决于所选择的模型。

该数据集可通过[此链接在 LangSmith 上](https://smith.langchain.com/public/c5e7a6ad-fdba-478c-88e6-3a388459ce8b/d)获取。要启动评估，请运行以下命令：

```bash
# Run comprehensive evaluation on LangSmith datasets
python tests/run_evaluate.py
```

这将提供一个指向 LangSmith experiment 的链接，其名称为 `YOUR_EXPERIMENT_NAME`。完成后，将结果提取到一个 JSONL 文件中，该文件可以提交给 Deep Research Bench。

```bash
python tests/extract_langsmith_data.py --project-name "YOUR_EXPERIMENT_NAME" --model-name "you-model-name" --dataset-name "deep_research_bench"
```

这会生成符合所需格式的 `tests/expt_results/deep_research_bench_model-name.jsonl`。将生成的 JSONL 文件移动到 Deep Research Bench 仓库的本地克隆中，并按照他们的 [Quick Start guide](https://github.com/Ayanami0730/deep_research_bench?tab=readme-ov-file#quick-start) 提交评估。

#### 结果

| Name                           | Commit                                                                                                                  | Summarization       | Research                           | Compression    | Total Cost | Total Tokens | RACE Score | Experiment                                                                                                                                                                                                |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------------------------- | -------------- | ---------- | ------------ | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GPT-5                          | [ca3951d](https://github.com/langchain-ai/open_deep_research/pull/168/commits)                                          | openai:gpt-4.1-mini | openai:gpt-5                       | openai:gpt-4.1 |            | 204,640,896  | 0.4943     | [Link](https://smith.langchain.com/o/ebbaf2eb-769b-4505-aca2-d11de10372a4/datasets/6e4766ca-613c-4bda-8bde-f64f0422bbf3/compare?selectedSessions=4d5941c8-69ce-4f3d-8b3e-e3c99dfbd4cc&baseline=undefined) |
| Defaults                       | [6532a41](https://github.com/langchain-ai/open_deep_research/commit/6532a4176a93cc9bb2102b3d825dcefa560c85d9)           | openai:gpt-4.1-mini | openai:gpt-4.1                     | openai:gpt-4.1 | $45.98     | 58,015,332   | 0.4309     | [Link](https://smith.langchain.com/o/ebbaf2eb-769b-4505-aca2-d11de10372a4/datasets/6e4766ca-6[…]ons=cf4355d7-6347-47e2-a774-484f290e79bc&baseline=undefined)                                              |
| Claude Sonnet 4                | [f877ea9](https://github.com/langchain-ai/open_deep_research/pull/163/commits/f877ea93641680879c420ea991e998b47aab9bcc) | openai:gpt-4.1-mini | anthropic:claude-sonnet-4-20250514 | openai:gpt-4.1 | $187.09    | 138,917,050  | 0.4401     | [Link](https://smith.langchain.com/o/ebbaf2eb-769b-4505-aca2-d11de10372a4/datasets/6e4766ca-6[…]ons=04f6002d-6080-4759-bcf5-9a52e57449ea&baseline=undefined)                                              |
| Deep Research Bench Submission | [c0a160b](https://github.com/langchain-ai/open_deep_research/commit/c0a160b57a9b5ecd4b8217c3811a14d8eff97f72)           | openai:gpt-4.1-nano | openai:gpt-4.1                     | openai:gpt-4.1 | $87.83     | 207,005,549  | 0.4344     | [Link](https://smith.langchain.com/o/ebbaf2eb-769b-4505-aca2-d11de10372a4/datasets/6e4766ca-6[…]ons=e6647f74-ad2f-4cb9-887e-acb38b5f73c0&baseline=undefined)                                              |

### 🚀 部署与使用

#### LangGraph Studio

按照[快速开始](#-quickstart)在本地启动 LangGraph server，并在 LangGraph Studio 中测试该 agent。

#### 托管部署

你可以轻松部署到 [LangGraph Platform](https://docs.langchain.com/langsmith/deployments)。

#### Open Agent Platform

Open Agent Platform (OAP) 是一个 UI，非技术用户可以通过它构建和配置自己的 agents。OAP 非常适合让用户用不同的 MCP tools 和 search APIs 来配置 Deep Researcher，以最适合他们的需求以及他们想要解决的问题。

我们已将 Open Deep Research 部署到 OAP 的公共演示实例。你只需添加自己的 API Keys，就可以亲自测试 Deep Researcher！在[这里](https://oap.langchain.com)试试看

你也可以部署自己的 OAP 实例，并将自己定制的 agents（如 Deep Researcher）提供给用户使用。

1. [部署 Open Agent Platform](https://docs.oap.langchain.com/quickstart)
2. [将 Deep Researcher 添加到 OAP](https://docs.oap.langchain.com/setup/agents)

### 旧版实现 🏛️

`src/legacy/` 文件夹包含两个更早的实现，它们提供了自动化研究的替代方法。它们的性能不如当前实现，但提供了理解深度研究不同方法的替代思路。

#### 1. 工作流实现（`legacy/graph.py`）

- **Plan-and-Execute**：结构化工作流，带有 human-in-the-loop 规划
- **顺序处理**：通过反思逐个创建章节
- **交互式控制**：允许对报告计划进行反馈与批准
- **注重质量**：通过迭代式改进强调准确性

#### 2. Multi-Agent 实现（`legacy/multi_agent.py`）

- **Supervisor-Researcher 架构**：协同的多 agent 系统
- **并行处理**：多个 researcher 同时工作
- **速度优化**：通过并发实现更快的报告生成
- **MCP 支持**：广泛的 Model Context Protocol 集成
