from pathlib import Path

lesson = Path('src/content/chapters/tooling/02-orchestration-stack.mdx').read_text()
meta = Path('src/content/chapters/tooling/meta.ts').read_text()

required = [
    '原始 pip resolver 输出没有归档',
    '`langchain-core>=1.4.7,<2`',
    '`langchain-core>=0.3.15,<0.4`',
    '没有交集',
    'python -m pip install --dry-run --report /tmp/install-plan.json -r requirements.txt',
    '不能把任意格式的 lockfile 直接交给 pip',
    '完整示例在临时 Python 3.14.7 虚拟环境（`packaging` 26.3）中运行',
    'pip 文档明确提醒，单独安装一个包时可能破坏其他已安装包',
    '`packaging` 是 PyPA 的第三方库，不是 Python 标准库',
    '代码不处理完整传递依赖、环境 marker、extras、平台条件或 pip 升级策略，不能代替 resolver',
    '1.10.0',
    '冲突表是风险摘要，不是自动决策',
    '原始 `params` 和 `result` 可能含个人信息、凭据或业务敏感内容，不能默认原样写入 trace',
    '按排查问题选择',
    '先脱敏并限制访问和保留时间',
    '具体产品的功能、数据保留和访问控制各不相同',
    '每日任务数 × 每任务事件数 × 平均每条字节数 × 保留天数',
    '再根据预算、诊断目标、敏感字段、保留配置和平台限额选择全量、采样、字段裁剪或分层保留',
    "sourceIds: ['pip-user-guide', 'pip-install-cli']",
    "'pypi-langgraph-1-2-14'",
    "'pypi-langchain-0-3-7'",
    "'pypa-packaging-version'",
    "sourceIds: ['opentelemetry-semconv-guidance']",
]
missing = [item for item in required if item not in lesson and item not in meta]
assert not missing, f'missing orchestration and trace boundaries: {missing}'

for overclaim in (
    'packaging 标准库十几行',
    '有冲突就必须',
    '原始参数是 `params`（**存原始对象，不要存格式化后的字符串**',
    '`result` 必须按收到时的原样存',
    '如果那个数字是千万级，采样策略就不是可选项而是必需项',
    '这个判据的好处是它不依赖工具对比。**自己写 vs 用平台不是技术问题，是组织问题**',
):
    assert overclaim not in lesson, f'overclaim remains: {overclaim}'

assert '`1.10.0 > 1.9.0`' in lesson
print({'checks': len(required) + 7, 'passed': len(required) + 7})
