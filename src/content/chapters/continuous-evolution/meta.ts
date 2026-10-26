import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'continuous-evolution',
  stageId: 'stage-5-practice',
  order: 24,
  title: '持续进化',
  subtitle: '上线之后，它怎么变更好',
  summary:
    '前面的章节讲怎么把 agent 做出来，这一章讲做出来之后的事。已记录的线上轨迹是观察真实任务表现的重要来源之一，但并非真实分布的完整记录；从中可以提炼出四种形态的产物。闭环只优化它能观测的东西。',
  outcomes: [
    '能判断一条经验该写成哪种形态：知识、指令、程序还是参数',
    '能从失败轨迹里提炼规则，区分逐条留出与格式族留出，并说清旧实验为何无法复核',
    '能说清可验证闭环的边界在哪，以及为什么它会自信地跑偏',
  ],
  depth: 'deep',
  difficulty: 'expert',
  estimatedMinutes: 50,
  tags: ['continuous-improvement', 'distillation', 'closed-loop'],
  prerequisiteIds: ['evaluation', 'memory'],
  lessons: [
    {
      id: 'continuous-evolution/from-traces',
      chapterId: 'continuous-evolution',
      slug: 'from-traces',
      title: '从轨迹里能学到什么',
      summary: '从轨迹提取改进候选；区分知识、指令、程序与参数的边界，并落实来源、访问控制和评测。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['traces', 'learning-loops', 'distillation'],
      checkpoints: [
        {
          id: 'four-forms',
          basis: 'inferred',
          question: '从轨迹里学到的经验，可以写成哪四种形态？怎么判断该用哪种？',
          answer:
            '四种形态是分类，不是通用成本序列：**知识**需来源、范围、时效与访问控制；**指令**需审查、冲突检查和回归，且不保证模型必然遵守；**程序/工作流**需可信执行、测试、发布和副作用治理；**参数**需数据治理、评测及版本回退。选择前先明确目标指标、风险和责任边界，并比较验证成本。可审查偏好可作为提示，硬约束须由可信策略/代码强制；事实写入知识库之前需要验证来源与范围。参数更新不是其他方式难以表达时的默认兜底。保留旧模型/适配器版本支持回到已发布版本，但不等于能精确撤销某一类行为变化。',
        },
        {
          id: 'trace-hit-count-limit',
          basis: 'inferred',
          question: '为什么不能仅凭知识条目的 hit_count 或低命中阈值自动删除条目？',
          answer:
            'hit_count 记录检索次数，不直接衡量知识是否正确、有用或对高风险决策重要。低命中可能反映低频任务、检索召回缺陷、权限范围或采样偏差；应结合命中上下文、决策影响、风险和目标流量做候选复核，再由治理流程决定保留、更新或淘汰。被新事实替代时保留 superseded_by 关系，便于回溯。',
        },
        {
          id: 'non-failure-sources',
          basis: 'inferred',
          question: '除了失败案例，轨迹里还有哪三类同样有价值的信号？',
          answer:
            '**一、人的修正** —— 审批中的修改/拒绝可作为调查线索，但修正成本和优先级需结合风险、频率与用户影响判断。**二、成功但绕远路** —— 按同一任务类型比较成本和步骤分布尾部，作为候选优化信号，不直接等同于可改善性。**三、重复运行不稳定** —— Pass^k 衡量同一任务 k 次全部成功；有时成功有时失败表示在当前模型、提示词、工具、采样和评测条件下不稳定，不单独证明它位于能力边界，也不证明优化收益最高。应固定任务集与判分标准，区分模型随机性、环境变化、工具故障和评测噪声。',
        },
        {
          id: 'retrieval-trust-boundary',
          basis: 'documented',
          sourceIds: ['owasp-authorization-cheat-sheet', 'owasp-llm-prompt-injection'],
          question: '把检索到的记忆交给模型前，哪些安全边界不能交给模型自行保证？',
          answer:
            '服务端须依据已认证身份和可信租户上下文执行对象级访问控制，不能把向量相似度、不可猜测 ID 或模型生成的过滤条件当授权。检索文档可能包含间接 prompt injection；应把文档作为不可信数据处理。提示词不能形成可靠隔离；应以检索前授权、最小工具权限和写操作服务端重新授权作为边界。参考 OWASP Authorization Cheat Sheet 与 GenAI LLM01:2025 Prompt Injection。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen', 'owasp-authorization-cheat-sheet', 'owasp-llm-prompt-injection'],
    },
    {
      id: 'continuous-evolution/distill-and-test',
      chapterId: 'continuous-evolution',
      slug: 'distill-and-test',
      title: '从失败里提炼规则：历史数据与评测边界',
      summary: '旧实验档案计数与明细冲突，无法独立复核效果；本节补齐规则评估与闭环治理边界。',
      estimatedMinutes: 26,
      difficulty: 'expert',
      hasBody: true,
      status: 'published',
      keywords: ['rule-distillation', 'generalization', 'closed-loop'],
      checkpoints: [
        {
          id: 'distill-no-gain',
          basis: 'inferred',
          question: '现存历史档案能否证明从失败提炼规则带来提升？重新设计评估时要补什么？',
          answer:
            '不能。旧正文记 A 7/7、B 与对照组各 4/4；存档日志却记 A 6/7，并有一条“错”项的可见期望与实际相同。日志没有逐次原始响应、stop_reason、usage、响应标识或 scorer 版本，且当前脚本修改时间晚于日志，不能证明它就是产生日志的版本。当前脚本还会把截断标记拼进输出后继续用子串匹配打分。因此旧分数和“max_tokens 太小导致假发现”的解释都无法独立确认，实验效果未知。新评估应在同一任务集上比较规则组与对照组，保存任务/标签/版本/scorer/完整响应状态，拒绝未完成或协议不符的样本，分开报告代表性主集与定向压力切片，并报告不确定性与未完成数。候选规则先达到预先约定的离线验收标准，再经人工审批和受控发布；命中后结果相关联只能用于诊断，因果效果需匹配比较设计。',
        },
        {
          id: 'distill-dataset-boundary',
          basis: 'inferred',
          question: '这 4 条留出输入能否证明跨格式族泛化？设计日期任务时如何处理歧义标签？',
          answer:
            '不能。四条都未参与规则提炼，但都属于已见的宽泛格式族：日-月-年只换分隔符、年-月-日只换分隔符、紧凑 YYYYMMDD 重复已有模式、英文月份只在缩写与全称之间变化。因此只能检查这些已见格式族内的变体泛化，不能称为格式族隔离评测。日期 scorer 还需先定义顺序、locale 与时区；例如本节固定 fixture 将 12-10-2026 按 DD-MM-YYYY 解释，带时区时间转为 UTC 日期。这个新契约不能反向推断旧请求的提示词。',
        },
        {
          id: 'distill-stop-reason-contract',
          basis: 'documented',
          sourceIds: ['anthropic-stop-reasons', 'anthropic-extended-thinking', 'deepseek-anthropic-api'],
          question: '为什么不能仅凭输出文本或一个 stop_reason 字段判断样本有效？',
          answer:
            'Anthropic 当前 Messages API 文档列出 end_turn、max_tokens、stop_sequence、tool_use、pause_turn、refusal 与 model_context_window_exceeded 等 stop_reason；当前轮 thinking token 计入 max_tokens。评分器还应验证任务协议、完整输出、解析与标签。对 DeepSeek Anthropic-compatible endpoint，应以该 endpoint 当前文档和实际响应验证兼容范围，不能把 Anthropic 所有语义自动推广过去。stop_reason 是必要诊断信息，但不是唯一有效性判据。',
        },
        {
          id: 'distill-promotion-gate',
          basis: 'inferred',
          question: '从规则草案到受控发布，离线评测、人工审批和灰度分别要留下什么证据？',
          answer:
            '离线评测先冻结规则、任务集与 scorer，预先写通过标准，再分别报告代表性主集、目标压力切片和回归集的逐题结果、无效/未完成数、分层指标及不确定性；未通过时保留为草案，不发布。人工审批记录范围、标签质量、副作用、评测结论、审批人及批准/驳回。通过后再做受控发布，记录规则版本、曝光分母、命中与结果指标、停止条件和回滚责任。影子运行可以验证触发与兼容性，不能单独证明用户效果。',
        },
        {
          id: 'closed-loop-boundary',
          basis: 'inferred',
          question: '可验证闭环的边界在哪？为什么说它会「自信地跑偏」？',
          answer:
            '闭环的形态是「运行 → 收集 → 提炼 → 上线 → 再运行」，它有一个隐含假设：**「这次做得对」等于「系统变好了」**。两件事在三种情况下会分开：**一、目标被改写** —— 如果规则本身是错的，闭环会高效地把错误固化下来，而从失败提炼的规则，其质量取决于「失败原因的判断」，那个判断通常也是模型做的；**二、反馈被稀释** —— 如果规则只作用于少量流量，它对总体指标的影响可能被稀释；仍可在命中切片上积累可比较结果。能否回滚取决于是否有版本、开关和责任流程；**三、指标被优化而目标没有** —— 通过率涨了，但涨的是你测的那个通过率，不是用户满意度。所以结论是：**闭环能优化的只有它能观测的东西；对观测不到的部分，它不会保守，它会自信地跑偏。** 三个闸门：规则必须能被人读懂、必须能回滚、必须有独立于它的指标。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen', 'anthropic-stop-reasons', 'anthropic-extended-thinking', 'deepseek-anthropic-api'],
    },
  ],
  resourceIds: ['open-deep-research', 'ai-engineering-huyen', 'anthropic-context-engineering'],
  backendMapping: {
    analogy:
      '持续进化 ≈ 一个不能只靠改配置、还要靠运行数据自我修正的服务：慢是慢的，但停下来就会落后',
    transferable: [
      '线上反馈驱动改进的整套习惯：收集、归因、灰度、回滚',
      '回归测试的思路：改动的风险主要来自副作用，而不是它本身没生效',
      '配置与代码的边界判断：能写死的就别做成可配置的',
    ],
    pitfalls: [
      '只从失败里学，忽略人的修正、成功但绕远路和重复运行不稳定等候选调查信号',
      '把授权与业务不变量只写进提示词，没有在可信执行路径强制检查',
      '不断追加规则却不检查适用范围、冲突、回归和回滚关系',
      '用同一套指标准备优化又用来评价，于是它开始失真',
      '规则上线后没有「命中」信号，看不出有没有用，也无法回滚',
      '在解释「模型没做到」之前不看 stop_reason —— 空输出会被读成能力问题',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-10',
  verifiedAt: '2026-10-10',
} satisfies Chapter;
