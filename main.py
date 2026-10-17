"""
main.py — CLI runner. Nothing but I/O here.
"""

from dotenv import load_dotenv
load_dotenv()

from langgraph.types import Command

from src.config import settings
from src.graph import chatbot

config = {"configurable": {"thread_id": settings.default_thread_id}}


def chat(user_message: str) -> str:
    response = chatbot.invoke(
        [{"role": "user", "content": user_message}],
        config=config,
    )
    # The agent may pause to ask the customer to confirm an action
    while interrupts := chatbot.get_state(config).interrupts:
        request = interrupts[0].value
        answer = input(f"\nBot: {request['title']} {request['description']} [y/n] ")
        response = chatbot.invoke(
            Command(resume={"approved": answer.strip().lower().startswith("y")}),
            config=config,
        )
    return response.content


if __name__ == "__main__":
    print(f"[{settings.business_name}] Support bot ready. Type 'exit' to quit.\n")
    while True:
        user_input = input("Customer: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break
        print(f"\nBot: {chat(user_input)}\n")