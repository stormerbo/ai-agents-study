from pathlib import Path
import re
import subprocess
import sys
import tempfile


lesson_path = Path('src/content/chapters/tooling/02-orchestration-stack.mdx')
meta_path = Path('src/content/chapters/tooling/meta.ts')
resources_path = Path('src/content/curriculum/resources.ts')
lesson = lesson_path.read_text()
meta = meta_path.read_text()
resources = resources_path.read_text()

checks = [
    ('historical resolver output is disclosed as unavailable', '原始 resolver 输出没有保存在当前工作树' in lesson),
    ('LangGraph exact core constraint is stated', '`langchain-core>=1.4.7,<2`' in lesson),
    ('LangChain exact core constraint is stated', '`langchain-core>=0.3.15,<0.4`' in lesson),
    ('non-overlap is stated without treating it as a historical install replay', '两个区间没有交集' in lesson and '不能独立确认' in lesson),
    ('Pydantic range conclusion is scoped to declared metadata', '`pydantic 2.9.2` 满足这两个发行版各自声明的 Pydantic 范围' in lesson),
    ('full project inputs are required for resolver planning', '检查完整依赖集合' in lesson and '包含完整的目标约束' in lesson),
    ('lockfile format compatibility is not assumed', '不能把任意格式的 lockfile 直接交给 pip' in lesson),
    ('pip dry-run example uses report output', '--dry-run --report /tmp/install-plan.json -r requirements.txt' in lesson),
    ('direct-constraint sample is not represented as full resolver', '不能代替 resolver' in lesson and '环境 marker、extras、平台条件' in lesson),
    ('separate venv is recommended', '用独立 venv 试' in lesson),
    ('trace payload minimization is explicit', '不能默认原样写入 trace' in lesson),
    ('trace raw data requires safeguards', '脱敏、访问控制、加密和保留期限' in lesson),
    ('trace ID and business task ID are distinguished', '区分运行追踪 ID 与业务任务 ID' in lesson),
    ('platform capabilities vary by product', '具体产品的功能、数据保留和访问控制各不相同' in lesson),
    ('cost estimate is an input model, not a universal sampling threshold', '每日任务数 × 每任务事件数 × 平均每条字节数 × 保留天数' in lesson and '没有跨产品通用的“千万级”采样阈值' in lesson),
    ('documented checkpoint cites registered official sources', "sourceIds: ['pypi-langgraph-1-2-14', 'pypi-langchain-0-3-7', 'pypa-packaging-version', 'pip-user-guide', 'pip-install-cli']" in meta),
    ('trace-minimization checkpoint cites OpenTelemetry guidance', "sourceIds: ['opentelemetry-semconv-guidance']" in meta),
    ('all package references resolve in the resource registry', all(key in resources for key in ('pypi-langgraph-1-2-14', 'pypi-langchain-0-3-7', 'pypa-packaging-version', 'pip-user-guide', 'pip-install-cli'))),
    ('exact LangGraph PyPI resource URL is pinned', 'https://pypi.org/pypi/langgraph/1.2.14/json' in resources),
    ('exact LangChain PyPI resource URL is pinned', 'https://pypi.org/pypi/langchain/0.3.7/json' in resources),
    ('no product-wide observability guarantee is asserted', '符合需求的平台可能提供' in lesson and '每个平台会自动填充' in lesson),
]

python_fences = re.findall(r'^```python\n(.*?)^```', lesson, re.MULTILINE | re.DOTALL)
checks.append(('one complete Python example is available', len(python_fences) == 1))
if len(python_fences) == 1:
    with tempfile.TemporaryDirectory(prefix='orchestration-stack-w6-') as temp_dir:
        example_path = Path(temp_dir) / 'lesson_example.py'
        example_path.write_text(python_fences[0])
        run = subprocess.run([sys.executable, str(example_path)], capture_output=True, text=True)
        checks.append(('complete Python example exits successfully', run.returncode == 0))
        expected = (
            'langchain-core   <2,>=1.4.7       0.3.63     冲突\n'
            'pydantic         >=2.7.4          2.9.2      兼容\n'
        )
        checks.append(('complete Python example matches published output', run.stdout == expected))
        checks.append(('complete Python example emits no unexpected stderr', run.stderr == ''))

missing = [name for name, passed in checks if not passed]
assert not missing, f'W6 orchestration-stack checks failed: {missing}'
print({'checks': len(checks), 'passed': len(checks), 'providerCalls': 0})
