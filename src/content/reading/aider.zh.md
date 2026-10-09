<p align="center">
    <a href="https://aider.chat/"><img src="https://aider.chat/assets/logo.svg" alt="Aider Logo" width="300"></a>
</p>

<h1 align="center">
在终端中进行 AI 结对编程
</h1>

<p align="center">
Aider 让你与 LLM 结对编程，既可以启动一个新项目，也可以在现有代码库上继续开发。
</p>

<p align="center">
  <img
    src="https://aider.chat/assets/screencast.svg"
    alt="aider screencast"
  >
</p>

<p align="center">
<!--[[[cog
from scripts.homepage import get_badges_md
text = get_badges_md()
cog.out(text)
]]]-->
  <a href="https://github.com/Aider-AI/aider/stargazers"><img alt="GitHub Stars" title="Total number of GitHub stars the Aider project has received"
src="https://img.shields.io/github/stars/Aider-AI/aider?style=flat-square&logo=github&color=f1c40f&labelColor=555555"/></a>
  <a href="https://pypi.org/project/aider-chat/"><img alt="PyPI Downloads" title="Total number of installations via pip from PyPI"
src="https://img.shields.io/badge/📦%20Installs-6.8M-2ecc71?style=flat-square&labelColor=555555"/></a>
  <img alt="Tokens per week" title="Number of tokens processed weekly by Aider users"
src="https://img.shields.io/badge/📈%20Tokens%2Fweek-15B-3498db?style=flat-square&labelColor=555555"/>
  <a href="https://openrouter.ai/#options-menu"><img alt="OpenRouter Ranking" title="Aider's ranking among applications on the OpenRouter platform"
src="https://img.shields.io/badge/🏆%20OpenRouter-Top%2020-9b59b6?style=flat-square&labelColor=555555"/></a>
  <a href="https://aider.chat/HISTORY.html"><img alt="Singularity" title="Percentage of the new code in Aider's last release written by Aider itself"
src="https://img.shields.io/badge/🔄%20Singularity-88%25-e74c3c?style=flat-square&labelColor=555555"/></a>
<!--[[[end]]]-->  
</p>

## Features

### [Cloud and local LLMs](https://aider.chat/docs/llms.html)

<a href="https://aider.chat/docs/llms.html"><img src="https://aider.chat/assets/icons/brain.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
Aider 与 Claude 3.7 Sonnet、DeepSeek R1 & Chat V3、OpenAI o1、o3-mini & GPT-4o 配合效果最佳，但几乎可以连接任何 LLM，包括本地模型。

<br>

### [映射你的代码库](https://aider.chat/docs/repomap.html)

<a href="https://aider.chat/docs/repomap.html"><img src="https://aider.chat/assets/icons/map-outline.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
Aider 会为你的整个代码库生成一张地图，这有助于它在更大的项目中良好运作。

<br>

### [100+ 种代码语言](https://aider.chat/docs/languages.html)

<a href="https://aider.chat/docs/languages.html"><img src="https://aider.chat/assets/icons/code-tags.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
Aider 可用于大多数流行的编程语言：python、javascript、rust、ruby、go、cpp、php、html、css 以及数十种其他语言。

<br>

### [Git 集成](https://aider.chat/docs/git.html)

<a href="https://aider.chat/docs/git.html"><img src="https://aider.chat/assets/icons/source-branch.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
Aider 会自动提交更改，并附上合理的 commit messages。使用熟悉的 git 工具即可轻松地 diff、管理和撤销 AI 更改。

<br>

### [在你的 IDE 中使用](https://aider.chat/docs/usage/watch.html)

<a href="https://aider.chat/docs/usage/watch.html"><img src="https://aider.chat/assets/icons/monitor.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
在你最喜欢的 IDE 或编辑器中使用 aider。通过向代码添加注释来请求更改，aider 就会开始工作。

<br>

### [图片与网页](https://aider.chat/docs/usage/images-urls.html)

<a href="https://aider.chat/docs/usage/images-urls.html"><img src="https://aider.chat/assets/icons/image-multiple.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
向 chat 中添加图片和网页，以提供可视化上下文、截图、参考文档等。

<br>

### [语音到代码](https://aider.chat/docs/usage/voice.html)

<a href="https://aider.chat/docs/usage/voice.html"><img src="https://aider.chat/assets/icons/microphone.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
用语音与 aider 讨论你的代码！用语音请求新功能、测试用例或 bug 修复，让 aider 来实现这些改动。

<br>

### [Linting 与 testing](https://aider.chat/docs/usage/lint-test.html)

