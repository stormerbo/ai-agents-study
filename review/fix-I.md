# 深度修复报告：批次 I（reading-source / coding-agent / continuous-evolution / capstone）

> 审计依据：review/depth-I.md；标准：docs/CONTENT-DEPTH.md（五要素 + 术语规则 + 禁止清单）。
> 范围：17 节 .mdx（第 22-25 章），未触碰 meta.ts、其他章、src 其他文件。
> 修复日期：2026-10-12。

## 一、验收输出（本次实跑）

**1. 深度门禁（硬错误必须 0）**

```text
$ node scripts/depth-check.mjs --chapter=reading-source
## 术语首现无解释（0/0）
汇总：硬错误 0 条，建议项 0 条

$ node scripts/depth-check.mjs --chapter=coding-agent
## 术语首现无解释（0/0）
汇总：硬错误 0 条，建议项 0 条

$ node scripts/depth-check.mjs --chapter=continuous-evolution
## 术语首现无解释（0/3）
汇总：硬错误 0 条，建议项 0 条

$ node scripts/depth-check.mjs --chapter=capstone
## 术语首现无解释（0/1）
汇总：硬错误 0 条，建议项 0 条
```

四章均为 E=0 W=0（修复前 reading-source W1、coding-agent W5、continuous-evolution W2 + 3 个术语、capstone W3 + 1 个术语）。

**2. 字数（不能降）**

```text
$ node scripts/verify-depth-fixes.mjs --chapter=reading-source
改动文件 5 / 未改动 0，净增 3038 字符
✅ 没有实质性的字数下降
$ node scripts/verify-depth-fixes.mjs --chapter=coding-agent
改动文件 5 / 未改动 0，净增 6619 字符
$ node scripts/verify-depth-fixes.mjs --chapter=continuous-evolution
改动文件 2 / 未改动 0，净增 4165 字符
$ node scripts/verify-depth-fixes.mjs --chapter=capstone
改动文件 5 / 未改动 0，净增 6489 字符

$ node scripts/content-stats.mjs | tail -1
共 134 节，达标 134 节（标准：中文≥1500 且 说明文字≥3000）
```

**3. 测试（全绿）**

```text
$ pnpm test
 ✓ tests/sse.test.ts (15 tests) 7ms
 ✓ tests/image-tokens.test.ts (4 tests) 12ms
 ✓ tests/inline-md.test.ts (5 tests) 8ms
 ✓ tests/depth.test.ts (2 tests) 144ms
 ✓ tests/curriculum.test.ts (41 tests) 105ms
 Test Files  5 passed (5)
      Tests  67 passed (67)
```

**4. 本次真跑新增的数据（不是构造）**

| 来源 | 命令/脚本 | 输出要点 |
|---|---|---|
| edit JSON 原始输出 | 直连 ANTHROPIC_BASE_URL（deepseek-flash）2 次 | 2/2 不可直接 `json.loads`：一次套 `json` 围栏，一次是「字段名+缩进块」+ 末尾解释（stop_reason 都是 end_turn） |
| rank_and_truncate | langchain_core 0.3.63，169 个 .py | 查 `def `：2070 行/157 文件（84978 字符）→ top5×每文件 8 行 = 40 行/5 文件（2254 字符） |
| 审批续跑 | 宿主侧脚本导入 capstone_agent.py | 第一次 run→input_required；带 key 重入→sent:true；再重入→skipped:true |
| 接手试跑 | `python3 capstone_agent.py`（根目录） | `can't open file .../capstone_agent.py: [Errno 2] No such file or directory`；改到 verify-output/ 后 6/6，脚本运行 0.03s |

## 二、逐节补了什么

### reading-source（第 22 章）

