from pprint import pprint
import random
from langchain_core.messages import AIMessage, HumanMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState, StateGraph, START, END
from IPython.display import Image, display
from langchain_core.tools import tool
# from langgraph.prebuilt import  [todo I do not know how to import tools_condition from langgraph.prebuilt]

load_dotenv()

# Ensure the API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing. Please check your .env file.")

llm = ChatOpenAI(model="gpt-4o")

def pomnozimacke(a: int, b: int) -> int:
    print("ENTERING THE FUNCTION", a, "and", b)
    return a * b

llm_with_tools = llm.bind_tools([pomnozimacke])

class MessagesState(TypedDict):
    print("MessagesState")
    messages: Annotated[list[AnyMessage], add_messages]

def tool_calling_llm(state: MessagesState):
    print("Tool calling LLM...",state["messages"])
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def route(state: MessagesState):
    if random.choice([True, False]):
        return "node_1"
    return "__end__"

builder = StateGraph(MessagesState)
builder.add_node("node_1", tool_calling_llm)
builder.add_node("tools", tool(pomnozimacke))

builder.add_edge(START, "node_1")
builder.add_edge("tools", END)
builder.add_conditional_edges(
    "tool_calling_llm",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    #tools_condition,
    route
)
graph = builder.compile()



messages = graph.invoke({"messages": HumanMessage(content="Multiply 5 and 6")})  # Multiply 5 and 6 or Hi
for m in messages['messages']:
    m.pretty_print()
