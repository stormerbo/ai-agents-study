from pathlib import Path

lesson = Path('src/content/chapters/tooling/03-local-models.mdx').read_text()
meta = Path('src/content/chapters/tooling/meta.ts').read_text()

required = [
    '数据必须留在本组织控制的处理边界内',
    '这不自动等于所有托管服务都不合适',
    '候选服务的数据处理条款、保留策略、部署区域与日志链路',
    '响应里的 `model` 字段不一定是底层权重或构建版本的证明',
    '固定评测集只能监测行为变化，不能识别具体模型版本',
    'embedding、分类和抽取并不天然比生成任务简单',
    '是否需要 GPU 取决于模型、吞吐、延迟和硬件',
    '在线持续编码时，推理成本会随请求量累积',
    '这组数字只适用于该机器、模型、批大小和语料',
    '新增或更新文档可能触发新的编码工作，不能视为一次性成本',
    '向量矩阵占用：2.6 MiB（按 1024² 字节换算；不含索引）',
    'resourceIds: [\'microsoft-foundry-data-privacy\', \'openai-enterprise-privacy\', \'claude-model-deprecations\', \'osi-open-source-ai-definition\', \'huggingface-model-card-guides\']',
]
missing = [item for item in required if item not in lesson and item not in meta]
assert not missing, f'missing corrected accuracy boundaries: {missing}'

assert round(1311 * 512 * 4 / 1024**2, 1) == 2.6
assert '2.6 MB' not in lesson

for absolute in ('唯一「花钱也解决不了」', '不能 → 必须本地', '这类用本地小模型，质量差距小', '因为它**不需要 GPU**'):
    assert absolute not in lesson, f'overbroad statement remains: {absolute}'

print({'checks': len(required) + 6, 'passed': len(required) + 6})
