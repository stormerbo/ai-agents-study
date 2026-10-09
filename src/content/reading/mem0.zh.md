<p align="center">
  <a href="https://github.com/mem0ai/mem0">
    <img src="docs/images/banner-sm.png" width="800px" alt="Mem0 - 面向个性化 AI 的记忆层">
  </a>
</p>
<p align="center" style="display: flex; justify-content: center; gap: 20px; align-items: center;">
  <a href="https://trendshift.io/repositories/11194" target="blank">
    <img src="https://trendshift.io/api/badge/repositories/11194" alt="mem0ai%2Fmem0 | Trendshift" width="250" height="55"/>
  </a>
</p>

<p align="center">
  <a href="https://mem0.ai">了解更多</a>
  ·
  <a href="https://mem0.dev/DiG">加入 Discord</a>
  ·
  <a href="https://mem0.dev/demo">Demo</a>
</p>

<p align="center">
  <a href="https://mem0.dev/DiG">
    <img src="https://img.shields.io/badge/Discord-%235865F2.svg?&logo=discord&logoColor=white" alt="Mem0 Discord">
  </a>
  <a href="https://pepy.tech/project/mem0ai">
    <img src="https://img.shields.io/pypi/dm/mem0ai" alt="Mem0 PyPI - 下载量">
  </a>
  <a href="https://github.com/mem0ai/mem0">
    <img src="https://img.shields.io/github/commit-activity/m/mem0ai/mem0?style=flat-square" alt="GitHub commit 活动">
  </a>
  <a href="https://pypi.org/project/mem0ai" target="blank">
    <img src="https://img.shields.io/pypi/v/mem0ai?color=%2334D058&label=pypi%20package" alt="包版本">
  </a>
  <a href="https://www.npmjs.com/package/mem0ai" target="blank">
    <img src="https://img.shields.io/npm/v/mem0ai" alt="Npm 包">
  </a>
  <a href="https://www.ycombinator.com/companies/mem0">
    <img src="https://img.shields.io/badge/Y%20Combinator-S24-orange?style=flat-square" alt="Y Combinator S24">
  </a>
</p>

<p align="center">
  <a href="https://mem0.ai/research"><strong>📄 对 Mem0 的 token 高效记忆算法进行基准测试 →</strong></a>
</p>

## 新的记忆算法（2026 年 4 月）

| Benchmark       | 旧版 | 新版     | Tokens | Latency p50 |
| --------------- | ---- | -------- | ------ | ----------- |
| **LoCoMo**      | 71.4 | **92.5** | 7.0K   | 0.88s       |
| **LongMemEval** | 67.8 | **94.4** | 6.8K   | 1.09s       |
| **BEAM (1M)**   | —    | **64.1** | 6.7K   | 1.00s       |
| **BEAM (10M)**  | —    | **48.6** | 6.9K   | 1.05s       |

所有 benchmark 均运行在同一个具备生产代表性的 model stack 上。在 top_200 检索预算下进行单轮检索（一次调用，无 agentic 循环）。得分反映的是 Mem0 的托管平台，其中包含开源 SDK 中不具备的专有优化；开源用户应预期获得方向相似的提升，但数值不会完全相同。

**变更内容：**

- **单轮仅 ADD 抽取** —— 一次 LLM 调用，不进行 UPDATE/DELETE。记忆不断累积；不会覆盖任何内容。
- **Agent 生成的事实是一等公民** —— 当 agent 确认某个动作时，该信息现在会以同等权重存储。
- **实体链接** —— 实体被抽取、embedding，并跨记忆链接以提升检索效果。
- **多信号检索** —— 语义、BM25 关键词和实体匹配并行打分并融合。
- **时间推理** —— 时间感知检索，针对关于当前状态、过去事件和即将到来的计划的查询，对正确的带日期实例进行排序。

