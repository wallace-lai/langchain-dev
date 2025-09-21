import cv2
import numpy as np

from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END

from supervisor_agent import supervisor_agent, supervisor_agent_with_description
from research_agent import research_agent
from math_agent import math_agent
from utils import pretty_print_messages

def app():
    state = StateGraph(MessagesState)

    # NOTE: `destinations` is only needed for visualization and doesn't affect runtime behavior
    # state.add_node(supervisor_agent, destinations=("research_agent", "math_agent", END))
    state.add_node(supervisor_agent)
    state.add_node(research_agent)
    state.add_node(math_agent)

    state.add_edge(START, "supervisor_agent")
    state.add_edge("research_agent", "supervisor_agent")
    state.add_edge("math_agent", "supervisor_agent")

    app = state.compile()

    # image_bytes = supervisor.get_graph().draw_mermaid_png()
    # nparr = np.frombuffer(image_bytes, np.uint8)
    # img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # if not img is None:
    #     cv2.imshow("State Graph", img)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()

    for chunk in app.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "find US and New York state GDP in 2024. what % of us GDP was New York state?"
                }
            ]
        }
    ):
        pretty_print_messages(chunk, last_message=True)

def app_with_description():
    state = StateGraph(MessagesState)

    state.add_node(supervisor_agent_with_description)
    state.add_node(research_agent)
    state.add_node(math_agent)

    state.add_edge(START, "supervisor_agent_with_description")
    state.add_edge("research_agent", "supervisor_agent_with_description")
    state.add_edge("math_agent", "supervisor_agent_with_description")

    app = state.compile()

    # image_bytes = supervisor.get_graph().draw_mermaid_png()
    # nparr = np.frombuffer(image_bytes, np.uint8)
    # img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # if not img is None:
    #     cv2.imshow("State Graph", img)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()

    for chunk in app.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "find US and New York state GDP in 2024. what % of us GDP was New York state?"
                }
            ]
        },
        subgraphs=True,
    ):
        pretty_print_messages(chunk, last_message=True)

if __name__ == '__main__':
    app_with_description()