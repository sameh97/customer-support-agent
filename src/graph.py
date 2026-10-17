"""
src/graph.py — agent brain with tool-calling loop.
"""

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt

from src.config import settings
from src.tools import tools, execute_tool_call, confirmation_for, search_knowledge_base

llm = init_chat_model(
    settings.ollama_model,
    model_provider="ollama",
    temperature=settings.temperature,
    base_url=settings.ollama_base_url,
    reasoning=settings.ollama_reasoning,
).bind_tools(tools)


@task
def call_model(messages: list[BaseMessage]) -> BaseMessage:
    return llm.invoke(messages)


@task
def run_tool(tool_call: dict) -> BaseMessage:
    return execute_tool_call(tool_call)


@task
def retrieve_context(query: str) -> str:
    return search_knowledge_base.invoke(query)


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

    # Also converts dict input into message objects on the first turn
    messages = add_messages(previous or [], messages)

    # Always ground the reply in the docs — small models often skip the
    # search tool, then answer from memory. The tool stays available for
    # follow-up searches. Not saved to memory; fetched fresh each turn.
    context = retrieve_context(messages[-1].content).result()
    system = SystemMessage(content=(
        f"{settings.system_prompt}\n\n"
        "Help center excerpts for the customer's latest message. Base your answer on these "
        "(or on search_knowledge_base results) and never mention them to the customer:\n\n"
        f"{context}\n\n"
        "If these excerpts don't answer the question, call tavily_search before "
        "saying you don't have the information."
    ))
    all_messages = [system] + messages

    iterations = 0
    response = call_model(all_messages).result()

    while response.tool_calls and iterations < settings.max_tool_iterations:
        tool_results = []
        for tc in response.tool_calls:
            # Human-in-the-loop: pause and let the customer confirm.
            # On resume, interrupt() returns the API's {"approved": bool}.
            request = confirmation_for(tc)
            if request and not interrupt(request).get("approved"):
                tool_results.append(ToolMessage(
                    content="The customer declined this. Don't retry it; ask how else you can help.",
                    tool_call_id=tc["id"],
                ))
            else:
                tool_results.append(run_tool(tc).result())
        all_messages = add_messages(all_messages, [response] + tool_results)
        response = call_model(all_messages).result()
        iterations += 1

    return entrypoint.final(
        value=response,
        save=add_messages(messages, response),
    )