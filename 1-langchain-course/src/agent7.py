import random
from typing import List, TypedDict
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    name: str
    num: int
    guesses: List[int]
    attempts: int
    lower_bound: int
    upper_bound: int

    hint: str

def setup_node(state: AgentState) -> AgentState:
    state['guesses'].clear()
    state['attempts'] = 0
    state['hint'] = ""

    state['num'] = random.randint(state["lower_bound"], state['upper_bound'])
    return state

def guess_node(state: AgentState) -> AgentState:
    lb = state['lower_bound']
    ub = state['upper_bound']

    while True:
        try:
            num = int(input(f"Please input a num ({state["lower_bound"]} ~ {state['upper_bound']}): "))
        except ValueError:
            print("Invalid input, try again please.")
            continue
        
        if num >= lb and num <= ub:
            break
        else:
            print("Invalid bound, try again please.")

    state['guesses'].append(num)
    state['attempts'] += 1
    return state

def hint_node(state: AgentState) -> AgentState:
    if state['guesses'][-1] < state['num']:
        state['hint'] = "too small"
    elif state['guesses'][-1] > state['num']:
        state['hint'] = "too big"
    else:
        state['hint'] = "equal"

    print(state)
    return state

def should_continue(state: AgentState) -> AgentState:
    if state['hint'] == "equal":
        return "exit"
    else:
        return "continue"

if __name__ == '__main__':
    graph = StateGraph(AgentState)

    graph.add_node("setup_node", setup_node)
    graph.add_node("guess_node", guess_node)
    graph.add_node("hint_node", hint_node)

    graph.add_edge(START, "setup_node")
    graph.add_edge("setup_node", "guess_node")
    graph.add_edge("guess_node", "hint_node")

    # 使用条件选择构造循环逻辑
    graph.add_conditional_edges(
        "hint_node",
        should_continue,
        {
            "continue": "guess_node",
            "exit": END
        }
    )

    # 编译StateGraph
    app = graph.compile()

    # 运行
    result = app.invoke({
        "name": "Bob",
        "guesses": [],
        "lower_bound": 0,
        "upper_bound": 20
    })
    print(result)