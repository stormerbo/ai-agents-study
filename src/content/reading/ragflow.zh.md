<div align="center">
<a href="https://cloud.ragflow.io/">
<img src="https://raw.githubusercontent.com/infiniflow/ragflow/main/web/src/assets/logo-with-text.svg" width="520" alt="ragflow logo">
</a>
</div>

<p align="center">
  <a href="./README.md"><img alt="英文版 README" src="https://img.shields.io/badge/English-DBEDFA"></a>
  <a href="./README_zh.md"><img alt="简体中文版自述文件" src="https://img.shields.io/badge/简体中文-DFE0E5"></a>
  <a href="./README_tzh.md"><img alt="繁體版中文自述文件" src="https://img.shields.io/badge/繁體中文-DFE0E5"></a>
  <a href="./README_ja.md"><img alt="日本語のREADME" src="https://img.shields.io/badge/日本語-DFE0E5"></a>
  <a href="./README_ko.md"><img alt="한국어" src="https://img.shields.io/badge/한국어-DFE0E5"></a>
  <a href="./README_fr.md"><img alt="法文版 README" src="https://img.shields.io/badge/Français-DFE0E5"></a>
  <a href="./README_id.md"><img alt="Bahasa Indonesia" src="https://img.shields.io/badge/Bahasa Indonesia-DFE0E5"></a>
  <a href="./README_pt_br.md"><img alt="Português(Brasil)" src="https://img.shields.io/badge/Português(Brasil)-DFE0E5"></a>
  <a href="./README_ar.md"><img alt="阿拉伯文版 README" src="https://img.shields.io/badge/Arabic-DFE0E5"></a>
  <a href="./README_tr.md"><img alt="Türkçe README" src="https://img.shields.io/badge/Türkçe-DFE0E5"></a>
  <a href="./README_ru.md"><img alt="俄文版 README" src="https://img.shields.io/badge/Русский-DFE0E5"></a>
</p>

<p align="center">
    <a href="https://x.com/intent/follow?screen_name=infiniflowai" target="_blank">
        <img src="https://img.shields.io/twitter/follow/infiniflow?logo=X&color=%20%23f5f5f5" alt="在 X(Twitter) 上关注">
    </a>
    <a href="https://cloud.ragflow.io" target="_blank">
        <img alt="静态徽章" src="https://img.shields.io/badge/Get-Started-4e6b99">
    </a>
    <a href="https://hub.docker.com/r/infiniflow/ragflow" target="_blank">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/infiniflow/ragflow-stats/main/badges/docker-pulls.json&style=flat-square&logo=docker&logoColor=white" alt="RAGFlow Docker image downloads">
    </a>
    <a href="https://github.com/infiniflow/ragflow/releases/latest">
        <img src="https://img.shields.io/github/v/release/infiniflow/ragflow?color=blue&label=Latest%20Release" alt="Latest Release">
    </a>
    <a href="https://github.com/infiniflow/ragflow/blob/main/LICENSE">
        <img height="21" src="https://img.shields.io/badge/License-Apache--2.0-ffffff?labelColor=d4eaf7&color=2e6cc4" alt="license">
    </a>
</p>

<h4 align="center">
  <a href="https://cloud.ragflow.io">Cloud</a> |
  <a href="https://ragflow.io/docs/dev/">Documentation</a> |
  <a href="https://github.com/infiniflow/ragflow/issues/12241">Roadmap</a> |
  <a href="https://discord.gg/NjYzJD3GM3">Discord</a>
</h4>

<div align="center" style="margin-top:20px;margin-bottom:20px;">
<img alt="RAGFlow in the GitHub Octoverse" src="https://raw.githubusercontent.com/infiniflow/ragflow-docs/refs/heads/image/image/ragflow-octoverse.png" width="1200"/>
</div>

<div align="center">
<a href="https://trendshift.io/repositories/9064" target="_blank"><img src="https://trendshift.io/api/badge/repositories/9064" alt="infiniflow%2Fragflow | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</div>

