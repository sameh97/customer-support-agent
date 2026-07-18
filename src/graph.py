"""
src/graph.py — agent brain with tool-calling loop.

Flow per turn:
  1. Merge new message with conversation history
  2. Call LLM (with tools bound — it knows what tools exist)
  3. If LLM returns tool_calls → execute them → feed results back → go to 2
  4. When LLM returns plain text → done, save to checkpointer
"""

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from src.config import settings
from src.tools import tools, execute_tool_call


# ── LLM with tools bound ──────────────────────────────────────────────────────
# bind_tools tells the LLM what tools exist and their signatures.
# The LLM won't call them directly — it returns tool_calls in its response,
# and WE execute them (in the loop below).

_base_llm = init_chat_model(
    settings.ollama_model,
    model_provider="ollama",
    temperature=settings.temperature,
    base_url=settings.ollama_base_url,
)
llm = _base_llm.bind_tools(tools)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@task
def call_model(messages: list[BaseMessage]) -> BaseMessage:
    return llm.invoke(messages)


@task
def run_tool(tool_call: dict) -> BaseMessage:
    return execute_tool_call(tool_call)


# ── Entrypoint ────────────────────────────────────────────────────────────────

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def chatbot(
    messages: list[BaseMessage],
    *,
    previous: list[BaseMessage] = None,
) -> BaseMessage:

    # Merge new message with full history from checkpointer
    if previous:
        messages = add_messages(previous, messages)

    system = SystemMessage(content=settings.system_prompt)
    all_messages = [system] + messages

    # Tool-calling loop:
    # LLM can call tools multiple times before giving a final answer.
    # e.g. search docs → read result → search again → final answer
    iterations = 0
    response = call_model(all_messages).result()

    while response.tool_calls and iterations < settings.max_tool_iterations:
        # Run all tool calls the LLM requested (possibly multiple at once)
        tool_results = [
            run_tool(tc).result()
            for tc in response.tool_calls
        ]

        # Append LLM response + tool results to message list
        all_messages = add_messages(all_messages, [response] + tool_results)

        # Let LLM process the tool results and decide next step
        response = call_model(all_messages).result()
        iterations += 1

    # Persist this turn to checkpointer (history without system prompt)
    return entrypoint.final(
        value=response,
        save=add_messages(messages, response),
    )