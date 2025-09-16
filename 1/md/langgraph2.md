# Agent开发案例2

## 1. 开发目标

目标：
1. Define a more complex AgentState

2. Create a processing node that performs operations on list data.

3. Set up a LangGraph that processes and outputs computed results.

4. Invoke the graph with structured inputs and retrieve outputs.

核心目标：
- Learn how to handle multiple inputs

## 2. 实现

```py
from typing import List, TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    values: List[int]
    name: str
    result: str

def process_values(state: AgentState) -> AgentState:
    """This function handles multiple different inputs"""
    # {'values': [1, 2, 3, 4], 'name': 'Bob'}
    print(state)
    state['result'] = f'Hi there {state['name']}! Your sum = {sum(state['values'])}'
    # {'values': [1, 2, 3, 4], 'name': 'Bob', 'result': 'Hi there Bob! Your sum = 10'}
    print(state)
    return state

if __name__ == '__main__':
    graph = StateGraph(AgentState)
    graph.add_node("processor", process_values)

    # 添加START和END节点
    graph.set_entry_point("processor")
    graph.set_finish_point("processor")

    # 编译StateGraph
    app = graph.compile()

    # 运行
    result = app.invoke({"name":"Bob", "values":[1, 2, 3, 4]})
    print(result["result"])
```

## 3. 练习

要求通过operation的实际值来控制对values数组的操作

```py
import math
from typing import List, TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    values: List[int]
    name: str
    operation: str
    result: str

def process_values(state: AgentState) -> AgentState:
    """This function handles multiple different inputs"""
    print(state)

    if state['operation'] == '+':
        result = sum(state['values'])
    elif state['operation'] == '*':
        result = math.prod(state['values'])
    else:
        result = ""

    state['result'] = f'Hi there {state['name']}! Your answer is {result if result else None}'
    print(state)
    return state

if __name__ == '__main__':
    graph = StateGraph(AgentState)
    graph.add_node("processor", process_values)

    # 添加START和END节点
    graph.set_entry_point("processor")
    graph.set_finish_point("processor")

    # 编译StateGraph
    app = graph.compile()

    # 运行
    result = app.invoke({
        "operation":"-",
        "name":"Bob",
        "values":[1, 2, 3, 4]
    })
    print(result["result"])
```
