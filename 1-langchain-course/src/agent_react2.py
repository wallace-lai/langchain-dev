import os

from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# This is the global variable to store document content
document_content = ""

# buggy code

class AgentState(TypedDict):
    llm: ChatOpenAI
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def update(content: str) -> str:
    """Updates the document with the provided content."""
    global document_content
    document_content = content
    return "Document has been updated successfully! The current content is:\n{document_content}"

@tool
def save(filename: str) -> str:
    """Save the current document to a text file and finish the process.

    Args:
        filename: Name for the text file
    """

    global document_content

    if not filename.endswith('.txt'):
        filename = f"{filename}.txt"
    
    try:
        with open(filename, "w") as file:
            file.write(document_content)
        print(f"\nDocument has been saved to: {filename}")
        return f"Document has been saved successfully to '{filename}'"
    except Exception as e:
        return f"Error saving document: {str(e)}"

tools = [update, save]

def agent(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(content=f"""
    You are Drafter, a helpful writing assistant. You are going to help the user update and modify documents.
    
    - If the user wants to update or modify content, use the 'update' tool with the complete updated content.
    - If the user wants to save and finish, you need to use the 'save' tool.
    - Make sure to always show the current document state after modifications.
    
    The current document content is:{document_content}
    """)
    
    if not state['messages']:
        user_input = "I'm ready to helpyou update a document. What would you like to create?"
        user_message = HumanMessage(content=user_input)
    else:
        user_input = "What would you like to do with the document?"
        print(f"\n  USER: {user_input}")
        user_message = HumanMessage(content=user_input)
    
    all_messages = [system_prompt] + list(state["messages"]) + [user_message]
    response = state['llm'].invoke(all_messages)

    print(f"AI:\n{response.content}")
    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"USING TOOLS: {[tc['name'] for tc in response.tool_calls]}")
    
    return {"messages": list(state["messages"]) + [user_message, response]}

def should_continue(state: AgentState) -> str:
    """Determine if we should continue or end the conversation."""

    messages = state['messages']
    if not messages:
        return "continue"
    
    # This looks for the most recent tool message
    for msg in reversed(messages):
        # and checks if this is a ToolMessage resulting from save
        if (isinstance(msg, ToolMessage) and
            "saved" in msg.content.lower() and
            "document" in msg.content.lower()):
            return "end"    # goes to the end edge which leads to the endpoint
    
    return "continue"

def print_messages(messages):
    """Function I made to print the messages in a more readable format."""
    if not messages:
        return
    
    for msg in messages[-3:]:
        if isinstance(msg, ToolMessage):
            print(f"TOOL RESULT: {msg.content}")

def run_document_agent(app, llm):
    print("\n ===== DRAFTER ===== ")
    state = {
        "llm": llm,
        "messages": []
    }

    for step in app.stream(state, stream_mode="values"):
        if "messages" in step:
            print_messages(step['messages'])
    
    print("\n ===== DRAFTER FINISHED ===== ")

if __name__ == '__main__':
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    proj_dir = os.path.dirname(os.path.dirname(curr_dir))
    env_path = os.path.join(proj_dir, ".env")
    _ = load_dotenv(dotenv_path=env_path, override=True)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=os.environ['OPENAI_API_KEY'],
        base_url=os.environ['OPENAI_API_BASE']
    ).bind_tools(tools)

    graph = StateGraph(AgentState)

    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_edge("agent", "tools")
    graph.add_conditional_edges(
        "tools",
        should_continue,
        {
            "continue": "agent",
            "end": END
        }
    )

    app = graph.compile()

    run_document_agent(app, llm)