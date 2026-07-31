"""
src/graph.py — agent brain with tool-calling loop.
"""

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from src.config import settings
from src.tools import tools, execute_tool_call

llm = init_chat_model(
    settings.ollama_model,
    model_provider="ollama",
    temperature=settings.temperature,
    base_url=settings.ollama_base_url,
).bind_tools(tools)


@task
def call_model(messages: list[BaseMessage]) -> BaseMessage:
    return llm.invoke(messages)


@task
def run_tool(tool_call: dict) -> BaseMessage:
    return execute_tool_call(tool_call)


checkpointer = InMemorySaver()


@entrypoint(checkpointer=checkpointer)
def chatbot(
    messages: list[BaseMessage],
    *,
    previous: list[BaseMessage] = None,
) -> BaseMessage:

    # ── Debug: confirm memory state ────────────────────────────────────
    print(f"[MEMORY] previous messages count: {len(previous) if previous else 0}")
    if previous:
        for m in previous:
            print(f"  [{m.__class__.__name__}] {str(m.content)[:80]}")
    # ──────────────────────────────────────────────────────────────────

    if previous:
        messages = add_messages(previous, messages)

    system = SystemMessage(content=settings.system_prompt)
    all_messages = [system] + messages

    iterations = 0
    response = call_model(all_messages).result()

    while response.tool_calls and iterations < settings.max_tool_iterations:
        tool_results = [run_tool(tc).result() for tc in response.tool_calls]
        all_messages = add_messages(all_messages, [response] + tool_results)
        response = call_model(all_messages).result()
        iterations += 1

    return entrypoint.final(
        value=response,
        save=add_messages(messages, response),
    )