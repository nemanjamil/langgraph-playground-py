from pprint import pprint
from langchain_core.messages import AIMessage, HumanMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import  ToolNode

load_dotenv()

# Ensure the API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing. Please check your .env file.")

llm = ChatOpenAI(model="gpt-4o")

def pomnozimacke(a: int, b: int) -> int:
    """Multiplies two numbers and returns the result."""
    print("pomnozimacke ARGS", a, "and", b)
    print("pomnozimacke Resolving ", a * b)
    return a * b

def divide(a: int, b: int) -> float:
    """Divides two numbers and returns the result."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    print("divide ARGS", a, "and", b)
    print("divide Resolving ", a / b)
    return a / b

llm_with_tools = llm.bind_tools([pomnozimacke, divide])

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def custom_tools_condition(state: MessagesState) -> str:
    """Routes execution based on whether the last message contains a tool call."""
    print("1. custom_tools_condition",state["messages"][-1])


    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("2. custom_tools_condition - Returning tools")
        return "tools"
    print("3. custom_tools_condition - Returning node_1")
    return END

def calling_llm(state: MessagesState):
    print("1. Calling LLM with binded Tools :", state["messages"])
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def process_tool_response(state: MessagesState):
    """Passes tool results back to the LLM for further processing."""
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("node_1", calling_llm)
builder.add_node("tools", ToolNode([pomnozimacke, divide]))
builder.add_node("process_tool_response", process_tool_response)

builder.add_conditional_edges("node_1", custom_tools_condition)
builder.add_edge(START, "node_1")
builder.add_edge("tools", "process_tool_response")
builder.add_edge("process_tool_response", END)

graph = builder.compile()

messages = graph.invoke({"messages": HumanMessage(content="Multiply 5 and 6")})  # Multiply 5 and 6 or Hi
for m in messages['messages']:
    m.pretty_print()
