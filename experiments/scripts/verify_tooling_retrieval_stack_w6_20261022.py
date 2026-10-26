from pathlib import Path
import ast
import re


lesson_path = Path('src/content/chapters/tooling/01-retrieval-stack.mdx')
meta_path = Path('src/content/chapters/tooling/meta.ts')
resources_path = Path('src/content/curriculum/resources.ts')
lesson = lesson_path.read_text()
meta = meta_path.read_text()
resources = resources_path.read_text()
fences = re.findall(r'^```python\n(.*?)^```', lesson, re.MULTILINE | re.DOTALL)
assert len(fences) == 4, f'expected four Python fences, got {len(fences)}'
tree = ast.parse(fences[3])

checks = [
    ('historical 40x claim is explicitly withdrawn', '不能直接支持“numpy 快 40 倍”的结论' in lesson),
    ('historical top-k mismatch is explained', 'NumPy 只取 top-1，而 Chroma 返回 top-5' in lesson),
    ('historical two-run upper statistic is disclosed', 'Chroma 只取 2 次中的较大值' in lesson),
    ('historical individual timings are marked unavailable', '原始逐次测量没有归档' in lesson),
    ('20万-row Chroma comparison is disclosed as skipped', '20 万条跳过 Chroma 对照' in lesson),
    ('current sample scopes itself as non-reproduction', '不能复现旧表格' in lesson),
    ('current sample aligns Chroma with top-1', 'n_results=1' in fences[3]),
    ('current sample uses eleven NumPy measurements', 'np.argmax(V @ q), n=11' in fences[3] and 'np.argmax(Vs @ qs), n=11' in fences[3]),
    ('current synthetic Chroma comparison uses eleven measurements', 'chroma_query_time(Vs, ids_s, qs, n=11)' in fences[3]),
    ('current sample states one warm-up and median comparison', '预热一次后 11 次查询的中位数' in lesson),
    ('current run prints the actual model device', '模型设备：%s' in fences[3]),
    ('ANN quality is not conflated with query latency', 'Chroma 的 ANN 结果质量仍需单独评估' in fences[3]),
    ('synthetic corpus is not used to claim semantic quality', '不评估语义召回质量或 ANN 召回率' in lesson),
    ('Chroma top-k documented checkpoint is registered', "id: 'benchmark-top-k'" in meta and "sourceIds: ['chroma-python-collection-query']" in meta),
    ('Chroma source URL is registered', 'https://docs.trychroma.com/reference/python/collection#query' in resources),
    ('no “cross point” is claimed as a measured universal result', '不能把这组数据称作同任务的性能交叉' in lesson and '不能据此断言大规模时 ANN 一定更快' in lesson),
    ('all Python examples parse without executing heavyweight dependencies', all(isinstance(ast.parse(fence), ast.Module) for fence in fences)),
]

# The exact method shown in the lesson takes an odd number of samples so the selected
# middle value is a median rather than the upper observation from an even sample.
bench = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'bench')
default_n = next(arg for arg in bench.args.defaults if isinstance(arg, ast.Constant))
checks.append(('bench default sample count is odd and equals eleven', default_n.value == 11))
bench_source = ast.get_source_segment(fences[3], bench) or ''
checks.append(('bench selects the middle sorted observation', 'sorted(ts)[len(ts) // 2]' in bench_source))

query_calls = [
    node for node in ast.walk(tree)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'query'
]
checks.append(('every Chroma query explicitly asks for one neighbor', len(query_calls) == 1 and any(
    kw.arg == 'n_results' and isinstance(kw.value, ast.Constant) and kw.value.value == 1
    for kw in query_calls[0].keywords
)))

long_lines = [
    (fence_index, line_index, len(line))
    for fence_index, fence in enumerate(fences, 1)
    for line_index, line in enumerate(fence.splitlines(), 1)
    if len(line) > 88
]
checks.append(('Python code lines fit the 88-character display target', not long_lines))

missing = [name for name, passed in checks if not passed]
assert not missing, f'W6 retrieval-stack checks failed: {missing}; long_lines={long_lines}'
print({'checks': len(checks), 'passed': len(checks), 'providerCalls': 0, 'historicalBenchmarksRerun': 0})
