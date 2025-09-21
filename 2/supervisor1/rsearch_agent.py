# from utils import pretty_print_messages

from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent

web_search = TavilySearch(max_result=3)

research_agent = create_react_agent(
    model="openai:gpt-4.1",
    tools=[web_search],
    prompt=(
        "You are a research agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with research-related tasks, DO NOT do any math\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="research_agent",
)

# for chunk in research_agent.stream(
#     {
#         "messages": [{
#             "role": "user",
#             "content": "who is the CEO of Intel Company?"
#         }]
#     }
# ):
#     pretty_print_messages(chunk)

    
