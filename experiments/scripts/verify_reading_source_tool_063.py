"""沿一次任务读到底：@tool 是怎么把函数变成 JSON schema 的。

第 13 章测出一个现象：@tool 生成的 schema 里 day 只有 {"type": "string"}，没有 enum ——
尽管文档字符串写了「只支持明天或后天」。当时我把它记成了「抽象泄漏」。

读了源码之后，结论要**修正**，而且比原来更具体。下面这组对照是这次读源码的产出。

环境：langchain_core 0.3.63 / langchain 0.3.7。实跑状态：2026-10-09。
"""
import inspect, json
from importlib.metadata import version
from typing import Literal

from langchain_core.tools import tool

DOC = """查天气。

Args:
    day: 只能是「明天」或「后天」
"""


@tool
def a_default(day: str) -> str:
    """查天气。

    Args:
        day: 只能是「明天」或「后天」
    """
    return day


@tool(parse_docstring=True)
def b_parsed(day: str) -> str:
    """查天气。

    Args:
        day: 只能是「明天」或「后天」
    """
    return day


@tool(parse_docstring=True)
def c_literal(day: Literal["明天", "后天"]) -> str:
    """查天气。

    Args:
        day: 查询的日期
    """
    return day


def summary(t):
    return t.args_schema.model_json_schema()["properties"]["day"]


if __name__ == "__main__":
    assert version("langchain-core") == "0.3.63", version("langchain-core")
    assert summary(a_default) == {"title": "Day", "type": "string"}
    assert summary(b_parsed).get("description") == "只能是「明天」或「后天」"
    assert "enum" not in summary(b_parsed)
    assert summary(c_literal).get("enum") == ["明天", "后天"]
    assert "Args:" in (a_default.description or "")
    assert "Args:" not in (b_parsed.description or "")
    print("离线断言通过：6 项；langchain-core==0.3.63；providerCalls=0")
    print()
    print("=== 一、调用链（file:line 由 inspect 取真实位置）===")
    from langchain_core.tools import base as base_mod, convert as convert_mod
    for label, fn in [("装饰器入口", convert_mod.tool),
                      ("建 schema", base_mod.create_schema_from_function),
                      ("取 properties", base_mod._get_filtered_args)]:
        src = inspect.getsourcefile(fn).split("site-packages/")[-1]
        print("  %-14s %s:%d" % (label, src, inspect.getsourcelines(fn)[1]))
    print()

    print("=== 二、参数 schema 对照 ===")
    rows = [
        ("A day: str，默认", a_default),
        ("B day: str，parse_docstring=True", b_parsed),
        ("C day: Literal[...]，True", c_literal),
    ]
    for label, t in rows:
        print("  %-32s %s" % (label, json.dumps(summary(t), ensure_ascii=False)))
    print()

    print("=== 三、工具级 description（前 30 字）===")
    for label, t in rows:
        d = (t.description or "（空）").replace(chr(10), " / ")[:34]
        print("  %-32s %s" % (label, d))
    print()

    print("=== 结论 ===")
    print("  1. parse_docstring 默认是 False（convert.py:23/38/52/66/80 五处重载）")
    print("     → 写在 Args: 段里的参数说明**被静默丢弃**，而且原文还漏进了工具级 description。")
    print("  2. 打开 parse_docstring 之后，那句「只能是明天或后天」进了 description ——")
    print("     但**仍然没有变成 enum**。散文只能生成 description，生成不了约束。")
    print("  3. 只有类型标注（Literal）能生成 enum。LangChain 在 base.py:103 用")
    print("     pydantic 的 model_json_schema() 取 schema，约束完全由类型决定。")
    print()
    print("  所以第 13 章那个现象更准确的解释是：")
    print("    **约束写在散文里，就等于把它从「机器可校验」降级成了「模型可以忽略的提示」。**")
    print("    这不是框架丢了信息 —— 是 prose 和 type 承载的东西不同：")
    print("      description ← 文档字符串    enum/range/pattern ← 类型标注")