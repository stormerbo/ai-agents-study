查看题为《MemGPT: Towards LLMs as Operating Systems》的论文PDF，作者为Charles Packer及其他6位作者
查看PDF
HTML（实验性）
摘要：
大型语言模型（LLMs）已经革新了AI，但受限于有限的context window，阻碍了其在扩展对话和文档分析等任务中的实用性。为了在有限的context window之外使用context，我们提出了virtual context management，这是一种从传统操作系统中的分层内存系统汲取灵感的技术，通过快速和慢速内存之间的数据移动来提供大内存资源的表象。利用这种技术，我们引入了MemGPT（Memory-GPT），这是一个智能管理不同内存层级的系统，以便在LLM有限的context window内有效提供扩展的context，并利用中断来管理其与用户之间的控制流。我们在两个领域中评估了我们受OS启发的设计，在这些领域中，现代LLM有限的context window严重损害了它们的性能：文档分析，MemGPT能够分析远远超过底层LLM context window的大型文档；以及多会话聊天，MemGPT能够创建通过与用户长期互动来记忆、反思和动态演化的conversational agents。我们在
this https URL
发布了用于我们实验的MemGPT代码和数据。
评论：
代码和数据可在
this https URL
获取
主题：
Artificial Intelligence (cs.AI)
引用为：
arXiv:2310.08560
[cs.AI]
（或
arXiv:2310.08560v2
[cs.AI]
，为本版本）
https://doi.org/10.48550/arXiv.2310.08560
Focus to learn more
arXiv-issued DOI via DataCite

## Submission history

From: Charles Packer [
view email
]
[v1]
Thu, 12 Oct 2023 17:51:32 UTC (391 KB)
[v2]
Mon, 12 Feb 2024 18:59:46 UTC (419 KB)
Full-text links:

## Access Paper:

View a PDF of the paper titled MemGPT: Towards LLMs as Operating Systems, by Charles Packer and 6 other authors
View PDF
HTML (experimental)
TeX 源码
查看许可证

### 当前浏览上下文：

cs.AI
< 上一页
|
下一页 >
新
|
近期
|
2023-10
更改为按以下类别浏览：
cs

### 参考文献与引用

NASA ADS
Google Scholar
Semantic Scholar

### 2 个博客链接

（
这是什么？
）
导出 BibTeX 引用
正在加载...

## BibTeX 格式引用

×
正在加载...
数据提供方：

### 书签

文献工具

# 文献与引用工具

Bibliographic Explorer 开关
Bibliographic Explorer
（
Explorer 是什么？
）
Connected Papers 开关
Connected Papers
（
Connected Papers 是什么？
）
Litmaps 开关
Litmaps
（
Litmaps 是什么？
）
scite.ai 开关
scite Smart Citations
（
Smart Citations 是什么？
）
代码、数据、媒体

# 与本文相关的代码、数据和媒体

alphaXiv 开关
alphaXiv
（
alphaXiv 是什么？
）
代码链接开关
CatalyzeX Code Finder for Papers
（
CatalyzeX 是什么？
）
DagsHub 开关
DagsHub
（
DagsHub 是什么？
）
GotitPub 开关
Gotit.pub
（
GotitPub 是什么？
）
Huggingface 开关
Hugging Face
（
Huggingface 是什么？
）
ScienceCast 开关
ScienceCast
（
ScienceCast 是什么？
）
演示

# 演示

Replicate 开关
Replicate
（
Replicate 是什么？
）
Spaces 开关
Hugging Face Spaces
（
Spaces 是什么？
）
Spaces 开关
TXYZ.AI
（
TXYZ.AI 是什么？
）
相关论文

# 推荐器与搜索工具

链接到 Influence Flower
Influence Flower
（
Influence Flowers 是什么？
）
Core 推荐器开关
CORE Recommender
（
CORE 是什么？
）
作者
会议/期刊
机构
主题
关于 arXivLabs

# arXivLabs：与社区合作者开展的实验性项目

arXivLabs 是一个框架，允许合作者直接在我们的网站上开发和分享新的 arXiv 功能。
与 arXivLabs 合作的个人和组织都秉持并接受了我们的价值观：开放、社区、卓越和用户数据隐私。arXiv 致力于这些价值观，并且只与遵守这些价值观的合作伙伴合作。
有一个能为 arXiv 社区带来价值的项目想法？
了解有关 arXivLabs 的更多信息
。
本文的哪些作者是 endorsers？
|
禁用 MathJax
(
什么是 MathJax？
)
