import type { Term, TermId } from './schema';

/**
 * 术语表 —— 中文技术内容的质量分水岭。
 *
 * 同一个概念有多种译法（agent / 智能体 / 代理）是中文技术内容最常见的
 * 败笔，读起来会不断怀疑"这两个词是不是同一件事"。规则很简单：
 * 正文里第一次出现时用 `<Term id="..." />` 渲染，此后一律按这里的译法，
 * 英文原词保留不译 —— 因为你要去读的文档、论文、报错信息全是英文，
 * 把术语翻成中文反而会增加你搜索时的阻力。
 *
 * `discouraged` 列出见过但不推荐的译法，供校对时比对。
 */
export const glossary: Record<TermId, Term> = {
  agent: {
    id: 'agent',
    en: 'agent',
    zh: '智能体',
    definition:
      '一个能自主决定下一步做什么、并在循环中根据观察结果调整的系统。关键在「自主决定」——如果每一步都是你在代码里写死的，那它是 workflow，不是 agent。',
    discouraged: ['代理', '代理程序'],
  },
  workflow: {
    id: 'workflow',
    en: 'workflow',
    zh: '工作流',
    definition:
      '由你预先编排好步骤、LLM 只在固定环节被调用的系统。与 agent 的区别不是「高级 vs 低级」，而是「控制权在你手里还是在模型手里」。多数场景 workflow 已经够用，且更可靠、更便宜。',
  },
  token: {
    id: 'token',
    en: 'token',
    zh: '词元',
    definition:
      '模型处理文本的最小单位，约等于英文的 3/4 个单词、中文的 1~2 个字。它同时是计费单位、上下文容量的度量单位，以及延迟的主要来源。',
    discouraged: ['令牌'],
  },
  'context-window': {
    id: 'context-window',
    en: 'context window',
    zh: '上下文窗口',
    definition:
      '单次请求中模型能看到的 token 总量上限，包含输入与输出。可以类比为 session state，但有两个关键差别：它是**有损的**（中间部分容易被忽略），且**每次都要重新付费**。',
    discouraged: ['上下文长度'],
  },
  'context-engineering': {
    id: 'context-engineering',
    en: 'context engineering',
    zh: '上下文工程',
    definition:
      '决定「在每一次模型调用时，让模型看到什么」的工程实践。比 prompt engineering 的层次更高：不只要写好指令，还要管理工具定义、检索结果、历史对话、记忆的取舍与压缩。',
  },
  harness: {
    id: 'harness',
    en: 'harness',
    zh: '执行框架',
    definition:
      '包在模型外面、负责驱动循环、执行工具、管理上下文的那层代码。Claude Code、Cursor 这类产品的能力差异，很大一部分不在模型，而在 harness。',
    discouraged: ['脚手架', '马具'],
  },
  'tool-use': {
    id: 'tool-use',
    en: 'tool use / function calling',
    zh: '工具调用',
    definition:
      '让模型输出「我想调用哪个函数、参数是什么」，由你的代码实际执行后再把结果喂回去。注意：**模型从不真正执行任何东西**，它只是生成一个结构化的调用意图。',
    discouraged: ['函数调用（可混用，但首次出现用工具调用）'],
  },
  'structured-output': {
    id: 'structured-output',
    en: 'structured output',
    zh: '结构化输出',
    definition:
      '约束模型输出成可被程序解析的格式（通常是 JSON）。本质是把「自然语言」这个不可靠的输出通道，收窄成可校验的接口。',
  },
  react: {
    id: 'react',
    en: 'ReAct',
    zh: 'ReAct（推理 + 行动）',
    definition:
      'Reasoning + Acting 的缩写。让模型交替输出思考（Thought）、动作（Action），接收观察结果（Observation），再进入下一轮。2022 年提出，是今天几乎所有 agent 循环的祖先。',
  },
  'chain-of-thought': {
    id: 'chain-of-thought',
    en: 'chain-of-thought (CoT)',
    zh: '思维链',
    definition:
      '让模型在给出答案前先写出推理步骤。对多步推理任务提升明显，代价是输出更长、更贵、更慢。',
  },
  'few-shot': {
    id: 'few-shot',
    en: 'few-shot prompting',
    zh: '少样本提示',
    definition: '在 prompt 里给几个输入输出示例，让模型照着模仿。示例的质量比数量重要得多。',
  },
  prefill: {
    id: 'prefill',
    en: 'prefill',
    zh: '预填充',
    definition:
      '由你先把 assistant 回复的开头几个字符写好，让模型从这个前缀继续生成。用于强制输出格式（如预填 `{`）或绕过模型的开场白。',
  },
  temperature: {
    id: 'temperature',
    en: 'temperature',
    zh: '温度',
    definition:
      '采样随机性参数。低值（如 0）让输出更确定、更适合抽取与分类；高值让输出更发散、适合创意任务。注意：**温度设为 0 也不保证结果完全可复现**。',
  },
  'prompt-injection': {
    id: 'prompt-injection',
    en: 'prompt injection',
    zh: '提示注入',
    definition:
      '攻击者在模型会读到的内容里（网页、文档、邮件、工具返回值）埋入指令，诱使模型偏离原本的任务。本质是**数据与指令无法在同一个通道里可靠区分** —— 这是 LLM 应用最根本的安全弱点。',
    discouraged: ['提示词注入'],
  },
  rag: {
    id: 'rag',
    en: 'RAG (Retrieval-Augmented Generation)',
    zh: '检索增强生成',
    definition:
      '先从知识库检索相关内容，再把检索结果拼进 prompt 让模型基于它作答。解决的问题是：模型不知道你的私有数据，而且它的训练知识有截止日期。',
  },
  embedding: {
    id: 'embedding',
    en: 'embedding',
    zh: '嵌入向量',
    definition:
      '把一段文本映射成一个高维向量，使语义相近的文本在向量空间里也彼此靠近。检索的基础，但它捕捉的是**语义相似**，不是**事实相关** —— 这个差别是很多 RAG 效果不佳的根源。',
  },
  rerank: {
    id: 'rerank',
    en: 'rerank',
    zh: '重排序',
    definition:
      '在向量检索召回一批候选后，用更精确（也更慢）的模型重新打分排序。常见做法是「便宜的手段召回 100 条，贵的手段精选 10 条」。',
  },
  'lost-in-the-middle': {
    id: 'lost-in-the-middle',
    en: 'lost in the middle',
    zh: '中间遗忘',
    definition:
      '长上下文里，位于中间位置的信息最容易被模型忽略，开头和结尾的利用率明显更高。所以「上下文窗口够大」不等于「放多少都行」。',
  },
  'context-rot': {
    id: 'context-rot',
    en: 'context rot',
    zh: '上下文腐化',
    definition:
      '随着塞进上下文的内容增多，模型对其中每一部分的注意力反而下降的现象。它是上下文工程存在的理由：不是能塞多少，而是该塞什么、该丢什么。',
  },
  compaction: {
    id: 'compaction',
    en: 'compaction',
    zh: '上下文压缩',
    definition:
      '当对话历史接近上下文上限时，把较早的内容摘要化、丢弃冗余部分，只保留决策与关键结论。相当于给上下文做 GC。',
  },
  subagent: {
    id: 'subagent',
    en: 'subagent',
    zh: '子智能体',
    definition:
      '由主 agent 派生出来、拥有独立上下文窗口的从属 agent，通常只负责一个子任务并把结论回传。核心价值不是并行，而是**上下文隔离** —— 让探索过程中的大量中间输出不污染主上下文。',
  },
  orchestration: {
    id: 'orchestration',
    en: 'orchestration',
    zh: '编排',
    definition: '决定多个 agent 或步骤之间如何分工、传递数据、以及何时收敛的顶层逻辑。',
  },
  trajectory: {
    id: 'trajectory',
    en: 'trajectory',
    zh: '轨迹',
    definition:
      'agent 完成任务过程中走过的完整路径：每一步的思考、工具调用与观察结果。评估 agent 时，轨迹往往比最终答案更能说明问题 —— 答案对了但路径是错的，下一次就会出错。',
  },
  'pass-k': {
    id: 'pass-k',
    en: 'pass^k',
    zh: 'pass^k（k 次全对率）',
    definition:
      '同一个任务独立跑 k 次、要求**每次都成功**才算通过。与 pass@k（k 次里有一次成功即可）相反，它衡量的是可靠性。一个 pass@1 有 60% 的 agent，pass^8 可能不到 25% —— 这个落差是"demo 很惊艳、上线就翻车"的量化解释。',
  },
  'human-in-the-loop': {
    id: 'human-in-the-loop',
    en: 'human-in-the-loop (HITL)',
    zh: '人在回路',
    definition:
      '在关键动作执行前插入人工确认。工程上的难点不是加个弹窗，而是**在等待期间把 agent 的状态持久化下来** —— 人可能几小时后才回来点确认。',
  },
  'durable-execution': {
    id: 'durable-execution',
    en: 'durable execution',
    zh: '持久化执行',
    definition:
      '把每个执行步骤的状态落盘，使进程中断后能从断点恢复，而不是从头重跑。对动辄跑几十分钟、烧掉大量 token 的 agent 任务，这是刚需。与你熟悉的工作流引擎是同一类问题。',
  },
  'denial-of-wallet': {
    id: 'denial-of-wallet',
    en: 'denial of wallet',
    zh: '钱包拒绝服务',
    definition:
      '攻击者不需要让你的服务宕机，只要触发足够多的昂贵调用，就能让你在账单上"被 DoS"。Agent 系统因为单次请求成本高、循环次数不受控，尤其容易中招。',
  },
  guardrails: {
    id: 'guardrails',
    en: 'guardrails',
    zh: '护栏',
    definition:
      '在模型输入输出两侧加的程序化约束：输入过滤、输出校验、敏感操作拦截、循环与预算上限。原则是**用代码而不是用 prompt 来兜底**，因为 prompt 是可以被说服的。',
  },
  sandbox: {
    id: 'sandbox',
    en: 'sandbox',
    zh: '沙箱',
    definition:
      '用于约束代码可见资源与副作用的执行环境。讨论时可区分进程内、语言层限制、独立进程、共享宿主内核的容器、以及带 guest kernel 的 VM/microVM；这些不是自动成立的安全等级。应按信任来源、数据与副作用、租户隔离、宿主配置和可验证的运行时边界选型。',
  },
  'model-context-protocol': {
    id: 'model-context-protocol',
    en: 'Model Context Protocol (MCP)',
    zh: '模型上下文协议',
    definition:
      '一套把「工具与数据源」和「模型客户端」解耦的开放协议。价值类比：在它出现前，每接一个工具都要为每个客户端写一遍适配；MCP 相当于给这个领域定了 USB 接口。',
  },
};
