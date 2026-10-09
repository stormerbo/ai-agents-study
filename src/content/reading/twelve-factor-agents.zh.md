# 12-Factor Agents - 构建可靠 LLM 应用的原则

<div align="center">
<a href="https://www.apache.org/licenses/LICENSE-2.0">
        <img src="https://img.shields.io/badge/Code-Apache%202.0-blue.svg" alt="Code License: Apache 2.0"></a>
<a href="https://creativecommons.org/licenses/by-sa/4.0/">
        <img src="https://img.shields.io/badge/Content-CC%20BY--SA%204.0-lightgrey.svg" alt="Content License: CC BY-SA 4.0"></a>
<a href="https://humanlayer.dev/discord">
    <img src="https://img.shields.io/badge/chat-discord-5865F2" alt="Discord Server"></a>
<a href="https://www.youtube.com/watch?v=8kMaTybvDUw">
    <img src="https://img.shields.io/badge/aidotengineer-conf_talk_(17m)-white" alt="YouTube
Deep Dive"></a>
<a href="https://www.youtube.com/watch?v=yxJDyQ8v6P0">
    <img src="https://img.shields.io/badge/youtube-deep_dive-crimson" alt="YouTube
Deep Dive"></a>

</div>

<p></p>

_本着 [12 Factor Apps](https://12factor.net/) 的精神_。_本项目的源码公开在 https://github.com/humanlayer/12-factor-agents，我欢迎你的反馈与贡献。让我们一起把它搞清楚！_

> [!TIP]
> 错过了 AI Engineer World's Fair？[在这里看这场演讲](https://www.youtube.com/watch?v=8kMaTybvDUw)
>
> 在找 Context Engineering？[直接跳到 factor 3](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)
>
> 想为 `npx/uvx create-12-factor-agent` 做贡献 —— 看看[这个讨论帖](https://github.com/humanlayer/12-factor-agents/discussions/61)

<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=2acad99a-c2d9-48df-86f5-9ca8061b7bf9" />

<a href="#visual-nav"><img width="907" alt="Screenshot 2025-04-03 at 2 49 07 PM" src="https://github.com/user-attachments/assets/23286ad8-7bef-4902-b371-88ff6a22e998" /></a>
大家好，我是 Dex。我在 [AI agents](https://theouterloop.substack.com) 上 [hacking](https://youtu.be/8bIHcttkOTE) 已经 [有一段时间了](https://humanlayer.dev)。

**我尝试过市面上所有的 agent 框架**，从即插即用的 crew/langchains，到世界上那些“极简主义”的 smolagents，再到“生产级”的 langraph、griptape 等等。

**我和很多非常强的创始人聊过**，有 YC 内也有 YC 外的，他们都在用 AI 构建非常令人印象深刻的东西。他们中的大多数人都是自己搭建整套技术栈。我在面向客户的生产级 agent 中很少看到框架的身影。

**我很惊讶地发现**，市面上大多数标榜自己是“AI Agents”的产品，其实并没有那么 agentic。它们中的很多主要是确定性代码，只是在恰到好处的位置点缀了一些 LLM 步骤，从而让体验真正变得神奇。

Agents，至少是好的 agents，并不遵循 [“这是你的 prompt，这是一袋工具，循环直到达成目标”](https://www.anthropic.com/engineering/building-effective-agents#agents) 这种模式。相反，它们主要由软件构成。

所以，我开始尝试回答：

> ### **我们可以用哪些原则来构建由 LLM 驱动的软件，使其真正好到足以交到生产客户手中？**

欢迎来到 12-factor agents。正如自 Daley 以来每一任芝加哥市长都持续在这座城市的主要机场到处张贴的那样，我们很高兴你来到这里。

_特别感谢 [@iantbutler01](https://github.com/iantbutler01)、[@tnm](https://github.com/tnm)、[@hellovai](https://www.github.com/hellovai)、[@stantonk](https://www.github.com/stantonk)、[@balanceiskey](https://www.github.com/balanceiskey)、[@AdjectiveAllison](https://www.github.com/AdjectiveAllison)、[@pfbyjy](https://www.github.com/pfbyjy)、[@a-churchill](https://www.github.com/a-churchill)，以及 SF MLOps 社区对本指南的早期反馈。_

## 简版：12 个因素

即使 LLM [继续以指数级变得更强大](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md#what-if-llms-get-smarter)，仍会有一些核心工程技术，使 LLM 驱动的软件更可靠、更可扩展、更易于维护。

- [我们是如何走到这里的：软件简史](https://github.com/humanlayer/12-factor-agents/blob/main/content/brief-history-of-software.md)
- [Factor 1：从自然语言到 tool calls](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-01-natural-language-to-tool-calls.md)
- [Factor 2：拥有你的 prompts](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-02-own-your-prompts.md)
- [Factor 3：拥有你的 context window](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)
- [Factor 4：tools 只是结构化输出](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-04-tools-are-structured-outputs.md)
- [Factor 5：统一执行状态与业务状态](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-05-unify-execution-state.md)
- [Factor 6：用简单的 APIs 实现启动/暂停/恢复](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-06-launch-pause-resume.md)
- [Factor 7：通过 tool calls 联系人类](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-07-contact-humans-with-tools.md)
- [Factor 8：拥有你的 control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md)
- [Factor 9：将错误压缩进 context window](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-09-compact-errors.md)
- [Factor 10：小型、专注的 agents](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md)
- [要素 11：从任何地方触发，在用户所在之处与其相遇](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-11-trigger-from-anywhere.md)
- [要素 12：让你的 agent 成为无状态 reducer](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-12-stateless-reducer.md)

### 可视化导航

|                                                                                                                                                                                                                                   |                                                                                                                                                                                                                 |                                                                                                                                                                                                                      |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [![factor 1](https://github.com/humanlayer/12-factor-agents/blob/main/img/110-natural-language-tool-calls.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-01-natural-language-to-tool-calls.md)     | [![factor 2](https://github.com/humanlayer/12-factor-agents/blob/main/img/120-own-your-prompts.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-02-own-your-prompts.md)            | [![factor 3](https://github.com/humanlayer/12-factor-agents/blob/main/img/130-own-your-context-building.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md) |
| [![factor 4](https://github.com/humanlayer/12-factor-agents/blob/main/img/140-tools-are-just-structured-outputs.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-04-tools-are-structured-outputs.md) | [![factor 5](https://github.com/humanlayer/12-factor-agents/blob/main/img/150-unify-state.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-05-unify-execution-state.md)            | [![factor 6](https://github.com/humanlayer/12-factor-agents/blob/main/img/160-pause-resume-with-simple-apis.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-06-launch-pause-resume.md) |
| [![factor 7](https://github.com/humanlayer/12-factor-agents/blob/main/img/170-contact-humans-with-tools.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-07-contact-humans-with-tools.md)            | [![factor 8](https://github.com/humanlayer/12-factor-agents/blob/main/img/180-control-flow.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md)           | [![factor 9](https://github.com/humanlayer/12-factor-agents/blob/main/img/190-factor-9-errors-static.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-09-compact-errors.md)             |
| [![factor 10](https://github.com/humanlayer/12-factor-agents/blob/main/img/1a0-small-focused-agents.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md)                     | [![factor 11](https://github.com/humanlayer/12-factor-agents/blob/main/img/1b0-trigger-from-anywhere.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-11-trigger-from-anywhere.md) | [![factor 12](https://github.com/humanlayer/12-factor-agents/blob/main/img/1c0-stateless-reducer.png)](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-12-stateless-reducer.md)              |

## 我们是如何走到这一步的

关于我的 agent 之旅以及是什么引导我们走到这一步的更深入探讨，请查看 [A Brief History of Software](https://github.com/humanlayer/12-factor-agents/blob/main/content/brief-history-of-software.md) —— 这里是一个快速总结：

### agent 的承诺

我们将大量讨论 Directed Graphs（DGs）以及它们的无环朋友，DAGs。我首先要指出的是……嗯……软件就是一个 directed graph。我们过去用流程图来表示程序是有原因的。

![010-software-dag](https://github.com/humanlayer/12-factor-agents/blob/main/img/010-software-dag.png)

### 从代码到 DAGs

大约 20 年前，我们开始看到 DAG 编排器变得流行。我们说的是 [Airflow](https://airflow.apache.org/)、[Prefect](https://www.prefect.io/) 这样的经典之作，以及一些前辈，还有一些更新的，比如 [dagster](https://dagster.io/)、[inggest](https://www.inngest.com/)、[windmill](https://www.windmill.dev/)。它们遵循相同的图模式，并额外带来了可观测性、模块化、重试、管理等好处。

![015-dag-orchestrators](https://github.com/humanlayer/12-factor-agents/blob/main/img/015-dag-orchestrators.png)

### Agents 的承诺

我不是[第一个这么说的人](https://youtu.be/Dc99-zTMyMg?si=bcT0hIwWij2mR-40&t=73)，但当我开始学习 agents 时，我最大的收获是：你可以把 DAG 扔掉了。不必由软件工程师编写每一步和每种边界情况，你可以给 agent 一个目标和一组转换：

![025-agent-dag](https://github.com/humanlayer/12-factor-agents/blob/main/img/025-agent-dag.png)

然后让 LLM 实时做出决策，找出路径

![026-agent-dag-lines](https://github.com/humanlayer/12-factor-agents/blob/main/img/026-agent-dag-lines.png)

这里的承诺是：你写更少的软件，只需把图的“边”交给 LLM，让它自己弄清楚节点。你可以从错误中恢复，可以写更少的代码，而且你可能会发现 LLM 能找到新颖的问题解决方案。

### Agents 即循环

正如我们稍后会看到的，事实证明这并不太可行。

让我们再深入一步——使用 agents 时，你会有这样一个由 3 个步骤组成的循环：

1. LLM 确定工作流中的下一步，输出结构化 json（“tool calling”）
2. 确定性代码执行 tool call
3. 结果被追加到上下文窗口
4. 重复，直到确定下一步是“完成”

````python
initial_event = {"message": "..."}
context = [initial_event]
while True:
  next_step = await llm.determine_next_step(context)
```python
  context.append(next_step)

  if (next_step.intent === "done"):
    return next_step.final_answer

  result = await execute_step(next_step)
  context.append(result)
````

我们初始的 context 只是起始事件（可能是用户消息，可能是 cron 触发，可能是 webhook 等等），然后我们让 llm 选择下一步（tool），或者判断我们已经完成了。

下面是一个多步骤的示例：

[![027-agent-loop-animation](https://github.com/humanlayer/12-factor-agents/blob/main/img/027-agent-loop-animation.gif)](https://github.com/user-attachments/assets/3beb0966-fdb1-4c12-a47f-ed4e8240f8fd)

<details>
<summary><a href="https://github.com/humanlayer/12-factor-agents/blob/main/img/027-agent-loop-animation.gif">GIF 版本</a></summary>

![027-agent-loop-animation](https://github.com/humanlayer/12-factor-agents/blob/main/img/027-agent-loop-animation.gif)

</details>

## 为什么是 12-factor agents？

归根结底，这种方法的效果并没有我们期望的那么好。

在构建 HumanLayer 的过程中，我至少与 100 位 SaaS 构建者（大多是技术创始人）交流过，他们都希望让自己的现有产品更具 agentic 能力。这个过程通常是这样：

1. 决定要构建一个 agent
2. 产品设计、UX 映射、要解决哪些问题
3. 想要快速推进，于是抓来 $FRAMEWORK 然后*开始构建*
4. 达到 70-80% 的质量标准
5. 意识到 80% 对于大多数面向客户的功能来说还不够好
6. 意识到要突破 80% 就需要对 framework、prompts、flow 等进行逆向工程
7. 从头开始重来

<details>
<summary>一些随机的免责声明</summary>

**免责声明**：我不确定这句话到底该放在哪里才合适，但这里似乎和其他地方一样合适：**这绝不是为了贬低现有的众多 framework，也不是为了贬低那些为它们工作的非常聪明的人**。它们实现了不可思议的事情，并加速了 AI 生态系统的发展。
</details>
我希望这篇文章的一个成果是，agent 框架的构建者能够从我和他人的历程中学习，把框架做得更好。

尤其是对于那些想要快速推进但需要深度控制的构建者。

**免责声明 2**：我不打算讨论 MCP。我相信你能看出它适合放在哪里。

**免责声明 3**：我主要使用 typescript，出于[某些原因](https://www.linkedin.com/posts/dexterihorthy_llms-typescript-aiagents-activity-7290858296679313408-Lh9e?utm_source=share&utm_medium=member_desktop&rcm=ACoAAA4oHTkByAiD-wZjnGsMBUL_JT6nyyhOh30)，但所有这些内容在 python 或你喜欢的任何其他语言中都能用。

总之，回到正题……

</details>

### 构建出色 LLM 应用的设计模式

在翻遍了数百个 AI 库并与数十位创始人合作之后，我的直觉是这样的：

1. 有一些核心要素能让 agent 变得出色
2. 全力投入一个框架并构建本质上相当于推倒重来的东西，可能会适得其反
3. 有一些核心原则能让 agent 变得出色，只要你引入一个框架，就能获得其中大部分甚至全部
4. 但是，我见过的构建者最快把高质量 AI 软件交到客户手中的方式，是从 agent 构建中提取小型、模块化的概念，并将它们融入现有产品
5. 这些来自 agent 的模块化概念，大多数熟练的软件工程师都能定义和应用，即使他们没有 AI 背景

> #### 我见过的构建者最快把优秀 AI 软件交到客户手中的方式，是从 agent 构建中提取小型、模块化的概念，并将它们融入现有产品

## 12 个要素（再次讨论）

- [我们如何走到这里：软件简史](https://github.com/humanlayer/12-factor-agents/blob/main/content/brief-history-of-software.md)
- [要素 1：从自然语言到 Tool Calls](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-01-natural-language-to-tool-calls.md)
- [要素 2：拥有你自己的 prompts](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-02-own-your-prompts.md)
- [要素 3：拥有你自己的 context window](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)
- [要素 4：Tools 只是结构化输出](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-04-tools-are-structured-outputs.md)
- [要素 5：统一 execution state 与 business state](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-05-unify-execution-state.md)
- [要素 6：用简单的 APIs 实现 Launch/Pause/Resume](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-06-launch-pause-resume.md)
- [要素 7：用 tool calls 与人联系](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-07-contact-humans-with-tools.md)
- [要素 8：拥有你自己的 control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md)
- [要素 9：将 Errors 压缩进 Context Window](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-09-compact-errors.md)
- [要素 10：小而专注的 Agents](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md)
- [要素 11：从任何地方触发，在用户所在之处与其会合](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-11-trigger-from-anywhere.md)
- [要素 12：让你的 agent 成为无状态 reducer](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-12-stateless-reducer.md)

## 荣誉提名 / 其他建议

- [要素 13：预先获取你可能需要的所有 context](https://github.com/humanlayer/12-factor-agents/blob/main/content/appendix-13-pre-fetch.md)

## 相关资源

- 在[这里](https://github.com/humanlayer/12-factor-agents)为这份指南做贡献
- 我在2025年3月的[Tool Use podcast一期节目](https://youtu.be/8bIHcttkOTE)中聊了很多这方面的内容
- 我在[The Outer Loop](https://theouterloop.substack.com)写了一些这方面的东西
- 我和[@hellovai](https://github.com/hellovai)一起做[关于Maximizing LLM Performance的webinars](https://github.com/hellovai/ai-that-works/tree/main)
- 我们在[got-agents/agents](https://github.com/got-agents/agents)下用这套方法论构建OSS agents
- 我们无视了自己所有的建议，构建了一个[在kubernetes中运行分布式agents的framework](https://github.com/humanlayer/kubechain)
- 本指南中的其他链接：
  - [12 Factor Apps](https://12factor.net)
  - [Building Effective Agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents#agents)
  - [Prompts are Functions](https://thedataexchange.media/baml-revolution-in-ai-engineering/)
  - [Library patterns: Why frameworks are evil](https://tomasp.net/blog/2015/library-frameworks/)
  - [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)
  - [Mailcrew Agent](https://github.com/dexhorthy/mailcrew)
  - [Mailcrew Demo Video](https://www.youtube.com/watch?v=f_cKnoPC_Oo)
  - [Chainlit Demo](https://x.com/chainlit_io/status/1858613325921480922)
  - [TypeScript for LLMs](https://www.linkedin.com/posts/dexterihorthy_llms-typescript-aiagents-activity-7290858296679313408-Lh9e)
  - [Schema Aligned Parsing](https://www.boundaryml.com/blog/schema-aligned-parsing)
  - [Function Calling vs Structured Outputs vs JSON Mode](https://www.vellum.ai/blog/when-should-i-use-function-calling-structured-outputs-or-json-mode)
  - [BAML on GitHub](https://github.com/boundaryml/baml)
  - [OpenAI JSON vs Function Calling](https://docs.llamaindex.ai/en/stable/examples/llm/openai_json_vs_function_calling/)
- [Outer Loop Agents](https://theouterloop.substack.com/p/openais-realtime-api-is-a-step-towards)
  - [Airflow](https://airflow.apache.org/)
  - [Prefect](https://www.prefect.io/)
  - [Dagster](https://dagster.io/)
  - [Inngest](https://www.inngest.com/)
  - [Windmill](https://www.windmill.dev/)
  - [The AI Agent Index (MIT)](https://aiagentindex.mit.edu/)
  - [NotebookLM on Finding Model Capability Boundaries](https://open.substack.com/pub/swyx/p/notebooklm?selection=08e1187c-cfee-4c63-93c9-71216640a5f8)

## 贡献者

感谢所有为 12-factor agents 做出贡献的人！

[<img src="https://avatars.githubusercontent.com/u/3730605?v=4&s=80" width="80px" alt="dexhorthy" />](https://github.com/dexhorthy) [<img src="https://avatars.githubusercontent.com/u/50557586?v=4&s=80" width="80px" alt="Sypherd" />](https://github.com/Sypherd) [<img src="https://avatars.githubusercontent.com/u/66259401?v=4&s=80" width="80px" alt="tofaramususa" />](https://github.com/tofaramususa) [<img src="https://avatars.githubusercontent.com/u/18105223?v=4&s=80" width="80px" alt="a-churchill" />](https://github.com/a-churchill) [<img src="https://avatars.githubusercontent.com/u/4084885?v=4&s=80" width="80px" alt="Elijas" />](https://github.com/Elijas) [<img src="https://avatars.githubusercontent.com/u/39267118?v=4&s=80" width="80px" alt="hugolmn" />](https://github.com/hugolmn) [<img src="https://avatars.githubusercontent.com/u/1882972?v=4&s=80" width="80px" alt="jeremypeters" />](https://github.com/jeremypeters)
[<img src="https://avatars.githubusercontent.com/u/380402?v=4&s=80" width="80px" alt="kndl" />](https://github.com/kndl) [<img src="https://avatars.githubusercontent.com/u/16674643?v=4&s=80" width="80px" alt="maciejkos" />](https://github.com/maciejkos) [<img src="https://avatars.githubusercontent.com/u/85041180?v=4&s=80" width="80px" alt="pfbyjy" />](https://github.com/pfbyjy) [<img src="https://avatars.githubusercontent.com/u/36044389?v=4&s=80" width="80px" alt="0xRaduan" />](https://github.com/0xRaduan) [<img src="https://avatars.githubusercontent.com/u/7169731?v=4&s=80" width="80px" alt="zyuanlim" />](https://github.com/zyuanlim) [<img src="https://avatars.githubusercontent.com/u/15862501?v=4&s=80" width="80px" alt="lombardo-chcg" />](https://github.com/lombardo-chcg) [<img src="https://avatars.githubusercontent.com/u/160066852?v=4&s=80" width="80px" alt="sahanatvessel" />](https://github.com/sahanatvessel)

## 许可证

所有内容和图像均依据 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0 License</a> 授权

代码依据 <a href="https://www.apache.org/licenses/LICENSE-2.0">Apache 2.0 License</a> 授权
