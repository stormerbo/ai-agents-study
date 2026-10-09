# 当前进度

> 决定「接下来做什么」时读这一份。各章完成情况与逐节进度表。

> 本文档内出现的 §x.y 引用，若不在本文件里，则在 AGENTS.md 或 docs/ 的另一份中 —— **§ 编号与原 AGENTS.md 完全一致**，可以直接按编号找。
>
> 本文件从 AGENTS.md 拆出，**保留了原来的 § 编号** ——
> 这样全库现有的「见 §4.9」这类引用仍然指向正确位置。

---

## 6. 当前进度

### 6.1 已完成

**基础设施**：脚手架、Tailwind 4 设计令牌、深色模式、MDX 管线、Mermaid 组件、资源库（48 条）、术语表（30 条）、实验定义（9 个）、作业（1 个）、准确性机制、63 个测试断言

**章 0「起点」** —— 4 节完整正文（从中途开始写，此前只有大纲）

**章 1「LLM 基础与 API 调用」** —— 5 节完整正文

**章 2「Prompt 工程」** —— 5 节完整正文（2026-10-08 全部完成）

**章 3「上下文工程」** —— 5 节完整正文（2026-10-08 完成）

**章 4「Tool / Function Calling」** —— 5 节完整正文（2026-10-08 完成）

**章 5「结构化输出」** —— 4 节完整正文（2026-10-08 完成）

**章 6「检索」/ 章 7「记忆」/ 章 8「多模态输入」/ 章 9「计算机使用」** —— 各 5 节完整正文（2026-10-08 / 10-09 完成）

**章 10「Agent 范式」/ 章 11「手写循环」/ 章 12「多智能体」/ 章 13「框架选型」/ 章 14「MCP」** —— 各 5 节完整正文（2026-10-09 完成）

> **阶段 3 到此收口。** 编排层的五章全部有正文：范式（怎么选控制流）、循环（从零写一遍）、多智能体（成本模型）、框架（抽象与泄漏）、协议（工具生态）。
> 这一轮里最有价值的两次实测是：**静态计划在带分支的任务上 0/3 且贵 57%**，以及**用真 LangChain 抓到装饰器不给 enum 的抽象泄漏**。

> **阶段 2 到此收口。** 六个原语全部有正文：4 工具调用 / 5 结构化输出 / 6 检索 / 7 记忆 / 8 多模态 / 9 计算机使用。
> 这也是第二轮规划里点名的那个缺口的闭合处 —— `vision` 与「计算机使用」两项零覆盖，现在都有正文 + 实验。

**实验与交互补缺（2026-10-09）** —— Playground 增加**图像上传**，并补上第 8 章的 `lab-vision-extract`（视觉提取）。
  `vision` 从此不再是空置的 capability —— 补它的动因就是第二轮规划时点出的那个缺口。

> ⚠️ **章 3、4 写完后建议人工复核一遍** —— 这两章的实验密度最高、结论也最多反直觉，而且期间被我自己纠正过五次测量缺陷。复核重点是「反例的边界说得够不够准」。

**全站 23 章，其中章 6-14 已有完整正文（阶段 0-3 收口）**：

- 阶段 2 六个原语：4 工具调用 / 5 结构化输出 / **6 检索（有正文）** / **7 记忆（有正文）** / **8 多模态输入（有正文）** / **9 计算机使用（有正文，2026-10-09 完成）**
- 阶段 3 五章：**10 Agent 范式（有正文）** / **11 手写循环（有正文）** / **12 多智能体（有正文）** / **13 框架选型（有正文）** / **14 MCP（有正文，2026-10-09 完成）**
- 阶段 4 六章：15 评估与可观测性 / 16 沙箱与权限 / 17 安全与信任边界 / 18 成本与延迟 / 19 人机协作 / 20 部署与交付
- 阶段 5 两章：21 源码研读 / 22 综合项目

