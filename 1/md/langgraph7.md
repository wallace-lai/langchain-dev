# AI Agent开发案例2 —— 带记忆的对话机器人

## 1. 目标

1. Use different message types HumanMessage and AlMessage

2. Maintain a full conversation history using both message types

3. Use GPT-4o model using LangChain's ChatOpenAl

4. Create a sophisticated conversation loop

核心目标：

1. Create a form of memory for our Agent

## 2. 实现

要想实现一个带记忆的Agent，我们可以在AgentState里记录每段对话的内容，然后在每次请求大模型的时候将对话历史内容也一并传递给大模型。

```py
class AgentState(TypedDict):
    llm: ChatOpenAI
    messages: List[Union[HumanMessage, AIMessage]]
```

完整代码实现：

```py
import os

from typing import TypedDict, List, Union
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

class AgentState(TypedDict):
    llm: ChatOpenAI
    messages: List[Union[HumanMessage, AIMessage]]

def process(state: AgentState) -> AgentState:
    """This node will solve the request you input"""
    try:
        response = state['llm'].invoke(state['messages'])
    except Exception as e:
        print("LLM Error")
        return state

    # 添加AIMessage
    state['messages'].append(AIMessage(content=response.content))

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

    conversation_history = []

    query_input = input("Enter: ")
    while query_input != "exit":
        if query_input:
            # 添加HumanMessage
            conversation_history.append(HumanMessage(content=query_input))

            result = agent.invoke({
                "llm": llm,
                "messages": conversation_history
            })

        query_input = input("Enter: ")
    
    # 打印所有的对话内容
    for msg in conversation_history:
        print(msg.content)
```
