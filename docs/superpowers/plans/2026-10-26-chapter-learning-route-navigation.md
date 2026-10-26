### Task 5：自动、真实浏览器、视觉和辅助技术检查

- [ ] Step 1：分别执行并检查 pnpm test、pnpm typecheck、pnpm lint、pnpm build。
- [ ] Step 2：核验 overview stage 元数据、正文 availability、进度、本地说明和章卡所有字段；核验详情头所有字段、全部 outcomes、路线序号和 last/first/no-body/cross chapter href。
- [ ] Step 3：真实浏览器视口 1440×900、1280×640、320×640、375×812 CSS px 及 1280×800 浏览器的 200% zoom。检查无横溢、短屏 sticky fallback、移动目录位置、focus/scroll 与目标尺寸。
- [ ] Step 4：使用 next-themes 切换后 reload 检查 light/dark。运行 Chromium DevTools accessibility/contrast inspection 或 axe color-contrast / WCAG ratio script，记录色对比样本；普通字至少 4.5:1，大字/焦点/边界至少 3:1。
- [ ] Step 5：键盘 smoke test Tab/Shift+Tab/Enter/Space、所有链接。用 VoiceOver+Safari 或 NVDA+Chrome 实际检查命名 landmark、树层级、开合状态、aria-current 和顺序；未跑则明确记录未验证。
- [ ] Step 6：运行 git diff --check 并对比 Chunk 0 baseline，确认无已有 hunk 丢失；只复核实际修改文件，不格式化全库或回滚无关内容。

### Task 5：自动、真实浏览器、视觉和辅助技术检查

- [ ] Step 1：全量验证尚未完成：`pnpm test`（147 tests）与 `pnpm typecheck` 通过；`pnpm lint` 被工作树中外部构建/验证产物与已有脚本错误阻塞；本轮未成功运行完整 `pnpm build`。
- [ ] Step 2：核验 overview stage 元数据、正文 availability、进度、本地说明和章卡所有字段；核验详情头所有字段、全部 outcomes、路线序号和 last/first/no-body/cross chapter href。
- [ ] Step 3：Chromium 真实浏览器已检查 1440×900、1280×640、640×400、320×640、375×812 CSS px：无横溢、短屏 sticky fallback、移动目录次序、44px disclosure hit area 和可见键盘焦点；1280×800 浏览器的 200% zoom 尚未单独运行。
- [x] Step 4：在 Playwright 中通过 next-themes `theme` localStorage preference + reload 检查 light/dark；WCAG 颜色比值脚本在 Chromium 实色背景和 alpha-composited像素上对比 chapter/stage/metadata 文本，均 ≥4.5:1。
- [ ] Step 5：Chromium 已验证焦点可见且桌面/移动 disclosure 的 Enter、Space 触发开合；VoiceOver+Safari / NVDA+Chrome 辅助技术实测未运行，待单独执行后关闭。
- [x] Step 6：对本轮修改文件运行 `git diff --check` 并保留现存 dirty worktree hunks；未清理或格式化无关文件。
