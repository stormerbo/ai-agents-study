from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
lesson = (ROOT / 'src/content/chapters/coding-agent/05-safety.mdx').read_text()
meta = (ROOT / 'src/content/chapters/coding-agent/meta.ts').read_text()
resources = (ROOT / 'src/content/curriculum/resources.ts').read_text()
checks = {
    'pytest claim scoped to command-and-repo behavior': '命令名 allowlist 单独不足以约束这类命令的全部副作用' in meta and '挡不住任何东西' not in lesson,
    'pytest mechanism reproduction is version- and fixture-bounded': 'pytest 8.4.2' in meta and '不是对 2026-10-10 历史环境或日志的重放' in meta,
    'policy sample explicitly says it does not enforce isolation': '不会创建任何隔离' in lesson and '没有执行语义' in lesson,
    'network host list is not presented as an implemented control': 'allow_network_hosts' in lesson and '不能靠字符串匹配' in lesson,
    'container mounts and defaults have documented limits': '默认配置可能不足以形成完整隔离' in lesson,
    'approval observation is bounded to its original sample': '不能证明 coding agent 场景中的普遍效果' in lesson,
    'package installation code-execution risk has official source': 'pip-secure-installs' in resources and 'pip.pypa.io/en/stable/topics/secure-installs/' in resources,
    'pytest/npm/Cargo official references are registered': all(x in resources for x in ['pytest-plugins', 'npm-scripts', 'cargo-build-scripts']),
    'no claim that a low-privilege user alone is a sandbox': '单独使用不等同于文件系统或网络隔离' in lesson,
    'threat categories are not presented as a severity or frequency ranking': '不表示相对频率或严重性排序' in lesson and '最危险' not in lesson and '最频繁' not in lesson,
    'secret exposure is conditional on effective file and network access': '具体能否触达取决于进程权限、挂载和网络策略' in lesson,
    'read-only mode is scoped to task mounts, not every host filesystem': '仅暴露任务所需目录且只读；宿主其它目录不挂载' in lesson,
    'policy example name does not imply actual sandbox behavior': 'class SandboxPolicy:' in lesson,
}
for name, passed in checks.items():
    print(('PASS' if passed else 'FAIL') + ': ' + name)
if not all(checks.values()):
    sys.exit(1)
