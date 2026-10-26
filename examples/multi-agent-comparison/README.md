# 单 Agent 与多 Agent 对照练习

这个练习用固定的售后工单和离线模型替身，观察拆分角色之后编排成本与失败路径如何变化。它不访问网络、不调用模型，也不证明多 Agent 的回答质量更好。

从仓库根目录运行：

```bash
python3 -m unittest discover -s examples/multi-agent-comparison -v
python3 examples/multi-agent-comparison/verify.py
```

## 观察什么

默认任务集固定为 3 个工单。单 Agent 每个工单调用一次；多 Agent 顺序经过 `classifier → policy → synthesizer`。两种方案收到相同工单，输出相同的预设答案，因此 `fixture_matches` 只验证 fixture 和解析/路由契约。它不是模型质量分数。

报告里的 `calls`、`input_tokens`、`output_tokens` 和 `fixture_elapsed_ms` 是脚本写定的模拟值。多 Agent fixture 需要更多调用和输入 token；`fixture_elapsed_ms` 是设定的时延之和，不是本机测出的耗时，更不是线上 p95。trace 会保留每次模型调用的角色、输入、原始输出，以及 worker 之间显式交接的 payload。

脚本还注入 worker timeout、非法 JSON、拒答和重复 JSON key。检查每种失败是否停止后续角色调用，并确保失败工单没有答案。当前示例选择快速失败，没有重试、并发调度或共享状态写入；生产设计需按任务风险决定重试、补偿、取消与重复副作用边界。

## 如何把练习用于项目

1. 保持任务集、模型版本、生成参数、工具权限和评分规则一致，再比较单 Agent 与多 Agent。
2. 在线实验按任务配对，记录每次模型调用及完整 usage、端到端耗时、错误和重复次数；单独报告失败样本，不要只比较成功样本。
3. 预先定义人工或经验证 scorer 的任务级 rubric。调用次数、token 和耗时只能说明开销，词面差异也不能替代答案质量与观点覆盖。
4. 离线替身只用于稳定重放编排和注入故障。真实模型质量差异必须由独立、版本化的配对任务集和评分证据支持。
