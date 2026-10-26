"""Offline whole-lesson checks for prompt caching; no provider calls."""
from __future__ import annotations
import contextlib, io, os, re, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LESSON=ROOT/'src/content/chapters/llm-api-basics/05-prompt-caching.mdx'
META=ROOT/'src/content/chapters/llm-api-basics/meta.ts'
def main():
    text=LESSON.read_text(encoding='utf-8'); meta=META.read_text(encoding='utf-8')
    fences=re.findall(r'^```python\s*\n([\s\S]*?)^```\s*$',text,re.M)
    assert len(fences)==5
    for i,code in enumerate(fences): compile(code,f'prompt-caching-{i}.py','exec')
    checks=1
    assert 256+2432==2688 and 188+1536==1724
    assert '不能把 3.4 倍当作稳定延迟收益' in text
    assert '不能把它归因于某个最小长度阈值' in text
    assert '不能从 token 比值推断具体省费百分比' in text
    checks+=1
    assert 'GPT-5.6 及以后与较早模型分开说明' in text
    assert 'prompt_cache_hit_tokens' in text and 'prompt_cache_miss_tokens' in text
    assert '总输入 token = input_tokens + cache_read_input_tokens + cache_creation_input_tokens' in text
    assert '官方文档核对日期为 2026-10-22' in meta
    checks+=1
    assert '若没有启用缓存，它并不是一次“缓存未命中”' in text
    assert '警告：缓存未生效' not in text
    # Exercise the cache-status helper in all three cases.
    helper_ns={'__name__':'cache_status_fixture'}
    exec(compile(fences[0],str(LESSON),'exec'),helper_ns)
    report=helper_ns['report_anthropic_cache_usage']
    usage=types.SimpleNamespace(cache_creation_input_tokens=0,cache_read_input_tokens=0)
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): report(usage,cache_requested=False)
    assert '不要把它记作缓存未命中' in buf.getvalue()
    with contextlib.redirect_stdout(buf): report(usage,cache_requested=True)
    assert '请求了缓存' in buf.getvalue()
    with contextlib.redirect_stdout(buf): report(types.SimpleNamespace(),cache_requested=True)
    assert '响应缺少缓存 usage 字段' in buf.getvalue()
    usage=types.SimpleNamespace(cache_creation_input_tokens=1500,cache_read_input_tokens=1000)
    with contextlib.redirect_stdout(buf): report(usage,cache_requested=True)
    assert 'cache writes=1500, reads=1000' in buf.getvalue()
    checks+=1
    # Run the local SHA example and require equal inputs to have equal fingerprints.
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): exec(compile(fences[1],str(LESSON),'exec'),{'__name__':'__main__'})
    hashes=re.findall(r'\b[0-9a-f]{16}\b',buf.getvalue())
    assert len(hashes)==2 and hashes[0]==hashes[1] and '本地表示一致' in buf.getvalue()
    checks+=1
    # Execute the complete teaching program against a local fake SDK.
    class FakeMessages:
        request=None
        def create(self,**kwargs):
            self.request=kwargs
            return types.SimpleNamespace(usage=types.SimpleNamespace(model_dump_json=lambda **_: '{"input_tokens":12,"cache_creation_input_tokens":0,"cache_read_input_tokens":0}'))
    fake_messages=FakeMessages(); fake_client=types.SimpleNamespace(messages=fake_messages)
    fake_sdk=types.ModuleType('anthropic'); fake_sdk.Anthropic=lambda **_:fake_client
    old_sdk=sys.modules.get('anthropic');sys.modules['anthropic']=fake_sdk
    old_model=os.environ.get('VERIFY_MODEL');os.environ['VERIFY_MODEL']='offline-fixture-model'
    try:
        ns={'__name__':'__main__'}; out=io.StringIO()
        with contextlib.redirect_stdout(out): exec(compile(fences[2],str(LESSON),'exec'),ns)
    finally:
        if old_sdk is None: sys.modules.pop('anthropic',None)
        else: sys.modules['anthropic']=old_sdk
        if old_model is None: os.environ.pop('VERIFY_MODEL',None)
        else: os.environ['VERIFY_MODEL']=old_model
    req=fake_messages.request
    assert req and req['model']=='offline-fixture-model' and len(req['tools'])==3
    assert 'cache_control' not in req['tools'][0] and 'cache_control' not in req['tools'][1]
    assert req['tools'][2]['cache_control']=={'type':'ephemeral'}
    assert req['tools'][2]['input_schema']['required']==['query']
    assert 'input_tokens' in out.getvalue()
    checks+=1
    assert '下方是请求片段' in text
    assert '下面仅展示 `system` 参数的内容形状，不是完整脚本' in text
    assert '不能说明其所有版本或请求都忽略' in text
    checks+=1
    print(f'whole-lesson offline checks: {checks}/7; Python fences compiled: {len(fences)}; complete example exercised with mock SDK; providerCalls=0; externalNetworkCalls=0')
if __name__=='__main__': main()
