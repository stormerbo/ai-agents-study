import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'tooling',
  stageId: 'stage-5-practice',
  order: 21,
  title: '工具与上手',
  subtitle: '知道该装什么，然后装一次',
  summary:
    '前面二十章讲的是机制，这一章讲生态：检索链路要装什么、编排框架给你什么又拿走什么、本地模型什么时候值得、以及界面那层怎么做。每一节都配了在本机真跑出来的数字 —— 因为工具会过时，而「怎么量、怎么判」不会。',
  outcomes: [
    '能根据规模与运维需求，判断一个检索场景要不要上向量库',
    '能在装框架之前先算出它会动到哪些已有依赖',
    '能用真框架跑通一个最小 agent，并说清它替你解决了什么、没解决什么',
    '能把审批与进度做成界面，并说得出为什么不需要客户端状态',
  ],
  depth: 'guided',
  difficulty: 'intermediate',
  estimatedMinutes: 90,
  tags: ['tooling', 'ecosystem', 'hands-on'],
  prerequisiteIds: ['retrieval', 'agent-frameworks', 'human-in-the-loop'],
  resourceIds: ['langchain-docs'],
  backendMapping: {
    analogy:
      '选 agent 工具链 ≈ 选一套中间件：先量自己的规模与运维需求，再看候选；能自己写的那一层不要引依赖',
    transferable: [
      '先量后选：别问「哪个最好」，先问「我的规模落在哪一侧」',
      '依赖是有成本的：装一个框架会动到已有的版本约束，先算再装',
      '能自己写的那一层不引依赖 —— 一行矩阵乘法顶得上一套向量库',
    ],
    pitfalls: [
      '按榜单/热度挑工具，而不是按自己的规模与运维需求',
      '上来就自建推理服务，而没有先试「编码型任务换本地小模型」这条轻路径',
      '以为用了框架就不用自己写幂等 —— 检查点管状态，不管副作用',
      '把审批界面做成带状态的前端组件，而它其实只是四条不同的请求',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-09',
  verifiedAt: '2026-10-09',
  lessons: [
    {
      id: 'tooling/retrieval-stack',
      chapterId: 'tooling',
      slug: 'retrieval-stack',
      title: '工具地图（一）：检索链路',
      summary: '向量库、embedding、切分工具 —— 什么时候需要它们，什么时候一段矩阵乘法就够。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'vector-db-when',
          basis: 'inferred',
          question: '为什么不能只问「哪个向量库好」？',
          answer:
            '因为选型问题的真正形式是**「我的规模落在哪一侧」**。本站实测（1311 块语料、512 维）：numpy 暴力检索一次查询 **0.02 毫秒**，而 chromadb 是 **0.83 毫秒** —— 后者慢了 40 倍，因为它每次调用有自己的开销。放大到合成向量后交叉点出现在 **1 万到 5 万之间**（1 万时 numpy 0.83ms 仍快于 chromadb 1.50ms；5 万时 chromadb 4.58ms 对 1.73ms 反超）。所以「哪个向量库好」是个错问题；「我的 N 有多大、要不要过滤/更新/持久化」才决定答案。',
        },
        {
          id: 'embedding-local-vs-api',
          basis: 'inferred',
          question: '本地 embedding 和调 API，该怎么选？',
          answer:
            '先量本地那一侧的成本。本站实测 `BAAI/bge-small-zh-v1.5`（512 维）：**246 块/秒**，1311 块编码 5.3 秒，向量共 2.6 MB —— 而且是**一次性**的（建完索引就不用再编）。这个数字决定了判断：如果语料规模在万级、且不频繁重建，本地的吞吐完全够用，而它换来的是**零网络依赖、零按量计费、数据不出机器**。反过来，如果语料在百万级、或者需要多语言/长文本的特殊能力，API 的模型质量与免运维才划得来。注意判据里没有「哪个更准」—— 那需要在你的数据上评测（第 6 章那套），不该靠别人给的榜单。',
        },
      ],
      resourceIds: ['langchain-docs'],
    },
    {
      id: 'tooling/orchestration-stack',
      chapterId: 'tooling',
      slug: 'orchestration-stack',
      title: '工具地图（二）：编排与可观测性',
      summary: '框架给你什么、拿走什么；以及 trace 平台解决了哪一刻的问题。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'version-constraint',
          basis: 'inferred',
          question: '为什么「装一个框架」是选型里被低估的一步？',
          answer:
            '因为它会动到你已经装好的东西 —— 而那个影响在需求文档里看不到。本站实测：环境里是 `langchain-core 0.3.63` + `langchain 0.3.7`，而 `langgraph 1.2.14` 要求 `langchain-core<2,>=1.4.7` —— **冲突**（`pydantic>=2.7.4` 对 2.9.2 则兼容）。直接装会把 langchain-core 升到 1.x，于是 langchain 0.3.7 坏掉，而第 13 章那些绑在 0.3.63 上的实测结论也失去可复现性。解法是**独立 venv**：框架可以试，但不许污染已验证过的环境。这条经验对后端工程师不新鲜 —— 新鲜的是一开始就要把它算进选型成本。',
        },
        {
          id: 'observability-what',
          basis: 'inferred',
          question: '可观测性平台解决的是哪一刻的问题？',
          answer:
            '它解决的是**「线上出问题、你不在场」**那一刻。自己写轨迹（第 15 章那四个字段）能让**你在场时**定位到具体哪一步；而平台补的是另外三件：跨请求的聚合（哪些输入模式在失败）、留痕与共享（别人能看你看到的那次轨迹）、以及时间轴上的对比（这次变差是从哪个版本开始的）。所以判据是**「出问题的时候，除了你还有谁会来看」**：只有你一个人看，自己写就够了；有值班、有交接、有多个服务，那平台的价值立刻出现 —— 因为它把「你脑子里的上下文」变成了「别人能打开的东西」。',
        },
      ],
      resourceIds: ['langchain-docs'],
    },
    {
      id: 'tooling/local-models',
      chapterId: 'tooling',
      slug: 'local-models',
      title: '本地与开源模型：什么时候该自己跑',
      summary: '不是「省钱」那么简单 —— 本地模型的三个真实理由与三个真实代价。',
      estimatedMinutes: 16,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'why-local',
          basis: 'inferred',
          question: '抛开成本，什么时候必须用本地模型？',
          answer:
            '三个理由里只有一个是成本。**数据不能出机器** —— 这是唯一「花钱也解决不了」的理由，也是本站这个项目私有的原因之一。**离线或网络不可靠** —— 生产环境未必有稳定出口。**要固定版本** —— 托管模型的滚动更新你说了不算（第 20 章讲过这个区分）。而成本是最弱的理由：本地要自己承担 GPU、运维、以及质量可能下降带来的返工。所以判断顺序应该是「有没有前两个理由」→ 有就本地；没有 → 再算成本账，而那时托管通常赢。',
        },
        {
          id: 'local-embedding',
          basis: 'inferred',
          question: '本地跑 embedding 是一个被低估的切入点。',
          answer:
            '因为它**不需要 GPU**、不需要模型服务、而且是一次性的。本站实测：`bge-small-zh-v1.5` 在纯 CPU 上 246 块/秒，1311 块编码 5.3 秒，模型只有 512 维、向量共 2.6 MB。这个量级意味着「本地」的成本几乎可以忽略 —— 而它换来的是数据不出机器。所以一个实用的路径是：**生成类任务继续用托管模型，检索/分类这类「编码型」任务换成本地小模型。** 这个切分能覆盖「数据敏感」需求的一大部分，而不必一上来就自建推理服务。',
        },
      ],
      resourceIds: ['langchain-docs'],
    },
    {
      id: 'tooling/first-agent',
      chapterId: 'tooling',
      slug: 'first-agent',
      title: '动手：用 LangGraph 搭一个最小 agent',
      summary: '一个真能跑的最小 agent，以及它没替你解决的那个问题。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'checkpoint-boundary',
          basis: 'inferred',
          question: '框架的检查点为什么防不住「重复副作用」？',
          answer:
            '因为它**在节点返回之后**才写。本站实测（langgraph 1.2.14）：一个节点内先写库、再返回状态，中间注入崩溃 —— 恢复后节点重跑，库里出现了三条**相同的 u2 记录**，节点被执行 **3 次**。这不是框架的缺陷，是**检查点机制的原理边界**：它保证「已完成节点的状态不丢」，不保证「未完成节点的副作用不重」。副作用与状态落盘之间的那个窗口，任何检查点机制都覆盖不到 —— 所以第 11 章那条结论（幂等要自己写）在用了框架之后**仍然成立**。',
        },
        {
          id: 'framework-value',
          basis: 'inferred',
          question: '那用框架换来了什么？',
          answer:
            '换来的是**「已完成部分」的可靠性与可运维性**：状态的结构化管理、跨进程恢复（把检查点换成数据库即可）、流式输出、以及可视化。第 11 章那个手写循环能跑，但它的状态是你自己序列化的、恢复语义是你自己定的、并发与时序的坑要自己趟。所以框架的价值不在「帮你写 agent 逻辑」（那部分它给得很少），而在**把状态与恢复这套基础设施标准化**。判断要不要用它，就问一句：**你的 agent 需不需要跨进程恢复和多人协作运维？** 不需要，手写更清楚；需要，框架省下的正是最难自己写好的那一层。',
        },
      ],
      resourceIds: ['langchain-docs'],
    },
    {
      id: 'tooling/agent-ui',
      chapterId: 'tooling',
      slug: 'agent-ui',
      title: '界面：把审批与进度做出来',
      summary: '第 19 章那些设计结论，落到代码上是什么样。',
      estimatedMinutes: 16,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'ui-no-state',
          basis: 'inferred',
          question: '审批界面为什么可以不需要客户端状态？',
          answer:
            '因为**审批的四个选项本质上是四条不同的请求，不是内存里的一次选择**：同意、拒绝、修改后同意、换个方式 —— 它们各自对应一个不同的下一步，而不是「先选中再提交」。理解这一点之后，界面可以是一个纯 server component，用原生 `<details>` 折叠正文、用按钮发请求，**零客户端 JS**。好处很实际：没有水合、没有 hydration mismatch 的风险（§4.7 记录过这个坑）、也没有状态同步问题。反面例子是把它做成一个带 modal 状态、loading 状态、二次确认状态的前端组件 —— 那些状态都来自「先选中再提交」这个错误的模型。',
        },
        {
          id: 'ui-progress',
          basis: 'inferred',
          question: '进度为什么不该用百分比？',
          answer:
            '因为**步数在 agent 里不可预知**。第 10 章实测过静态计划在分支任务上有 0/3 的成功率 —— 计划本身都不可靠，用它来算总步数就更不可靠。百分比会因此跳来跳去，而且给出虚假的精确感。更诚实的是**按动作显示**：「正在读取第 3 份文档」「等待确认发送给 zhangsan@example.com」。它具体、不会跳，而且信息量并不比百分比少。如果确实需要一个粗糙的进度感，用**可预知的阶段**（已找到资料 → 正在整理 → 准备发送），而不是用步数。',
        },
      ],
      resourceIds: ['langchain-docs'],
    },
  ],
} satisfies Chapter;
