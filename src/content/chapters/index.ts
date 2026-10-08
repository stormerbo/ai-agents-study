import type { Chapter } from '@/content/curriculum/schema';

import { chapter as whatIsAnAgent } from './what-is-an-agent/meta';
import { chapter as llmApiBasics } from './llm-api-basics/meta';
import { chapter as promptEngineering } from './prompt-engineering/meta';
import { chapter as contextEngineering } from './context-engineering/meta';
import { chapter as toolCalling } from './tool-calling/meta';
import { chapter as structuredOutput } from './structured-output/meta';
import { chapter as retrieval } from './retrieval/meta';
import { chapter as memory } from './memory/meta';
import { chapter as agentParadigms } from './agent-paradigms/meta';
import { chapter as agentLoop } from './agent-loop/meta';
import { chapter as multiAgent } from './multi-agent/meta';
import { chapter as agentFrameworks } from './agent-frameworks/meta';
import { chapter as mcp } from './mcp/meta';
import { chapter as multimodal } from './multimodal/meta';
import { chapter as computerUse } from './computer-use/meta';
import { chapter as evaluation } from './evaluation/meta';
import { chapter as sandboxing } from './sandboxing/meta';
import { chapter as agentSecurity } from './agent-security/meta';
import { chapter as costAndLatency } from './cost-and-latency/meta';
import { chapter as humanInTheLoop } from './human-in-the-loop/meta';
import { chapter as agentDeployment } from './agent-deployment/meta';
import { chapter as readingSource } from './reading-source/meta';
import { chapter as capstone } from './capstone/meta';

/**
 * 章节清单。
 *
 * 为什么**显式逐个导入**而不是用 glob 扫描目录？
 *
 * 1. 路径写错会在 tsc 阶段就报错，而不是等到运行时才发现某一章凭空消失
 * 2. 打包器能静态分析出确切的依赖，每章精确切分
 * 3. 这一章有没有写、写了哪几章，在代码里一眼可见 —— 这比翻目录可靠
 *
 * 新增一章时需要在这里加一行。`scripts/check-content.ts` 会校验
 * 阶段里声明的 chapterIds 与实际存在的章是否一致，漏加会被拦下。
 */
export const chapters: Chapter[] = [
  whatIsAnAgent,
  llmApiBasics,
  promptEngineering,
  contextEngineering,
  toolCalling,
  structuredOutput,
  retrieval,
  memory,
  agentParadigms,
  agentLoop,
  multiAgent,
  agentFrameworks,
  mcp,
  multimodal,
  computerUse,
  evaluation,
  sandboxing,
  agentSecurity,
  costAndLatency,
  humanInTheLoop,
  agentDeployment,
  readingSource,
  capstone,
].sort((a, b) => a.order - b.order);
