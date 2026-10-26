"""Offline whole-lesson scope audit for model selection and cost."""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LESSON=ROOT/'src/content/chapters/llm-api-basics/04-model-selection.mdx'
OLD=ROOT/'experiments/scripts/verify_llm_model_selection_review_20261021.py'
def main():
    text=LESSON.read_text(encoding='utf-8')
    fences=re.findall(r'^```python\s*\n([\s\S]*?)^```\s*$',text,re.M)
    assert len(fences)==2
    for i,code in enumerate(fences): compile(code,f'model-selection-{i}.py','exec')
    checks=1
    vals=[57,89,121,153,185,217]
    assert sum(vals)==822 and all(vals[i]-vals[i-1]==32 for i in range(1,len(vals)))
    assert 50*57 + 32*50*49//2 == 42050 and 57+49*32 == 1625
    assert 8+20+44+86 == 158 and (4945-678)/(86-8) < 55
    checks+=1
    for phrase in ('billable usage × 对应单价','缓存读取与写入可能是 input usage 的不同子类','客户端每轮完整重发','不能称作固定开销或普遍价格','每个成功任务成本','不直接等同于模型能力档位','manual_review_required','缓存命中不必然让总成本下降'):
        assert phrase in text, phrase
    checks+=1
    assert 'Haiku 4.5 不支持 Anthropic `effort`' in text
    assert '截至 2026-10-21' in text
    meta=(ROOT/'src/content/chapters/llm-api-basics/meta.ts').read_text()
    assert '这是编辑原则，不是价格每月必变的技术规律' in meta
    checks+=1
    assert '## 常见坑\n## 常见坑' not in text
    assert 'Anthropic 定价页' in text and 'anthropic-cost-intelligence' in (ROOT/'src/content/chapters/llm-api-basics/meta.ts').read_text()
    checks+=1
    old=subprocess.run([sys.executable,str(OLD)],capture_output=True,text=True,check=True)
    assert '36/36 checks passed' in old.stdout,old.stdout
    checks+=1
    print(f'whole-lesson offline checks: {checks}/6; Python fences compiled: {len(fences)}; preserved verifier: 36/36; providerCalls=0; externalNetworkCalls=0')
if __name__=='__main__': main()
