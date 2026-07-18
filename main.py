
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model("qwen2.5:3b", model_provider="ollama", temperature=0.2)


@task
def call_model(messages: list[BaseMessage]) -> BaseMessage:
    return llm.invoke(messages)


checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def chatbot(messages: list[BaseMessage], *, previous: list[BaseMessage] = None) -> BaseMessage:
    if previous:
        messages = add_messages(previous, messages)

    system_prompt = SystemMessage(content="You are a helpfull customer support assistant.")
    all_messages = [system_prompt] + messages


    response = call_model(all_messages).result()

    return entrypoint.final(value=response, save=add_messages(messages, response))

config = {"configurable": {"thread_id": "support-session-1"}}

response = chatbot.invoke([{"role": "user", "content": "How do I reset my password?"}], config=config)


print(response.content)

print("\n\n-------------------------------------------------------------\n\n")

response2 = chatbot.invoke(
    [{"role": "user", "content": "What was my question just now?"}], 
    config=config
)
print(response2.content)