- **01-why-and-how**（审计：enum/schema/docstring 零解释）
  - L13–21：新增四个词的解释 —— JSON schema（工具说明书，类比 IDL/OpenAPI）、docstring、description（软建议）、enum（取值集合 + 校验位置）；并加「模型输出『大后天』会发生什么」的失败形态（W2 由这一段补上）。
  - L174：解释代码里 `split("site-packages/")[-1]`（含项目内代码不含该词的退化情况）。
  - 依据：第 5 章「约束解码」口径、第 4/5 章 enum 实测；满足「定义/失败形态」两要素。
- **02-picking-projects**（审计：缺定位调用链的可操作步骤）
  - L113–124：新增三步 grep 定位调用链的最小命令。
  - 依据：第 3 节的实际追踪流程。
- **03-trace-one-task**（审计：summary 未定义、overload 未解释、base.py 95/103 打架）
  - L26：解释 `@typing.overload`（为什么五个同名定义、哪个真正执行）；并说明 `grep -n "^def tool"` 实际输出就是 16/29/44/58/71 五行（**审计说该命令与「五个定义」对不上，实查不成立**）。
  - L70：统一 95/103 —— `_get_filtered_args` 定义在 95，调 `model_json_schema()` 在 103；并解释 `["properties"]`。
  - L272–274：脚本新增三条断言（`assert summary(a_default) == {"title":"Day","type":"string"}` 等），兑现「行号会变、断言不变」。
  - **审计说本节脚本缺 `def summary`：实查它在 L244 已定义（基线 HEAD 与 verify-output/baseline 都有），该断点不成立。** 真正的问题是 95/103 与断言，已补。
- **04-compare**（审计：inputSchema/tools-list 未解释、C 不可验证）
  - L50：解释 `tools/list`（请求方法）与 `inputSchema`（响应字段）。
  - L36 与 L194：把 C 标成「按协议允许的形态构造的最小示例（示例：构造数据，未实跑）」，并给出复现步骤（起 MCP server + 一次 tools/list）。**没有采纳审计建议的「第 14 章实测抓到的真实响应」——实查 `verify-output/mcp_server.py` 的 inputSchema 是带 `required` 的，照审计写法会造出假实测。**
- **05-outputs**（审计：site-packages 未解释、缺归档命名）
  - L56：四行模板的归档约定（scripts/ 目录、`read-source-<主题>.py` + 同名 .md）。
  - L140：解释 `split("site-packages/")[-1]` 与「手写位置」反例的关系。

### coding-agent（第 23 章）

- **01-why-coding-agent**（审计：agent 循环只引用不解释、无正例循环）
  - L33：定义 agent 循环（多轮调用 + 回灌真实结果）。
  - L70：加实跑标注（W3）。
  - L132–152：新增 20 行最小修复循环正例，并指出三个位置与第 4 节的对应。
  - L193：解释「世界图景」。
- **02-search-strategy**（审计：两级检索只有一句话、tree-sitter/repo-map 未解释）
  - L24：实跑标注（W3）。
  - L83–111：新增 `rank_and_truncate(hits, top_k=5, per_file=8)` 实现 + langchain_core 上的真实测量（本次真跑数据）。
  - L117：解释 AST 与 tree-sitter/repo-map，并给 JS/TS 的可执行替代。
  - L159–165：索引不同步的三种处置（版本/mtime/重建）。
- **03-file-editing**（审计：看不到 JSON 解析失败的原始输出）
  - L13：实跑标注（W3）。
  - L69–96：贴本次复现的两段真实裸输出（围栏版与块格式版；用 [FENCE] 代字面三反引号以免破坏外层代码块）。
  - L99–113：容错解析 `parse_edit`（先剥壳再取最外层对象）+ 三段式降级。
- **04-error-recovery**（审计：ask_model 只有签名，无提示词产物）
  - L14：实跑标注（W3）。
  - L165–199：完整 `ask_model` 三段式提示模板（原始报错/已试方向/本轮要求）+ 断言 `assert err.strip().splitlines()[-1] in prompt` + 第 2 轮 vs 第 4 轮 hint 对照（标注「示例：构造数据，未实跑」）。
