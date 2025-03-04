import os
import getpass
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables from .env file
load_dotenv()

# Set environment variables
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing. Please check your .env file.")


# Define tools
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers and returns the result."""
    print("1. TOOL RESPONSE:  multiply ARGS", a, "and", b, "\n\n")
    return a * b

def add(a: int, b: int) -> int:
    """Adds two numbers and returns the result."""
    return a + b

def divide(a: int, b: int) -> float:
    """Divides two numbers and returns the result."""
    return a / b

tools = [add, multiply, divide]

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

# Define agent behavior
sys_msg = SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs.")

def assistant(state: MessagesState):
    print("1. Assistant START", state["messages"])
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            print(f"2. HumanMessage: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"3. AIMessage: {message.additional_kwargs}")
            if hasattr(message, "tool_calls") and message.tool_calls:
                print(f"3.1. Tool Calls: {message.tool_calls}")
        elif isinstance(message, SystemMessage):
            print(f"4. SystemMessage: {message.content}")
        elif isinstance(message, ToolMessage):
            print(f"5. ToolMessage: {message.content}, Tool Name: {message.name}, Tool Call ID: {message.tool_call_id}")

    
    print("6. Assistant [sys_msg]: ", [sys_msg])
    responseFromLLm =llm_with_tools.invoke([sys_msg] + state["messages"])
    print("10. Assistant responseFromLLm additional_kwargs: ", responseFromLLm.additional_kwargs)
    print("11. Assistant responseFromLLm content: ", responseFromLLm.content, "\n\n")
    return {"messages": [responseFromLLm]}

# Build agent graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

memory = MemorySaver()
react_graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}

# Execute agent
messages = [HumanMessage(content="Multiply 5 by 4")]
messages = react_graph.invoke({"messages": messages}, config)
for m in messages['messages']:
    m.pretty_print()


messages = [HumanMessage(content="Add that to 4.")]
messages = react_graph.invoke({"messages": messages},config)
for m in messages['messages']:
    m.pretty_print()