> **2026-10-08 第二轮规划的依据**：在当时的 13 章里逐个搜能力关键词，结论是：**多模态 / 视觉输入、计算机使用、人机协作 / 审批** 三项**零覆盖**（`vision` 曾是 `LAB_CAPABILITIES` 里唯一没有任何实验使用的值 —— **已于 2026-10-09 补上 `lab-vision-extract`**）；**微调**只有 2 处顺带提及、没有任何章节承载它。据此补了 4 章；同时把原先只有一行描述的阶段 4、阶段 5 补成完整大纲。
>
> **明确排除在范围外的**：**语音 / 音频输入**与**模型蒸馏**。理由是本站定位是「怎么用模型」而不是「怎么训模型 / 怎么处理音频流」—— 两者都需要一整套独立的基础设施（音频管线、训练与评测环境），塞进来只会稀释主线。**写清楚不做什么，和写清楚做什么同样重要**：此前「微调」的问题正是既没讲也没说不讲。
>
> **没有新增阶段**。理由：阶段代表依赖层，而上述缺口都是「已有层里缺章」—— 多模态与计算机使用属于原语层（与第 4 章的工具调用同层），安全与人机协作属于生产化层。把它们独立成阶段会虚假地引入顺序依赖。唯一接近新增阶段的是「迭代闭环」（轨迹 → 评测 → 改进），最终作为第 20 章的收口节处理。

### 6.2 进度明细

> 下表由 scripts/content-stats.mjs 同源口径生成（当前 73/73 达标）。

