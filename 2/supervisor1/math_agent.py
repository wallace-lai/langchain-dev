import os

# from utils import pretty_print_messages
from langgraph.prebuilt import create_react_agent

def add(a: float, b: float):
    """Add two numbers."""
    return a + b


def multiply(a: float, b: float):
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float):
    """Divide two numbers."""
    return a / b


math_agent = create_react_agent(
    model="openai:gpt-4.1",
    tools=[add, multiply, divide],
    prompt=(
        "You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="math_agent",
)

# for chunk in math_agent.stream(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "what is (3+ 5) * 7"
#             }
#         ]
#     }
# ):
#     pretty_print_messages(chunk)