升级说明请参阅 [migration guide](https://docs.mem0.ai/migration/oss-v2-to-v3)。[evaluation framework](https://github.com/mem0ai/memory-benchmarks) 已开源，任何人都可以复现这些数字。

## 研究亮点

- **LoCoMo 上 92.5** —— 相比之前的算法 +21 分
- **LongMemEval 上 94.4** —— +27 分，其中 assistant memory recall 为 98.2
- **BEAM (1M) 上 64.1** —— 在 1M tokens 规模上的生产级记忆评测
- [阅读完整论文](https://mem0.ai/research)

# 简介

[Mem0](https://mem0.ai)（“mem-zero”）通过智能记忆层增强 AI assistants 和 agents，实现个性化的 AI 交互。它能记住用户偏好、适应个人需求，并随着时间不断学习——非常适合客户支持 chatbots、AI assistants 和自主系统。

### 主要特性与使用场景

**核心能力：**

- **多层级记忆**：无缝保留 User、Session 和 Agent 状态，并具备自适应个性化能力
- **对开发者友好**：直观的 API、跨平台 SDK，以及全托管的服务选项

**应用场景：**

- **AI Assistants**：一致、上下文丰富的对话
- **Customer Support**：回忆历史工单与用户历史记录，以提供量身定制的帮助
- **Healthcare**：追踪患者偏好与病史，以实现个性化护理
- **Productivity & Gaming**：基于用户行为的自适应工作流与环境

## 🚀 快速开始指南 <a name="quickstart"></a>

### 以 agent 身份注册

AI agents 可以在五秒内生成一个可用的 Mem0 API key —— 无需邮箱、无需 dashboard、无需 OTP。四条命令完成全流程：

```bash
# 1. Install
npm install -g @mem0/cli      # or: pip install mem0-cli

# 2. Sign up as an agent (replace `claude-code` with your name)
mem0 init --agent --agent-caller claude-code

# 3. Add a memory
mem0 add "I am using mem0"

# 4. Search
mem0 search "am I using mem0"
```

人类所有者之后可以用 `mem0 init --email <their-email>` 认领该账户 —— 同一个 key，记忆保持不变。完整指南：[以 agent 身份注册](https://docs.mem0.ai/platform/agent-signup)。

|                     | Library              | Self-Hosted Server                           | Cloud Platform                                                              |
| ------------------- | -------------------- | -------------------------------------------- | --------------------------------------------------------------------------- |
| **最适合**          | 测试、原型开发       | 在自有基础设施上运行的团队                   | 零运维的生产使用                                                            |
| **安装配置**        | `pip install mem0ai` | `docker compose up`                          | 在 [app.mem0.ai](https://app.mem0.ai?utm_source=oss&utm_medium=readme) 注册 |
| **Dashboard**       | --                   | [是](https://docs.mem0.ai/open-source/setup) | 是                                                                          |
| **Auth & API Keys** | --                   | 是                                           | 是                                                                          |
| **高级功能**        | --                   | 预览                                         | 全部包含                                                                    |

只是测试？使用 library。为团队构建？使用 self-hosted。想要零运维？使用 Cloud。

### Library（pip / npm）

```bash
pip install mem0ai
```

为了增强混合搜索能力，支持 BM25 关键词匹配和实体提取，请安装 NLP 支持：

```bash
pip install mem0ai[nlp]
python -m spacy download en_core_web_sm
```

通过 npm 安装 sdk：

```bash
npm install mem0ai
```

### 自托管服务器

> **注意：** 自托管 auth 默认开启。从 pre-auth 版本升级？设置 `ADMIN_API_KEY`，通过向导注册一个 admin，或仅本地开发时设置 `AUTH_DISABLED=true`。参见[升级说明](https://docs.mem0.ai/open-source/setup#upgrade-notes)。

```bash
# 推荐：一条命令——启动 stack、创建 admin、签发首个 API key。
cd server && make bootstrap

# 手动：启动 stack，并通过浏览器向导完成设置。
cd server && docker compose up -d    # http://localhost:3000
```

配置请参见[自托管文档](https://docs.mem0.ai/open-source/overview)。

### Cloud Platform

1. 在 [Mem0 Platform](https://app.mem0.ai?utm_source=oss&utm_medium=readme) 上注册
2. 通过 SDK 或 API keys 嵌入 memory layer
3. 使用托管的 Qdrant vectors？参见[Platform 迁移指南](https://docs.mem0.ai/migration/oss-to-platform)，将其导入 Mem0 Platform。

### CLI

从终端管理 memories：

```bash
npm install -g @mem0/cli   # or: pip install mem0-cli

mem0 init
mem0 add "Prefers dark mode and vim keybindings" --user-id alice
mem0 search "What does Alice prefer?" --user-id alice
```

完整命令参考请参见 [CLI 文档](https://docs.mem0.ai/platform/cli)。

### Agent Skills

教会你的 AI coding assistant（Claude Code、Codex、Cursor、Windsurf、OpenCode、OpenClaw，以及任何支持 skills 标准的工具）如何基于 Mem0 构建。分为两类：

**Reference skills — 始终开启**（SDK 知识加载到 assistant 的上下文中）：

```bash
npx skills add https://github.com/mem0ai/mem0 --skill mem0
npx skills add https://github.com/mem0ai/mem0 --skill mem0-cli
npx skills add https://github.com/mem0ai/mem0 --skill mem0-vercel-ai-sdk
```

**Pipeline skills — 按需运行**（在现有 repo 中执行端到端工作流）：

```bash
npx skills add https://github.com/mem0ai/mem0 --skill mem0-integrate
npx skills add https://github.com/mem0ai/mem0 --skill mem0-test-integration
npx skills add https://github.com/mem0ai/mem0 --skill mem0-oss-to-platform
```

使用 `/mem0-integrate` 通过测试优先的 pipeline 将 Mem0 接入现有 repo，然后用 `/mem0-test-integration` 进行验证。使用 `/mem0-oss-to-platform` 将现有项目从 Mem0 OSS 迁移到托管的 Platform SDK。完整概况参见 [skills catalog](./skills/) 或 [Vibecoding with Mem0](https://docs.mem0.ai/vibecoding)。

### 基本用法

Mem0 需要 LLM 才能运行，默认使用 OpenAI 的 `gpt-5-mini`。不过，它支持多种 LLM；详情请参阅我们的 [Supported LLMs documentation](https://docs.mem0.ai/components/llms/overview)。

Mem0 默认使用 OpenAI 的 `text-embedding-3-small` 作为 embedding model。为获得混合搜索（semantic + keyword + entity boosting）的最佳效果，我们建议至少使用 [Qwen 600M](https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct) 或同等级的 embedding model。配置详情参见 [Supported Embeddings](https://docs.mem0.ai/components/embedders/overview)。

第一步是实例化 memory：

```python
from openai import OpenAI
from mem0 import Memory

openai_client = OpenAI()
memory = Memory()

def chat_with_memories(message: str, user_id: str = "default_user") -> str:
    # Retrieve relevant memories
    relevant_memories = memory.search(query=message, filters={"user_id": user_id}, top_k=3)
    memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])

    # Generate Assistant response
    system_prompt = f"You are a helpful AI. Answer the question based on query and memories.\nUser Memories:\n{memories_str}"
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    response = openai_client.chat.completions.create(model="gpt-5-mini", messages=messages)
    assistant_response = response.choices[0].message.content

    # 从对话中创建新的 memories
    messages.append({"role": "assistant", "content": assistant_response})
    memory.add(messages, user_id=user_id)

    return assistant_response

def main():
    print("Chat with AI (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        print(f"AI: {chat_with_memories(user_input)}")

if __name__ == "__main__":
    main()
```

详细的集成步骤，请参见 [Quickstart](https://docs.mem0.ai/quickstart) 和 [API Reference](https://docs.mem0.ai/api-reference)。

## 🔗 集成与 Demo

- **ChatGPT with Memory**：由 Mem0 驱动的个性化聊天（[Live Demo](https://mem0.dev/demo)）
- **Browser Extension**：在 ChatGPT、Perplexity 和 Claude 之间存储 memories（[Chrome Extension](https://chromewebstore.google.com/detail/onihkkbipkfeijkadecaafbgagkhglop?utm_source=item-share-cb)）
- **Langgraph Support**：用 Langgraph + Mem0 构建客服 bot（[Guide](https://docs.mem0.ai/integrations/langgraph)）
- **CrewAI Integration**：用 Mem0 定制 CrewAI 的输出（[Example](https://docs.mem0.ai/integrations/crewai)）

## 📚 文档与支持

- 完整文档：https://docs.mem0.ai
- 社区：[Discord](https://mem0.dev/DiG) · [X（原 Twitter）](https://x.com/mem0ai)
- 联系方式：founders@mem0.ai

## Citation

我们现在有一篇可供引用的论文：

```bibtex
@article{mem0,
  title={Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory},
  author={Chhikara, Prateek and Khant, Dev and Aryan, Saket and Singh, Taranjeet and Yadav, Deshraj},
  journal={arXiv preprint arXiv:2504.19413},
  year={2025}
}
```

## ⚖️ License

Apache 2.0 — 详情请参阅 [LICENSE](https://github.com/mem0ai/mem0/blob/main/LICENSE) 文件。
