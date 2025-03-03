import os
import getpass
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set environment variables
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing. Please check your .env file.")


# Define tools
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers and returns the result."""
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
    print("Assistant invoked message", state["messages"])
    print("Assistant sys_msg", sys_msg)
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Build agent graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")
react_graph = builder.compile()

# Execute agent
messages = [HumanMessage(content="Add 3 and 4. Multiply the output by 2. Divide the output by 5")]
messages = react_graph.invoke({"messages": messages})

# Print results
for m in messages['messages']:
    m.pretty_print()
