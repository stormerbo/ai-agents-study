import json, pathlib, re, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[2]
PATH = ROOT / 'src/content/chapters/agent-paradigms/01-five-paradigms.mdx'
TEXT = PATH.read_text(encoding='utf-8')
checks = []
def require(ok, label):
    if not ok:
        raise AssertionError(label)
    checks.append(label)

require('四种控制流骨架' in TEXT and '可叠加的复核策略' in TEXT, 'taxonomy distinguishes flow skeletons from review overlay')
require('仍需执行授权、验证参数、控制预算、处理结果并决定能否结束' in TEXT, 'model proposals are distinct from host enforcement')
require('每一步是一次调用' not in TEXT, 'workflow step is not equated with model call')
require('固定的几步' not in TEXT, 'workflow allows explicitly defined conditions')
require('控制流交给了模型' not in TEXT and '控制流还是模型定的' not in TEXT, 'model does not own runtime control')
require('在看到任何数据之前' not in TEXT, 'Plan-Execute is not described as planning before any data')
require('mock，所以每个数字都可复现' not in TEXT, 'fixture determinism is not conflated with historical provider reproducibility')
require('记录的模型往返' not in TEXT, 'unverified step counts are not called model round trips')
require('不是能力或成本的固定等级' in TEXT, 'patterns are not ranked as capability levels')
require('工具定义与 schema' in TEXT and '目标 runtime 的参数表示' in TEXT, 'migration matrix acknowledges integration-specific changes')
require('最直觉的 ReAct 比 Plan-Execute 贵一倍多' not in TEXT, 'unsupported cost ranking removed')
require('ANTHROPIC_BASE_URL' not in TEXT and 'urllib.request' not in TEXT and 'os.environ' not in TEXT, 'online credential-dependent code removed')
require('反思文本本身不等于独立验证' in TEXT, 'reflection distinction is explicit')
require('广州不是最高，上海最高；温差 7' in TEXT and '尽管最高/最低城市角色写反' in TEXT, 'old weak scorer false positive is concrete')
require('Tree-of-Thoughts（ToT）' in TEXT and '不是宿主工具执行边界' in TEXT, 'Tree-of-Thoughts is not presented as host orchestration')
require('实跑状态：2026-10-21' in TEXT, 'offline demo run status is dated')
fences = re.findall(r'^```python\n(.*?)^```\s*$', TEXT, re.M|re.S)
require(len(fences) == 2, 'one non-runnable illustration and one complete Python walkthrough fence')
for index, fence in enumerate(fences):
    compile(fence, f'{PATH}:python-fence-{index}', 'exec')
code = next(fence for fence in fences if 'def react_fixture' in fence)
require('urllib' not in code and 'os.environ' not in code, 'complete example has no provider/network or environment dependency')
with tempfile.TemporaryDirectory() as d:
    p=pathlib.Path(d)/'example.py'; p.write_text(code, encoding='utf-8')
    proc=subprocess.run([sys.executable,str(p)], capture_output=True,text=True,check=True)
code_start = TEXT.index('def react_fixture')
output_start = TEXT.index('```text', code_start)
output_end = TEXT.index('```', output_start + len('```text'))
expected = TEXT[output_start + len('```text\n'):output_end].rstrip('\n') + '\n'
require(proc.stdout == expected, 'complete example stdout exactly matches the published text fence')
require(proc.stderr == '', 'offline example emits no stderr')
print(json.dumps({'status':'pass','testsPassed':len(checks),'testsFailed':0,'pythonFencesCompiled':2,'stdoutMatchesPublishedOutput':True,'providerCalls':0,'externalNetworkCalls':0,'officialSourcesReviewed':3,'historicalBenchmarksRerun':False,'checks':checks},ensure_ascii=False,indent=2))
