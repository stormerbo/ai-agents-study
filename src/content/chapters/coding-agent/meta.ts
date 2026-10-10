import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'coding-agent',
  stageId: 'stage-5-practice',
  order: 23,
  title: 'Coding Agent',
  subtitle: '唯一自带验证信号的 agent',
  summary:
    'coder agent 是 agent 里最先成熟的形态，因为它有免费的验证信号：编译、测试、类型检查都是二值的。这一章按一次改动的顺序讲四个问题 —— 怎么找到要改的地方、怎么把改动写进去、失败之后怎么重来、以及能执行代码意味着什么。',
  outcomes: [
    '能说清 coding agent 相对其他 agent 的独特优势，以及「有验证信号」不等于「能自动解决」',
    '能按问题类型选择搜索策略，并解释为什么符号索引答不了「谁调用它」',
    '能设计一个带跳出机制的修复循环，并说清验证分层的顺序与各自能拦住什么',
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
      title: '为什么 Coding Agent 是一个分水岭',
      summary: '它是唯一一类自带验证信号的 agent —— 但验证信号不等于自动解决。',
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
            '为什么 coding agent 是「唯一一类自带验证信号」的 agent？这个信号带来哪三个别的 agent 没有的东西？',
          answer:
            '因为代码的对错可以自动判定：编译、单元测试、类型检查全是**二值且无歧义**的。别的 agent 要靠外部判断（客服有没有解决问题要问用户，研究报告好不好要人读），而它跑一下就知道。这个性质带来三样东西：**一、反馈便宜且即时**（不需要人点评，也不需要 LLM-as-judge）；**二、可以自动重试**（「改一版、跑一遍、再改」能完全自动化，这就是 agent 循环最自然的形态）；**三、可以自动构造评测与训练数据**（每个能编译通过的提交都是正样本）—— 这也是 coding 成为 agent 能力最先成熟领域的原因。',
        },
        {
          id: 'verify-not-solve',
          basis: 'documented',
          sourceIds: ['open-deep-research'],
          question:
            '「有测试就能自动判定对错」这句话里藏着什么前提？实测里那个 5 轮没修好的案例说明了什么？',
          answer:
            '前提是**测试本身是对的，而且覆盖了你改的那部分**。实测（5 个 fixture、每个埋一个 bug、最多 5 轮）：4 个修好、1 个 5 轮都没修好，成功率 80%。那个失败案例是「按长度截断字符串」，测试要求省略号算在 n 里，模型一直在「先切再补省略号」这条路上微调，从没转向正确方向。它说明：**有验证信号不等于能自动解决** —— 报错只告诉你「错了」，不告诉你「怎么才对」。把「能自动判定」误读成「能自动解决」，是这一章最容易犯的错。',
        },
      ],
      resourceIds: ['open-deep-research', 'aider'],
    },
    {
      id: 'coding-agent/search-strategy',
      chapterId: 'coding-agent',
      slug: 'search-strategy',
      title: '搜索：在大仓库里找到那一处',
      summary: 'grep 省一半 token 且正确率不掉；符号索引最省，但答不了「谁调用它」。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['code-search', 'grep', 'symbol-index', 'context-budget'],
      checkpoints: [
        {
          id: 'search-by-question-type',
          basis: 'documented',
          sourceIds: ['aider'],
          question: '三种上下文组织方式（全文、grep 命中行、符号索引）各适合回答什么类型的问题？',
          answer:
            '实测：全文 4/4 正确、763 token；grep 命中行 4/4 正确、405 token（**省 47% 且正确率不掉**）；只给符号索引 3/4 正确、323 token（最省但漏了一题）。漏的那题是「谁调用了 compute_total 但没传 with_tax」—— 符号索引里只有 `def` 行，没有任何调用信息。所以判据是问题类型：**定义在哪、有哪些符号** → 符号索引就够；**谁调用它、改动影响范围** → 必须有引用信息（grep 或 AST 反向索引）；**这段逻辑怎么实现** → 要读源码正文。先确定问题类型，再决定取什么。',
        },
        {
          id: 'index-partial',
          basis: 'inferred',
          question:
            '为什么搜索工具必须区分「找到了 0 条」和「搜索失败了」？索引器为什么必须能部分成功？',
          answer:
            '因为两者的后续动作完全不同：**0 条命中**要换关键词或扩大范围，**搜索失败**要修工具。混在一起会让 agent 走上完全错误的路径 —— 它拿到空索引，会以为「仓库里没有这个符号」。我的第一版 `build_index` 直接 `ast.parse` 而没有 try/except，遇到一个语法错的文件就整个崩掉，搜索退化成「什么也没找到」，**而它不报错给用户**。真实仓库里总有解析不了的文件（生成的代码、模板、不支持的语法版本），所以索引器必须跳过它们继续工作。这类失败的共同形态是：**基础设施坏了，但表现得像「查无此物」。**',
        },
      ],
      resourceIds: ['aider', 'openhands'],
    },
    {
      id: 'coding-agent/file-editing',
      chapterId: 'coding-agent',
      slug: 'file-editing',
      title: '文件编辑：为什么模型总改错',
      summary: '给全文 80%、只给片段 0% —— 差别只在信息可得性。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['patch', 'exact-match', 'edit-strategy'],
      checkpoints: [
        {
          id: 'exact-match-failures',
          basis: 'documented',
          sourceIds: ['aider'],
          question: '精确匹配替换（old_string / new_string）有哪两种失败模式？实测的成功率如何？',
          answer:
            '两种：**匹配 0 次**（原文在文件里不存在 —— 模型凭记忆编造的）和**匹配多次**（old_string 太短太通用，可能改错位置）。三组实测：小文件无重复时 **8/8 全对**；83 行、8 个近乎相同 handler 的文件，**给全文时 4/5 = 80%**（一次因 JSON 解析失败）；**只给文件开头片段时 0/5 = 0%** —— 失败明细是「匹配 0 次」「匹配 1879 次」「JSON 解析失败」。从 80% 掉到 0，唯一的差别是给不给逐字符的原文。所以执行器必须检查「匹配数恰为 1」，不满足就拒绝，并把实际匹配数告诉模型。',
        },
        {
          id: 'edit-strategy-choose',
          basis: 'inferred',
          question: '几种编辑策略（精确替换、整文件重写、按行号替换、结构化编辑）各有什么取舍？',
          answer:
            '**精确匹配替换**：省 token、改动最小、diff 直观，是 Claude Code / Aider 的主流选择；代价是上面那两条失败模式。**整文件重写**：永远不会「匹配不上」，但模型必须复现它没改的部分，长文件上极易引入无关改动且 token 成本高 —— 只在很短的文件（约 100 行以内）用。**按行号替换**：省 token，但**行号会随编辑漂移**（同一轮改了前面一处，后面全错），只适合「每轮只改一处、改完立即重算行号」。**结构化编辑（AST 替换）**：最稳、不受格式影响，但要求语言有可用解析器，且对注释与格式无能为力。务实组合：默认精确替换，匹配失败时降级到整文件重写，并记录降级率作为健康指标。',
        },
      ],
      resourceIds: ['aider', 'openhands'],
    },
    {
      id: 'coding-agent/error-recovery',
      chapterId: 'coding-agent',
      slug: 'error-recovery',
      title: '验证与恢复：报错之后该给它什么',
      summary: '修好的四个 fixture 全都用了 2 轮 —— 一次成型不现实。',
      estimatedMinutes: 26,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['error-recovery', 'retry', 'verification-layers'],
      checkpoints: [
        {
          id: 'why-two-turns',
          basis: 'documented',
          sourceIds: ['openhands'],
          question: '为什么修好的四个 fixture 全都恰好用了 2 轮？这对 agent 设计意味着什么？',
          answer:
            '因为模型第一次只能看到报错**文字**，它得先从报错反推出「测试到底期望什么」，才发现第一次改的方向不对。举一个具体的：`average([])` 报 `ZeroDivisionError`，模型第一次改成 `sum(nums) / max(len(nums), 1)`（掩盖了问题），第二条断言才让它改对。**所以「一次成型」在 coding agent 上不现实** —— 这不是模型不够强，而是任务的信息结构决定的：报错只提供部分信息，隐藏约束要靠一次失败的尝试才暴露。这也是为什么这一章的重点不在「怎么让模型写出代码」，而在**改完之后怎么验证、失败之后怎么重来**。',
        },
        {
          id: 'verification-layers',
          basis: 'inferred',
          question: '验证为什么要分层？哪一层最容易被漏、为什么它在 agent 场景里特别重要？',
          answer:
            '五层：**语法**（能不能解析，极低）、**类型**（接口有没有用错，低）、**单测**（行为对不对，中）、**改动范围**（只改了预期的文件吗，极低）、**端到端**（整体还跑得通吗，高）。**第 4 层最容易被漏，但在 agent 场景里特别重要** —— 因为 agent 很容易顺手改掉别的东西。判据很简单：对比 diff，如果出现了任务没要求的文件就应该停下来问。它是所有层里最便宜、又能拦住最危险情况的一层。另外恢复能力的上限由测试覆盖率决定：测试没覆盖到的地方，循环拿到的是「通过」，于是错误改动被当成成功 —— 这是最危险的失败形态，因为它看起来完全成功。',
        },
      ],
      resourceIds: ['openhands', 'aider'],
    },
    {
      id: 'coding-agent/safety',
      chapterId: 'coding-agent',
      slug: 'safety',
      title: '安全边界：能执行代码意味着什么',
      summary: 'pytest 会执行仓库里的 conftest.py —— 按命令名做白名单无效。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['sandbox', 'command-allowlist', 'exfiltration'],
      checkpoints: [
        {
          id: 'allowlist-useless',
          basis: 'documented',
          sourceIds: ['openhands'],
          question: '为什么「按命令名做白名单」挡不住任何东西？实测是怎么证明的？',
          answer:
            '因为有些命令的语义本身就是「运行这个仓库里的代码」：`pytest` 会加载 `conftest.py`、`npm test` 会执行 `package.json` 里的 scripts、`make` 会执行 `Makefile`、`cargo test` 会编译并运行 `build.rs`。实测：一个只有 `conftest.py`（内容是写一个标记文件）和 `test_demo.py` 的仓库，运行被白名单放行的 `pytest`，输出 `1 passed` 且正常退出，**但标记文件出现了** —— 任意代码被执行，且整个过程没有任何异常。所以白名单的粒度必须是**隔离级别**（进程、文件系统、网络），而不是命令名。',
        },
        {
          id: 'four-boundaries',
          basis: 'inferred',
          question: '防护的四条边界是什么？风险有哪三个方向？',
          answer:
            '四条边界**叠加使用，不是四选一**：**进程边界**（容器/bubblewrap/低权限用户，保护命令能碰到宿主机的什么）、**文件系统边界**（只挂载要改的目录，凭据目录不进容器 —— 这是防外泄最有效的一层）、**网络边界**（默认禁出网，按域名白名单放行，专治外泄与供应链）、**审批边界**（不可逆动作要人工确认 —— 注意第 19 章的实测：按可逆性审批 2 次打断 0 漏网，按危险程度审批 1 次打断 1 漏网）。风险三个方向：**破坏**（最显眼所以最容易被规则拦住）、**外泄**（最危险 —— 能读 `.env` 又能发网络请求，两者合起来就是外泄；而且不需要说服模型，仓库里的一段代码就能做到）、**供应链**（最频繁 —— agent 装包不会犹豫）。另外：隔离环境要显式清空凭据类环境变量，一个 `print(os.environ)` 就能外泄。',
        },
      ],
      resourceIds: ['openhands', 'deer-flow'],
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
      '以为「小改动很简单」—— 实测最简单的 bug 也要 2 轮，因为 agent 要先重建世界图景',
      '以为「有测试就能自动修好」—— 实测有一个案例 5 轮都在同一个方向上打转',
      '以为「按命令名做白名单就安全」—— pytest 会执行仓库里的 conftest.py',
      '给它看文件片段就让它改 —— 实测精确匹配成功率从 80% 掉到 0%',
      '只跑测试不检查改动范围，于是它顺手改了别的文件而你没发现',
      '把报错原样丢回去而不说「你试过什么」，于是它在同一个局部最优里反复打转',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-10',
  verifiedAt: '2026-10-10',
} satisfies Chapter;
