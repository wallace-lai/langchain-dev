import os
import numpy as np

from utils import pretty_print_messages
from search_agent import research_agent
from math_agent import math_agent

from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model

supervisor = create_supervisor(
    model=init_chat_model("openai:gpt-4.1"),
    agents=[research_agent, math_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research agent. Assign research-related tasks to this agent\n"
        "- a math agent. Assign math-related tasks to this agent\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile()

# image_bytes = supervisor.get_graph().draw_mermaid_png()
# nparr = np.frombuffer(image_bytes, np.uint8)
# img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
# if not img is None:
#     cv2.imshow("State Graph", img)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()

