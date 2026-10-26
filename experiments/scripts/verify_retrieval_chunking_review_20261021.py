from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
lesson = (ROOT / "src/content/chapters/retrieval/02-chunking.mdx").read_text()
meta = (ROOT / "src/content/chapters/retrieval/meta.ts").read_text()
resources = (ROOT / "src/content/curriculum/resources.ts").read_text()

checks = [
    "工具提供的默认值是实现选择；例如 LangChain 当前文档以 `RecursiveCharacterTextSplitter` 作为多数用例的起点，RAGFlow 当前 Chunker 文档说明 token-based 是其默认方法。",
    "它们是各自版本的产品说明，不构成跨语料通则。",
]
assert all(check in lesson for check in checks)
assert "'langchain-text-splitters'" in resources
assert "'ragflow-chunker'" in resources
assert "'langchain-text-splitters'" in meta
assert "'ragflow-chunker'" in meta
assert "句末标点率" in lesson
assert "不能证明块语义完整" in lesson

print(f"retrieval/chunking scope checks: {len(checks) + 6}/{len(checks) + 6} passed; providerCalls=0")
