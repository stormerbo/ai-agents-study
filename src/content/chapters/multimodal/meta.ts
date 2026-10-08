import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'multimodal',
  stageId: 'stage-2-primitives',
  order: 8,
  title: '多模态输入',
  subtitle: '让模型看得见',
  summary:
    '前七章都假设输入是文本。但真实任务里有大量信息只存在于图像、PDF、表格与截图里。这一章讲图像怎么进入上下文、它按什么计费、什么时候该用视觉而不是先做文本抽取，以及视觉特有的失败模式该怎么验。',
  outcomes: [
    '能估算一张图或一页 PDF 的 token 成本，并据此做分辨率取舍',
    '能在「先抽文本」与「直接交给视觉」之间给出有依据的选择',
    '能针对视觉抽取设计交叉校验，而不是默认「它看到了就是看对了」',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 95,
  tags: ['vision', 'multimodal', 'documents'],
  prerequisiteIds: ['llm-api-basics', 'structured-output'],
  lessons: [
    {
      id: 'multimodal/how-images-enter-context',
      chapterId: 'multimodal',
      slug: 'how-images-enter-context',
      title: '图像是怎么进入上下文的',
      summary: '它不是附件，是内容块 —— 和文本走同一条通道，按同一套规则计费。',
      estimatedMinutes: 18,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['image-block', 'multimodal-basics'],
      checkpoints: [
        {
          id: 'image-is-a-block',
          basis: 'documented',
          question: '图像在消息里是以什么形式传递的？',
          answer:
            '它和文本一样，是消息 content 数组里的一个**内容块**（类型为 image），而不是一个附带的文件引用。这一点决定了三件事：它可以和文本交错排列（图片前后的文字会影响理解）、它参与对话历史（传过之后每轮都还在）、以及它按内容计费。本站 Playground 的适配层就是按这个模型统一的 —— 内容块是 Anthropic 与 OpenAI 的最小公共上界，图像只是其中一种。',
          sourceIds: ['claude-messages-api'],
        },
        {
          id: 'vision-not-free',
          basis: 'inferred',
          question: '为什么说「多模态几乎免费」是一种误解？',
          answer:
            '因为图像与文本走的是同一套上下文预算。一张高分辨率截图可能比一段很长的文本占得更多，而**它一旦进入历史，之后每一轮都要重新计费一次** —— 第 1 章那条 O(N²) 的算式对图片同样成立。所以在 agent 循环里反复截图，是一个成本模型完全不同的问题：每一轮都在往历史里追加一张图。结论是：视觉输入不是「加个功能」，它改变的是成本结构。设计时先算清楚一张图值多少 token，再决定分辨率与截图频率。',
        },
      ],
      resourceIds: ['claude-messages-api'],
    },
    {
      id: 'multimodal/document-routes',
      chapterId: 'multimodal',
      slug: 'document-routes',
      title: 'PDF 与表格的三条路线',
      summary: '先抽文本、直接交给视觉、或者两者结合 —— 差别不只在效果，更在可验证性。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['pdf', 'ocr', 'parsing'],
      checkpoints: [
        {
          id: 'three-routes',
          basis: 'inferred',
          question: '处理一份 PDF 时，有哪几条路？各自适合什么？',
          answer:
            '三条。一是**纯文本抽取**：PDF 自带文本层就直接取，扫描件则先做 OCR。它便宜、可检索、可 diff，适合以文字为主的合同与报告。二是**整页交给视觉**：能保留版面信息（表格结构、栏位、勾选框、印章），适合版式本身承载语义的文档，比如发票、保单、表单。三是**混合**：先用文本层定位，再对关键页做视觉理解。选择的关键不是「哪个更准」，而是**你的下游需要什么** —— 如果只要几段文字，路线一就够；如果要还原一张表，路线一会丢掉行列关系。',
        },
        {
          id: 'verifiability',
          basis: 'inferred',
          question: '为什么说这三条路的差别「不只在效果，更在可验证性」？',
          answer:
            '因为纯文本路线的中间产物**肉眼可查**：抽出来的文本你能直接读、能 diff、能 grep。而视觉路线的中间产物是模型的内部理解，你只能看最终答案 —— 一旦错了，你没有中间层可以定位。这个区别在工程上很实际：文本路线出错时你能说「是 OCR 把 8 认成了 3」；视觉路线出错时你只能说「它读错了」。所以一条务实的做法是：**能用文本层就先抽文本，把视觉留给你无法用文本表达的那部分** —— 版面、印章、手写。这样至少大部分字段是可核对的。',
        },
      ],
      resourceIds: ['claude-messages-api'],
    },
    {
      id: 'multimodal/resolution-and-cost',
      chapterId: 'multimodal',
      slug: 'resolution-and-cost',
      title: '分辨率、分块与成本',
      summary: '图像 token 是可以估算的，而估算能力直接决定你的取舍。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['cost', 'resolution', 'tokens'],
      checkpoints: [
        {
          id: 'estimate-image-tokens',
          basis: 'inferred',
          question: '怎么估算一张图会占多少 token？不要背数字，说方法。',
          answer:
            '方法是：**看图像被切成多少块**。视觉模型通常先把图像缩放到一个上限尺寸，再按固定大小的块切分，每块折算成固定 token 数，最后加一个固定开销。所以估算的关键变量是**缩放后的面积**，而不是原始文件大小 —— 一张 4000×3000 的图如果被缩到上限，成本和一张刚好等于上限的图是一样的。工程含义有三条：先缩放到必要尺寸再传，多数场景下原图分辨率是浪费；但缩太多会丢掉小字，这是一条真实的取舍线，不是「越小越好」；具体倍数与上限各家不同且会变，**以官方文档的当前口径为准**，不要背教程里的数字。',
        },
        {
          id: 'resolution-tradeoff',
          basis: 'inferred',
          question: '降低分辨率省了成本，代价是什么？该怎么权衡？',
          answer:
            '代价是**密集文本与细节的识别率下降**：小字号、表格线、勾选框、印章这些靠像素区分的内容最先受影响。权衡办法是把它变成一个可测的问题，而不是凭感觉调：拿一份**有标准答案的样本**（比如 20 页有明确字段的发票），在几档分辨率下各跑一遍，看字段级准确率在哪一档开始掉。这个实验通常半小时能做完，比任何经验数字都可靠。另一个容易被忽略的不对称是：**缩放对「找信息」的影响远大于对「判断整体」的影响**。让模型回答「这一页是不是发票」，低分辨率下几乎不受影响；让它读出金额，就必须给足像素。同一份文档的不同任务可以有完全不同的分辨率策略。',
        },
      ],
      resourceIds: ['claude-messages-api', 'claude-pricing'],
    },
    {
      id: 'multimodal/when-vision-fails',
      chapterId: 'multimodal',
      slug: 'when-vision-fails',
      title: '视觉会怎么错',
      summary: '它和文本任务的失败模式不一样，所以校验方式也得不一样。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['failure-modes', 'validation'],
      checkpoints: [
        {
          id: 'vision-failure-modes',
          basis: 'inferred',
          question: '视觉抽取有哪几类典型错误？',
          answer:
            '四类，按可检测程度从高到低。一是**漏读**：表里某一行没被读出来，用「行数对不对」这类结构校验就能发现。二是**串行或串列**：把 A 行的数值读到了 B 行，它比漏读更隐蔽，但用**合计校验**能抓住 —— 各列求和应当与总额一致。三是**幻觉**：读出图里根本不存在的内容，比如声称有盖章而实际没有；这类错误在图像模糊、或模板里有但当前样本缺失该字段时最常出现。四是**单位与精度丢失**：小数点、千分位、货币符号读错。关键在于：**这几类都能用交叉校验发现，而不是靠再看一眼。** 表格用行列合计，金额用「明细之和等于总额」，日期用格式与区间校验。',
        },
        {
          id: 'vision-needs-grounding',
          basis: 'inferred',
          question: '为什么让模型顺便说出「它在图里的哪个位置看到的」能提高可靠性？',
          answer:
            '因为要求给出位置（页码、区域、原文片段）会**迫使它把结论锚定到具体的像素证据上**，而不是从「这看起来像一张发票」直接跳到「金额是某个值」。这和结构化输出那一章是同一个思路：让模型先产出可核对的东西，再由你校验。它也给了你一条排查路径 —— 结果不对时，你可以回到它指的位置看一眼：是它看错了，还是那块区域本身就不清楚。没有这个锚点，你只能重跑一遍然后祈祷。但要诚实：这个方法降低错误率，**不能消除幻觉**，模型完全可能同时编造结论和「证据」。所以它要和交叉校验一起用，不能替代。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'claude-messages-api'],
    },
    {
      id: 'multimodal/vision-in-the-loop',
      chapterId: 'multimodal',
      slug: 'vision-in-the-loop',
      title: '把视觉接进循环',
      summary: '当图像变成工具返回值，成本和上下文管理的问题会一起放大。',
      estimatedMinutes: 18,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['agent-loop', 'context'],
      checkpoints: [
        {
          id: 'images-accumulate',
          basis: 'inferred',
          question: '在 agent 循环里反复产生图像（比如每一步截一张图），最大的工程风险是什么？',
          answer:
            '是**历史累积**。每一步的截图都会留在对话历史里，之后每一轮请求都要把它们全部重新发一遍，于是成本随轮次近似按平方增长，而不是线性。这和子智能体那一节是同一个规律：**成本 = 内容 × 装载次数**。三种缓解手段按代价排序：只保留最近若干张截图；把较早的截图替换成文字摘要；以及把「看图」这一步隔离到子智能体里，它看完只回传结论，原始图像随它的上下文一起消失。第三种最彻底，也最符合第 3 章得出的那条规律。',
        },
        {
          id: 'image-vs-text-tool-result',
          basis: 'inferred',
          question: '工具返回一张图，与返回一段描述它的文本，各自适合什么？',
          answer:
            '**返回图**适合「细节不确定、需要模型自己判断」的场景 —— 比如让它在页面里找一个按钮、判断布局是否异常。你无法预知它要看什么，所以不能提前把图转成文字；代价是 token 与累积成本。**返回文本描述**适合「你明确知道需要哪些信息」的场景 —— 比如只需要页面上某个字段的值。这时先用确定性代码或一次小的视觉抽取调用把图变成结构化文本，再交给主循环，成本低一个量级，而且中间产物可核对。判断依据可以简化成一句：**如果你想不出「让它自己看图能得到什么额外信息」，就不要把图交给它。**',
        },
      ],
      resourceIds: ['anthropic-context-engineering', 'claude-messages-api'],
    },
  ],
  resourceIds: ['claude-messages-api', 'claude-pricing', 'anthropic-context-engineering'],
  backendMapping: {
    analogy: '多模态输入 ≈ 给系统加一种新的请求体类型：走同一条通道、占同一份预算，但多了一层「分辨率」的取舍',
    transferable: [
      '文档处理与版式解析的经验（表单、票据、扫描件）',
      '成本估算的习惯：先算单次成本，再决定频率与分辨率',
      '用交叉校验发现数据错误：合计、格式、区间',
    ],
    pitfalls: [
      '把图像当成「免费附件」：它进入历史后每轮都要重新计费',
      '一上来就整页交给视觉，放弃了可读、可 diff、可 grep 的文本层',
      '以为降低分辨率只有好处，忽略了小字与表格线最先受损',
      '不做交叉校验：视觉错误里最危险的一类（串行串列）肉眼看不出来',
      '在循环里无上限地累积截图',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
