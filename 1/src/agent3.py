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