# 本地计算机使用练习

这是一个无需安装依赖、无需 API Key、没有后端的静态练习页。它只在当前浏览器内存中维护两张合成发票；刷新页面即可重置。浏览器只从本机 HTTP 服务读取页面和脚本，不调用外部网络 API，也不会连接真实系统。

从仓库根目录运行：

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory examples/computer-use-safety
```

然后访问 <http://localhost:8765/>。练习任务和验收证据见 [`TASK.md`](TASK.md)。

控制器规则可用 Node.js 内置测试验证：

```bash
node --test examples/computer-use-safety/test_controller.mjs
```

本地页面不提供盲测登记或结果收集后台。若要评估多个学习者，应先离线保存各自的作答和评分记录；只有明确需要多人协作、身份管理或集中汇总时，才另行设计服务端存储与访问控制。