| 节 | 中文 | 说明文字 | 图 | 代码块 | 达标 |
|---|---:|---:|---:|---:|:--:|
| agent-frameworks/01-what-frameworks-give | 2508 | 3411 | 1 | 4 | ✅ |
| agent-frameworks/02-abstraction-models | 2152 | 3037 | 1 | 4 | ✅ |
| agent-frameworks/03-leaky-abstractions | 2202 | 3264 | 1 | 5 | ✅ |
| agent-frameworks/04-build-vs-buy | 2310 | 3223 | 1 | 1 | ✅ |
| agent-frameworks/05-selection-matrix | 2305 | 3128 | 1 | 3 | ✅ |
| agent-loop/01-minimal-loop | 2267 | 3083 | 1 | 3 | ✅ |
| agent-loop/02-tool-registry | 2233 | 3092 | 1 | 7 | ✅ |
| agent-loop/03-budgets-and-guards | 2212 | 3146 | 1 | 5 | ✅ |
| agent-loop/04-state-and-resume | 2311 | 3271 | 1 | 2 | ✅ |
| agent-loop/05-what-frameworks-do | 2093 | 3001 | 1 | 3 | ✅ |
| agent-paradigms/01-five-paradigms | 2013 | 3034 | 1 | 1 | ✅ |
| agent-paradigms/02-react-loop | 1955 | 3003 | 1 | 5 | ✅ |
| agent-paradigms/03-plan-and-execute | 1912 | 3002 | 1 | 2 | ✅ |
| agent-paradigms/04-reflection | 2223 | 3222 | 1 | 2 | ✅ |
| agent-paradigms/05-choosing | 2124 | 3158 | 1 | 1 | ✅ |
| computer-use/01-what-differs | 1977 | 3044 | 1 | 4 | ✅ |
| computer-use/02-observe-act-loop | 1997 | 3152 | 1 | 3 | ✅ |
| computer-use/03-failure-modes | 2069 | 3046 | 1 | 4 | ✅ |
| computer-use/04-safety-and-scope | 2194 | 3052 | 1 | 5 | ✅ |
| computer-use/05-when-not-to-use | 1918 | 3007 | 1 | 2 | ✅ |
| context-engineering/01-context-is-finite | 2006 | 3285 | 1 | 3 | ✅ |
| context-engineering/02-system-prompt-altitude | 2028 | 3049 | 1 | 3 | ✅ |
| context-engineering/03-just-in-time | 1890 | 3130 | 1 | 2 | ✅ |
| context-engineering/04-compaction | 2110 | 3150 | 1 | 3 | ✅ |
| context-engineering/05-subagent-isolation | 2047 | 3301 | 1 | 1 | ✅ |
| llm-api-basics/01-tokens-and-context | 3922 | 6704 | 2 | 7 | ✅ |
| llm-api-basics/02-sampling-params | 3026 | 5794 | 1 | 5 | ✅ |
| llm-api-basics/03-messages-api | 1661 | 3560 | 1 | 8 | ✅ |
| llm-api-basics/04-model-selection | 1903 | 3179 | 2 | 11 | ✅ |
| llm-api-basics/05-prompt-caching | 1958 | 3567 | 1 | 10 | ✅ |
| mcp/01-why-protocol | 2227 | 3713 | 1 | 1 | ✅ |
| mcp/02-roles-and-capabilities | 1772 | 3104 | 1 | 2 | ✅ |
| mcp/03-stateless-2026 | 2134 | 3551 | 1 | 6 | ✅ |
| mcp/04-build-a-server | 1616 | 3051 | 1 | 3 | ✅ |
| mcp/05-security-boundary | 2423 | 3719 | 1 | 3 | ✅ |
| memory/01-context-is-not-memory | 1865 | 3033 | 1 | 2 | ✅ |
| memory/02-what-to-write | 2220 | 3055 | 1 | 2 | ✅ |
| memory/03-when-to-recall | 2077 | 3012 | 1 | 2 | ✅ |
| memory/04-forgetting-and-conflict | 2205 | 3011 | 1 | 2 | ✅ |
| memory/05-memory-cost-and-eval | 2136 | 3017 | 1 | 2 | ✅ |
| multi-agent/01-topologies | 2150 | 3017 | 1 | 1 | ✅ |
| multi-agent/02-cost-model | 2072 | 3034 | 1 | 4 | ✅ |
| multi-agent/03-isolation-is-the-point | 2200 | 3015 | 1 | 1 | ✅ |
| multi-agent/04-failure-modes | 2380 | 3150 | 1 | 1 | ✅ |
| multi-agent/05-alternatives | 2179 | 3008 | 1 | 1 | ✅ |
| multimodal/01-how-images-enter-context | 1690 | 3332 | 1 | 3 | ✅ |
| multimodal/02-document-routes | 1822 | 3005 | 1 | 2 | ✅ |
| multimodal/03-resolution-and-cost | 1636 | 3126 | 1 | 2 | ✅ |
| multimodal/04-when-vision-fails | 1743 | 3002 | 1 | 2 | ✅ |
| multimodal/05-vision-in-the-loop | 2086 | 3029 | 1 | 2 | ✅ |
| prompt-engineering/01-instruction-clarity | 1956 | 3034 | 1 | 2 | ✅ |
| prompt-engineering/02-structure-and-separation | 2013 | 3053 | 1 | 3 | ✅ |
| prompt-engineering/03-few-shot | 2021 | 3001 | 1 | 1 | ✅ |
| prompt-engineering/04-chain-of-thought | 1854 | 3063 | 1 | 4 | ✅ |
| prompt-engineering/05-reliability | 2945 | 4733 | 2 | 2 | ✅ |
| retrieval/01-why-retrieval | 2095 | 3257 | 1 | 4 | ✅ |
| retrieval/02-chunking | 1771 | 3197 | 1 | 3 | ✅ |
| retrieval/03-vector-limits | 2114 | 3270 | 1 | 3 | ✅ |
| retrieval/04-evaluating-retrieval | 2024 | 3041 | 1 | 2 | ✅ |
| retrieval/05-agentic-retrieval | 2078 | 3043 | 1 | 2 | ✅ |
| structured-output/01-why-not-prompt-only | 1900 | 3243 | 1 | 6 | ✅ |
| structured-output/02-json-schema-strict | 1968 | 3975 | 1 | 7 | ✅ |
| structured-output/03-validation-retry | 2049 | 3096 | 1 | 3 | ✅ |
| structured-output/04-beyond-json | 1818 | 3114 | 1 | 4 | ✅ |
| tool-calling/01-what-really-happens | 1798 | 3013 | 1 | 5 | ✅ |
| tool-calling/02-schema-design | 1693 | 3196 | 1 | 2 | ✅ |
| tool-calling/03-poka-yoke | 1634 | 3103 | 1 | 1 | ✅ |
| tool-calling/04-parallel-and-errors | 1899 | 3055 | 1 | 4 | ✅ |
| tool-calling/05-tool-count | 1859 | 3222 | 1 | 2 | ✅ |
| what-is-an-agent/01-why-now | 2561 | 4293 | 1 | 5 | ✅ |
| what-is-an-agent/02-what-counts-as-agent | 2106 | 3679 | 2 | 3 | ✅ |
| what-is-an-agent/03-mindset-shift | 2446 | 3936 | 2 | 6 | ✅ |
| what-is-an-agent/04-how-to-use-this-site | 2151 | 3157 | 1 | 2 | ✅ |

**章 2 / 3 / 4（2026-10-08）完成的工作**：

1. 五节正文，全部含「实测数据 + Mermaid 图 + 完整可运行代码 + 真实错误案例」四块
2. **7 组新实测**：否定式 vs 正面指令、提示注入 6 种形式、少样本（典型 vs 边界）、CoT 成本、self-consistency 多数投票、self-eval 判别力、temperature 透传对照
3. **章 1 遗留的 5 处 Mermaid 代码块转成了 `<Mermaid>` 组件**（1-2/1-3/1-4/1-5）
4. 修了全站 8 个页面的静默渲染失效（见 §4.8）
