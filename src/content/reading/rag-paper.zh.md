查看题为《Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks》的论文PDF，作者为Patrick Lewis及其他11位作者
查看PDF
HTML（实验性）
摘要：
大型预训练语言模型已被证明在其参数中存储了事实知识，并在下游NLP任务上微调时达到了最先进的结果。然而，它们访问和精确操作知识的能力仍然有限，因此在知识密集型任务上，它们的表现落后于特定任务的架构。此外，为其决策提供出处和更新其世界知识仍是未解决的研究问题。具有对显式非参数记忆的可微分访问机制的预训练模型可以克服这一问题，但迄今为止仅在抽取式下游任务中进行了研究。我们探索了一种通用的检索增强生成（RAG）微调方法——这些模型结合了预训练的参数和非参数记忆来进行语言生成。我们引入了RAG模型，其中参数记忆是一个预训练的seq2seq模型，非参数记忆是Wikipedia的稠密向量索引，通过预训练的神经检索器访问。我们比较了两种RAG公式，一种是在整个生成序列中以相同的检索段落为条件，另一种是每个token可以使用不同的段落。我们在广泛的知识密集型NLP任务上微调和评估了我们的模型，并在三个开放域QA任务上设定了最先进水平，超越了参数seq2seq模型和特定任务的检索-抽取架构。对于语言生成任务，我们发现RAG模型比最先进的仅参数seq2seq基线生成更具体、多样和事实性的语言。
评论：
Accepted at NeurIPS 2020
主题：
Computation and Language (cs.CL)
；Machine Learning (cs.LG)
引用为：
arXiv:2005.11401
[cs.CL]
（或
arXiv:2005.11401v4
[cs.CL]
用于此版本）
https://doi.org/10.48550/arXiv.2005.11401
聚焦以了解更多
arXiv 颁发的 DOI，经由 DataCite

## 提交历史

来自：Patrick Lewis [
查看电子邮件
]
[v1]
2020年5月22日星期五 21:34:34 UTC (698 KB)
[v2]
2020年12月7日星期一 16:23:06 UTC (767 KB)
[v3]
2021年3月29日星期一 10:12:16 UTC (767 KB)
[v4]
2021年4月12日星期一 15:42:18 UTC (767 KB)
全文链接：

## 访问论文：

查看 PDF：论文标题为 Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks，作者为 Patrick Lewis 及其他 11 位作者
查看 PDF
HTML（实验性）
TeX 源文件
查看许可证

### 当前浏览上下文：

cs.CL
< 上一页
|
下一页 >
新
|
最近
|
2020-05
切换为按以下方式浏览：
cs
cs.LG

### 参考文献与引用

NASA ADS
Google Scholar
Semantic Scholar

### 13 个博客链接

(
这是什么？
)

### DBLP - CS 文献目录

列表
|
bibtex
Ethan Perez
Aleksandra Piktus
Fabio Petroni
Vladimir Karpukhin
Naman Goyal
…
导出 BibTeX 引用
加载中...

## BibTeX 格式化引用

×
加载中...
数据提供方：

### 书签

书目工具

# 文献与引用工具

Bibliographic Explorer 开关
Bibliographic Explorer
(
Explorer 是什么？
)
Connected Papers 开关
Connected Papers
(
Connected Papers 是什么？
)
Litmaps 开关
Litmaps
(
Litmaps 是什么？
)
scite.ai 开关
scite Smart Citations
(
什么是 Smart Citations？
)
代码、数据、媒体

# 与本文相关的代码、数据和媒体

alphaXiv 开关
alphaXiv
(
alphaXiv 是什么？
)
代码链接开关
CatalyzeX Code Finder for Papers
(
CatalyzeX 是什么？
)
DagsHub 开关
DagsHub
(
DagsHub 是什么？
)
GotitPub 开关
Gotit.pub
(
GotitPub 是什么？
)
Huggingface 开关
Hugging Face
(
Huggingface 是什么？
)
ScienceCast 开关
ScienceCast
(
ScienceCast 是什么？
)
演示

# 演示

Replicate 开关
Replicate
(
Replicate 是什么？
)
Spaces 开关
Hugging Face Spaces
(
Spaces 是什么？
)
Spaces 开关
TXYZ.AI
(
TXYZ.AI 是什么？
)
相关论文

# 推荐器与搜索工具

链接到 Influence Flower
Influence Flower
(
Influence Flowers 是什么？
)
核心推荐器开关
CORE推荐器
(
什么是CORE？
)
作者
会议/期刊
机构
主题
关于arXivLabs

# arXivLabs：与社区合作者的实验项目

arXivLabs是一个框架，允许合作者直接在我们的网站上开发和分享新的arXiv功能。
与arXivLabs合作的个人和组织都认同并接受了我们的价值观：开放、社区、卓越和用户数据隐私。arXiv致力于这些价值观，并且只与遵守这些价值观的合作伙伴合作。
对为arXiv社区增加价值的项目有想法吗？
了解有关arXivLabs的更多信息
。
这篇论文的哪些作者是背书人？
|
禁用MathJax
(
什么是MathJax？
)
