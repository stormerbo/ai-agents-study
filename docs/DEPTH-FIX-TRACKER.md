# 深度修复进度表

> 标准：[docs/CONTENT-DEPTH.md](CONTENT-DEPTH.md)（定义 / 产物 / 判据 / 步骤 / 失败形态）。
> 审计依据：`review/depth-A…I.md`；修复报告：`review/fix-A…I.md`。
> 状态：**全部 26 章 / 134 节已修复**（2026-10-12，9 个批次 + Lead 收口）。

| 章 | 节数 | 批次 | 状态 |
|---|---:|---|---|
| what-is-an-agent | 4 | A | ✅ 已修复 |
| llm-api-basics | 5 | A | ✅ 已修复 |
| prompt-engineering | 5 | A | ✅ 已修复 |
| context-engineering | 8 | B | ✅ 已修复 |
| tool-calling | 5 | B | ✅ 已修复 |
| structured-output | 4 | C | ✅ 已修复 |
| retrieval | 5 | C | ✅ 已修复 |
| memory | 5 | C | ✅ 已修复 |
| multimodal | 5 | D | ✅ 已修复 |
| computer-use | 5 | D | ✅ 已修复 |
| agent-paradigms | 5 | D | ✅ 已修复 |
| agent-loop | 5 | E | ✅ 已修复 |
| multi-agent | 6 | E | ✅ 已修复 |
| agent-frameworks | 5 | E | ✅ 已修复 |
| mcp | 5 | F | ✅ 已修复 |
| evaluation | 11 | F | ✅ 已修复 |
| sandboxing | 5 | G | ✅ 已修复 |
| agent-security | 5 | G | ✅ 已修复 |
| cost-and-latency | 5 | G | ✅ 已修复 |
| human-in-the-loop | 5 | H | ✅ 已修复 |
| agent-deployment | 4 | H | ✅ 已修复 |
| tooling | 5 | H | ✅ 已修复 |
| reading-source | 5 | I | ✅ 已修复 |
| coding-agent | 5 | I | ✅ 已修复 |
| continuous-evolution | 2 | I | ✅ 已修复 |
| capstone | 5 | I | ✅ 已修复 |

合计 26 章 / 134 节。

## 验收（全绿）

| 命令 | 结果 |
|---|---|
| `pnpm depth-check` | 硬错误 0 条、建议项 0 条、术语首现无解释 0/17 |
| `node scripts/content-stats.mjs` | 134/134 达标，无一下降 |
| `pnpm verify:depth` | 134 个文件改动、净增 336,643 字符、无未批准的字数下降 |
| `pnpm test` | 67 断言 / 5 文件全绿（含新增 `tests/depth.test.ts` 门禁） |
| `pnpm typecheck` / `pnpm lint` / `pnpm build` | 全部通过 |

## 刻意保留的「不完美」与例外（都已就地标注）

1. **llm-api-basics/04**：弱/强模型同题对照未跑（本机端点只暴露一个模型名），已标为经验判断。
2. **context-engineering/3.4**：原始那份 138 字摘要与 880 字笔记原文未留存，给的是等价构造笔记（已标注）。
3. **context-engineering/3.5–3.7、4.5**：新增脚本部分未在官方端点实跑，正文均显式声明。
4. **retrieval/05 多跳轨迹、retrieval/03 假嵌入语义效果、memory/05 完成率**：构造/测试替身，已就地标注。
5. **computer-use 全章**：真实截屏与输入注入仍是伪代码（环境无 mss/pyautogui、无授权 GUI 会话），已给替代路径。
6. **multimodal 的 186 下限**：官方无说明，标注为推断。
7. **multi-agent 01–05**：仍共用同一份成本实验代码（「只加不删」的边界），各节另行补了对应论题的可运行产物。
8. **mcp/03 的规范字段键名**：站内无法核实，已声明「本节约定的形态，以对方规范为准」。
9. **evaluation/11**：正文 ±20.0 与脚本 20.4 的 0.4 为既有误差，按纪律未改数、只加注。
10. **capstone/04**：接手试跑复现了 FileNotFoundError（在根目录跑脚本），已把真实记录写进正文。

## Lead 收口时额外做的事

- 删除第 19 章里混入的第 13 章段落（4 处整段重复），改为指向第 13 章的指引（`verify:depth` 已列为「已批准的删除」）。
- 修正 `what-is-an-agent/04` 里「学习进度还没有做」的过期陈述，并补一份自检项记录示例（该节原本缺产物）。
- 修复两个会让 `pnpm build` 失败的文件（`agent-paradigms/02` 的 `{"id": ...}`、`evaluation/10` 的 `p<0.05` 需包成行内代码）。
- 新增 `tests/depth.test.ts` 与 `pnpm depth-check` / `pnpm verify:depth`，把标准固化下来。
