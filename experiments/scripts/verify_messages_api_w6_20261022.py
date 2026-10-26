"""Offline whole-lesson scope checks for Messages API; no provider calls."""
from __future__ import annotations
import ast, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LESSON=ROOT/'src/content/chapters/llm-api-basics/03-messages-api.mdx'
META=ROOT/'src/content/chapters/llm-api-basics/meta.ts'
def main():
    lesson=LESSON.read_text(encoding='utf-8'); meta=META.read_text(encoding='utf-8')
    fences=re.findall(r'^```python\s*\n([\s\S]*?)^```\s*$',lesson,re.M)
    assert len(fences)==4
    for i,code in enumerate(fences): ast.parse(code,filename=f'messages-api-{i}.py')
    assert '本次生成的上限；如果响应以 max_tokens 结束，输出可能不完整' in meta
    assert 'JSON 一定无效' in meta and '不能假设每次都会返回半截字符串' in meta
    assert '达到上限时响应可能不完整' in lesson
    assert '在完整响应后按' in lesson and '最终 `stop_reason == "tool_use"`' in lesson
    assert '工具结果配对，不是业务幂等键' in lesson
    assert 'usage.output_tokens` 是到该事件为止的累计量' in lesson
    assert '63/129 个事件' in lesson and '具体 usage' in lesson
    assert '严格模式保证' not in lesson
    assert '不会执行任何外部副作用' in lesson
    print(f'whole-lesson offline checks: 7/7; Python fences parsed: {len(fences)}; providerCalls=0; externalNetworkCalls=0')
if __name__=='__main__': main()
