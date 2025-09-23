import os

from typing import TypedDict, List
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

class AgentState(TypedDict):
    llm: ChatOpenAI
    messages: List[HumanMessage]

def process(state: AgentState) -> AgentState:
    response = state['llm'].invoke(state['messages'])
    print('#' * 64)
    print(f"AI:\n{response.content}")
    print('#' * 64)
    return state

if __name__ == '__main__':
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    proj_dir = os.path.dirname(os.path.dirname(curr_dir))
    env_path = os.path.join(proj_dir, ".env")
    _ = load_dotenv(dotenv_path=env_path, override=True)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=os.environ['OPENAI_API_KEY'],
        base_url=os.environ['OPENAI_API_BASE']
    )

    graph = StateGraph(AgentState)
    graph.add_node("process", process)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)

    agent = graph.compile()

    query_input = input("Enter: ")
    while query_input != "exit":
        if query_input:
            agent.invoke({
                "llm": llm,
                "messages": [HumanMessage(content=query_input)]
            })

        query_input = input("Enter: ")




