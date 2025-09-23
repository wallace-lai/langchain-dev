import os

from dotenv import load_dotenv
curr_dir = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(curr_dir))
env_path = os.path.join(proj_dir, ".env")
_ = load_dotenv(dotenv_path=env_path, override=True)

# Define tools
from langchain_tavily import TavilySearch
tools = [TavilySearch(max_result=3)]

# Define our execution agent
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.environ['OPENAI_API_KEY'],
    base_url=os.environ['OPENAI_API_BASE']
)
prompt = "You are a helpful assistant."
agent_executor = create_react_agent(llm, tools, prompt=prompt)

# Define the state
import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict

class PlanExecuteState(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

# Planning step
from pydantic import BaseModel, Field

class Plan(BaseModel):
    """Plan to follow in future"""
    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

from langchain_core.prompts import ChatPromptTemplate

planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.""",
        ),
        ("placeholder", "{messages}"),
    ]
)
planner = planner_prompt | ChatOpenAI(
    model="gpt-4o",
    api_key=os.environ['OPENAI_API_KEY'],
    base_url=os.environ['OPENAI_API_BASE'],
    temperature=0
).with_structured_output(Plan)

# print(planner.invoke(
#     {
#         "messages": [
#             ("user", "what is the hometown of the current Australia open winner?")
#         ]
#     }
# ))

# Re-Plan step
from typing import Union

class Response(BaseModel):
    """Response to user."""

    response: str

class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )

replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan."""
)


replanner = replanner_prompt | ChatOpenAI(
    model="gpt-4o",
    api_key=os.environ['OPENAI_API_KEY'],
    base_url=os.environ['OPENAI_API_BASE'],
    temperature=0
).with_structured_output(Act)

# Create the Graph
from typing import Literal
from langgraph.graph import END

async def execute_step(state: PlanExecuteState):
    plan = state["plan"]
    plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {1}, {task}."""
    agent_response = await agent_executor.ainvoke(
        {"messages": [("user", task_formatted)]}
    )
    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
    }


async def plan_step(state: PlanExecuteState):
    plan = await planner.ainvoke({"messages": [("user", state["input"])]})
    return {"plan": plan.steps}


async def replan_step(state: PlanExecuteState):
    output = await replanner.ainvoke(state)
    if isinstance(output.action, Response):
        return {"response": output.action.response}
    else:
        return {"plan": output.action.steps}


def should_end(state: PlanExecuteState):
    if "response" in state and state["response"]:
        return END
    else:
        return "agent"

from langgraph.graph import StateGraph, START

workflow = StateGraph(PlanExecuteState)

# Add the plan node
workflow.add_node("planner", plan_step)

# Add the execution step
workflow.add_node("agent", execute_step)

# Add a replan node
workflow.add_node("replan", replan_step)

workflow.add_edge(START, "planner")

# From plan we go to agent
workflow.add_edge("planner", "agent")

# From agent, we replan
workflow.add_edge("agent", "replan")

workflow.add_conditional_edges(
    "replan",
    # Next, we pass in the function that will determine which node is called next.
    should_end,
    ["agent", END],
)

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile()

# import cv2
# import numpy as np
# image_bytes = app.get_graph(xray=True).draw_mermaid_png()
# nparr = np.frombuffer(image_bytes, np.uint8)
# img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
# if not img is None:
#     cv2.imshow("State Graph", img)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()

config = {"recursion_limit": 50}
inputs = {"input": "what is the hometown of the mens 2024 Australia open winner?"}
async for event in app.astream(inputs, config=config):
    for k, v in event.items():
        if k != "__end__":
            print(v)