- **05-safety**（审计：网络白名单形同虚设、bubblewrap/typosquatting 未解释）
  - L31：实跑标注（W3）。
  - L75：typosquatting 的机制 + 「固定镜像源/新增依赖人工确认」两条对策。
  - L84：bubblewrap 是什么、Linux 可用、macOS 的回退。
  - L92：补「域名白名单防的是把数据发到自己家服务器，不防往白名单域名发任意请求」，并给对策（出网代理 + 内容检查）。

### continuous-evolution（第 24 章）

- **01-from-traces**（审计：classify 与正文结论冲突、Pass^k 未解释、知识无产物）
  - L127 与 L90：解释 Pass^k（可靠性指标，k 次全过）与「时对时错」判据。
  - L149–165：**修正 classify** —— 把 `applies_to/deterministic` 换成三个正交字段 `as_code/as_rule/has_expiry`。原文代码下「什么样的回答算得体」会返回「指令」，与它自己声称的实跑输出「参数」冲突；改后本地重跑四例输出与正文完全一致（程序/指令/知识/参数）。L175 的字段说明同步更新。
  - L62–84：新增知识条目 JSON（id/text/source/written_at/expires_at/scope/hit_count/superseded_by）+ 字段判据 + 写入/读回/更新四步。
  - L179：实跑标注（纯本地）。
- **02-distill-and-test**（审计：实验记录缺席、stop_reason/max_tokens 黑箱、结论过强）
  - L19–31：列出 8 条样本与 4 条「没见过的格式」（来自站内 evolve-distill.py 的真实输入）。
  - L72–84：完整实验记录表（条件 A/B/对照组 + 规则原文 + 判分输入 + 结果）。
  - L129–137：解释 `max_tokens` / `stop_reason`（顶层字段、end_turn vs max_tokens）+ 500→3000 的实测教训。
  - L50–52：把「规则没有带来任何可测的提升」改成「在这个任务上测不出规则带来的提升」，并显式切开「测不出」与「没用」。
  - L239–270：新增命中事件 JSON、触发时机、规则上线四步产物、回滚三件事（覆盖审计的「成本与触发时机」缺口）。
  - 小结 L4 同步改为条件式表述。

### capstone（第 25 章）

- **01-scope**（审计：正文表与代码 SCOPE 两份清单对不上）
  - L27–36：正文表改成带 id 的统一表（id/类型/条目/理由/若做了会引入什么），与代码同源。
  - L130–153：`SCOPE` 重写为同一份带 id 的数据（S1–S4 / X1–X4 + `if_done`），打印逻辑同步；本地跑通。
  - L117–121：新增失败形态（第二周被悄悄违反；解法是做成断言）。
- **02-skeleton**（审计：审批只有停下、没有续跑）
  - L69：区分任务级 `max_tokens` 与单次输出上限（补 depth-check 的术语首现）。
  - L105–131：新增宿主侧续跑协议（展示→批准→带 `approved_ids` 重入）+ 三个必须说清的点 + 本次真跑的实测输出（幂等 skip）。
- **03-hardening**（审计：声称扫描项目实为静态 CHECKLIST）
  - L137–183：代码重构为 `auto_checks()`（真读 POLICY/REGISTRY/APPROVALS/VERSION + 空集合陷阱防护）+ `MANUAL`（带 owner/review）/`SKIP` 两段；本地跑出 3 ✅ / 2 ❌ 缺口。
  - L185–195：新增「两段怎么用，以及它会怎么坏」（空集合、读常量还是读项目、改常量才变绿=脱钩；声明不等于证据）——同时补上 W2。
- **04-deliver**（审计：无真实接手试跑、第 20 节指路错）
  - L37/109/139/207：`第 20 节` → `第 20 章`（replace_all，实查 4 处）。
  - L83–99：新增本次真跑试跑记录（三步行 + 真实 FileNotFoundError + 0.03s + 因此补写的两句）。
  - 交付片段 L106/121 的命令补上「在脚本所在目录运行」（避免代码块出现 verify-output/ 触发 E3）。
