import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'evaluation',
  stageId: 'stage-4-production',
  order: 15,
  title: '评估与可观测性',
  subtitle: '先能看见，才能改好',
  summary:
    '没有评估的 agent 项目，改 prompt 就是凭感觉调参。这一章讲怎么把「好」定义成可测的指标、评测集从哪来、用模型打分在什么条件下可信，以及一次失败要怎样才能定位到具体那一轮。',
  outcomes: [
    '能把一个模糊的「效果不好」拆成可测的指标与可复现的用例',
    '能建一套几十条规模就够用的评测集，并说得出它防的是什么',
    '能设计追踪，使一次失败可以定位到具体的轮次与工具调用',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 105,
  tags: ['evaluation', 'observability', 'tracing'],
  prerequisiteIds: ['agent-loop'],
  lessons: [
    {
      id: 'evaluation/define-good',
      chapterId: 'evaluation',
      slug: 'define-good',
      title: '先把「好」定义清楚',
      summary: '「效果不好」不是一个可用的需求，它至少要拆成四个维度。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['metrics', 'success-criteria'],
      checkpoints: [
        {
          id: 'four-dimensions',
          basis: 'inferred',
          question: '一个 agent 系统的「好」，至少要拆成哪几个可测维度？',
          answer:
            '四个：**任务是否完成**（端到端成功率，最重要但粒度最粗）、**中间步骤是否正确**（工具选对了没有、参数对不对）、**成本**（每次任务消耗的 token 与调用次数）、以及**延迟**（首字节与整任务完成时间）。只测第一个会掩盖问题：成功率没变，成本可能翻了三倍；或者成功率提升了但延迟从 3 秒变成 40 秒，体验反而更差。这四个维度要一起看，而且**不要合成一个总分** —— 加权总分会把「哪一项退化了」这个关键信息抹掉。',
        },
        {
          id: 'intent-vs-outcome',
          basis: 'inferred',
          question: '为什么必须分开测「结果对不对」和「过程对不对」？',
          answer:
            '因为它们的修法完全不同，而且**结果对不代表过程对**。一个 agent 可能用错误的工具、绕了三倍的路，最后侥幸得到正确答案 —— 这次成功了，但换一个输入就会失败，而你在结果指标上完全看不出来。反过来，过程正确但结果失败通常指向外部原因（数据缺失、权限问题），不该改 prompt。所以过程指标（工具选择准确率、参数合法率）的价值不是「更严格」，而是**更早发出预警**：它在结果指标还没掉下来的时候就能告诉你系统在变脆。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'claude-agent-sdk'],
    },
    {
      id: 'evaluation/pass-k',
      chapterId: 'evaluation',
      slug: 'pass-k',
      title: 'Pass@k 与 Pass^k：能力和可靠性是两件事',
      summary: '一个看「能不能做对」，一个看「稳不稳」—— k 越大，两者差得越远。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['pass@k', 'reliability', 'ceiling-effect'],
      checkpoints: [
        {
          id: 'at-vs-pow',
          basis: 'inferred',
          question: 'Pass@k 和 Pass^k 分别在测什么？为什么必须一起报？',
          answer:
            'Pass@k 测的是**能力上限** —— k 次里至少成功一次，回答「它到底会不会做」；Pass^k 测的是**可靠性下限** —— k 次全部成功，回答「它稳不稳」。k=1 时两者相等，k 越大差得越远：前者只升不降，后者只降不升。必须一起报的理由很直接 —— **只报 Pass@k 会掩盖失败率**。「Pass@5 有 95%」听起来很好，但如果 Pass^5 只有 60%，意思是每五个用户里就有两个会遇到至少一次失败。它们在规模化时的差距还会被放大：单步 99% 的任务，50 步之后全对率只剩 60.5%。所以低 k 看能力、高 k 看可靠性，两个数字对应两种完全不同的工程动作 —— 能力不足要换模型或改提示词，可靠性不足要加重试、检查点与幂等。',
        },
        {
          id: 'saturated-eval',
          basis: 'inferred',
          question: '评测集跑出来一片绿、Pass@k 与 Pass^k 都是 100%，第一个要怀疑什么？',
          answer:
            '**先怀疑评测集饱和，而不是庆幸模型稳定。** 这是天花板效应：任务太简单，分数顶在 100%，于是任何改动都测不出差异。它的危险在于**静默** —— 评测集不会报错，只会一直给你绿色的勾，直到线上出事你才发现它从来没测到过东西。判断办法是看成功率分布：一批题全对或全错，这批题对该模型就是无效的，你要的是成功率落在 50%~90% 的区间。修法是四条：从**真实失败轨迹**造题（而不是凭空想，因为你能想到的都是模型会做的）、让难度可调（同一个任务做简单/标准/困难三版）、看方差而不只看总分（同题跑五次，是否每次都一致）、以及**给评测集记一个「当前成功率」当监控指标** —— 长期 100% 不是好信号，是该加难度了。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/dataset',
      chapterId: 'evaluation',
      slug: 'dataset',
      title: '评测集从哪来，多小才够',
      summary: '不是先有数据集再开发，而是把失败案例攒起来。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['dataset', 'regression'],
      checkpoints: [
        {
          id: 'where-cases-come-from',
          basis: 'inferred',
          question: '一个刚起步的项目，评测集应该从哪来？',
          answer:
            '按优先级有三个来源。**真实失败案例**（最值钱）：每次线上出问题，把当时的输入原样存下来，修好之后加进评测集 —— 这条闭环能保证你不在同一个坑里摔两次。**边界样本**：你自己能想到的最刁钻的输入（空值、超长、互相矛盾的字段、非目标语言）。**常规样本**：从已有数据里随机抽一批，保证改动没有破坏主流程。注意顺序 —— 很多人反过来，先造一堆常规样本，结果 90% 都通过，剩下的 10% 全是真实案例，而那 90% 从未发现过任何问题。**评测集的价值来自它含有的困难样本比例，不来自它的规模。**',
        },
        {
          id: 'how-big-is-enough',
          basis: 'inferred',
          question: '几十条的评测集真的有意义吗？',
          answer:
            '有，但它能回答的问题有限。**几十条**足以回答「这次改动是变好还是变坏」中的明显情形（成功率从 60% 到 90% 一定看得出来），也足以在 CI 里挡住明显回归。它**不足以**分辨 88% 与 90% 这种细微差别 —— 那种差距需要几百条才能统计上区分开。所以正确用法是分两层：小而快的集合进 CI，每次提交都跑，防的是「明显变坏」；大而慢的集合定期跑，用于做选型与调参决策。另外要警惕一个反效果：**评测集一旦被反复用来调参，就会过拟合**。缓解办法是留一份从不参与调优的留出集，只在做最终判断时打开。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/contamination',
      chapterId: 'evaluation',
      slug: 'contamination',
      title: '数据泄漏与「模型出题」的陷阱',
      summary: '评测集坏了不会报错 —— 它会继续给你绿色的勾。',
      estimatedMinutes: 26,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['contamination', 'leakage', 'synthetic-data'],
      checkpoints: [
        {
          id: 'three-kinds',
          basis: 'inferred',
          question: '数据泄漏有哪三种？自己项目里最危险的是哪一种？',
          answer:
            '三种：**训练集泄漏**（测试题在模型预训练时见过，你基本无能为力，只能靠选新题）、**提示词泄漏**（评测时把参考答案或相似样例放进了上下文，常见于 few-shot 例子与测试集内容重合）、**迭代泄漏**（反复用同一套评测集调参，直到分数好看）。**自己项目里最危险的是第三种** —— 它不需要任何外部条件，只要你有「改一版、跑一下、再改一版」这个循环，它就在发生。危害在于分数此时代表的是「你对这套题的拟合程度」，而不是能力。唯一有效的对抗办法是留一份**从不参与调优的留出集**，只在做最终判断时打开。',
        },
        {
          id: 'generated-questions',
          basis: 'documented',
          sourceIds: ['open-deep-research'],
          question: '让模型批量生成单选题，实测会出哪三个问题？',
          answer:
            '三个都可测。**一、答案分布严重偏斜**：两次独立运行里 B 占 60% 与 73.7%，而 D **一次都没出现**，卡方统计量 16.80 远超临界值 7.81 —— 一个「总是选 B」的策略能拿 70 分。**二、考点高度重复**：名义 19 道题按语义归并后只覆盖 6 个概念（重复率 68%），而且措辞会漂移 ——「中间遗失」「位置偏差」「位置偏见」在字面上是三条，实际是一条。**三、格式并不总是听话**：同样的严格格式要求，一次 8 道里 3 道解析不出答案（62.5% 合规），另一次 20 道里只 1 道不合格（95%）—— 失败率不可复现，所以必须准备解析失败的重试与兜底。结论：模型生成的题只能当**候选池**，准入环节要人工筛、配平答案分布、补齐缺失概念。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/eval-env',
      chapterId: 'evaluation',
      slug: 'eval-env',
      title: '评测环境：分数是「模型 + 环境」的结果',
      summary: '模型答 5 而真实值是 3 —— 错的不是模型，是环境没重置。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['eval-environment', 'state-isolation', 'reproducibility'],
      checkpoints: [
        {
          id: 'five-elements',
          basis: 'inferred',
          question: '一个能复现的评测环境，至少要把哪五件事定清楚？',
          answer:
            '五件：**初始状态**（开始前世界是什么样 —— 不定清楚就会跑出本节那个「第二次结果变了」）、**工具集**（有哪些工具、返回什么格式 —— 换了工具描述就说不清分数变化来自模型还是环境）、**终止条件**（什么算做完了 —— 否则有的跑 3 步有的跑 20 步，成本与成功率都不可比）、**验证器**（判成功的依据 —— 没有它分数不可复现）、**隔离方式**（用例之间怎么互不影响 —— 否则用例顺序会改变结果）。其中**初始状态与隔离方式是工程上最容易漏、后果最严重的两条**：它们不会让评测报错，只会让分数悄悄偏移。',
        },
        {
          id: 'setup-teardown',
          basis: 'inferred',
          question: '为什么 teardown 应该「只检查不修复」？setup 为什么要深拷贝？',
          answer:
            '**teardown 只检查不修复**：如果它顺手帮你把状态重置了，那么忘记调 setup 的用例仍然能跑对 —— 污染被自愈掩盖了。让它只做断言（assert self.state == self.initial），忘记 setup 的代码就会在下一次跑时立刻失败。**让问题暴露比让它自愈更有价值**，因为自愈掩盖的是「你的评测框架有 bug」这个事实。**setup 必须深拷贝**：直接赋值 self.state = self.initial 会让第一次运行改掉 initial 本身，于是第二次的「初始状态」已经不是初始状态了 —— 这是最隐蔽的一类污染，因为它只在跑第二遍时才出现。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/ablation',
      chapterId: 'evaluation',
      slug: 'ablation',
      title: '消融：怎么知道哪个改动真的有用',
      summary: '单独去掉都没事、两个都去掉才掉分 —— 单变量消融会低估。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['ablation', 'interaction-effect', 'attribution'],
      checkpoints: [
        {
          id: 'single-vs-combined',
          basis: 'documented',
          sourceIds: ['open-deep-research'],
          question: '为什么单变量消融会低估组件的价值？',
          answer:
            '**单变量消融会系统性低估**：实测里去掉角色定义、去掉格式要求，各自对约束合规得分的影响都是 0；但**两个一起去掉**分数掉到 7.0，而且掉分那一次明细是 8 8 3 8 8 —— 五次里有一次严重不合格。原因是这两个组件**互为兜底**：只去掉一个时另一个还在起作用，两个都去掉兜底才消失。所以消融必须做成**组合消融**：至少覆盖每个组件单独去掉、以及全部去掉两个端点。第二个发现是去掉约束后**输出 token 反而变长**（2404 → 2872），因为格式要求同时禁止了模型写前言与后记 —— 约束不只是为了好解析，它也在省输出成本。第三条是**重复次数不够会出假阴性**：8 8 3 8 8 如果只跑一次恰好抽到 8，就会得出「完全没影响」的错误结论。',
        },
        {
          id: 'metric-layers',
          basis: 'inferred',
          question: '为什么消融的指标不能只用 0/1 的均值？',
          answer:
            '因为 0/1 的均值丢掉了两种关键信息。**一、失败得有多严重**：8 8 3 8 8 的均值是 7.0，而假设的 7 7 7 7 7 均值也是 7.0，但前者是「四次完美一次崩」、后者是「每次都差一点」—— 前者要查那个偶发坏输入，后者要整体调提示词。**二、失败的频率与尾部**：均值会把偶尔的严重失败平均掉，而生产上你关心的正是尾部 —— 那 20% 的概率完全不合格，比均值掉 1 分严重得多。所以指标至少要分两层：**分级分数**（知道差多少）与**合格率/最小值**（知道多久崩一次）。这也是消融跑完要同时记录 mean 与 min 的原因。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/paired-comparison',
      chapterId: 'evaluation',
      slug: 'paired-comparison',
      title: '配对比较：为什么排名比绝对分可靠',
      summary: '正确率分不出差别时，配对能把任务级噪声消掉 17%。',
      estimatedMinutes: 26,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['paired-comparison', 'sign-test', 'sensitivity'],
      checkpoints: [
        {
          id: 'why-paired',
          basis: 'documented',
          sourceIds: ['open-deep-research'],
          question: '配对比较为什么比绝对比较灵敏？它能消掉哪部分噪声、消不掉哪部分？',
          answer:
            '**配对把任务级的差异消掉，所以更灵敏。** 实测：同 8 个任务上比较两个提示词变体，绝对比较下 A 组标准差 321.0、B 组 625.7，标准误 248.6；配对后看每个任务内部的差值，差值标准差 584.8，标准误 206.8 —— **降到约 83%，即灵敏度提升 17%**。降下来的是「任务本身造成的波动」（优惠券核销天然写得长、发票开具天然写得短），这部分在两组的绝对值里都存在、会互相干扰，做差之后被消掉，只剩同一任务下两个条件的差别。注意它只降 17% 不是降到零，因为任务对改动的敏感度本身也有差异（优惠券核销 B 长 1297、余额提现 B 短 534）。**但配对只整理数据、不给结论**，还要做检验：符号检验 6/8 同向、p≈0.145，**不显著** —— 方向明确但 8 个样本不足以判定。按这个方向性估算，要 p<0.05 约需 15~20 个任务。',
        },
        {
          id: 'write-denominator',
          basis: 'inferred',
          question: '为什么报告分数必须写清分母？本节犯的是一个什么错？',
          answer:
            '因为「7 分」看不出对错。本节的配对实验里每个格子都是 7，我第一反应是「16 次运行全是 7/8，说明有一条约束从未被满足，这不正常」，差点把它当成一个发现写进正文。回去数约束列表才发现那里只有 **7 条**，**7 就是满分**，从头到尾没有任何约束失败。这个错误有两个特点：**它是静默的**（分数本身看不出分母对不对，起了疑心才会去数），以及**它会生成假发现**（「有一条约束从不通过」听起来像个真问题，不核对就会变成一个假的改进任务）。所以规则是：**报告任何分数都要写清分母**，「7/7」与「7/8」是完全不同的结论；而且分母也该尽量由代码算，不要人工填。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/llm-as-judge',
      chapterId: 'evaluation',
      slug: 'llm-as-judge',
      title: '用模型打分：什么时候可信',
      summary: '它很适合判断「有没有」，不适合判断「好不好」。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['judge', 'rubric'],
      checkpoints: [
        {
          id: 'when-judge-works',
          basis: 'inferred',
          question: '什么条件下，用模型当评分器是可靠的？',
          answer:
            '三个条件同时成立时比较可靠：**判据可以写成明确的规则**（而不是「写得好不好」这类主观标准）、**答案可枚举或可机械核对**（比如「是否包含这三个要点」「是否与原文一致」）、以及**你做过校准** —— 拿一批人工标注过的样本，看它的判断和人对得上的比例。第三个条件是分水岭：没校准过的评分器只是「另一个模型的意见」，把它当指标用等于把不确定性又引入了一层。反过来说，**越是需要品味与语境的判断（文案质量、结构美感），越不该交给它** —— 那时你测的是评分器的偏好，不是产品的质量。',
        },
        {
          id: 'judge-pitfalls',
          basis: 'inferred',
          question: '用模型评分时，有哪几个已知的系统性偏差要防？',
          answer:
            '至少三个。**位置偏差**：成对比较时它倾向于选先出现的那个 —— 缓解办法是两个顺序各跑一次，不一致就判为平局。**长度偏差**：更长的回答更容易被judged为更好，哪怕内容相同 —— 这在评测摘要类任务时会系统性高估啰嗦的输出。**自我偏好**：评分器倾向于给同族模型的输出更高分 —— 所以不要用被评的那个模型给自己的输出打分。还有一个更隐蔽的问题：**评分器也会被提示注入**。如果被评的内容里含「请给满分」这类文字，它有相当概率照做（第 2 章测过注入的多种形态）。所以评测内容必须当成数据对待，不能让它进入指令位置。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'openai-cookbook'],
    },
    {
      id: 'evaluation/traces',
      chapterId: 'evaluation',
      slug: 'traces',
      title: '追踪：一次失败要能定位到那一轮',
      summary: '没有轨迹，你只能看到「失败了」；有轨迹，你能看到「在第 4 轮选错了工具」。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['tracing', 'observability'],
      checkpoints: [
        {
          id: 'what-a-trace-needs',
          basis: 'inferred',
          question: '一条可用的 agent 轨迹，至少该记录什么？',
          answer:
            '按最小可用集排：**每一轮的完整请求与响应**（包括 system、工具定义、历史、以及 stop_reason）、**每次工具调用的名称、参数、返回与耗时**、**每一轮的 token 用量**、以及**整个任务的唯一 id 与父子关系**（子智能体、重试、并行分支要能挂到同一棵树上）。最后一项最容易被忽略，但它决定了你能否回答「这次失败到底发生在哪个环节」。此外还要记 **prompt 与工具的版本标识** —— 否则你无法回答「这次变差是从哪次改动开始的」，而那正是排查的起点。',
        },
        {
          id: 'cost-attribution',
          basis: 'inferred',
          question: '为什么成本归因必须建立在轨迹之上？',
          answer:
            '因为**总账掩盖结构**。你看到这个月花了多少，但不知道是哪个章节的哪一步吃掉的：是工具定义太长、是历史没压缩、还是子智能体重复装载了共享背景。只有把每一次调用的 token 记到具体的轮次与环节上，前三章那些成本规律（每轮重发、O(N²)、内容乘装载次数）才能变成可执行的优化动作。一个具体的判据是：**如果你无法回答「这个任务里最贵的三次调用分别是什么」，那你的成本优化就是在猜。**',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openai-agents-sdk-python'],
    },
    {
      id: 'evaluation/confidence',
      chapterId: 'evaluation',
      slug: 'confidence',
      title: '置信区间：1pp 的提升需要多少样本',
      summary: 'p=0.9 时分辨 1pp 要一万四千次 —— 有些实验你根本做不起。',
      estimatedMinutes: 26,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['confidence-interval', 'sample-size', 'wilson'],
      checkpoints: [
        {
          id: 'baseline-matters',
          basis: 'documented',
          sourceIds: ['ai-engineering-huyen'],
          question: '为什么基线成功率会改变所需样本量？差多少？',
          answer:
            '因为**方差是 p(1-p)**。样本量公式里那一项在分子上：n = 4·z²·p(1-p)/delta²。p=0.5 时 p(1-p)=0.25 最大；p=0.9 时是 0.09；p=0.99 时只剩 0.0099 —— 约前者的 1/25，所以所需样本也小约 25 倍。实测：分辨 1pp，p=0.5 要 38,416 次，p=0.9 要 13,830 次，p=0.99 只要 1,522 次。直觉上也能理解：一个 99% 成功率的系统，失败本身很稀有，少数几次失败就能说明分布；而 50% 的系统两种结果各一半，需要更多样本才能确认偏离。这条推论的实用价值是：**基线在 50% 附近时不要指望靠评测看出 1~2pp 的改进**，那种改进要靠机制证据或换指标，而不是刷样本。',
        },
        {
          id: 'how-many-runs',
          basis: 'inferred',
          question: '为什么「跑 20 次全绿」不足以断言成功率 ≥95%？正确数字是多少？',
          answer:
            '因为「平均多久失败一次」和「置信下界」是两件事。我第一版写的是 n = 1/(1-0.95) = 20，思路是「95% 的反面是 5%，所以 20 次里错一次」。但这算的是**平均失败间隔**，而我们要的是「在 5% 的概率下真实成功率仍然低于 95%」这个条件，它是**乘积**关系：0.95^n <= 0.05，解得 n >= ln(0.05)/ln(0.95) = 58.4，即 **59 次**，不是 20 次 —— 差了三倍。这个错误诱人之处在于 20 这个数字「看起来合理」（「跑 20 次全绿就稳了」是常听到的说法），而它把置信要求放松了。判断办法：**凡是「至少需要多少次」的问题，先写出要满足的不等式再解它**，不要凭直觉套除法。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/regression',
      chapterId: 'evaluation',
      slug: 'regression',
      title: '把评测接进开发流程',
      summary: '改一次 prompt 就跑一遍，让「变好」成为一个可验证的主张。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['ci', 'regression', 'ab'],
      checkpoints: [
        {
          id: 'ci-for-prompts',
          basis: 'inferred',
          question: '把评测接进 CI，具体挡的是什么？',
          answer:
            '挡的是**无声退化**。prompt 与工具的改动很容易修好一类输入、弄坏另一类，而在没有回归测试的项目里，后一种情况通常要等到用户投诉才被发现。接进 CI 之后，每次改动都跑一遍小而快的评测集，失败就拦住 —— 这和后端写单元测试的逻辑完全一样。需要注意两点差异：模型输出是**非确定性**的，所以判据要允许一定波动（连续多次运行取稳定结论），不能像断言等于某个值那样严格；以及成本，评测要花钱，所以 CI 里跑的是小集合，大集合放夜间或按需触发。',
        },
        {
          id: 'ab-not-vibes',
          basis: 'inferred',
          question: '怎么避免「我觉得新版更好」这种结论？',
          answer:
            '强制自己用**同一份评测集 + 可复现的对照**。具体做法是：改动前先记录基线（同一个集合、同一个模型、同样的参数），改动后在同一条件下重跑，然后比较逐条的差异，而不是只看总分。逐条差异能告诉你**代价是什么** —— 总分涨了 5% 听起来不错，但如果它涨在容易的样本上、同时弄坏了三个困难样本，这个改动其实是有害的。另外要固定模型版本：很多所谓的「评测结果波动」其实是上游模型静默更新造成的，第 1 章的迁移指南就是为这类问题准备的。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
  ],
  resourceIds: [
    'ai-engineering-huyen',
    'claude-agent-sdk',
    'openai-agents-sdk-python',
    'open-deep-research',
    'twelve-factor-agents',
  ],
  labIds: ['lab-eval-contrast'],
  backendMapping: {
    analogy: '评估 ≈ 单元测试 + APM：一个保证「没变坏」，一个让你在出事时能定位到具体哪一步',
    transferable: [
      '测试金字塔的思路：小而快的进 CI，大而慢的定期跑',
      '可观测性三件套（日志、指标、追踪）在这里的对应物',
      '「先定义指标再优化」的习惯，以及不用总分掩盖分项退化',
    ],
    pitfalls: [
      '只测端到端成功率，掩盖成本与延迟的退化',
      '拿真实用例反复调参，把评测集过拟合掉',
      '使用没做过校准的模型评分器，把它当成客观指标',
      '不记录 prompt 与工具版本，无法回答「从哪次改动开始变差」',
      '把成本只看总数，不做归因',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
