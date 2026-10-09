import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'computer-use',
  stageId: 'stage-2-primitives',
  order: 9,
  title: '计算机使用',
  subtitle: '让模型操作界面',
  summary:
    '有一大类任务没有 API：只能在界面上点。这一章讲清它和函数调用的本质区别 —— 动作是通用原语、观测是截图、而错误是模糊的。同时给出它的失败模式、权限边界，以及「什么情况下你根本不该用它」。',
  outcomes: [
    '能说清计算机使用与函数调用在动作空间、观测与错误反馈上的三点差别',
    '能为一个界面自动化任务设计出「每步重新观测」的循环与停止条件',
    '能判断一个任务该走 API 还是走界面，并给出理由',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 90,
  tags: ['computer-use', 'gui', 'automation'],
  prerequisiteIds: ['tool-calling', 'multimodal'],
  lessons: [
    {
      id: 'computer-use/what-differs',
      chapterId: 'computer-use',
      slug: 'what-differs',
      title: '它和工具调用的三点区别',
      summary: '看起来都是「模型做了个动作」，但三处关键差别决定了它脆弱得多。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['computer-use', 'tool-use'],
      checkpoints: [
        {
          id: 'three-differences',
          basis: 'inferred',
          question: '计算机使用与函数调用，本质差别在哪三点？',
          answer:
            '**动作空间**：函数调用是「调用一个你定义的、语义明确的操作」；计算机使用是「点击坐标 (x, y)、输入字符、滚动」这类**通用原语** —— 语义完全由界面决定，同一个点击在不同页面意味着完全不同的东西。**观测**：函数调用返回结构化结果；计算机使用返回一张截图，需要靠视觉理解才能知道发生了什么。**错误反馈**：函数调用失败会抛异常或返回错误码；界面操作的失败常常表现为**什么都没发生** —— 你无法区分「点错了位置」与「点了但服务端处理慢」。这三点合起来意味着：它比函数调用脆弱一个量级，而且**默认没有可靠的错误信号**。',
        },
        {
          id: 'why-general-purpose-is-harder',
          basis: 'inferred',
          question: '为什么「动作更通用」反而让它更难做对？',
          answer:
            '因为通用动作**丢掉了语义约束，也就丢掉了可校验性**。函数调用里你的工具名和参数已经限定了合法动作，第 4 章那些 poka-yoke 的手段（枚举、互斥参数、拆成两个工具）全都能用上；而「点击坐标」这个动作没有非法值 —— 任何坐标都是合法输入，只是大部分是错的。可校验性的缺失带来两个后果：**出错时无法在动作层拦截**，只能事后从截图判断；以及**重放不安全** —— 同一个坐标在页面变化后指向别的东西。所以工程上要额外补两样东西：动作后的状态校验（下一步截图对不对），以及每步之前重新定位（而不是复用上一次的坐标）。',
        },
      ],
      resourceIds: ['claude-messages-api', 'twelve-factor-agents'],
    },
    {
      id: 'computer-use/observe-act-loop',
      chapterId: 'computer-use',
      slug: 'observe-act-loop',
      title: '观测-动作循环',
      summary: '每一步都必须重新看一遍 —— 这是它和普通 agent 循环最大的差别。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['loop', 'screenshot'],
      checkpoints: [
        {
          id: 'must-reobserve',
          basis: 'inferred',
          question: '为什么界面自动化里，每一步都必须重新截一次图？',
          answer:
            '因为**界面是外部可变状态**，而模型上一步的动作会改变它。三种典型情况都需要新截图：动作生效了但布局变了（弹窗遮住了目标）；动作没生效（点击落在了加载中的空白区）；以及页面自己变了（异步刷新、倒计时跳转）。如果你复用上一次的截图继续推理，模型会基于**已经过期的画面**做决策，而它完全不知道自己看的是旧图。这一点和第 3 章「按需取」的结论相通：**上下文里的信息有保质期**，而在界面场景里这个保质期短到只有一步。',
        },
        {
          id: 'loop-termination',
          basis: 'inferred',
          question: '这个循环的终止条件，和普通 agent 循环有什么不同？',
          answer:
            '多了一道**「看不出进展」**的判断。普通 agent 循环可以靠 stop_reason 判断该不该继续，但界面操作没有这样的协议信号 —— 它只能靠两种外部证据：任务目标是否达成（比如目标按钮已消失、出现成功提示），或者**连续若干步的截图没有实质变化**。后者是关键补充：如果连续三步画面几乎一样，说明循环卡住了，继续下去只是烧钱。所以终止条件通常是三个的组合：达成目标、轮次上限、以及**无进展检测**。第三项在普通 agent 里是可选项，在这里是必需品。',
        },
      ],
      resourceIds: ['anthropic-context-engineering', 'claude-messages-api'],
    },
    {
      id: 'computer-use/failure-modes',
      chapterId: 'computer-use',
      slug: 'failure-modes',
      title: '失败模式',
      summary: '它最典型的失败不是报错，而是「安静地做错」。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['failure-modes', 'reliability'],
      checkpoints: [
        {
          id: 'silent-failures',
          basis: 'inferred',
          question: '界面自动化里最危险的失败形态是什么？',
          answer:
            '**静默做错**：动作执行了、界面也有反应，但作用在错误的元素上。最典型的是**坐标漂移** —— 页面多了一个横幅、字体没加载完、窗口尺寸变了，原本指向「确认」的坐标现在落在「取消」上，而截图看起来一切正常。它比报错危险得多，因为报错会被你的重试逻辑抓住，静默做错会一路走到不可逆的那一步。缓解手段有两个方向：**尽量不用绝对坐标** —— 优先使用可定位的语义目标（元素选择器、可访问性标签、文本锚点），只有在没有别的办法时才退回坐标；以及**在不可逆动作前插入确认点**（下一节展开）。',
        },
        {
          id: 'state-unknown',
          basis: 'inferred',
          question: '「点了但不知道有没有生效」这种情况该怎么处理？',
          answer:
            '这是界面场景里的**状态未知**问题，和第 4 章那个「退款超时、状态未知」是同一类。原则也一样：**不要盲目重试**，因为重试可能造成重复动作（重复下单、重复发送）。正确的顺序是先**观测**再决定 —— 重新截一张图，或调用一个只读的检查（订单列表里有没有这一条）。只有当观测确认「确实没生效」时才重试。如果观测也无法确认（比如结果要等几分钟才出现），就应该停下来交给人工，而不是替用户做选择。要记住的是：这里的默认动作是「问」，而不是「再试一次」。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-messages-api'],
    },
    {
      id: 'computer-use/safety-and-scope',
      chapterId: 'computer-use',
      slug: 'safety-and-scope',
      title: '权限与活动范围',
      summary: '一个能点任何坐标的 agent，等于一个拥有你全部登录态的脚本。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['permissions', 'safety'],
      checkpoints: [
        {
          id: 'scope-definition',
          basis: 'inferred',
          question: '为一个界面 agent 划定活动范围，具体要限制哪些东西？',
          answer:
            '四个维度。**身份**：它用谁的凭据登录 —— 是专用账号还是你的账号？专用账号能把事故半径限制在那个账号的权限内，这是最有效的一道。**站点与页面**：允许访问哪些域名与路径，其余一律拒绝；不要给它一个能导航到任意 URL 的浏览器。**动作类型**：哪些动作是可逆的（搜索、筛选、翻阅），哪些是不可逆的（提交、支付、删除）—— 后者必须走确认。**数据**：它能读到什么、以及读到的东西会不会进入上下文并留在历史里（涉及凭据、个人信息的页面要排除）。这四项里，**身份与动作类型是最小可行集**，先做这两个。',
        },
        {
          id: 'irreversible-actions',
          basis: 'inferred',
          question: '对不可逆动作，确认点应该放在哪一层？',
          answer:
            '放在**代码层，而不是提示层**。也就是：在工具注册表里把「提交表单」「点击支付」这类动作标记为需要确认，由执行层在真正点击之前中断并请求人工放行 —— 而不是在 system prompt 里写一句「涉及支付前请先询问用户」。原因和第 9 章讲的一致：**模型决定下一步做什么，代码决定允不允许。** 把权限判断交给提示，等于让它成为一个可被绕过的约定；浏览器场景里这一点尤其危险，因为页面内容本身可能包含试图影响模型判断的文字（提示注入）。确认点还应当展示**即将执行的原始动作与目标元素**，让人能核对，而不是只给一句「要提交吗」。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk'],
    },
    {
      id: 'computer-use/when-not-to-use',
      chapterId: 'computer-use',
      slug: 'when-not-to-use',
      title: '什么时候别用它',
      summary: '能走 API 就走 API —— 这不是保守，是成本与可靠性的算术。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['trade-offs'],
      checkpoints: [
        {
          id: 'api-first',
          basis: 'inferred',
          question: '为什么「有 API 就别点界面」是一条应当默认遵守的规则？',
          answer:
            '因为界面操作在三个维度上同时更差。**成本**：每次交互要传一张截图，而截图是昂贵的输入；API 调用只传参数。**可靠性**：API 有明确的错误码与幂等语义，界面只有「看起来变了没有」。**速度**：一次界面操作是「截图 → 推理 → 点击 → 再截图」，比一次 HTTP 请求慢一到两个数量级。唯一的例外是**只有界面没有 API**，或者接口需要走一遍人工流程才能拿到（这种情况下界面的价值是自动化那段人工流程）。所以判断顺序应该是：先找官方 API；没有就看有没有非官方但稳定的接口；都没有才考虑界面。',
        },
        {
          id: 'when-gui-is-right',
          basis: 'inferred',
          question: '什么场景下界面自动化是明显正确的选择？',
          answer:
            '三类。**只有界面的老系统**：内部工具、遗留后台、供应商门户，没有 API 也不会给你开。**一次性的迁移或批量操作**：比如把 500 条数据从旧系统搬进新系统，写 API 集成的成本比重放一遍界面操作高得多。**验证类任务**：用真实浏览器确认「用户看到的确实是这样」—— 这类任务的目标本身就是界面，API 返回的数据再多也证明不了渲染正确。共同点是：**任务的价值高于它的低可靠性**，或者**它本来就是一次性的**。如果一个高频、长期、且对可靠性敏感的任务只能靠点界面完成，那更该做的是推动去补一个 API。',
        },
      ],
      resourceIds: ['mcp-docs', 'twelve-factor-agents'],
    },
  ],
  resourceIds: [
    'claude-messages-api',
    'twelve-factor-agents',
    'mcp-docs',
    'anthropic-context-engineering',
    'claude-agent-sdk',
  ],
  backendMapping: {
    analogy:
      '界面自动化 ≈ 用坐标代替接口：动作空间更通用，但没有类型约束、没有错误码、也没有幂等语义',
    transferable: [
      '你写过 UI 自动化测试 —— 等待、重试、选择器稳定性是同一套问题',
      '幂等与「状态未知」的处理经验：先观测再决定，不要盲目重试',
      '权限最小化：专用账号 + 白名单，把事故半径压到最小',
    ],
    pitfalls: [
      '把它当成「另一种工具调用」：它没有可靠的错误信号，失败常常是静默的',
      '复用上一步的截图或坐标继续推理，让模型基于过期画面做决策',
      '用提示词约束不可逆动作，而不是在执行层拦',
      '有 API 却选择点界面，为同一件事多付一到两个数量级的成本',
      '在状态未知时自动重试，造成重复提交',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
