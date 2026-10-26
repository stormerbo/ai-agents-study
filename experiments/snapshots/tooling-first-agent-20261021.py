"""用真 LangGraph 验证第 11 章那个问题：框架能防住「崩溃后重复副作用」吗？

第 11 章的实测：在「工具已执行、状态未落盘」之间注入崩溃，
原章节记录朴素版写入了 u1, u2, u2, u3（4 条，重复 1）；这是历史摘要，本次脚本只验证自己的固定列表情形。

关键：那次副作用写的是**固定 id**（处理用户 u2），所以重跑才会撞。
这一版照同样的构造重做 —— 第一版我用了自增 id，永远不会重复，
结果测出来的「没有重复」是我的构造错误（见文末说明）。

历史环境记录：langgraph 1.2.14 / langchain-core 1.6.9（2026-10-09）；该旧运行没有完整依赖锁。本节当前验证环境为 langgraph 1.2.14 / langchain-core 1.6.12（2026-10-21）。
"""
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

DB = []
RUNS = []          # 记录每个节点被执行了几次
CRASH = {"armed": False}


class S(TypedDict):
    done: list


def work(state: S):
    """副作用：为固定用户写一条记录（固定的 id，重跑会撞）。"""
    RUNS.append("work")
    DB.append({"user": "u2", "action": "send_reply"})  # 内存列表测试替身；固定业务键，不做自增
    if CRASH["armed"]:
        CRASH["armed"] = False
        raise RuntimeError("注入崩溃：副作用已发生，状态未落盘")
    return {"done": state["done"] + ["u2"]}


def build():
    g = StateGraph(S)
    g.add_node("work", work)
    g.add_edge(START, "work")
    g.add_edge("work", END)
    return g.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    logging.getLogger("langgraph").setLevel(logging.ERROR)
    app = build()
    cfg = {"configurable": {"thread_id": "t1"}}

    # 1) 正常跑一次
    app.invoke({"done": []}, cfg)
    print("  第 1 次执行后  测试列表 %d 条：%s" % (len(DB), DB))

    # 2) 同样的 thread，在副作用之后崩溃
    CRASH["armed"] = True
    try:
        app.invoke({"done": []}, cfg)
    except RuntimeError as e:
        print("  第 2 次 invoke 抛出异常：%s" % e)
    print("  异常后        测试列表 %d 条：%s" % (len(DB), DB))

    # 3) 恢复：重跑同一个 thread
    app.invoke({"done": []}, cfg)
    print("  再次 invoke 后 测试列表 %d 条：%s" % (len(DB), DB))
    print()

    users = [r["user"] for r in DB]
    dup = len(users) != len(set(users))
    print("=== 结果 ===")
    print("  work 节点被执行 %d 次" % len(RUNS))
    print("  测试列表中的 user: %s" % users)
    print("  有重复吗: %s" % ("❌ 有" if dup else "✅ 没有"))
    print()
    print("=== 结论 ===")
    print("  普通图状态在 super-step 边界检查点；节点函数中途失败后可能从节点开头重跑。")
    print("  因此副作用可能在恢复时重复。task 可记录已完成操作的返回值，但不提供外部 exactly-once。")
    print("  仍需使用业务幂等键、事务、接收端去重或结果对账。")
    print()
    print("  本例只验证同进程异常后的重试路径，不验证进程崩溃与持久化恢复。")
    print("  本例中的 DB 是内存列表，不代表真实数据库或外部服务。")
