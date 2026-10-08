import type { Stage } from './schema';

/**
 * 学习阶段划分。
 *
 * 划分依据是**依赖关系**，不是热度：后一阶段的每一章都假设前一阶段的内容
 * 已经成立。所以顺序不能随意调整。
 *
 * 这里不声明"本阶段包含哪些章" —— 那层关系只在每个 Chapter 的 stageId 上
 * 表达一次，阶段内的章列表由 `getChaptersByStage()` 派生。所以一个阶段
 * 下面有几章，取决于实际写了多少章，而不是取决于这份文件写了什么。
 */
export const stages = [
  {
    id: 'stage-0-orientation',
    order: 0,
    title: '起点',
    tagline: '先看清全貌，再决定投入什么',
    summary:
      'Agent 是什么、不是什么；为什么它是概率性系统，而你的后端直觉需要相应调整；以及整条路径的全貌。这一章的唯一目的是让你后面每一步都清楚自己在哪里。',
    assumedKnowledge: [
      '能在 Python 或 TypeScript 中读懂并修改代码',
      '调用过 HTTP API，理解请求 / 响应、状态码与错误处理',
      '知道 API Key 与环境变量的作用',
    ],
    capstone: '能用一句话说清「什么问题该用 agent、什么问题不该用」，并知道后面每一章分别解决什么',
    colorToken: 'stage-0',
  },
  {
    id: 'stage-1-foundation',
    order: 1,
    title: '地基',
    tagline: '把 LLM 当作一种新型依赖来对待',
    summary:
      '调用方式、prompt 的写法，以及上下文这个真正的稀缺资源。这三章决定了后面所有内容的可靠性上限 —— 后面每一个 bug，追根溯源大多在这里。',
    assumedKnowledge: [
      '读完阶段 0',
      '有一个可用的模型 API Key（Claude / OpenAI / DeepSeek 任一即可）',
    ],
    capstone: '能独立写出一个稳定返回结构化结果的 LLM 调用，并且说得出它为什么仍可能失败',
    colorToken: 'stage-1',
  },
  {
    id: 'stage-2-primitives',
    order: 2,
    title: '核心原语',
    tagline: '让模型能动手、能入格式、能查资料、能记事、能看、能操作界面',
    summary:
      '工具调用、结构化输出、检索、记忆、多模态输入、计算机使用 —— 这六个原语组合起来就是 agent 的全部零件。任何 agent 框架拆开看，都是它们在重复组合。',
    assumedKnowledge: ['完成阶段 1 全部内容', '能读懂 JSON Schema'],
    capstone: '手写一个能查资料、能读图并给出带引用答案的程序，全程不依赖任何 agent 框架',
    colorToken: 'stage-2',
  },
  {
    id: 'stage-3-orchestration',
    order: 3,
    title: '范式与编排',
    tagline: '框架只是语法糖，先手写一遍再选',
    summary:
      '各种 agent 范式的本质差别；从零实现一个 agent 循环；多智能体到底值不值那个成本；框架选型；以及 MCP 这类协议解决的是什么问题。',
    assumedKnowledge: ['完成阶段 2 全部内容', '理解状态机与循环控制'],
    capstone: '从零实现一个带工具注册、预算控制与循环检测的 agent，并说清它与主流框架的关系',
    colorToken: 'stage-3',
  },
  {
    id: 'stage-4-production',
    order: 4,
    title: '生产化',
    tagline: '你的主场 —— 后端经验在这里才真正值钱',
    summary:
      '评估与可观测性、沙箱与权限、安全与信任边界、成本与延迟、人机协作、部署与交付。绝大多数教程止步于「跑通 demo」，而这几章决定它能不能上线、以及上线之后能不能变好。',
    assumedKnowledge: ['完成阶段 3 全部内容', '有线上服务的部署与运维经验'],
    capstone: '能给一个 agent 服务加上评估、追踪、成本上限与故障恢复',
    colorToken: 'stage-4',
  },
  {
    id: 'stage-5-practice',
    order: 5,
    title: '实战与源码',
    tagline: '读最好的实现，做完整的项目',
    summary: '按「读它的理由」而非 star 数组织的源码研读路线，以及一个需要真正交付出去的完整项目。',
    assumedKnowledge: ['完成阶段 4 全部内容'],
    capstone: '一个带持久化、可观测、成本受控的完整 agent 项目',
    colorToken: 'stage-5',
  },
] satisfies Stage[];
