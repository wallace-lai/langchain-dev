import os

from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain.tools.retriever import create_retriever_tool
from langchain.chat_models import init_chat_model

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.messages import convert_to_messages
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import WebBaseLoader

from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

curr_dir = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(curr_dir))
env_path = os.path.join(proj_dir, ".env")
_ = load_dotenv(dotenv_path=env_path, override=True)

# 1. Preprocess documents
## 1.1 Fetch documents to use in our RAG system
urls = [
    "https://lilianweng.github.io/posts/2024-11-28-reward-hacking/",
    "https://lilianweng.github.io/posts/2024-07-07-hallucination/",
    "https://lilianweng.github.io/posts/2024-04-12-diffusion-video/", 
]

docs = [WebBaseLoader(url).load() for url in urls]

## 1.2 Split the fetched documents into smaller chunks for indexing into vectorstore
docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=100, chunk_overlap=50
)
doc_splits = text_splitter.split_documents(docs_list)

# 2. Create a retriever tool
## 2.1 Use in-memory vector store and OpenAI embeddings
## 注意：这个步骤非常非常慢，有待优化
vertorstore = InMemoryVectorStore.from_documents(
    documents=doc_splits,
    embedding=OpenAIEmbeddings(),
)
retriever = vertorstore.as_retriever()

## 2.2 Create a retriever tool
retriever_tool = create_retriever_tool(
    retriever,
    "retrieve_blog_posts",
    "Search and return information about Lilian Weng blog posts.",
)
# print(retriever_tool.invoke({
#     "query": "types of reward hacking."
# }))

# 3. Generate query
## 3.1 Build a generate_query_or_respond node
response_model = init_chat_model(
    model="openai:gpt-4.1",
    temperature=0,
)

def generate_query_or_respond(state: MessagesState) -> MessagesState:
    """
    Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or
    simply respond to the user.
    """
    response = (
        response_model
        .bind_tools([retriever_tool])
        .invoke(state["messages"])
    )

    return {"messages": [response]}

# input = {
#     "messages": [
#         {
#             "role": "user",
#             "content": "hello"
#         }
#     ]
# }

# input = {
#     "messages": [
#         {
#             "role": "user",
#             "content": "What does Lilian Weng say about types of reward hacking?"
#         }
#     ]
# }

# print(generate_query_or_respond(input)["messages"][-1].pretty_print())

# 4. Grade documents
## 4.1 Add a conditional edge — grade_documents — to determine
## whether the retrieved documents are relevant to the question. 
GRADE_PROMPT = (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
)


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


grader_model = init_chat_model(
    model="openai:gpt-4.1",
    temperature=0
)


def grade_documents(
    state: MessagesState,
) -> Literal["generate_answer", "rewrite_question"]:
    """Determine whether the retrieved documents are relevant to the question."""
    question = state["messages"][0].content
    context = state["messages"][-1].content

    prompt = GRADE_PROMPT.format(question=question, context=context)
    response = (
        grader_model
        .with_structured_output(GradeDocuments)
        .invoke([{"role": "user", "content": prompt}])
    )
    score = response.binary_score

    if score == "yes":
        return "generate_answer"
    else:
        return "rewrite_question"

## 4.2 Run this with irrelevant documents in the tool response
# input = {
#     "messages": convert_to_messages(
#         [
#             {
#                 "role": "user",
#                 "content": "What does Lilian Weng say about types of reward hacking?",
#             },
#             {
#                 "role": "assistant",
#                 "content": "",
#                 "tool_calls": [
#                     {
#                         "id": "1",
#                         "name": "retrieve_blog_posts",
#                         "args": {"query": "types of reward hacking"},
#                     }
#                 ],
#             },
#             {"role": "tool", "content": "meow", "tool_call_id": "1"},
#         ]
#     )
# }
# print(grade_documents(input))

# 5. Rewrite question
## 5.1 Build the rewrite_question node. The retriever tool can return potentially
## irrelevant documents, which indicates a need to improve the original user question.
## To do so, we will call the rewrite_question node
REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)

def rewrite_question(state: MessagesState) -> MessagesState:
    """Rewrite the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [{"role": "user", "content": response.content}]}

# input = {
#     "messages": convert_to_messages(
#         [
#             {
#                 "role": "user",
#                 "content": "What does Lilian Weng say about types of reward hacking?",
#             },
#             {
#                 "role": "assistant",
#                 "content": "",
#                 "tool_calls": [
#                     {
#                         "id": "1",
#                         "name": "retrieve_blog_posts",
#                         "args": {"query": "types of reward hacking"},
#                     }
#                 ],
#             },
#             {"role": "tool", "content": "meow", "tool_call_id": "1"},
#         ]
#     )
# }

# response = rewrite_question(input)
# print(response["messages"][-1]["content"])

# 6. Generate an answer
## 6.1 Build generate_answer node: if we pass the grader checks, we can generate
## the final answer based on the original question and the retrieved context
GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise.\n"
    "Question: {question} \n"
    "Context: {context}"
)


def generate_answer(state: MessagesState):
    """Generate an answer."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}

# input = {
#     "messages": convert_to_messages(
#         [
#             {
#                 "role": "user",
#                 "content": "What does Lilian Weng say about types of reward hacking?",
#             },
#             {
#                 "role": "assistant",
#                 "content": "",
#                 "tool_calls": [
#                     {
#                         "id": "1",
#                         "name": "retrieve_blog_posts",
#                         "args": {"query": "types of reward hacking"},
#                     }
#                 ],
#             },
#             {
#                 "role": "tool",
#                 "content": "reward hacking can be categorized into two types: environment or goal misspecification, and reward tampering",
#                 "tool_call_id": "1",
#             },
#         ]
#     )
# }

# response = generate_answer(input)
# response["messages"][-1].pretty_print()

# 7. Assemble the graph
workflow = StateGraph(MessagesState)

# Define the nodes we will cycle between
workflow.add_node(generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node(rewrite_question)
workflow.add_node(generate_answer)

workflow.add_edge(START, "generate_query_or_respond")

# Decide whether to retrieve
workflow.add_conditional_edges(
    "generate_query_or_respond",
    # Assess LLM decision (call `retriever_tool` tool or respond to the user)
    tools_condition,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)

# Edges taken after the `action` node is called.
workflow.add_conditional_edges(
    "retrieve",
    # Assess agent decision
    grade_documents,
)
workflow.add_edge("generate_answer", END)
workflow.add_edge("rewrite_question", "generate_query_or_respond")

# Compile
graph = workflow.compile()

# import cv2
# import numpy as np
# image_bytes = graph.get_graph().draw_mermaid_png(max_retries=5, retry_delay=2.0)
# nparr = np.frombuffer(image_bytes, np.uint8)
# img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
# if not img is None:
#     cv2.imshow("State Graph", img)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()

# 8. Run the agentic RAG
for chunk in graph.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "What does Lilian Weng say about types of reward hacking?",
            }
        ]
    }
):
    for node, update in chunk.items():
        print("Update from node", node)
        update["messages"][-1].pretty_print()
        print("\n\n")