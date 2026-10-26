from pathlib import Path

lesson_path = Path('src/content/chapters/tooling/01-retrieval-stack.mdx')
lesson = lesson_path.read_text()
meta = Path('src/content/chapters/tooling/meta.ts').read_text()

required = [
    '词法检索（例如 BM25）不需要 embedding 模型',
    '只有采用稠密向量检索时，才需要选择 embedding 模型',
    '小语料可以直接对全库候选做 cross-encoder 打分',
    '查询相关的 cross-encoder 分数不能像文档 embedding 一样提前独立缓存',
    '单位为 MiB（按 1024² 字节换算）',
    '这只是 2026-10-09 时的语料快照',
    '当前仓库的 MDX 数量不同，重跑会得到不同语料和结果',
    '没有 profiling 数据，不能判断哪一部分占主导',
    'OpenAI `text-embedding-3` 系列可通过 `dimensions` 请求较短向量',
    '向量库可以提供 ANN 召回，也可能提供持久化、元数据过滤、增量更新、分片和运维接口',
    '10000, 50000, 200000',
    "resourceIds: ['sentence-transformers-retrieve-rerank', 'openai-embeddings-create', 'openai-embeddings-faq', 'faiss-index-guide', 'chroma-python-collection-query']",
    "sourceIds: ['openai-embeddings-create']",
]
missing = [x for x in required if x not in lesson and x not in meta]
assert not missing, f'missing retrieval-path scope corrections: {missing}'

for overclaim in ('embedding 是必须选一个模型', '它只能用在"重排"那一段', '不能用来做全库召回', '1 万以内暴力就够，5 万以上考虑索引', '390.6 MB', '100 万 —— 找交叉点'):
    assert overclaim not in lesson, f'overclaim remains: {overclaim}'

print({'checks': len(required) + 6, 'passed': len(required) + 6})