<a href="https://aider.chat/docs/usage/lint-test.html"><img src="https://aider.chat/assets/icons/check-all.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
每次 aider 做出改动时，自动对代码进行 lint 和 test。Aider 可以修复你的 linter 和 test suite 检测出的问题。

<br>

### [复制/粘贴到 web chat](https://aider.chat/docs/usage/copypaste.html)

<a href="https://aider.chat/docs/usage/copypaste.html"><img src="https://aider.chat/assets/icons/content-copy.svg" width="32" height="32" align="left" valign="middle" style="margin-right:10px"></a>
通过任意 LLM 的 web chat 界面与其协作。Aider 简化了在浏览器中来回复制/粘贴代码上下文与编辑内容的流程。

## Getting Started

```bash
python -m pip install aider-install
aider-install

# Change directory into your codebase
cd /to/your/project

# DeepSeek
aider --model deepseek --api-key deepseek=<key>

# Claude 3.7 Sonnet
aider --model sonnet --api-key anthropic=<key>

# o3-mini
aider --model o3-mini --api-key openai=<key>
```

详情请参见[安装说明](https://aider.chat/docs/install.html)和[使用文档](https://aider.chat/docs/usage.html)。

## 更多信息

### 文档

- [安装指南](https://aider.chat/docs/install.html)
- [使用指南](https://aider.chat/docs/usage.html)
- [教程视频](https://aider.chat/docs/usage/tutorials.html)
- [连接 LLM](https://aider.chat/docs/llms.html)
- [配置选项](https://aider.chat/docs/config.html)
- [故障排除](https://aider.chat/docs/troubleshooting.html)
- [常见问题](https://aider.chat/docs/faq.html)

### 社区与资源

- [LLM 排行榜](https://aider.chat/docs/leaderboards/)
- [GitHub 仓库](https://github.com/Aider-AI/aider)
- [Discord 社区](https://discord.gg/Y7X7bhMQFV)
- [发布说明](https://aider.chat/HISTORY.html)
- [博客](https://aider.chat/blog/)

## 用户的赞誉

- _“我的生活改变了……Aider……它将震撼你的世界。”_ — [Eric S. Raymond 在 X 上](https://x.com/esrtweet/status/1910809356381413593)
- _“最好的免费开源 AI 编码助手。”_ — [IndyDevDan 在 YouTube 上](https://youtu.be/YALpX8oOn78)
- _“迄今为止最好的 AI 编码助手。”_ — [Matthew Berman 在 YouTube 上](https://www.youtube.com/watch?v=df8afeb1FY8)
- _“Aider……轻松让我的编码生产力翻了两番。”_ — [SOLAR_FIELDS 在 Hacker News 上](https://news.ycombinator.com/item?id=36212100)
- _“这是一个很酷的工作流……Aider 的人机工程设计对我来说很完美。”_ — [qup 在 Hacker News 上](https://news.ycombinator.com/item?id=38185326)
- _“这真的就像让你的资深开发者直接住在你的 Git 仓库里——太惊人了！”_ — [rappster 在 GitHub 上](https://github.com/Aider-AI/aider/issues/124)
- _“多么神奇的工具。它令人难以置信。”_ — [valyagolev 在 GitHub 上](https://github.com/Aider-AI/aider/issues/6#issue-1722897858)
- _“Aider 真是令人惊叹的东西！”_ — [cgrothaus 在 GitHub 上](https://github.com/Aider-AI/aider/issues/82#issuecomment-1631876700)
- _“这比我从头开始并做出最初几个可用版本要快得多。”_ — [Daniel Feldman 在 X 上](https://twitter.com/d_feldman/status/1662295077387923456)
- _“感谢 Aider！它真的让人感觉像是瞥见了编程的未来。”_ — [derwiki 在 Hacker News 上](https://news.ycombinator.com/item?id=38205643)
- _“这太棒了。它让我能够去做那些以前我觉得超出自己舒适区的事情。”_ — [Dougie 在 Discord 上](https://discord.com/channels/1131200896827654144/1174002618058678323/1174084556257775656)
- _“这个项目非常出色。”_ — [funkytaco 在 GitHub 上](https://github.com/Aider-AI/aider/issues/112#issuecomment-1637429008)
- _“了不起的项目，绝对是我用过的最好的 AI 编程助手。”_ — [joshuavial 在 GitHub 上](https://github.com/Aider-AI/aider/issues/84)
- _“我绝对喜欢使用 Aider……它让软件开发作为一种体验感觉轻松多了。”_ — [principalideal0 在 Discord 上](https://discord.com/channels/1131200896827654144/1133421607499595858/1229689636012691468)
- _“我一直在从……手术中恢复……aider……让我能够继续保持生产力。”_ — [codeninja 在 Reddit 上](https://www.reddit.com/r/OpenAI/s/nmNwkHy1zG)
- _“我是个 aider 上瘾者。我完成了比以前多得多的工作，但用的时间更少。”_ — [dandandan 在 Discord 上](https://discord.com/channels/1131200896827654144/1131200896827654149/1135913253483069470)
- _“Aider……毫不夸张地把其他所有东西都甩在了后面，完全没有任何竞争。”_ — [SystemSculpt 在 Discord 上](https://discord.com/channels/1131200896827654144/1131200896827654149/1178736602797846548)
- _“Aider 很棒，再结合 Sonnet 3.5，真的令人震撼。”_ — [Josh Dingus 在 Discord 上](https://discord.com/channels/1131200896827654144/1133060684540813372/1262374225298198548)
- _“毫无疑问，这是迄今为止最好的 AI 编程助手工具。”_ — [IndyDevDan 在 YouTube 上](https://www.youtube.com/watch?v=MPYFPvxfGZs)
- _“[Aider] 改变了我的日常编码工作流。它……能改变你的生活，这太令人震撼了。”_ — [maledorak 在 Discord 上](https://discord.com/channels/1131200896827654144/1131200896827654149/1258453375620747264)
- _“在现有代码库中做实际开发工作的最佳 agent。”_ — [Nick Dobos 在 X 上](https://twitter.com/NickADobos/status/1690408967963652097?s=20)
- _“我最喜欢的软件之一。在新范式上开辟道路！”_ — [Chris Wall 在 X 上](https://x.com/chris65536/status/1905053299251798432)
- _“Aider 对我和我的工作来说是一场革命。”_ — [Starry Hope 在 X 上](https://x.com/starryhopeblog/status/1904985812137132056)
- _“试试 aider！最好的 vibe code 方式之一。”_ — [Chris Wall 在 X 上](https://x.com/Chris65536/status/1905053418961391929)
- _“超级爱 Aider。”_ — [hztar 在 Hacker News 上](https://news.ycombinator.com/item?id=44035015)
- _“Aider 毫无疑问是最好的。而且它免费且开源。”_ — [AriyaSavakaLurker 在 Reddit 上](https://www.reddit.com/r/ChatGPTCoding/comments/1ik16y6/whats_your_take_on_aider/mbip39n/)
- _“Aider 也是我最好的朋友。”_ — [jzn21 在 Reddit 上](https://www.reddit.com/r/ChatGPTCoding/comments/1heuvuo/aider_vs_cline_vs_windsurf_vs_cursor/m27dcnb/)
- _“试试 Aider，值得一试。”_ — [jorgejhms 在 Reddit 上](https://www.reddit.com/r/ChatGPTCoding/comments/1heuvuo/aider_vs_cline_vs_windsurf_vs_cursor/m27cp99/)
- _“我喜欢 aider :)”_ — [Chenwei Cui 在 X 上](https://x.com/ccui42/status/1904965344999145698)
- _“Aider 是 LLM code gen 的精密工具……极简、深思熟虑，且能进行外科手术式的更改……同时让开发者保持掌控。”_ — [Reilly Sweetland 在 X 上](https://x.com/rsweetland/status/1904963807237259586)
- _“不敢相信 aider vibe code 了一个 650 LOC 的 feature，横跨 service 和 cli，今天一次性完成。”_ - [autopoietist 在 Discord 上](https://discord.com/channels/1131200896827654144/1131200896827654149/1355675042259796101)
- _"哦不，秘密泄露了！是的，Aider 是最好的编程工具。我强烈、强烈地推荐给任何人。"_ — [Joshua D Vander Hook 在 X 上](https://x.com/jodavaho/status/1911154899057795218)
- _"感谢 aider，我在过去两天内开始并完成了三个个人项目"_ — [joseph stalzyn 在 X 上](https://x.com/anitaheeder/status/1908338609645904160)
- _"使用 aider 作为我的日常主力工具已经超过一年了……我绝对喜爱这个工具，简直无法用言语形容。"_ — [koleok 在 Discord 上](https://discord.com/channels/1131200896827654144/1273248471394291754/1356727448372252783)
- _"Aider……是拿来对标基准的工具。"_ — [BeetleB 在 Hacker News 上](https://news.ycombinator.com/item?id=43930201)
- _"aider 真的很酷"_ — [kache 在 X 上](https://x.com/yacineMTB/status/1911224442430124387)
