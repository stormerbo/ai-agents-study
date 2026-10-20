import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'memory',
  stageId: 'stage-2-primitives',
  order: 7,
  title: '记忆',
  subtitle: '跨会话的状态，以及遗忘',
  summary:
    '上下文是工作记忆，不是记忆系统。这一章讲清什么信息值得写进外部存储、什么时候该召回、记错了怎么收回，以及为什么绝大多数记忆系统的失败不在于「记不住」，而在于「记了不该记的」。',
  outcomes: [
    '能区分工作记忆与长期记忆，并说出各自的失效方式',
    '能设计写入规则：什么该记、什么绝对不能记',
    '能处理记忆的过期与冲突，而不是让它们互相矛盾地堆在库里',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 100,
  tags: ['memory', 'state', 'persistence'],
  prerequisiteIds: ['retrieval', 'context-engineering'],
  lessons: [
    {
      id: 'memory/context-is-not-memory',
      chapterId: 'memory',
      slug: 'context-is-not-memory',
      title: '上下文不是记忆',
      summary: '单次调用的上下文输入不自动构成记忆系统；持久化与编辑行为由应用或 API 决定，记忆还需要选择性写入、检索与冲突裁决。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['working-memory', 'long-term-memory'],
      checkpoints: [
        {
          id: 'why-context-isnt-memory',
          basis: 'inferred',
          question: '为什么「把对话历史全部留着」不能算记忆？',
          answer:
            '单次调用的上下文是交给模型处理的输入，不会自动决定哪些事实应长期保留、何时召回、如何更新或解决冲突。应用可以保存和编辑自己的对话状态，供应商 API 也可能提供托管会话；具体生命周期与编辑能力应按所用产品/API 合约确认。外部记忆的价值在于把选择性写入、来源、有效期、检索与冲突裁决做成明确的系统语义，而不是因为上下文必然会在请求后消失或不能修改。',
        },
        {
          id: 'three-kinds-of-memory',
          basis: 'inferred',
          question: '把「记忆」笼统当成一件事，会漏掉什么区别？',
          answer:
            '至少该分成三类，因为它们的写入方式、生命周期与失效模式都不同：\n\n1. **对话历史** —— 这一轮任务的上下文，任务结束就该丢。\n2. **事实记忆** —— 用户的偏好、项目的约束、系统的既有配置。跨会话有效，但会过期。\n3. **程序性记忆** —— 这个 agent 会哪些工具、走过哪些成功路径。它更接近「技能」，更新频率最低。\n\n把它们混在一个存储里，就会出现「把一次性的闲聊当成长期偏好」这类错误 —— 而这是多数记忆系统上线后最先暴露的问题。',
        },
      ],
      resourceIds: ['memgpt-paper', 'anthropic-context-engineering'],
    },
    {
      id: 'memory/what-to-write',
      chapterId: 'memory',
      slug: 'what-to-write',
      title: '写入：什么该记，什么绝对不能记',
      summary: '记忆系统的第一道关口是写入规则，而不是检索算法。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['write-policy', 'privacy'],
      checkpoints: [
        {
          id: 'write-criteria',
          basis: 'inferred',
          question: '一条信息要满足什么条件才值得写进长期记忆？',
          answer:
            '三个条件同时满足才写：**跨会话仍然有效**、**相对稳定**、**可验证或可归因**。\n\n举例：「用户偏好简洁回复」满足三条，值得记。「用户今天问了发票流程」不满足第一条，那是一次任务上下文。而「用户可能对价格敏感」——这是模型的**推断**，不是用户说过的事实，写进去之后你再也分不清哪些记忆来自观察、哪些来自猜测。\n\n所以每条记忆都应该带**来源**：用户明说的、还是系统观测到的、还是模型推断的。第 5 章那个 status_source 字段解决的是同一个问题 —— 让「这条信息从哪来」在数据结构里可分辨。',
        },
        {
          id: 'why-store-everything-fails',
          basis: 'inferred',
          question: '「把用户说的每句话都存下来」为什么会在长期变成灾难？',
          answer:
            '三个后果叠加。**一是噪声淹没信号**：真正有用的偏好被大量一次性陈述稀释，召回时更容易捞上来无关内容。**二是矛盾会累积**：用户三个月前说过「不要给我发邮件」，上周又改了口，两条都在库里，召回哪条取决于排序 —— 而你没有任何裁决依据。**三是合规风险**：无差别存储会把敏感信息一并留下，而且删不掉（你不知道它藏在哪条记忆里）。\n\n写入规则的价值就在于**在入口处**做减法。这比事后清理容易得多。',
        },
      ],
      resourceIds: ['mem0', 'letta'],
    },
    {
      id: 'memory/when-to-recall',
      chapterId: 'memory',
      slug: 'when-to-recall',
      title: '读取：什么时候召回，以及误召回的代价',
      summary: '召回不是越多越好 —— 不相关的记忆会改变模型的行为，而你不会收到任何提示。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['recall', 'injection'],
      checkpoints: [
        {
          id: 'inject-vs-tool',
          basis: 'inferred',
          question: '记忆是「每轮自动注入」好，还是「做成工具让模型自己查」好？',
          answer:
            '取决于记忆是**普遍相关**还是**条件相关**。\n\n用户的语言偏好、回答风格这类几乎每轮都成立，适合少量常驻注入 —— 但必须严格控制条数，因为它们每一轮都要重新计费（第 1 章的成本算术在这里同样成立）。\n\n而「这个项目上次用了哪个部署环境」只在特定任务下相关，就该做成工具让模型按需查。自动注入的代价是：**不相关的记忆会影响模型行为**，而且失败是静默的 —— 你不会知道是记忆把它带偏了。',
        },
        {
          id: 'false-recall-cost',
          basis: 'inferred',
          question: '为什么「误召回」可能比「召回不到」更糟？',
          answer:
            '召回不到时，模型面对的是信息缺失，它至少有机会说「我不确定」—— 而这条路径我们在第 5 章测过，只要指令明确，模型会如实承认。\n\n误召回则相反：它给模型一条**看起来可信、但与当前情境无关**的信息。模型没有理由怀疑它，于是会把它当作前提使用。结果是带着错误前提产出一个逻辑自洽的答案 —— 这类错误在日志里完全看不出来。\n\n所以记忆召回的门槛应该比检索更高：**宁可少召回，不可错召回。**',
        },
      ],
      resourceIds: ['letta', 'anthropic-context-engineering'],
    },
    {
      id: 'memory/forgetting-and-conflict',
      chapterId: 'memory',
      slug: 'forgetting-and-conflict',
      title: '遗忘、更新与冲突',
      summary: '记忆会过期、会互相矛盾。没有处理策略，库里存的就只是一堆有时序的断言。',
      estimatedMinutes: 22,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['conflict', 'ttl', 'provenance'],
      checkpoints: [
        {
          id: 'conflicting-memories',
          basis: 'inferred',
          question: '两条互相矛盾的记忆同时被召回，系统该怎么办？',
          answer:
            '首先必须能**发现**它们矛盾 —— 这要求每条记忆带时间戳与来源。只带内容的话，你连哪条更新都不知道。\n\n处理方式按代价从低到高：**取最新**（最简单，适合偏好类）；**按来源优先**（用户明说 > 系统观测 > 模型推断）；**交给模型裁决**（把两条一起给它，要求它指出冲突并询问用户）。\n\n无论选哪种，都不该选「都塞给模型让它自己看着办」—— 那是把冲突转嫁给一个没有裁决依据的组件。实践上更稳的做法是：**矛盾一旦被检测到，就在写入侧解决掉**（新记忆覆盖旧记忆，或在旧记忆上标记失效），而不是让冲突长期共存在库里。',
        },
        {
          id: 'why-forgetting-is-a-feature',
          basis: 'inferred',
          question: '为什么「遗忘」应该是记忆系统的显式功能，而不是可以一直拖延的事？',
          answer:
            '因为不遗忘的成本会随时间单调上升：库越大，召回越容易捞到过时信息；噪声越多，精确率越低；而每一次错误召回都会污染模型的判断。\n\n显式遗忘至少要有三样东西：**TTL**（这条记忆什么时候该失效）、**失效条件**（被新事实取代时怎样标记），以及**删除能力**（用户要求删除时能真的删干净）。最后一条既是合规要求，也是调试时的救命手段 —— 没有删除能力，你连「把某条可疑记忆拿掉再试一次」都做不到。',
        },
      ],
      resourceIds: ['mem0', 'letta', 'ai-engineering-huyen'],
    },
    {
      id: 'memory/memory-cost-and-eval',
      chapterId: 'memory',
      slug: 'memory-cost-and-eval',
      title: '记忆的成本与评估',
      summary: '记忆读写都要钱，而它到底改善了哪个指标，必须能被说清楚。',
      estimatedMinutes: 18,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['cost', 'evaluation'],
      checkpoints: [
        {
          id: 'memory-cost-model',
          basis: 'inferred',
          question: '记忆系统的成本由哪几部分组成？',
          answer:
            '四块：**写入**（每次判定「要不要记」并生成摘要，是一次模型调用）、**存储**（通常最便宜）、**召回**（一次检索，可能还带重排）、以及**注入**（最容易被忽略 —— 注入进上下文的内容会在之后每一轮重复计费）。\n\n最后一项往往是主要成本。第 1 章的算式在这里同样成立：多注入 200 token，在 20 轮的会话里就是 4000 token。所以「常驻注入哪些记忆」应该按每轮成本来定，而不是按「可能有用」来定。',
        },
        {
          id: 'memory-eval',
          basis: 'inferred',
          question: '怎么判断一套记忆系统值不值得？',
          answer:
            '先问**它改善的是哪个可测指标**，再问这个指标有没有在对照实验里真的变好。常见的三个候选：跨会话任务的完成率、需要重复澄清的次数、以及用户纠正「你记错了」的频率。\n\n要警惕的是只统计「记忆被召回了多少次」—— 那是活动量，不是效果。一个召回得很频繁的系统，也可能只是在频繁地把无关信息塞进上下文。判断方式与第 3 章那组实验一样：**做对照，别只看活动指标。**',
        },
      ],
      resourceIds: ['mem0', 'ai-engineering-huyen'],
    },
  ],
  resourceIds: [
    'memgpt-paper',
    'mem0',
    'letta',
    'anthropic-context-engineering',
    'ai-engineering-huyen',
  ],
  labIds: ['lab-memory-write'],
  backendMapping: {
    analogy: '记忆 ≈ 给一个无状态服务加持久化层，但写进去的是「模型得出的结论」而不是「事实」',
    transferable: [
      '缓存失效、TTL、最终一致性这些你熟悉的机制在这里全都用得上',
      '审计日志的思路：每条记忆都要能追到来源',
      '写入侧做减法（限流、脱敏、去重）比读侧优化更有效',
    ],
    pitfalls: [
      '把记忆当成「上下文不够用时的溢出容器」：它会变成噪声库',
      '无差别写入：把一次性陈述、无关信息、模型的推断一起存进去',
      '没有冲突解决策略，让互相矛盾的记忆长期共存',
      '只统计召回次数这类活动指标，而不是对照实验里的效果差异',
      '忽略「注入进上下文的内容每轮都要重新计费」',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
