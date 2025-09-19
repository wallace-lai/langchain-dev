import os

from dotenv import load_dotenv

from utils import pretty_print_messages
from supervisor_agent import supervisor

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    proj_dir = os.path.dirname(os.path.dirname(curr_dir))
    env_path = os.path.join(proj_dir, ".env")
    _ = load_dotenv(dotenv_path=env_path, override=True)

    for chunk in supervisor.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "find US and New York state GDP in 2024. what % of US GDP was New York state?"
                }
            ]
        },
    ):
        pretty_print_messages(chunk, last_message=True)

if __name__ == '__main__':
    main()
