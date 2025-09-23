import random
from typing import List, TypedDict
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    name: str
    nums: List[int]
    counter: int

def greeting_node(state: AgentState) -> AgentState:
    state['name'] = f"Hi there, {state['name']}"
    state['counter'] = 0
    return state

def random_node(state: AgentState) -> AgentState:
    state['nums'].append(random.randint(0, 10))
    state['counter'] += 1
    return state

def should_continue(state: AgentState) -> AgentState:
    if state['counter'] < 5:
        print("ENTERING LOOP", state['counter'])
        return "loop"   # continue looping
    else:
        return "exit"   # exit the loop

if __name__ == '__main__':
    graph = StateGraph(AgentState)

    graph.add_node("greeting_node", greeting_node)
    graph.add_node("random_node", random_node)
    graph.add_edge(START, "greeting_node")
    graph.add_edge("greeting_node", "random_node")

    # 使用条件选择构造循环逻辑
    graph.add_conditional_edges(
        "random_node",
        should_continue,
        {
            "loop": "random_node",
            "exit": END
        }
    )

    # 编译StateGraph
    app = graph.compile()

    # 运行
    result = app.invoke({
        "name": "Bob",
        "nums": [],
        "counter": -1
    })
    print(result)