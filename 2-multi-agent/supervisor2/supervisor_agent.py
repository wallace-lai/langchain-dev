from langgraph.prebuilt import create_react_agent

from handoff_tool import assign_to_math_agent, assign_to_research_agent
from handoff_tool_with_descrition import assign_to_math_agent_with_description
from handoff_tool_with_descrition import assign_to_research_agent_with_description

supervisor_agent = create_react_agent(
    model="openai:gpt-4.1",
    tools=[assign_to_research_agent, assign_to_math_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research agent. Assign research-related tasks to this agent.\n"
        "- a math agent. Assign math-related tasks to this agent.\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    name="supervisor_agent",
)

supervisor_agent_with_description = create_react_agent(
    model="openai:gpt-4.1",
    tools=[
        assign_to_math_agent_with_description,
        assign_to_research_agent_with_description
    ],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research agent. Assign research-related tasks to this agent.\n"
        "- a math agent. Assign math-related tasks to this agent.\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    name="supervisor_agent_with_description",
)
