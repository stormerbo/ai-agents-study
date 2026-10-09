查看题为 ReAct: Synergizing Reasoning and Acting in Language Models 的论文 PDF，作者为 Shunyu Yao 及其他 6 位作者
查看 PDF
HTML（实验性）
摘要：
尽管大型语言模型（LLMs）在语言理解和交互式决策等任务中展现出了令人印象深刻的能力，但它们在推理（例如 chain-of-thought prompting）和行动（例如 action plan generation）方面的能力主要被作为彼此独立的话题进行研究。在本文中，我们探索使用 LLMs 以交错方式生成 reasoning traces 和 task-specific actions，从而使两者之间实现更大的协同：reasoning traces 帮助模型归纳、跟踪和更新 action plans，并处理异常，而 actions 则使其能够与外部来源（如 knowledge bases 或 environments）交互，以收集额外信息。我们将我们的方法命名为 ReAct，并将其应用于多种语言和决策任务，证明其相较于 state-of-the-art baselines 的有效性，同时相较于没有 reasoning 或 acting 组件的方法，具有更好的人类可解释性和可信度。具体而言，在 question answering（HotpotQA）和 fact verification（Fever）上，ReAct 通过与一个简单的 Wikipedia API 交互，克服了 chain-of-thought reasoning 中普遍存在的 hallucination 和 error propagation 问题，并生成了类似人类的 task-solving trajectories，这些轨迹比没有 reasoning traces 的 baselines 更具可解释性。在两个交互式决策基准（ALFWorld 和 WebShop）上，ReAct 分别以 34% 和 10% 的绝对成功率优于 imitation 和 reinforcement learning 方法，同时仅通过一个或两个 in-context examples 进行 prompting。项目站点及代码：
this https URL
Comments：
v3 是 ICLR camera ready 版本，修复了一些拼写错误。项目站点及代码：
this https URL
Subjects：
Computation and Language (cs.CL)
；Artificial Intelligence (cs.AI)；Machine Learning (cs.LG)
引用为：
arXiv:2210.03629
[cs.CL]
（或
arXiv:2210.03629v3
[cs.CL]
用于此版本）
https://doi.org/10.48550/arXiv.2210.03629
聚焦以了解更多
arXiv 通过 DataCite 颁发的 DOI

## 提交历史

来自：Shunyu Yao [
查看电子邮件
]
[v1]
Thu, 6 Oct 2022 01:00:32 UTC (538 KB)
[v2]
Sun, 27 Nov 2022 22:55:54 UTC (538 KB)
[v3]
Fri, 10 Mar 2023 01:00:17 UTC (1,256 KB)
全文链接：

## 访问论文：

查看题为 ReAct: Synergizing Reasoning and Acting in Language Models 的论文 PDF，作者为 Shunyu Yao 和另外 6 位作者
查看 PDF
HTML（实验性）
TeX Source
查看许可证

### 当前浏览上下文：

cs.CL
< 上一个
|
下一个 >
新
|
近期
|
2022-10
切换浏览类别为：
cs
cs.AI
cs.LG

### 参考文献与引用

NASA ADS
Google Scholar
Semantic Scholar

### 13 个博客链接

(
这是什么？
)
导出 BibTeX 引用
加载中...

## BibTeX 格式引用

×
加载中...
数据提供方：

### 书签

书目工具

# 书目与引用工具

Bibliographic Explorer 开关
Bibliographic Explorer
(
什么是 Explorer？
)
Connected Papers 开关
Connected Papers
(
什么是 Connected Papers？
)
Litmaps 开关
Litmaps
(
什么是 Litmaps？
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
什么是 alphaXiv？
)
Links to Code 开关
CatalyzeX Code Finder for Papers
(
什么是 CatalyzeX？
)
DagsHub 开关
DagsHub
(
什么是 DagsHub？
)
GotitPub 开关
Gotit.pub
(
什么是 GotitPub？
)
Huggingface 开关
Hugging Face
(
什么是 Huggingface？
)
ScienceCast 开关
ScienceCast
(
什么是 ScienceCast？
)
演示

# 演示

Replicate 开关
Replicate
(
什么是 Replicate？
)
Spaces 开关
Hugging Face Spaces
(
什么是 Spaces？
)
Spaces 开关
TXYZ.AI
(
什么是 TXYZ.AI？
)
相关论文

# 推荐器与搜索工具

链接到 Influence Flower
Influence Flower
(
什么是 Influence Flowers？
)
Core recommender 开关
CORE Recommender
(
什么是 CORE？
)
作者
会议/期刊
机构
主题
关于 arXivLabs

# arXivLabs：与社区合作者的实验性项目

arXivLabs 是一个框架，允许合作者直接在我们的网站上开发和分享新的 arXiv 功能。
与 arXivLabs 合作的个人和组织都认同并接受了我们的价值观：开放、社区、卓越和用户数据隐私。arXiv 致力于这些价值观，并且只与遵守这些价值观的合作伙伴合作。
有一个能为 arXiv 社区增加价值的项目想法？
了解有关 arXivLabs 的更多信息
。
本文的哪些作者是 endorsers？
|
禁用 MathJax
(
什么是 MathJax？
)
