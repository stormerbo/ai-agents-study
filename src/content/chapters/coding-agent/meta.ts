import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'coding-agent',
  stageId: 'stage-5-practice',
  order: 23,
  title: 'Coding Agent',
  subtitle: '用代码检查形成反馈，但检查信号不等于正确性',
  summary:
    'coding agent 可以利用编译、测试、类型检查等机器反馈迭代代码；这些信号是否可靠取决于检查器、覆盖场景和运行环境。本章按一次改动的顺序讲定位、编辑、验证恢复与执行安全。',
  outcomes: [
    '能说明 coding agent 如何利用机器检查形成部分反馈，以及「检查通过」不等于「需求已正确实现」',
    '能按问题类型选择搜索策略，并解释为什么符号索引答不了「谁调用它」',
    '能设计有次数上限、会验证最终候选并区分 runner 故障的修复循环；能按风险组合不同验证',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 120,
  tags: ['coding-agent', 'code-editing', 'verification'],
  prerequisiteIds: ['agent-loop', 'tool-calling'],
  lessons: [
    {
      id: 'coding-agent/why-coding-agent',
      chapterId: 'coding-agent',
      slug: 'why-coding-agent',
      title: 'Coding Agent 为什么值得单独看',
      summary: '部分代码约束可由机器检查，但测试信号不等于需求完整或修复正确。',
      estimatedMinutes: 22,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['coding-agent', 'verification', 'feedback-loop'],
      checkpoints: [
        {
          id: 'why-linear-ok',
          basis: 'inferred',
          question:
            '编译、类型检查和测试能给 coding agent 什么反馈？为什么不能把它们当成完整正确性证明？',
          answer:
            '这些检查可以对已编码约束提供可重复的部分反馈，支持有预算和权限限制的迭代；其成本和确定性取决于 runner、测试与外部依赖。通过只说明本次执行的检查通过，不能证明需求被完整表达、断言正确、未覆盖行为安全，也不能自动把提交作为训练正例。',
        },
        {
          id: 'verify-not-solve',
          basis: 'inferred',
          question:
            '「测试通过」能证明什么？历史恢复摘要为什么不能证明模型成功率或修复轮数？',
          answer:
            '测试通过只表明当前 runner 执行的断言通过。历史摘要的 `truncate` 夹具有语法错误，且没有逐次 provider 响应；另外提示从第一轮就包含完整测试，循环数字计的是测试迭代。它不能支持 4/5 模型成功率、五轮不收敛或隐藏约束依靠先失败才暴露等结论。应先验证夹具、runner 和失败分类，再评估模型行为。',
        },
      ],
      resourceIds: ['open-deep-research', 'aider', 'anthropic-demystifying-evals'],
    },
    {
      id: 'coding-agent/search-strategy',
      chapterId: 'coding-agent',
      slug: 'search-strategy',
      title: '搜索：在大仓库里找到那一处',
      summary: '检索上下文要匹配问题；定义索引、调用点和源码实现回答的是不同问题。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['code-search', 'grep', 'symbol-index', 'context-budget'],
      checkpoints: [
        {
          id: 'search-by-question-type',
          basis: 'inferred',
          question: '为什么一次 fixture 的全文、grep 加定义列表、定义列表对照不能证明 grep 普遍更准确或更省？索引缺少什么信息时无法回答调用问题？',
          answer:
            '历史单次 fixture 摘要为全仓文本 4/4、定义列表加 grep 调用行 4/4、只有函数定义列表 3/4；判分基于答案是否为输出子串，原始响应未保留，不能估计准确率，也不能单独归因于 grep。应按问题提供定义位置、词法调用候选、依赖信息或相关源码；定义列表本身没有调用记录。简单 AST 索引也可能受别名、动态分派和同名属性影响，不能声称完整调用图。固定窗口要先过滤无效行号再限额，避免过期候选挤掉有效上下文。',
        },
        {
          id: 'index-partial',
          basis: 'inferred',
          question:
            '为什么搜索工具必须区分零命中、部分文件未索引和搜索失败？部分索引怎样把诊断传给调用者？',
          answer:
            '区分**零命中、部分文件未索引、搜索失败**：零命中可换词或扩大范围，部分索引要检查解析诊断，搜索失败则修工具。原教学实现遇到 SyntaxError 会整体抛错；修订后的索引应继续处理其它文件，并返回被跳过的路径和行号，不能把未索引文件伪装成“没有此符号”。',
        },
      ],
      resourceIds: ['aider', 'openhands'],
    },
    {
      id: 'coding-agent/file-editing',
      chapterId: 'coding-agent',
      slug: 'file-editing',
      title: '文件编辑：为什么模型总改错',
      summary: '文件编辑结果取决于提案协议、定位方式和验证；历史小样本不能外推为成功率。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['patch', 'exact-match', 'edit-strategy'],
      checkpoints: [
        {
          id: 'exact-match-failures',
          basis: 'inferred',
          question: '精确匹配替换（old_string / new_string）有哪些必须处理的失败模式？历史小样本能支持什么结论？',
          answer:
            '精确替换至少要处理零次匹配、多次匹配、重叠子串和空字符串；Python `str.count` 不计重叠，不能单独证明唯一定位。执行器应逐字符起点检查，并在非唯一时拒绝。历史 fixture 日志记为 8/8、4/5、0/5，但样本小、条件不同且无原始响应，不能外推成功率或证明全文上下文导致差异。日志中的 1879 次与长度约 1878 字符的文件上空字符串计数吻合，强烈暗示 old_string 为空；因原始响应缺失，这仍是推断。',
        },
        {
          id: 'edit-strategy-choose',
          basis: 'inferred',
          question: '几种编辑策略（精确替换、整文件重写、按行号替换、结构化编辑）各有什么取舍？',
          answer:
            '精确匹配、整文件输出、按行插入、diff 与 AST/CST 编辑各有格式保真、定位和输出成本上的取舍。不同工具实现不同；选择取决于任务范围、语言支持和执行器保证。无论采用何种方式，都检查协议、目标范围、实际 diff 和风险相关验证；历史 8/5/5 小样本不足以比较这些策略。',
        },
      ],
      resourceIds: ['aider', 'openhands'],
    },
    {
      id: 'coding-agent/error-recovery',
      chapterId: 'coding-agent',
      slug: 'error-recovery',
      title: '验证与恢复：报错之后该给它什么',
      summary: '历史修复摘要含有语法错误的测试夹具，不能据此估算模型修复成功率。',
      estimatedMinutes: 26,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['error-recovery', 'retry', 'verification-layers'],
      checkpoints: [
        {
          id: 'audit-recovery-measurement',
          basis: 'inferred',
          question: '为什么不能把历史日志里的 4/5 和“平均 2 轮”当成可靠模型效果？',
          answer:
            '脚本里“截断文本”的测试断言有多余右括号，测试自身无法解析；因此该失败不能计为模型修复失败。提示从首轮就包含测试文本，不支持“隐藏约束要先试错才暴露”的解释；循环的 `turn=2` 是第二次验证通过，不代表调用模型两次。脚本和日志没有保存逐次 provider 响应，不能还原其它案例的改动方向。结论是历史汇总不能用于估计成功率或重试收益；应检查测试夹具与 runner，并区分提案次数、验证次数和失败类型。',
        },
        {
          id: 'verification-layers',
          basis: 'inferred',
          question: '验证为什么要分层？哪一层最容易被漏、为什么它在 agent 场景里特别重要？',
          answer:
            '按风险选择语法/静态检查、类型与构建、单测、diff 范围、集成/端到端与人工审查。没有对所有项目都最优的固定顺序或统一成本等级。diff 检查能发现意外文件和越界变更，但应根据任务预先定义允许范围，不能因文件多就默认拒绝。测试通过只证明已执行断言通过；覆盖范围、断言质量、规格正确性和环境有效性都需要分别判断。',
        },
      ],
      resourceIds: ['openhands', 'aider'],
    },
    {
      id: 'coding-agent/safety',
      chapterId: 'coding-agent',
      slug: 'safety',
      title: '安全边界：能执行代码意味着什么',
      summary: '运行测试、构建与安装命令可能执行仓库或依赖代码；命令白名单不能替代按配置验证的 OS 隔离。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['sandbox', 'command-allowlist', 'exfiltration'],
      checkpoints: [
        {
          id: 'allowlist-useless',
          basis: 'documented',
          sourceIds: ['pytest-plugins', 'npm-scripts', 'cargo-build-scripts'],
          question: '为什么仅按命令名做白名单不足以约束会加载仓库代码的命令？这次复核能证明什么、不能证明什么？',
          answer:
            'pytest 官方文档说明测试路径上的 conftest.py 会作为插件加载；Cargo 会在构建 package 前运行 build.rs；npm test 会按 npm 的 scripts/lifecycle 规则运行项目声明的脚本及相关钩子。它们说明这些命令可能执行仓库代码，具体行为仍取决于路径、配置、版本与生命周期。Python 3.14.7 + pytest 8.4.2 的隔离临时仓库复核得到 1 passed，并观察到 conftest 写出 marker；这复现了该版本下的机制，不是对 2026-10-10 历史环境或日志的重放。结论限定为：命令名 allowlist 单独不足以约束这类命令的全部副作用，仍需由 OS/容器实施资源边界。'
        },
        {
          id: 'four-boundaries',
          basis: 'inferred',
          question: '防护的四条边界是什么？风险有哪三个方向？',
          answer:
            '风险方向可用破坏、外泄、供应链梳理，但它们是威胁建模分类，不是穷尽集合或频率/严重性排序。防护按任务组合：进程与资源限制、文件系统最小挂载、默认禁网并用受控代理、外部副作用审批/独立授权。容器、域名 allowlist、环境变量 denylist 与人工审批均不自动构成安全边界，必须检查真实执行配置。第 19 章的数据是有限合成任务观察，不能推出 coding agent 的普遍审批效果。pip 官方资料指出安装发行包涉及任意代码执行，并建议哈希校验等加固；Docker 文档也警告宿主目录挂载会授予访问权且默认配置可能隔离不足。'
        },
      ],
      resourceIds: ['pytest-plugins', 'npm-scripts', 'cargo-build-scripts', 'docker-engine-security', 'pip-secure-installs', 'python-subprocess'],
    },
  ],
  resourceIds: ['aider', 'openhands', 'open-deep-research', 'twelve-factor-agents'],
  backendMapping: {
    analogy:
      '让 agent 改代码 ≈ 让一个手很快但记不住文件的同事改你的仓库：他能干，但你必须给他测试、给他边界、并且 review 他的每一处改动',
    transferable: [
      '读代码、定位、改、跑测试、提交 —— 这套动作你本来就在做，差别只在谁的手在动',
      '编译与测试作为反馈信号：你熟悉的 CI 那套，在 agent 场景里就是它的感知器官',
      '代码评审的习惯：判断「这个改动该不该在这个文件里」的能力直接可迁移',
    ],
    pitfalls: [
      '把测试通过、历史轮数或覆盖率单独当成修复正确性的证明',
      '把未经筛选的命令输出原样塞回提示，可能泄露敏感值或混入不可信指令',
      '把 pytest 命令名加入白名单就当作隔离；应检查测试路径中会加载哪些 conftest.py，并由执行环境限制其权限',
      '把一次小样本的全文/片段对照当成普遍成功率或因果结论',
      '只跑测试不检查改动范围，于是它顺手改了别的文件而你没发现',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-22',
  verifiedAt: '2026-10-10',
} satisfies Chapter;
