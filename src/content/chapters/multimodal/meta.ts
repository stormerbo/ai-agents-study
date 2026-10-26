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
      summary: '图像按 provider-specific 协议进入消息；request bytes、视觉 token、上下文与账单要分别核对。',
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
            '多个 API 都支持图像输入，但 block 形状与传输模式由 provider/API 决定。DeepSeek Anthropic-compatible /messages 使用 image block；OpenAI-compatible Chat Completions 使用 image_url，Responses API 使用 input_image。客户端提交完整历史时，保留在历史中的图像会影响上下文；Files API file_id 与服务端会话可能改变重传字节的方式。不要把 token volume、请求字节与账单混为一谈。',
          sourceIds: ['deepseek-vision', 'deepseek-anthropic-api'],
        },
        {
          id: 'deepseek-vision-token-boundary',
          basis: 'documented',
          sourceIds: ['deepseek-vision', 'deepseek-image-token-usage'],
          question: 'DeepSeek 当前文档如何估算单图 token，实际用量以什么为准？',
          answer:
            '当前 Vision 文档称图像会按像素缩放：总像素低于约 544×544 时放大，较大时缩放到约 1300×1300 的总像素规模，每张图上限 1024 tokens；Token Usage 文档说明这是估算，实际处理量可能略有差异，应以 API 响应的 usage 为准。该边界仅适用于当前文档所述 DeepSeek API，不可外推到其他 provider 或历史端点。',
        },
        {
          id: 'vision-not-free',
          basis: 'inferred',
          question: '为什么说「多模态几乎免费」是一种误解？',
          answer:
            '图像会影响模型上下文与请求用量，但实际请求体、token volume 和费用取决于会话如何传递历史、是否使用 file_id/缓存，以及目标 API 的计量规则。客户端每轮附带完整历史时，新增消息会使输入量随轮次增加；旧图片是否重复传输及如何计费需按 API 验证。先从目标 provider 获取估算与 usage，再用任务质量决定截图分辨率和频率。',
        },
      ],
      resourceIds: ['deepseek-vision', 'deepseek-anthropic-api', 'deepseek-image-token-usage', 'deepseek-context-caching', 'owasp-ssrf-prevention'],
    },
    {
      id: 'multimodal/document-routes',
      chapterId: 'multimodal',
      slug: 'document-routes',
      title: 'PDF 与表格的三条路线',
      summary: '围绕 endpoint 能力、目标字段与可验证性选择 PDF 输入路线；不把单次历史摘要外推为通用成本或准确率。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['pdf', 'ocr', 'parsing'],
      checkpoints: [
        {
          id: 'anthropic-pdf-input-methods',
          basis: 'documented',
          sourceIds: ['anthropic-pdf-support'],
          question: 'Anthropic Messages API 官方文档列出了哪些 PDF 输入方式？',
          answer:
            '当前文档列出 URL 引用、base64 编码的 document block 与 Files API file_id 三种方式；这只描述 Anthropic API 的文档契约，不代表兼容 endpoint 或其他 provider 支持相同能力。',
        },
        {
          id: 'three-routes',
          basis: 'inferred',
          question: '处理一份 PDF 时，有哪几条路？各自适合什么？',
          answer:
            '常见表示包括：目标 API 支持的 PDF document block、由 PDF 页面渲染出的图像、以及从同一 PDF 抽取的文本；还可组合文本定位与关键页视觉处理。支持情况要按 provider、模型和 endpoint 文档核实。选择取决于下游字段、版面依赖与可验证性；文本抽取可能改变阅读顺序，图像处理也可能漏读，须用结构化字段、业务不变量和来源片段评估。历史 59/337/123 token 摘要及旧评分没有完整请求、响应和 scorer，不能据此推出通用成本或准确率。',
        },
        {
          id: 'verifiability',
          basis: 'inferred',
          question: '为什么说这三条路的差别「不只在效果，更在可验证性」？',
          answer:
            '两类路线都应保留可检查的中间证据：文本路线可归档抽取文本、页码与 parser 版本；视觉路线可保留原始页面、渲染参数、模型响应和引用片段。它们让排查更具体，但不自动证明抽取完整或答案正确。应用应检查终态、必需字段与结构化校验，再用可信来源或人工审批核对高风险值；具体选择需按文档族与目标 endpoint 实测。'
        },
      ],
      resourceIds: ['claude-messages-api', 'anthropic-pdf-support']
    },
    {
      id: 'multimodal/resolution-and-cost',
      chapterId: 'multimodal',
      slug: 'resolution-and-cost',
      title: '分辨率、分块与成本',
      summary: '用目标 API 的实际 usage 与任务质量门槛，决定是否缩放、压缩或裁块。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['cost', 'resolution', 'tokens'],
      checkpoints: [
        {
          id: 'estimate-image-tokens',
          basis: 'documented',
          sourceIds: ['deepseek-vision', 'deepseek-image-token-usage', 'claude-vision'],
          question: '怎么估算图像成本，为什么不能使用跨 provider 通用阈值？',
          answer:
            '先确认具体 endpoint、API 模式与 model id，再采用对应官方图像文档/估算器做预算；记录响应 usage 并与账单校准。DeepSeek 当前 Vision 文档描述其按像素缩放、单图估算上限；Claude Vision 文档按 28×28 patch 估算 visual tokens 并按模型档位设置限制。两者规则不同，不能互相外推，也不能用请求字节大小代替视觉 token。历史 186/996 摘要没有完整原始响应和重复测量，不作为当前阈值。',
        },
        {
          id: 'resolution-tradeoff',
          basis: 'inferred',
          question: '降低分辨率的代价是什么，如何决定何时裁块？',
          answer:
            '低分辨率可能损害小字、密集表格和坐标任务，但质量下降点取决于图像、任务、模型和预处理，不能仅由一次实验断言。先预设字段级质量门槛，用固定提示词和同一批标注图像做配对测试；每次只改变尺寸或压缩参数，并记录重复结果、响应 model、finish_reason、usage、延迟及错误样例。若关键区域因整图缩放不可读，再测试带页码/坐标标签的裁块。裁块增加请求和图像输入成本；只有达到质量门槛且其增益抵得过成本时才采用。',
        },
      ],
      resourceIds: ['deepseek-vision', 'deepseek-image-token-usage', 'claude-vision', 'claude-pricing'],
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
          question: '视觉抽取出现错误时，哪些校验可以发现，哪些不能？',
          answer:
            '常见失败包括漏项、行列错位、单字符替换、单位/精度错误和无依据补全。按层验证：schema/行数能发现部分缺项与格式错误；范围、总额等业务不变量能发现部分矛盾；与独立原始信源核对可发现更多合法但错误的值。每层都有盲点：总额也由同一视觉结果提取时，误读可能相互抵消；合法数字替换可同时通过 JSON、类型和范围检查。把失败状态、精确字段误差和独立核验结果分别记录，高风险字段再加入人工复核。',
        },
        {
          id: 'vision-needs-grounding',
          basis: 'inferred',
          question: '要求视觉结果附页码、区域或证据片段有什么作用，边界是什么？',
          answer:
            '位置、页码或短片段能帮助人和下游程序定位原图中的待检查区域，便于审阅和错误分类；它们不会迫使模型真正依据该区域作答，也不能证明答案正确。模型可能同时编造字段与看似合理的位置。把定位信息当作导航线索，与原始像素或可信文档文本独立核对；用标注样本评估定位准确率和字段准确率，而不是假定提供理由就能降低错误率。',
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
          id: 'openai-response-chain-input-billing',
          basis: 'documented',
          sourceIds: ['openai-conversation-state'],
          question: '使用 OpenAI Responses API 的 previous_response_id 是否免除历史输入 token 计量？',
          answer:
            'OpenAI 当前对话状态文档明确说明，即使使用 previous_response_id，响应链中先前的 input tokens 仍按 input tokens 计费。这是 OpenAI Responses API 的计量边界，不证明其他 provider 或图像块采用相同的状态、计量或计费方式。',
        },
        {
          id: 'images-accumulate',
          basis: 'inferred',
          question: '在 agent 循环里反复产生图像（比如每一步截一张图），最大的工程风险是什么？',
          answer:
            '风险之一是**历史累积**：如果客户端每轮都重发完整对话，先前图像可能再次进入请求上下文；请求/服务端状态、文件引用、缓存策略会改变重传内容、延迟和账单，需按目标 provider 实测。可按任务保留必要图像、摘要旧观察或把视觉步骤隔离；这些是需评估的设计选项，不保证降低特定 endpoint 的实际费用。',
        },
        {
          id: 'image-vs-text-tool-result',
          basis: 'inferred',
          question: '工具返回一张图，与返回一段描述它的文本，各自适合什么？',
          answer:
            '**返回图像**适合需要保留原始视觉证据、且模型需判断版面或视觉状态的任务；**返回文本或结构化结果**适合字段明确、可通过规则校验的任务。两者质量、延迟和成本取决于图像预处理、上下文设计、provider 与 usage，不能预设固定倍数。文本抽取也会丢失未表达的版面信息；保留可追溯的原图引用和抽取证据，按代表性任务配对评估。',
        },
      ],
      resourceIds: ['anthropic-context-engineering', 'claude-messages-api', 'openai-conversation-state'],
    },
  ],
  resourceIds: ['claude-messages-api', 'claude-pricing', 'anthropic-context-engineering'],
  labIds: ['lab-vision-extract'],
  backendMapping: {
    analogy:
      '多模态输入 ≈ 给系统加一种新的请求体类型：走同一条通道、占同一份预算，但多了一层「分辨率」的取舍',
    transferable: [
      '文档处理与版式解析的经验（表单、票据、扫描件）',
      '成本估算的习惯：先算单次成本，再决定频率与分辨率',
      '用交叉校验发现数据错误：合计、格式、区间',
    ],
    pitfalls: [
      '把图像当成「免费附件」：客户端若每轮重发完整历史，图像可能再次计入输入；具体按目标 API 核对 usage 与账单',
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
