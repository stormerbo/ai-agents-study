查看题为 Reflexion: Language Agents with Verbal Reinforcement Learning 的论文 PDF，作者为 Noah Shinn 及其他 5 位作者
查看 PDF
HTML（实验性）
摘要：
大型语言模型（LLM）越来越多地被用作目标驱动的 agent，与外部环境（例如游戏、编译器、API）进行交互。然而，这些 language agent 要像传统 reinforcement learning 方法那样快速高效地从试错中学习仍然具有挑战性，因为传统方法需要大量训练样本和昂贵的模型微调。我们提出 Reflexion，一种新的框架，它不通过更新权重，而是通过语言反馈来强化 language agent。具体而言，Reflexion agent 会对任务反馈信号进行口头反思，然后在 episodic memory buffer 中维护自己的反思文本，以在后续试验中诱导更好的决策。Reflexion 足够灵活，可以纳入各种类型（标量值或自由形式语言）和来源（外部或内部模拟）的反馈信号，并在多种任务（顺序决策、编码、语言推理）上相较于基线 agent 取得显著改进。例如，Reflexion 在 HumanEval 编码基准上达到 91% 的 pass@1 准确率，超过了此前达到 80% 的最先进 GPT-4。我们还使用不同的反馈信号、反馈整合方法和 agent 类型进行了消融与分析研究，并提供了关于它们如何影响性能的见解。
Comments：
v4 包含一些额外实验
Subjects：
Artificial Intelligence (cs.AI)
; Computation and Language (cs.CL); Machine Learning (cs.LG)
Cite as：
arXiv:2303.11366
[cs.AI]
(or
arXiv:2303.11366v4
[cs.AI]
for this version)
https://doi.org/10.48550/arXiv.2303.11366
Focus to learn more
arXiv-issued DOI via DataCite

## Submission history

From: Noah Shinn [
view email
]
[v1]
Mon, 20 Mar 2023 18:08:50 UTC (506 KB)
[v2]
Sun, 21 May 2023 06:20:36 UTC (404 KB)
[v3]
2023 年 6 月 10 日周六 04:32:30 UTC (396 KB)
[v4]
2023 年 10 月 10 日周二 05:21:45 UTC (386 KB)
全文链接：

## 访问论文：

查看题为 Reflexion: Language Agents with Verbal Reinforcement Learning 的论文 PDF，作者为 Noah Shinn 和另外 5 位作者
查看 PDF
HTML（实验性）
TeX 源码
查看许可证

### 当前浏览上下文：

cs.AI
< 上一页
|
下一页 >
新
|
最近
|
2023-03
切换到按以下分类浏览：
cs
cs.CL
cs.LG

### 参考文献与引用

NASA ADS
Google Scholar
Semantic Scholar

### 3 个博客链接

（
这是什么？
）
导出 BibTeX 引用
加载中...

## BibTeX 格式化引用

×
加载中...
数据提供方：

### 书签

书目工具

# 书目与引用工具

Bibliographic Explorer 开关
Bibliographic Explorer
（
什么是 Explorer？
）
Connected Papers 开关
Connected Papers
（
什么是 Connected Papers？
）
Litmaps 开关
Litmaps
（
什么是 Litmaps？
）
scite.ai 开关
scite Smart Citations
（
什么是 Smart Citations？
）
代码、数据、媒体

# 与本文相关的代码、数据和媒体

alphaXiv 开关
alphaXiv
（
什么是 alphaXiv？
）
代码链接开关
CatalyzeX Code Finder for Papers
（
什么是 CatalyzeX？
）
DagsHub 开关
DagsHub
（
什么是 DagsHub？
）
GotitPub 开关
Gotit.pub
（
什么是 GotitPub？
）
Huggingface 开关
Hugging Face
（
什么是 Huggingface？
）
ScienceCast 开关
ScienceCast
（
什么是 ScienceCast？
）
演示

# 演示

Replicate 开关
Replicate
（
什么是 Replicate？
）
Spaces 开关
Hugging Face Spaces
（
什么是 Spaces？
）
Spaces 开关
TXYZ.AI
（
什么是 TXYZ.AI？
）
相关论文

# 推荐器与搜索工具

链接到 Influence Flower
Influence Flower
（
什么是 Influence Flowers？
）
Core recommender 开关
CORE Recommender
（
什么是 CORE？
）
作者
会议/期刊
机构
主题
关于 arXivLabs

# arXivLabs：与社区合作者开展的实验性项目

arXivLabs 是一个框架，允许合作者直接在我们的网站上开发和分享新的 arXiv 功能。
与 arXivLabs 合作的个人和组织都已认同并接受了我们开放、社区、卓越和用户数据隐私的价值观。arXiv 致力于这些价值观，且只与遵循这些价值观的合作伙伴合作。
有一个能为 arXiv 社区带来价值的项目想法？
了解有关 arXivLabs 的更多信息
。
这篇论文的哪些作者是 endorser？
|
禁用 MathJax
(
什么是 MathJax？
)
