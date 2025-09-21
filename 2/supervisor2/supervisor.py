from langgraph.prebuilt import create_react_agent

from handoff_tool import assign_to_math_agent, assign_to_research_agent

supervisor_agent = create_react_agent(
    model="openai:gpt-4.1",
    tools=[assign_to_math_agent, assign_to_research_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research agent. Assign math-related tasks to this agent.\n"
        "- a math agent. Assign math-related tasks to this agent.\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
)