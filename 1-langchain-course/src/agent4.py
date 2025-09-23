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