- **05-retrospective**（审计：「依据」列无填法规则）
  - L83–85：三档定义（A 有可复现脚本 / B 有实测无脚本 / C 二手直觉）+ 每档改法。
  - L91–97：新增复盘表三种坏法（依据写成结论、给自己打分、只复盘失败）——补 W2。
  - L162–205：脚本加 `TIER` 与 `summarize()`，输出分档统计；本地跑通（A 0 / B 2 / C 2）。

## 三、改动的既有句子（明确错误才改，逐条列出）

1. `continuous-evolution/01` 的 `classify` 代码与 `Lesson` 字段：原代码会让「什么样的回答算得体」返回「指令」，与本节声称的实跑输出「参数」矛盾。已修正字段设计，正文那句「三个正交的字段（适用范围/是否确定性/是否过期）」同步改为「（能不能写成代码/能不能写成一句话/会不会过期）」。
2. `reading-source/03` 的 `base.py:95` 与 `base.py:103`：不是删改数据，而是区分「函数定义行」与「取值语句行」（实查 95=def、103=model_json_schema 调用）。原有两处数字都保留。
3. `continuous-evolution/02` 结论措辞与小结：把「都没带来可测提升」改为条件式；未改动 7/7、4/4、4/4 任何数字或日期。
4. `capstone/04` 的「第 20 节」→「第 20 章」：原文在章内找不到对应节。
5. `capstone/03` 的代码 docstring 日期 2026-10-09 → 2026-10-12（该段代码本次被重写为真正的自动检查，日期随之更新；其余节的既有实测日期一律未动）。

## 四、审计中经实查不成立的三点

1. **「22 章第 3 节脚本引用未定义的 summary(t)」** —— 不成立：`def summary` 在 L244 就存在（HEAD 与 baseline 均如此，见上）。
2. **「`grep -n "^def tool"` 与五个定义对不上」** —— 不成立：在 langchain_core 0.3.63 上实跑，输出正是 16/29/44/58/71 五行。
3. **「C 是第 14 章实测抓到的真实响应删减而成」** —— 不成立：第 14 章自己的 server 的 inputSchema 带 `required`。已按诚实口径标注为构造示例，并给出复现方法，而没有把它写成实测。

## 五、仍未解决 / 有意留白的点

- **22 章第 4 节 C 组无法在站内直接复现**：修复只到「标注 + 给复现步骤」，因为要真跑需要另起一个刻意省略 `required` 的 MCP server；本次未新造该 server。
- **23 章第 3 节的两段裸输出是「本次复现」而非原始那次实验的留档**：原始失败文本当时没保存，正文已明确标注这一点，并把 20% 的来历讲清（不重算比率）。
- **24 章条件 A 的逐条明细**：正文口径是「其余 7 条全部通过」，而 `evolve-distill.log` 是同脚本更早一次运行的记录（6/7，`12-10-2026` 失败）。按「不许删改已有实测」保留正文 7/7，未把 log 的逐条明细并入，故没有给出条件 A 的逐条通过表。
- **24 章两个假发现的原始空输出**未留档，只能给出机制（空文本 + stop_reason=max_tokens）与 500→3000 的配置差，没有伪造具体报文。
- **23 章第 2 节的 token 数**：本次实测给的是字符数（84978→2254），没有引入站内不存在的 token 估算口径；正文据此改用「字符」表述。
- **未做视觉验证**（`next start` + 截图）：本批次只改正文，且验收命令（depth-check / content-stats / pnpm test）全绿；如需页面级确认可另起一轮。

## 六、未触碰清单

- 未改 meta.ts、未改其他 22 章、未改 src 其他文件。
- 未引入新 MDX 组件或 frontmatter 字段；所有新增代码块均标语言；Mermaid 未改动。
- 新增数字来源：站内已有实测（脚本/log/正文）× 本次真跑（上表 4 类）；构造产物一律就地标注「示例：构造数据，未实跑」。
