import type { Lab, ModelRef } from './schema';

/**
 * 代码实验注册表。
 *
 * 关于 `allowedModels`：它既是给用户的下拉选项，也是**服务端的白名单二次来源**——
 * 客户端传来的 model 必须落在这里，否则 /api/chat 直接拒绝。
 * 这样即使有人拿到端点，也无法把它当通用 LLM 代理使用。
 *
 * 模型 id 会随厂商更新而变化，所以集中放在这里，改一处即可。
 */

const SONNET: ModelRef = {
  provider: 'anthropic',
  model: 'claude-sonnet-5',
  label: 'Claude Sonnet 5',
};
const HAIKU: ModelRef = {
  provider: 'anthropic',
  model: 'claude-haiku-4-5-20251001',
  label: 'Claude Haiku 4.5',
};
const OPUS: ModelRef = {
  provider: 'anthropic',
  model: 'claude-opus-5-5',
  label: 'Claude Opus 5.5',
};

const COMMON_MODELS: ModelRef[] = [SONNET, HAIKU, OPUS];

const userText = (text: string) => [
  { role: 'user' as const, content: [{ type: 'text' as const, text }] },
];

export const labs: Record<string, Lab> = {
  // ---------------------------------------------------------------------------
  'lab-raw-sse-observer': {
    id: 'lab-raw-sse-observer',
    chapterId: 'llm-api-basics',
    lessonId: 'llm-api-basics/messages-api',
    title: '观察原始流式事件',
    goal: '看清模型返回的每一个 SSE 事件，理解"流式响应"在协议层到底是什么样子。',
    surface: 'standalone',
    allowedModels: COMMON_MODELS,
    defaultModel: HAIKU,
    // 这个实验的重点是协议本身，所以锁死 system prompt，减少变量
    system: {
      content: '你是一个简洁的助手。回答控制在三句话以内。',
      locked: true,
    },
    presets: [
      {
        label: '短回答',
        hint: '观察一轮完整的流式事件序列',
        messages: userText('用一句话解释什么是 token。'),
      },
      {
        label: '长回答（事件更多）',
        hint: '事件数量上去了，更容易看清累积过程',
        messages: userText('用大约 200 字介绍 HTTP 长连接与短连接的区别。'),
      },
      {
        label: '流式里看用量',
        hint: '注意 usage 事件出现在开头和结尾，含义不同',
        messages: userText('为什么说"上下文窗口不是越大越好"？'),
      },
    ],
    defaults: { maxTokens: 1024 },
    objectives: [
      '在原始事件面板里找到 message_start —— 它已经带上了本次请求的输入 token 数',
      '观察文本是一个字一个字（严格说是逐个 token）累积的，而不是一次性到达',
      '找到最后的 stop_reason，并判断这次生成是正常结束还是被 max_tokens 截断',
      '对比"输入 token 数"与你自己的直觉估算，看差多少',
    ],
    troubleshooting: [
      {
        symptom: '点了运行却一直没有任何输出',
        cause: '最常见的是 API Key 未填或填错；其次是浏览器扩展或代理拦截了流式响应',
        fix: '先到设置页点"测试连接"确认 Key 有效，再检查网络面板里请求是否真的发出了。',
      },
      {
        symptom: '文字不是逐步出现，而是等了几秒后一次性全部出现',
        cause: '响应被中间层缓冲了。本地开发通常不会出现，但经过某些代理或部署平台时会发生',
        fix: '看网络面板里的响应是分块的还是一次性的。这类问题在本地往往复现不了，必须在实际部署环境验证 —— 这是本项目在部署阶段要专门检查的一项。',
      },
    ],
    capabilities: ['streaming'],
    showRawEvents: true,
    estimatedMinutes: 15,
  },

  // ---------------------------------------------------------------------------
  'lab-sampling-params': {
    id: 'lab-sampling-params',
    chapterId: 'llm-api-basics',
    lessonId: 'llm-api-basics/sampling-params',
    title: '采样参数对比',
    goal: '亲手感受 temperature 对输出的影响，并验证"温度设为 0 是否真的可复现"。',
    surface: 'inline',
    allowedModels: COMMON_MODELS,
    defaultModel: HAIKU,
    presets: [
      {
        label: '创意任务（差异明显）',
        hint: '用需要发散的题目，参数影响更容易观察',
        messages: userText('给一家只卖三种咖啡的小店起个名字，只说名字，不要解释。'),
      },
      {
        label: '抽取任务（应该稳定）',
        hint: '这类任务的输出本就不该随机',
        messages: userText('从这句话里抽出人名和公司名，用 JSON 输出：张三上周加入了字节跳动。'),
      },
    ],
    defaults: { temperature: 1, maxTokens: 512 },
    objectives: [
      '同一个提示连跑三次，比较 temperature=0 与 temperature=1 时输出差异的大小',
      '在 temperature=0 下多跑几次，确认输出是否**逐字**一致（大概率不是）',
      '对一个抽取类任务调高温度，观察输出什么时候开始不可靠',
    ],
    capabilities: ['streaming'],
    estimatedMinutes: 15,
  },

  // ---------------------------------------------------------------------------
  'lab-prompt-ab': {
    id: 'lab-prompt-ab',
    chapterId: 'prompt-engineering',
    lessonId: 'prompt-engineering/instruction-clarity',
    title: '两种 prompt 写法的 A/B 对比',
    goal: '对比否定式指令与正面指令的稳定性差异，亲眼看到"不要做 X"为什么不可靠。',
    surface: 'standalone',
    allowedModels: COMMON_MODELS,
    defaultModel: SONNET,
    // 这个实验的核心就是要改 system prompt，因此不锁定
    system: {
      content: '你是一个有帮助的助手。不要输出解释性文字。',
      locked: false,
    },
    presets: [
      {
        label: '触发差异的输入',
        hint: '这类"顺便解释一下"的请求最容易暴露否定式指令的弱点',
        messages: userText(
          '把下面这句话翻译成英文：这个功能的实现比预期复杂。顺便说一下你的翻译思路。',
        ),
      },
    ],
    defaults: { temperature: 1, maxTokens: 512 },
    objectives: [
      '先用默认的否定式 system prompt（"不要输出解释性文字"）跑几次，记录有几成遵守了约束',
      '把 system prompt 改成正面描述（明确要求只输出译文本身），再跑同样多次，对比遵守率',
      '观察温度对这一结果的影响：低温度下两种写法差异是否被掩盖了',
    ],
    troubleshooting: [
      {
        symptom: '两种写法的结果看起来差不多，看不出区别',
        cause: '多数情况下模型确实会遵守约束，差异体现在长尾上',
        fix: '多跑几次（比如各 5 次），并且选一个容易诱发解释的输入。差异不在平均数上，在失败次数上。',
      },
    ],
    capabilities: ['streaming'],
    estimatedMinutes: 20,
  },

  // ---------------------------------------------------------------------------
  'lab-tool-schema': {
    id: 'lab-tool-schema',
    chapterId: 'tool-calling',
    lessonId: 'tool-calling/schema-design',
    title: '改一改工具描述，看模型行为怎么变',
    goal: '亲手体验"工具描述即 prompt"——同一段用户输入，工具描述写法不同，模型的选择就不同。',
    surface: 'standalone',
    allowedModels: COMMON_MODELS,
    defaultModel: SONNET,
    system: {
      content:
        '你是一个助手。当用户的问题需要实时数据时，调用提供的工具来获取，然后基于工具返回结果作答。',
      locked: false,
    },
    presets: [
      {
        label: '参数类型被误用',
        hint: '观察模型会往参数里塞什么',
        messages: userText('北京今天热不热？'),
      },
      {
        label: '该不该调用工具',
        hint: '考察模型对工具适用边界的判断',
        messages: userText('一般什么季节去杭州比较好？'),
      },
    ],
    defaults: { maxTokens: 1024 },
    objectives: [
      '先用一个描述含糊的工具（"查询天气"），观察模型往参数里塞了什么',
      '把描述改成明确约束（"参数须为英文城市名，如 Beijing"），再跑同样的输入，对比参数质量',
      '构造一个"不该调用工具"的问题，看模型能否正确判断边界',
      '最后把参数改成 enum 限定取值，观察模型是否还会生成非法值',
    ],
    capabilities: ['tools', 'streaming'],
    estimatedMinutes: 25,
  },
};