<details open>
<summary><b>📕 目录</b></summary>

- 💡 [什么是 RAGFlow?](#-what-is-ragflow)
- 🎮 [快速开始](#-get-started)
- 🔥 [最新更新](#-latest-updates)
- 🌟 [核心特性](#-key-features)
- 🔎 [系统架构](#-system-architecture)
- 🏠 [本地部署](#-local-deployment)
- 📚 [文档](#-documentation)
- 📜 [路线图](#-roadmap)
- 🏄 [社区](#-community)
- 🙌 [贡献](#-contributing)

</details>

## 💡 什么是 RAGFlow?

[RAGFlow](https://ragflow.io/) 是一个领先的开源检索增强生成（[RAG](https://ragflow.io/basics/what-is-rag)）引擎，将前沿的 RAG 与 Agent 能力融合，为 LLM 打造卓越的上下文层。它提供精简的 RAG 工作流，可适配任意规模的企业。依托融合的[上下文引擎](https://ragflow.io/basics/what-is-agent-context-engine)与预置 agent 模板，RAGFlow 让开发者能够以卓越的效率和精度，将复杂数据转化为高保真、可投入生产的 AI 系统。

## 🎮 快速开始

试用我们的云服务：[https://cloud.ragflow.io](https://cloud.ragflow.io)。

本地部署请参见[本地部署](#-local-deployment)。

<div align="center" style="margin-top:20px;margin-bottom:20px;">
<img alt="Chunking demonstration" src="https://raw.githubusercontent.com/infiniflow/ragflow-docs/refs/heads/image/image/chunking.gif" width="1200"/>
<img alt="Agentic workflow demonstration" src="https://raw.githubusercontent.com/infiniflow/ragflow-docs/refs/heads/image/image/agentic-dark.gif" width="1200"/>
</div>

## 🔥 最新更新

- 2026-09-29 RAGFlow 1.0.0-rc1 发布。
- 2026-09-10 新增通过 sitemap 摄取网站内容。
- 2026-08-19 引入知识编译（Knowledge Compilation），可在文档和数据集级别生成 Wiki、Graph、Tree、PageIndex、Mind Map、Timeline 和 Skill。
- 2026-08-19 引入 Agentic RAG，支持 Low、Medium、High 和 Ultra 思考模式。
- 2026-07-02 新增 Google BigQuery 数据源摄取与增量同步。

更多更新请参见[完整发布说明](./docs/release_notes.md)。

## 🎉 敬请关注

⭐️ 为我们的仓库点 Star，及时获取令人期待的新功能和改进！第一时间收到新版本通知！🌟

<div align="center" style="margin-top:20px;margin-bottom:20px;">
<img alt="RAGFlow feature updates" src="https://github.com/user-attachments/assets/18c9707e-b8aa-4caf-a154-037089c105ba" width="1200"/>
</div>

## 🌟 核心特性

### 🍭 **“高质量输入，高质量输出”**

- 基于深度文档理解，从格式复杂的非结构化数据中提取知识。
- 在字面意义上无限 token 的“数据大海”中“捞针”。

### 🍱 **基于模板的分块**

- 智能且可解释。
- 提供大量模板可供选择。

### 🧩 **知识编译**

- 在文档和数据集级别将内容编译为结构化知识产物。
- 使用编译模板生成 Wiki、Graph、Tree、PageIndex、Mind Map、Timeline 和 Skill，以满足不同的知识组织和复用需求。
- 配置编译模型和处理规则，并查看、更新和重新生成知识产物。

### 🧠 **Agentic Retrieval**

- 针对复杂问题执行多步检索：模型分析问题，并在需要时将其分解、检索知识并验证证据。
- 通过多轮检索和推理收集更完整的上下文，以帮助生成有充分依据的答案。
- 根据问题复杂度选择 Low、Medium、High 或 Ultra 思考模式，以控制检索和推理深度。

### 🌱 **有依据的引用，减少幻觉**

- 文本分块可视化，允许人工干预。
- 快速查看关键参考和可追溯引用，以支持有依据的答案。

### 🍔 **兼容异构数据源**

- 支持 Word、Slides、Excel、TXT、图片、扫描件、结构化数据、网页等。

### 🛀 **自动化且轻松的 RAG 工作流**

- 面向个人和大型企业 streamlined 的 RAG 编排。
- 可配置的 LLM 以及 embedding 模型。
- 多路召回与融合重排序相配合。
- 直观的 API，可与业务无缝集成。

## 🔎 系统架构

<div align="center" style="margin-top:20px;margin-bottom:20px;">
<img src="https://raw.githubusercontent.com/infiniflow/ragflow-docs/main/images/structure.jpg" alt="RAGFlow system architecture" width="1000" />
</div>

## 🏠 本地部署

### 🐳 Docker 部署

#### 📝 Docker 部署前提条件

- 推荐起始配置：4 核 CPU、16 GB 内存、50 GB 可用磁盘空间。实际需求取决于文档引擎、数据量、解析任务和并发量。本地模型和其他可选组件可能需要额外资源。
- Docker >= 24.0.0 且 Docker Compose >= v2.26.1
- [gVisor](https://gvisor.dev/docs/user_guide/install/)：仅在使用 Self-Managed container Sandbox 时需要。

Docker 部署不要求在宿主机上安装 Go 编译器。Self-Managed container Sandbox 需要 gVisor；其他 Sandbox 提供方不要求在 RAGFlow 宿主机上安装 gVisor。

> [!TIP]
> 如果你尚未在本地机器（Windows、Mac 或 Linux）上安装 Docker，请参阅 [Install Docker Engine](https://docs.docker.com/engine/install/)。

#### 🚀 启动服务器

1. 如果使用 Elasticsearch，请将 Docker 宿主机上的 `vm.max_map_count` 设置为至少 262144。使用 Infinity 时通常无需此步骤：

   > 查看 `vm.max_map_count` 的值：
   >
   > ```bash
   > sysctl vm.max_map_count
   > ```
   >
   > 如果你使用 Elasticsearch 且该值低于 262144，请重新设置：
   >
   > ```bash
   > # In this case, we set it to 262144:
   > sudo sysctl -w vm.max_map_count=262144
   > ```
   >
   > 此更改将在系统重启后被重置。为确保更改永久生效，请在 **/etc/sysctl.conf** 中相应添加或更新
   > `vm.max_map_count` 值：
   >
   > ```bash
   > vm.max_map_count=262144
   > ```

2. 克隆仓库：

   ```bash
   git clone https://github.com/infiniflow/ragflow.git
   ```

3. 检出 Go 发布标签，并使用 Docker Compose 启动预构建的 Go 镜像：

   > [!NOTE]
   > `v1.0.0-rc1` tag 及之后的 release tag 使用 Go 实现。仅当你需要在本地构建镜像时，才参阅 [Go Docker 镜像构建与平台支持指南](./docs/develop/build_docker_image.mdx)。

   > ```bash
   > # 进入 Docker 部署目录。
   > cd ragflow/docker
   > # 检出 Go v1.0.0-rc1 release tag。
   > git checkout v1.0.0-rc1
   > # 在后台启动 Go 服务及其依赖项。
   > docker compose -f docker-compose.yml up -d
   > ```

   > 在默认 MySQL 配置中，Go 镜像 entrypoint 会先运行数据库迁移，然后通过 `bin/ragflow_server` 启动 Syncer、Admin、API 和 Ingestor。

   > 在 RAGFlow 开源 1.0 版本中，DeepDoc 使用 CPU inference 进行布局分析、OCR 和表格识别。

4. 启动后检查服务状态和 API 就绪情况：

   ```bash
   docker ps
   ```

   上述命令会显示依赖状态。RAGFlow 自身未定义 Compose healthcheck；通过其 API 确认就绪情况：

   ```bash
   curl -f http://localhost/api/v1/system/healthz
   ```

   返回 HTTP 200 响应表示已就绪。如果你更改了 `SVR_WEB_HTTP_PORT`，请在健康检查 URL 中使用该端口。如果启动失败，请使用 `docker logs --tail 50 <service>` 检查相关服务日志。

5. 在 Web 浏览器中，输入服务器的 IP 地址并登录 RAGFlow。

   > 使用默认设置时，你只需输入 `http://IP_OF_YOUR_MACHINE`（**无需**端口号），因为在使用默认配置时可以省略默认 HTTP 服务端口 `80`。

6. 登录后，在 model provider 页面添加 LLM、embedding 和 reranker，包括模型名称、服务地址和 API key。

#### ⚙️ Docker 配置与调整

Go Docker 部署使用 `docker/.env` 和 `docker/docker-compose.yml`，使用 Kvrocks 作为缓存和 Checkpoint 存储，并使用 NATS JetStream 作为消息队列。按 [Docker 配置指南](./docker/README.md) 中所述配置镜像、端口、密码、文档引擎和模型镜像源。macOS 暂不被 Go 后端支持（请使用 Linux x86_64 主机）；平台支持详情见 [Go Docker 镜像构建指南](./docs/develop/build_docker_image.mdx)。

关于文档引擎变更、配置更新、重启服务以及保留或移除现有数据，请遵循 Docker 配置指南。

### 🔨 从源码启动 Go 服务

#### 📝 源码构建前提条件

安装 `go.mod` 中指定的 Go 版本（当前为 Go 1.27）、Clang 20、LLD 20、CMake ≥ 4.0、PCRE2 开发文件，以及 CGO 所需的本机库。Node.js 和 npm 仅在开发 React 前端时需要。

1. 克隆仓库并安装 `go.mod` 中指定的 Go 版本（当前为 Go 1.27）、Clang 20、LLD 20、CMake ≥ 4.0 和 PCRE2 开发文件。Go 服务依赖 CGO 和本机静态库；[build.sh](./build.sh) 会设置所需的构建参数。

   ```bash
   git clone https://github.com/infiniflow/ragflow.git
   cd ragflow
   ```

2. 使用 [Go 依赖下载脚本](./ragflow_deps/download_deps.py) 准备本机库、模型文件和 tokenizer 资源，然后构建 Go 服务：

   ```bash
   python3 -m venv /tmp/ragflow-go-download-venv
   /tmp/ragflow-go-download-venv/bin/python -m pip install requests huggingface-hub
   /tmp/ragflow-go-download-venv/bin/python ragflow_deps/download_deps.py
   bash build.sh --all
   ```

该脚本会准备 Go 构建所需的 native libraries 和模型资源，并需要 `requests` 和 `huggingface-hub`。如果你已通过其他方式准备好相同的资源，请跳过此步骤。从仓库根目录启动时，Go 服务会自动找到 `internal/rag/res/deepdoc`；若要从其他目录启动，请将 `DEEPDOC_MODEL_DIR` 设置为其绝对路径。

3. 启动本地依赖，并确保 **conf/service_conf.yaml** 中的 hosts 和 ports 指向可从宿主机访问的地址。Go 源码服务连接 Compose 暴露的 Kvrocks（位于 `localhost:6379`），而 Go Docker 服务则通过容器网络连接 Kvrocks。如果使用默认的 Elasticsearch 引擎，请先将 Docker 宿主机上的 `vm.max_map_count` 设置为至少 `262144`。

   ```bash
   sudo sysctl -w vm.max_map_count=262144
   docker compose --env-file docker/.env -f docker/docker-compose-base.yml \
     up -d --wait es01 mysql minio nats kvrocks clickhouse
   ```

4. 先迁移数据库，然后在五个独立终端中按顺序启动 Go 服务。以下每条命令都请在仓库根目录下运行。保持四个服务终端持续运行。迁移命令不需要 `RAGFLOW_DEV_MODE`；在开发环境中，为 Admin、Ingestor、Syncer 和 API 设置 `RAGFLOW_DEV_MODE=true`。迁移完成后关闭迁移终端。

   终端 1：迁移数据库。

   ```bash
   ./bin/ragflow_server --migrate
   ```

   终端 2：启动 Admin（目标端口 `9381`）。

   ```bash
   RAGFLOW_DEV_MODE=true ./bin/ragflow_server --admin
   ```

   终端 3：启动 Ingestor。

   ```bash
   RAGFLOW_DEV_MODE=true ./bin/ragflow_server --ingestor
   ```

   终端 4：启动 Syncer。

   ```bash
   RAGFLOW_DEV_MODE=true ./bin/ragflow_server --syncer
   ```

   终端 5：启动 API（目标端口 `9380`）。

   ```bash
   RAGFLOW_DEV_MODE=true ./bin/ragflow_server --api
   ```

   各启动模式的工作方式如下：
   - `--migrate`：运行数据库迁移，完成后退出。
   - `--admin`：启动 Admin 服务，用于管理和初始化操作。
   - `--ingestor`：启动 Ingestor 服务，用于数据摄入和解析任务。
   - `--syncer`：启动 Syncer 服务，用于数据同步任务。
   - `--api`：启动 API 服务，供 Web UI、SDK 和外部客户端使用。

   `RAGFLOW_DEV_MODE=true` 仅用于开发；它会禁用代码与数据库迁移版本之间的降级检查，但不会运行迁移，也不会更改数据库 schema。请勿在生产环境中设置它。请先启动 Admin，再启动其他服务。数据库迁移完成后，`RAGFLOW_DEV_MODE=true bash build.sh --run` 可以方便地启动 Admin、Ingestor 和 API。它不会启动 Syncer；如需完整的服务链，请使用 `RAGFLOW_DEV_MODE=true ./bin/ragflow_server --syncer` 单独启动它。

5. 仅在开发前端时，安装 Node.js 和 npm，然后启动 React 前端：

   ```bash
   cd web
   npm install
   API_PROXY_SCHEME=go npm run dev
   ```

   在另一个终端中，确认 Go API 已就绪：

   ```bash
   curl -f http://127.0.0.1:9380/api/v1/system/healthz
   ```

   HTTP 200 响应表示 API 正常响应。完整的前端、ClickHouse 和 DeepDoc 验证步骤请参见 [Launch Service from Source](./docs/develop/launch_ragflow_from_source.md#5-verify-the-startup)。

   开发完成后，在每个服务终端中按 `Ctrl+C` 停止进程。若要停止依赖项但保留容器以便下次使用，请运行 `docker compose --env-file docker/.env -f docker/docker-compose-base.yml stop es01 mysql minio nats kvrocks clickhouse`。若要移除依赖容器和 Compose 网络，同时保留命名数据卷，请运行 `docker compose --env-file docker/.env -f docker/docker-compose-base.yml down`。

详见 [Launch Service from Source](./docs/develop/launch_ragflow_from_source.md)。

## 📚 文档

- [Quickstart](https://ragflow.io/docs/dev/)
- [Configuration](https://ragflow.io/docs/dev/configurations)
- [Release notes](https://ragflow.io/docs/dev/release_notes)
- [User guides](https://ragflow.io/docs/category/user-guides)
- [Developer guides](https://ragflow.io/docs/category/developer-guides)
- [References](https://ragflow.io/docs/dev/category/references)
- [FAQs](https://ragflow.io/docs/dev/faq)

## 📜 路线图

参见 [RAGFlow Roadmap 2026](https://github.com/infiniflow/ragflow/issues/12241)

## 🏄 社区

- [Discord](https://discord.gg/NjYzJD3GM3)
- [X](https://x.com/infiniflowai)
- [GitHub Discussions](https://github.com/orgs/infiniflow/discussions)

## 🙌 贡献

RAGFlow 通过开源协作蓬勃发展。本着这一精神，我们欢迎社区贡献者的多样化贡献。
如果您想参与其中，请先查阅我们的 [Contribution Guidelines](https://ragflow.io/docs/dev/contributing)。
