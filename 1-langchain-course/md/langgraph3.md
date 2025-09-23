# Agent开发案例3

## 1. 目标

目标：
1. Create multiple Nodes that sequentially process and update different parts of the state.

2. Connect Nodes together in a graph

3. Invoke the Graph and see how the state is transformed step-by-step.

核心目标：

1. Create and handle multiple Nodes

## 2. 实现

```py
from typing import List, TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    name: str
    age: str
    final: str

def first_node(state: AgentState) -> AgentState:
    """first node of our sequence"""
    state['final'] = f"Hi {state['name']}!"
    return state

def second_node(state: AgentState) -> AgentState:
    """second node of our sequence"""
    state['final'] = state['final'] + " " + f"You are {state['age']} years old!"
    return state

if __name__ == '__main__':
    graph = StateGraph(AgentState)
    graph.add_node("first_node", first_node)
    graph.add_node("second_node", second_node)

    # 添加START和END节点
    graph.set_entry_point("first_node")
    graph.add_edge("first_node", "second_node")
    graph.set_finish_point("second_node")

    # 编译StateGraph
    app = graph.compile()

    # 运行
    result = app.invoke({
        "name": "Bob",
        "age": 20
    })
    print(result["final"])
```

问题：如何跟踪单个节点的输出？

总结：

- 往StateGraph中添加边以连接多个不同的节点

```py
graph.add_edge("first_node", "second_node")
```
