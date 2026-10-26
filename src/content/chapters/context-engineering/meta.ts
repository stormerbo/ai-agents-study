import type { Chapter } from '@/content/curriculum/schema';

/**
 * 章 3。这一章是阶段 1 的收口，也是整站最能体现“后端经验值钱”的地方 ——
 * 上下文管理本质上就是资源调度：有容量上限、有淘汰策略、有热冷分层。
 */
export const chapter = {
  id: 'context-engineering',
  stageId: 'stage-1-foundation',
  order: 3,
  title: '上下文工程',
  subtitle: '决定模型每一次能看到什么',
  summary:
    'context rot 与 Lost in the Middle 的实证、system prompt 该写多具体、什么时候该检索而不是预先塞入、上下文快满时如何压缩、以及子智能体隔离为什么首先是上下文技巧而非并行技巧。',
  outcomes: [
    '能判断一份材料该放进上下文、该检索获取、还是根本不该让模型看到',
    '能设计一套上下文接近上限时的压缩与丢弃策略，而不是等它报错',
    '能说清 system prompt 写得过于具体和过于抽象各自会出什么问题',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 100,
  tags: ['context', 'compaction', 'subagent'],
  prerequisiteIds: ['prompt-engineering'],
  lessons: [
    {
      id: 'context-engineering/context-is-finite',
      chapterId: 'context-engineering',
      slug: 'context-is-finite',
      title: '上下文不是越多越好：两个实证',
      summary:
        'Lost in the Middle 与 context rot 是依赖模型、任务和材料的经验现象；窗口容量不等于任务表现，需在目标场景中测量。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['context-rot', 'lost-in-the-middle'],
      checkpoints: [
        {
          id: 'middle-neglect',
          basis: 'inferred',
          question: '如果必须在一个很长的上下文里放置一条关键约束，你会放在哪里？为什么？',
          answer:
            '可以把关键约束放在容易检查的位置，并在目标模型和任务上验证，但不能把 U 形效应当作普遍规律。Lost in the Middle 在其受测设置观察到位置效应；本书位置扫描最高到 22.8k token 未复现，第 7 章约 130k token 的海捞针任务也未复现。两组结果都只限定于各自的样本与任务，不证明其他设置没有位置效应。',
          note: '本节异质文档位置扫描最高 22.8k token 未复现；第 7 章约 130k token 海捞针为另一任务与样本，仍未复现。不能据此推广到所有模型或任务。',
          resourceIds: ['lost-in-the-middle', 'chroma-context-rot'],
        },
        {
          id: 'context-rot-definition',
          basis: 'inferred',
          question: 'context rot 说的是什么？它和「上下文窗口不够用」是同一个问题吗？',
          answer:
            '不是同一个问题。上下文上限属于容量问题；provider 可能拒绝请求，也可能返回专门的停止状态，Anthropic 当前定义 `model_context_window_exceeded`；context rot 是在某些模型与任务中，上下文变长伴随任务表现下降的经验现象。我在合成定位任务中测到 22.8k token 未见下降，第 7 章约 130k token 的单针定位也未复现位置效应；这些结果不能排除其他任务、语料或模型上的下降。是否发生应通过目标场景的对照评估确认。输入成本、延迟和容量预算仍需独立管理。',
          note: '本节 40→400 段（最高约 22.8k token）未见容量扫描性能下降；第 7 章约 130k token 海捞针是不同任务的未复现结果，不能外推。成本、延迟与容量约束独立成立。',
          resourceIds: ['chroma-context-rot'],
        },
        {
          id: 'truncated-run-classification',
          basis: 'documented',
          sourceIds: ['anthropic-stop-reasons', 'deepseek-anthropic-api', 'anthropic-python-sdk'],
          question: '`stop_reason=max_tokens` 与上下文窗口超限是同一件事吗？空文本能证明 thinking 消耗了预算吗？',
          answer:
            '在 Anthropic Messages API 中，`max_tokens` 表示响应达到生成上限，应将调用标记为未完成；Anthropic 还定义 `model_context_window_exceeded`，也应归为未完成。上下文超限的呈现方式依 provider 而定。Anthropic 的 usage 可将 thinking token 计入 output_tokens，但仅凭空可见文本与停止原因，不能证明本次预算具体花在何处。DeepSeek 当前支持 Anthropic API 格式的说明不能证明历史兼容端点的具体字段语义。评分时同时记录 stop_reason、内容块类型和可用 usage；只在预先定义的重跑策略允许时增加预算重跑，并单独计数和核算成本。',
        },
        {
          id: 'anthropic-sdk-auth',
          basis: 'documented',
          sourceIds: ['anthropic-python-sdk', 'deepseek-anthropic-api'],
          question: '为什么示例不把 ANTHROPIC_AUTH_TOKEN 的值塞进 api_key 参数？',
          answer:
            'Anthropic Python SDK 区分 API key 与 bearer auth token，并能从环境变量解析凭据；兼容端点是否接受相同认证头则需按端点文档核实。DeepSeek 的 Anthropic 兼容说明展示 ANTHROPIC_API_KEY、ANTHROPIC_BASE_URL 配置并列出 x-api-key 支持，所以示例保留 SDK 的环境凭据解析，只通过 base_url 选择端点，不把两类凭据混作一个 api_key。',
        },
      ],
    },
    {
      id: 'context-engineering/system-prompt-altitude',
      chapterId: 'context-engineering',
      slug: 'system-prompt-altitude',
      title: 'system prompt 的高度：太具体会僵化，太抽象会失控',
      summary:
        '区分模型行为指引与必须由宿主强制的业务约束，并用目标任务评测 system prompt。',
      estimatedMinutes: 17,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['system-prompt', 'instructions'],
      checkpoints: [
        {
          id: 'over-specification',
          basis: 'inferred',
          question: '把每种情况的处理方式都写进 system prompt，会带来什么问题？',
          answer:
            '过度枚举会增加维护负担，并可能让指令在交叉场景中互相冲突。若规则缺少明确的业务优先级，模型输出不能作为可靠的政策裁决；高风险约束应由宿主逻辑执行。历史摘要称一组矛盾规则的 12 次分类为 8:4，单条规则为 4/4 和 0/4；原始响应、精确端点/模型、请求参数和 scorer 未留存，因此无法复算、诊断成因或估计线上概率。',
          note: '2026-10-08 `deepseek-flash` 历史摘要，逐次输出、模型后端指纹、采样参数和分类器缺失；不构成随机性、概率或因果证据。',
        },
        {
          id: 'too-abstract',
          basis: 'inferred',
          question: '反过来，system prompt 写得太抽象（只说“你是一个有帮助的助手”）会怎样？',
          answer:
            'prompt 过于抽象时，可能没有表达任务成功条件、知识边界和不确定时的处理方式，模型会依赖当前模型、上下文与生成配置补足细节。历史摘要称抽象组 3/3 提及具体时间、原则组 3/3 拒绝承诺；原始输出、任务映射和 scorer 缺失，不能独立验证或推广成一般行为规律。应在目标模型、端点和任务集上评测清晰直接的要求与必要示例。',
          note: '2026-10-08 `deepseek-flash` 历史摘要，逐次输出、模型后端指纹、生成参数及 scorer 未归档，本轮未重放。',
        },
      ],
      resourceIds: ['anthropic-context-engineering', 'claude-prompting-best-practices', 'anthropic-stop-reasons', 'anthropic-python-sdk'],
    },
    {
      id: 'context-engineering/just-in-time',
      chapterId: 'context-engineering',
      slug: 'just-in-time',
      title: '即时检索：不要预先塞入所有可能用到的资料',
      summary: '把“预先准备一个完备的上下文”换成“让模型在需要时主动去取”，这两条路线的取舍。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['retrieval', 'just-in-time', 'tools'],
      checkpoints: [
        {
          id: 'jit-vs-preload',
          basis: 'inferred',
          question:
            '与其把整个知识库预先塞进上下文，不如让模型按需检索 —— 这样做的核心优势是什么？它什么时候会失效？',
          answer:
            '按需取可以避免一开始传入全部正文，但会增加工具调用、轮次、延迟和失败路径。哪条路线更合适，取决于目标任务所需内容、目录与检索质量、缓存、输出及工具成本。正文保留的历史摘要中，2/40 的 token 量低于预加载，20/40 与 40/40 高于预加载；原始轨迹、答案验收和 scorer 未归档，所谓 20% 交叉点不可推广，也不能据此证明质量相等或费用更低。',
          note: '2026-10-08 `deepseek-flash` 历史单次摘要：40 篇资料库，2/8/20/40 篇时按需路线 token 量比值为 0.64x / 0.95x / 2.47x / 3.60x；逐次原始响应、完整 usage、模型后端指纹与答案评分不可复核。',
        },
        {
          id: 'file-path-pattern',
          basis: 'inferred',
          question:
            '有一种介于两者之间的做法：只把“目录结构”或“文件路径列表”放进上下文，需要时再让模型去读具体内容。它的巧妙之处在哪？',
          answer:
            '它将发现用的索引和权威正文分开：路径、标题、摘要可能比整篇正文短，可帮助模型发现候选，但摘要可能遗漏规则，也不能代替正文校验。原文中的目录 token 数是构造样例的估算值，不是 tokenizer 实测；是否常驻要按目标模型的 token 计数、更新频率、权限边界与答案质量决定。',
          resourceIds: ['aider'],
        },
        {
          id: 'sdk-credential-routing',
          basis: 'documented',
          sourceIds: ['anthropic-python-sdk', 'deepseek-anthropic-api'],
          question: '使用 Anthropic Python SDK 时，为什么不能把 ANTHROPIC_AUTH_TOKEN 当作 api_key 传入？',
          answer:
            'SDK 将 API key 与 bearer auth token 作为不同凭据参数处理，分别传给 `api_key` 与 `auth_token`；不要把两者合并。兼容 endpoint 的 `base_url` 不决定它接受哪种认证，需核对该 endpoint 的认证契约。',
        },
        {
          id: 'provider-cache-and-completion-boundary',
          basis: 'documented',
          sourceIds: ['deepseek-context-caching', 'claude-prompt-caching', 'anthropic-stop-reasons'],
          question: '为什么不能只用一个通用公式解释缓存 token，或把达到工具轮次上限的样本当成完成？',
          answer:
            '缓存 usage 字段与缓存规则由 provider/endpoint 定义：DeepSeek 当前 API 记录 `prompt_cache_hit_tokens` 与 `prompt_cache_miss_tokens`，Anthropic Messages API 用 `input_tokens`、`cache_read_input_tokens` 和 `cache_creation_input_tokens` 表达输入组成；应按目标端点的官方语义实现并验证计数。Anthropic Messages API 中，`stop_reason=end_turn` 表示本轮正常结束，`max_tokens` 表示输出达到上限；停止状态不是 `tool_use` 也不自动表示答案已完成。示例脚本把非 `end_turn` 和工具轮次上限分类为未完成，但仅此仍不能证明答案正确；比较路线需另设相同的任务验收标准。',
        },
      ],
    },
    {
      id: 'context-engineering/compaction',
      chapterId: 'context-engineering',
      slug: 'compaction',
      title: '压缩与结构化笔记：上下文快满了怎么办',
      summary:
        '朴素做法是“总结一下之前的内容”。但压缩真正难的地方，是决定丢掉什么而不会在下一步后悔。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['compaction', 'summary', 'memory'],
      checkpoints: [
        {
          id: 'compaction-risk',
          basis: 'inferred',
          question: '对历史对话做摘要压缩，最大风险是什么？（还有一个容易忽略的成本，是什么？）',
          answer:
            '风险是压缩后的状态可能遗漏后续需要的信息；用目标任务的已知事实集与验收规则检查遗漏、改写和矛盾。2026-10-08 历史摘要记录了 7/8 与 2272 vs 1952 token，但逐次请求/响应、模型指纹、完整 usage 与 scorer 缺失，不能独立复算或推广。成本须按目标 provider 的压缩调用、后续复用、缓存、费用、延迟和质量实测。高风险约束与副作用状态应由宿主权威状态管理，不能靠摘要提示保障。',
          note: '2026-10-08 历史结果仅为不可复算摘要；见 ERR-079。',
          resourceIds: ['anthropic-compaction', 'anthropic-context-editing', 'openai-conversation-state', 'openai-compaction', 'anthropic-python-sdk'],
        },
        {
          id: 'structured-notes',
          basis: 'inferred',
          question: '为什么用“结构化的笔记文件”来承载跨轮次的信息，比把它们留在对话历史里更可靠？',
          answer:
            '固定字段让结构缺失、类型错误与缺少来源更容易被程序发现，但并不保证模型提取完整或事实正确。应保存来源/版本，和原始事实集或权威系统比对；冲突由宿主处理。2026-10-08 历史摘要称该样本结构化笔记 8/8，但不可独立复算；结构化结果也更长，收益须结合复用成本与任务质量评估。',
          resourceIds: ['anthropic-context-engineering', 'anthropic-compaction', 'openai-conversation-state', 'openai-compaction'],
        },
      ],
    },
    {
      id: 'context-engineering/subagent-isolation',
      chapterId: 'context-engineering',
      slug: 'subagent-isolation',
      title: '子智能体：它首先是个上下文技巧',
      summary: '区分子任务并行与上下文隔离，并用可验证的任务质量、token、费用与延迟指标评估取舍。',
      estimatedMinutes: 23,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['subagent', 'isolation', 'multi-agent'],
      checkpoints: [
        {
          id: 'subagent-real-value',
          basis: 'inferred',
          question:
            '一个探索型子任务（比如“在这 50 个文件里找出所有调用点”）交给子智能体去做，最主要的收益是什么？',
          answer:
            '子 agent 可以把探索过程留在独立运行中，只将结果交给主 agent；这是否隔离上下文，取决于宿主是否转发原始历史。它也不天然带来速度收益。历史摘要（DeepSeek 兼容端点，2026-10-08）记录 20 篇文档任务的主流程最大请求输入为 1258 vs 6816、总 token 为 9182 vs 25913，但原始轨迹、usage 口径、任务等价性和评分器未归档，不能据此证明答案质量相同或普遍省成本。',
          note: '历史单次观测摘要，无法独立复算；最大请求输入不能直接解释为上下文窗口占用或账单。来源说明见本节与 docs/DATA.md。',
          resourceIds: ['anthropic-multi-agent-research', 'anthropic-python-sdk', 'anthropic-stop-reasons'],
        },
        {
          id: 'subagent-cost',
          basis: 'inferred',
          question: '子智能体方案的主要代价是什么？什么情况下不该用它？',
          answer:
            '成本受输入重复、输出、工具结果、编排调用、缓存读写、endpoint 价格与质量门槛共同影响。历史摘要记录：共享背景计划装载 8 次与 1 次时，总 token 分别为 68548 与 8430（比值 8.1）；逐次请求、实际缓存命中和答案评分均缺失，不能归因于单一因素，也不能当作费用比值。是否适用，应在同一任务与验收规则下测量单 agent 和子 agent 的 token、费用、时延及质量。',
          note: '历史单次观测摘要（DeepSeek 兼容端点，2026-10-08），原始轨迹、精确模型/endpoint 与 scorer 未归档，不能独立复算。',
          resourceIds: ['anthropic-multi-agent-research', 'anthropic-python-sdk', 'anthropic-stop-reasons'],
        },
        {
          id: 'tool-result-correlation',
          basis: 'documented',
          sourceIds: ['anthropic-handle-tool-calls'],
          question: '一个响应返回多个 tool_use 时，宿主怎样避免 tool_result 关联错位？',
          answer:
            'Anthropic 将每个 tool_use 的 id 定义为该次调用的唯一标识，宿主回传的 tool_result.tool_use_id 必须对应它。批量执行前检查 id 非空且唯一，可避免畸形响应造成结果关联歧义；这是宿主侧的防御性校验，不等于授权或副作用安全证明。',
        },
        {
          id: 'usage-count-boundaries',
          basis: 'documented',
          sourceIds: ['python-built-in-types', 'anthropic-python-sdk'],
          question: '为什么 token usage 计数不能只用 isinstance(value, int) 判断？',
          answer:
            'Python 的 bool 是 int 的子类，因此 True/False 会通过普通 isinstance(value, int) 检查；计数器应排除 bool、负数和非整数，并把缺失或可选缓存字段按目标 provider 的契约处理。兼容端点对缺省 usage 的含义不能直接沿用 Anthropic SDK。',
        },
      ],
    },
    {
      id: 'context-engineering/chat-template',
      chapterId: 'context-engineering',
      slug: 'chat-template',
      title: 'Chat Template：你写的消息，模型看到的 token',
      summary: '用目标 provider 的 token-count 与缓存契约评估消息结构；历史 238/298 token 对照缺少原始请求且变量混杂，不能归因于边界开销。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['chat-template', 'tokenization', 'message-structure'],
      checkpoints: [
        {
          id: 'structure-costs',
          basis: 'documented',
          sourceIds: ['claude-token-counting', 'claude-messages-api', 'anthropic-compaction', 'claude-prompt-caching', 'openai-prompt-caching', 'deepseek-context-caching'],
          question: '如何判断消息结构变化对输入 token、缓存与行为的影响？',
          answer:
            '先区分 provider 的 token-count、实际响应 usage、缓存诊断和账单口径。Anthropic 提供针对指定模型请求的 count_tokens 接口；它统计输入 token，不等于缓存命中或完整账单。Anthropic、OpenAI、DeepSeek 的缓存断点、前缀要求与 usage 字段各有契约，不能假设统一模板哈希或“缓存全失效”。本节保留的历史 238/298 汇总缺少逐次请求、原始 usage、准确 endpoint/model 与 scorer；示意拆分请求还多出 10 条 assistant 应答，所以不能把 60 token 差值归因于消息边界，也不能外推通用成本或行为结论。要归因结构影响，应保存请求、控制信息与判据、使用目标 provider 的计数和运行 usage，并评估输出行为。',
        },
        {
          id: 'compare-preflight',
          basis: 'inferred',
          question: 'token-count 对照在发送请求前应验证什么？',
          answer:
            '先在本地检查 variant 名称唯一且 baseline 存在，再调用 token-count 接口。这样无效输入会在任何 provider 请求之前失败，避免浪费调用额度或触发限流。该预检只验证实验定义，不证明不同 variant 的内容可比。',
          note: '示例级工程建议；调用本身是否收费、限流由目标 endpoint 当前策略决定。',
        },
        {
          id: 'where-to-add',
          basis: 'inferred',
          question: '要往长会话里加一条每次都适用的规则，如何评估它对缓存复用与权限边界的影响？',
          answer:
            '先按语义、主体和 API 契约选择 system/developer/user 等位置；不要为了缓存把用户或租户专属数据放入跨主体共享前缀。稳定前缀可能有利于某些 provider 的复用，但命中取决于模型、断点、前缀长度、TTL、路由与 provider 策略，不是保证。逐轮重复追加会扩大后续 transcript；是否会破坏全部或部分复用，需检查目标 API 文档和实际 cache usage。把角色/位置变化列为独立实验变量，同时验证授权作用域、任务质量、token 计数与缓存诊断。',
          note: '工程建议；缓存匹配与 usage 规则由目标 provider/model/API 定义，不得将其解释为跨厂商保证。',
          resourceIds: ['claude-prompt-caching', 'openai-prompt-caching', 'deepseek-context-caching'],
        },
      ],
      resourceIds: ['claude-messages-api', 'claude-token-counting', 'anthropic-compaction', 'claude-prompt-caching', 'openai-prompt-caching', 'deepseek-context-caching'],
    },
    {
      id: 'context-engineering/kv-cache',
      chapterId: 'context-engineering',
      slug: 'kv-cache',
      title: 'KV Cache 与 Prompt Cache：机制和适用边界',
      summary: '区分模型推理时的 KV cache 与各 provider 的跨请求缓存；用一条 DeepSeek Anthropic 兼容端点观测说明命中表现及其适用边界。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['kv-cache', 'prompt-cache', 'prefix-stability'],
      checkpoints: [
        {
          id: 'why-prefix',
          basis: 'documented',
          sourceIds: ['claude-prompt-caching', 'deepseek-context-caching', 'deepseek-responses-guide'],
          question: 'KV cache 与跨请求 prompt/context cache 的关系是什么？一次前缀变化的实测能证明什么？',
          answer:
            '常见自回归 Transformer 推理中，序列前部变化通常会使后续位置的运行时 KV 状态无法直接复用；这不意味着所有 provider 的跨请求 prompt/context cache 都采用相同的键、断点或失效策略。Anthropic 文档描述的是其 API 的前缀断点与精确匹配规则；DeepSeek 当前 Context Caching 文档描述自动管理、完整持久化前缀单元、固定 token 间隔与尽力而为命中。另一条 2026-10-08 的旧表格摘要标注 `deepseek-flash` Anthropic 兼容端点，记录改词请求 `cache_read=0`，但原始请求/响应和 usage 均未归档，无法确认真实缓存命中或失效原因；首行 `cache_creation=0` 也不足以支持“冷启动”解释。当前文档不能反推旧兼容端点的缓存单位、字段口径或版本行为。它不能证明所有缓存条目或其他 endpoint 都按同一方式失效，也不能把 provider cache 简化为跨请求 KV cache。',
        },
        {
          id: 'cache-arch-constraint',
          basis: 'inferred',
          question: '在什么条件下前缀稳定有助于缓存复用？为什么不能把它当作所有 API 的正确性约束？',
          answer:
            '对提供前缀缓存的 API，稳定可复用的内容放在适当断点之前，通常有利于复用；但是否精确匹配、断点是否必须显式声明、缓存读写门槛、TTL、哪些参数参与键以及 usage 字段的含义，都由具体 provider/endpoint 定义。Anthropic 官方文档可作为一个具体例子；本节 DeepSeek 兼容端点只是一组有日期的观测。把序列化固定下来便于比较请求，但本地指纹不同不等于服务端必然缓存失效，本地指纹相同也不保证命中。是否有收益应由目标 API 文档、实际 usage 和计费共同验证。',
        },
      ],
      resourceIds: ['claude-prompt-caching', 'deepseek-context-caching', 'deepseek-responses-guide', 'deepseek-responses-api', 'claude-pricing'],

    },
    {
      id: 'context-engineering/agent-skills',
      chapterId: 'context-engineering',
      slug: 'agent-skills',
      title: 'Agent Skills：可组合的上下文单元',
      summary: '把 Skill 当作可版本化指令包；渐进披露是常见模式，具体加载和授权边界由 runtime 决定。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['agent-skills', 'lazy-loading', 'instruction-packages'],
      checkpoints: [
        {
          id: 'progressive-disclosure',
          basis: 'documented',
          sourceIds: ['anthropic-agent-skills', 'openai-agent-skills'],
          question: 'Skill 的渐进披露通常有哪些层次？这些加载方式是否是跨平台统一协议？',
          answer:
            'Anthropic Agent Skills 文档描述三级披露：启动时提供 name/description 元数据，触发后读取 SKILL.md，引用的资料和脚本再按需访问。OpenAI API 也使用 SKILL.md 目录，但 Responses shell skill_reference 与 Agents API capability directories 是不同接入方式。共同的分层思路不意味着发现位置、调用次数、上下文注入方式或 token 成本跨 runtime 相同。',
        },
        {
          id: 'skill-instruction-role',
          basis: 'documented',
          sourceIds: ['anthropic-agent-skills', 'openai-agent-skills'],
          question: 'Skill 指令会以什么消息角色进入模型上下文？它是否拥有系统级优先级？',
          answer:
            '按当前文档，Anthropic 的 Skill 元数据示例进入 system prompt，正文在触发后由文件读取；OpenAI Responses API hosted shell 将技能 name、description 与 path 放入 user prompt，读取的 Skill 指令也按 user 提供的指令处理。OpenAI Agents API 使用 sandbox capability directories 发现 Skill，不能将 hosted shell 的注入形式一概而论。消息角色与来源会影响指令优先级，但不构成工具授权或安全边界；宿主仍须独立执行策略检查。',
          note: '这里只描述所引官方文档中的具体 runtime；产品和 API 可能变化，部署时应复核目标表面当前的上下文与指令优先级契约。',
        },
        {
          id: 'index-only-danger',
          basis: 'inferred',
          question: '历史索引/按需加载对照能支持哪些结论？哪些结论不能从现有记录推出？',
          answer:
            '旧记录列出全文预载 5/5、516 tokens，索引 4/5、148 tokens，两阶段 3/3、201 tokens；但逐次请求/响应、精确 endpoint/model、usage 原文、任务映射与 scorer 未归档，且 C 条件分母为 3、A/B 为 5。因此这些汇总不可独立复算，不能证明“正确率不掉”，也不能把 71%/61% 当作一般节省。按需暴露规则是值得在目标 harness 评估的模式；需在相同任务集、判据和配置下记录选择质量、最终质量、token、工具/文件读取、往返延迟和安全结果。',
          note: '仅保留 2026-10-08 历史摘要；原始实验材料缺失，旧错误归因和比较结论未复现。',
        },
        {
          id: 'skill-vs-tool',
          basis: 'inferred',
          question: 'Agent Skill、工具定义和工作流编排分别承担什么职责？',
          answer:
            'Skill 通常提供可复用的流程指引与参考资源；工具提供宿主/平台控制的操作能力。skill 可以指导模型何时提出工具调用，但它不是授权策略、权限范围或工作流引擎。宿主仍需对身份、参数、对象、预算、审批、副作用和完成条件作独立校验。不同运行时可能改变这些组件的发现与执行方式。',
          note: '架构区分是教学抽象；需按具体 runtime/API 的工具调用与 skill 发现契约核实。',
          resourceIds: ['openai-agent-skills'],
        },
        {
          id: 'skill-security-boundary',
          basis: 'documented',
          sourceIds: ['anthropic-agent-skills', 'openai-agent-skills'],
          question: '为什么安装 Skill 前要审查整个目录？它是否授予模型执行权限？',
          answer:
            'Anthropic 与 OpenAI 官方资料都提醒审查 Skill 内容：指令、参考资料和脚本可影响规划、工具使用或命令执行，并可能造成提示注入、数据外泄或破坏性动作。Skill 本身不是授权边界；来源、版本、网络/文件访问、工具权限与高影响操作审批仍需由宿主按实际运行时控制。',
        },
      ],
      resourceIds: ['openai-agent-skills', 'anthropic-agent-skills'],
    },
  ],
  resourceIds: [
    'anthropic-context-engineering',
    'anthropic-compaction',
    'anthropic-context-editing',
    'openai-conversation-state',
    'openai-compaction',
    'lost-in-the-middle',
    'chroma-context-rot',
    'anthropic-stop-reasons',
    'deepseek-anthropic-api',
    'anthropic-multi-agent-research',
    'aider',
    'memgpt-paper',
  ],
  backendMapping: {
    analogy: '上下文工程 ≈ 内存管理与缓存淘汰，只不过这块“内存”有损、且每字节每次都重新计费',
    transferable: [
      '缓存淘汰与 GC 的思路：容量有限、需要策略、需要分层',
      '热数据 / 冷数据分层，按访问频率决定留存',
      '批处理与流式的取舍，以及“延迟换吞吐”这类权衡',
    ],
    pitfalls: [
      '以为窗口大就不必取舍：部分任务与模型会随上下文增加而表现下降，须在目标场景实测；本章的相关实验未复现该现象',
      '把检索结果无差别全部塞入，反而把真正关键的那条淹没了',
      '以为压缩就是“总结一下”：摘要会丢掉后续步骤真正需要的细节',
      '把子智能体当成纯并行手段：它的主要价值是上下文隔离，代价是数倍 token',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
  flagship: true,
} satisfies Chapter;
