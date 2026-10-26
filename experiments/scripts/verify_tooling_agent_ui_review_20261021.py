import contextlib
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/tooling/05-agent-ui.mdx"
COMPONENT = ROOT / "src/components/mdx/approval-demo.tsx"
META = ROOT / "src/content/chapters/tooling/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
NEXT_SERVER_DOC = ROOT / "node_modules/next/dist/docs/01-app/01-getting-started/05-server-and-client-components.md"
NEXT_FORMS_DOC = ROOT / "node_modules/next/dist/docs/01-app/02-guides/forms.md"

lesson = LESSON.read_text()
component = COMPONENT.read_text()
meta = META.read_text()
resources = RESOURCES.read_text()
server_doc = NEXT_SERVER_DOC.read_text()
forms_doc = NEXT_FORMS_DOC.read_text()
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


python_fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", lesson, re.M)
check(len(python_fences) == 1, f"expected one executable Python fence, found {len(python_fences)}")
compile(python_fences[0], str(LESSON), "exec")
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(python_fences[0], str(LESSON), "exec"), {"__name__": "__main__"})
output = captured.getvalue()
check("queued -> 已提交执行，正在等待结果" in output, output)
check("rejected -> 提案已拒绝；是否重新规划由你决定" in output, output)
check("pending_new_approval -> 新提案 ap_new 已生成，请核对后再批准" in output, output)
check("unknown -> 执行结果尚不确定，正在核对；请勿重复提交" in output, output)

check("def status_message(status, proposal_id=None):" in python_fences[0], "local sample must only map statuses to copy")
check("execute(" not in python_fences[0] and "requests." not in python_fences[0], "local sample must not execute side effects")
check("```text\n# 伪代码：只原子化本地审批状态与 outbox 写入" in lesson, "transaction sketch must be labeled pseudocode")
check("它不能一般性地把任意外部邮件发送与本地状态更新变成同一个原子事务" in lesson, "external side-effect atomicity boundary must be explicit")
check("unknown/reconciling" in lesson and "不能仅凭本地审批状态宣称 exactly-once" in lesson, "ambiguous external outcomes must be reconciled")
check("修改后同意”不能把新参数直接塞进旧审批的 `approve` 请求" in lesson, "edited parameters must not reuse the old approval")
check("收到一条“换个方式”的意见，只能证明用户提交了约束，不能证明模型已采纳" in lesson, "submitted constraints must not be treated as adopted output")
check("拒绝            → 将提案标记为拒绝；是否另行重新规划由产品明确决定" in lesson, "reject must not imply an automatic replan")
check("若流程确有稳定、可解释的总步骤或阶段，百分比可以是合理摘要" in lesson, "progress percentage must be scoped to a stable denominator")
check("稳定流程仍可用百分比" in meta, "metadata must retain percentage for stable workflows")

button = re.search(r"<button\b[\s\S]*?</button>", component)
check(button is not None, "presentational component must render a button")
check('type="button"' in button.group(0) and "disabled" in button.group(0), "demo button must be inert and disabled")
check("onClick=" not in component and "<form" not in component, "demo component must not claim to submit")
check("当前四个按钮只有 `type=\"button\"`" in lesson, "lesson must accurately describe the rendered control")
check("没有 `action`、表单或事件处理器；点击不会发请求" in lesson, "lesson must disclose that the demo has no backend")
check("`<ApprovalDemo />` 只展示视觉信息，不实现提交、审批或执行。" in lesson, "demo role and product gap must be explicit")
check("四个 `type=\"button\"` 按钮不会提交审批" in lesson, "copyable source must disclose inert controls")

check("nextjs-server-client-components" in meta and "nextjs-forms-server-actions" in meta, "checkpoint must link official framework references")
check("id: 'nextjs-server-client-components'" in resources and "id: 'nextjs-forms-server-actions'" in resources, "official framework references must be registered")
check("event handlers" in server_doc and "Hydration is React's process for attaching" in server_doc, "pinned Next docs must support event/hydration scope")
check("Always verify [authentication and authorization]" in forms_doc and "supports progressive enhancement" in forms_doc, "pinned Next docs must support form and authorization scope")
check("服务端仍须逐请求认证、授权、校验" in lesson, "no-client-state claim must not weaken server authorization")

for overclaim in ["实测计划 0/3", "四个选项是四条不同的请求", "按钮发请求", "最常见的真实需求"]:
    check(overclaim not in lesson and overclaim not in meta and overclaim not in component, f"stale overclaim remains: {overclaim}")

print({"checks": checks, "passed": checks, "pythonFencesCompiled": 1, "providerCalls": 0, "fixtureOnly": True})
