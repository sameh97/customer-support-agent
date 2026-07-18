"""
src/graph.py — chatbot brain.
All values come from src/config.py — nothing hardcoded here.
"""

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from src.config import settings

llm = init_chat_model(
    settings.ollama_model,
    model_provider="ollama",
    temperature=settings.temperature,
    base_url=settings.ollama_base_url,
)


@task
def call_model(messages: list[BaseMessage]) -> BaseMessage:
    return llm.invoke(messages)


checkpointer = InMemorySaver()


@entrypoint(checkpointer=checkpointer)
def chatbot(
    messages: list[BaseMessage],
    *,
    previous: list[BaseMessage] = None,
) -> BaseMessage:
    if previous:
        messages = add_messages(previous, messages)

    system = SystemMessage(content=settings.system_prompt)
    response = call_model([system] + messages).result()

    return entrypoint.final(
        value=response,
        save=add_messages(messages, response),
    )