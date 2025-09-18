import os

from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from langchain_community.document_loaders import PyPDFLoader

# buggy code

@tool
def retriever_tool(query: str, retriever) -> str:
    """
    This tool searches and returns the information from the Multi-Agent Collaboration Mechanisms document.
    """

    docs = retriever.invoke(query)
    if not docs:
        return "I found no relevant information in the Multi-Agent Collaboration Mechanisms document."

    results = []
    for i, doc in enumerate(docs):
        results.append(f"Document {i + 1}:\n{doc.page_count}")
    
    return "\n\n".join(results)

tools = [retriever_tool]

class AgentState(TypedDict):
    llm: ChatOpenAI
    messages: Annotated[Sequence[BaseMessage], add_messages]

def should_continue(state: AgentState):
    """Check if the last message contain tool calls."""
    result = state['messages'][-1]
    return hasattr(result, 'tool_calls') and len(result.tool_calls) > 0

system_prompt = """
You are an intelligent AI assistant who answers questions about Stock Market Performance in 2024 based on the PDF document loaded into your knowledge base.
Use the retriever tool available to answer questions about the stock market performance data. You can make multiple calls if needed.
If you need to look up some information before asking a follow up question, you are allowed to do that!
Please always cite the specific parts of the documents you use in your answers.
"""

# Creating a dictionary of our tools
tools_dict = {
    our_tool.name: our_tool for our_tool in tools
}

def call_llm(state: AgentState) -> AgentState:
    """Function to call the LLM with the current state."""
    messages = list(state['messages'])
    messages = [SystemMessage(content=system_prompt)] + messages
    message = state['llm'].invoke(messages)
    
    state['messages'] = [message]
    return state

# Retriever Agent
def take_action(state: AgentState) -> AgentState:
    """Execute tool calls from the LLM's response."""

    tool_calls = state['messages'][-1].tool_calls
    results = []
    for t in tool_calls:
        print(f"Calling Tool: {t['name']} with query: {t['args'].get('query', 'No query provided')}")
        
        if not t['name'] in tools_dict: # Checks if a valid tool is present
            print(f"\nTool: {t['name']} does not exist.")
            result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."
        
        else:
            result = tools_dict[t['name']].invoke(t['args'].get('query', ''))
            print(f"Result length: {len(str(result))}")
            

        # Appends the Tool Message
        results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

    print("Tools Execution Complete. Back to the model!")
    return {'messages': results}

def running_agent():
    print("\n=== RAG AGENT===")
    
    while True:
        user_input = input("\nWhat is your question: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        messages = [HumanMessage(content=user_input)] # converts back to a HumanMessage type

        result = rag_agent.invoke({"messages": messages})
        
        print("\n=== ANSWER ===")
        print(result['messages'][-1].content)

if __name__ == '__main__':
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    proj_dir = os.path.dirname(os.path.dirname(curr_dir))
    env_path = os.path.join(proj_dir, ".env")
    _ = load_dotenv(dotenv_path=env_path, override=True)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=os.environ['OPENAI_API_KEY'],
        base_url=os.environ['OPENAI_API_BASE'],
        temperature=0
    )

    # Our Embedding Model - has to also be compatible with the LLM
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    # Load pdf
    pdf_path = os.path.join(proj_dir, "data", "agent.pdf")
    pdf_loader = PyPDFLoader(pdf_path)
    try:
        pages = pdf_loader.load()
        print(f"PDF has been loaded and has {len(pages)} pages.")
    except Exception as e:
        print(f"Error loading PDF: {e}")
        raise

    # Chunking Process
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    pages_split = text_splitter.split_documents(pages)

    collection_name = "agent_paper"
    persist_dir = os.path.join(proj_dir, "data", "persist")
    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)
    
    # Create the chroma database using our embeddings model
    try:
        vectorstore = Chroma.from_documents(
            documents=pages_split,
            embeddings=embeddings,
            persist_dir=persist_dir,
            collection_name=collection_name
        )
        print(f"Create ChromaDB vector store success.")
    except Exception as e:
        print(f"Error setting up ChromaDB: {e}")
        raise

    # Now we creat our retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # K is the amount of chunks to return
    )

    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("retriever_agent", take_action)

    graph.add_conditional_edges(
        "llm",
        should_continue,
        {True: "retriever_agent", False: END}
    )
    graph.add_edge("retriever_agent", "llm")
    graph.set_entry_point("llm")

    rag_agent = graph.compile()
