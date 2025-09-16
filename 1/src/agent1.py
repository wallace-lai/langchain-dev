from typing import Dict, TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    message : str

def greeting_node(state: AgentState) -> AgentState:
    """Simple node that adds a greeting message to the state"""
    state['message'] = 'Hey ' + state['message'] + ", how is your day going?"
    return state

if __name__ == '__main__':
    graph = StateGraph(AgentState)
    graph.add_node("greeter", greeting_node)

    # 添加START和END节点
    graph.set_entry_point("greeter")
    graph.set_finish_point("greeter")

    # 编译StateGraph
    app = graph.compile()

    # 运行
    result = app.invoke({"message":"Bob"})
    print(result["message"])

