from pprint import pprint
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, HumanMessage
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END

# Load environment variables
load_dotenv()

# Ensure the API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing. Please check your .env file.")

# Initialize OpenAI model
llm = ChatOpenAI(model="gpt-4o")

# Define tool: Multiply two numbers
def pomnozimacke(a: int, b: int) -> int:
    """Multiplies two numbers and returns the result."""
    print("Executing tool: pomnozimacke ->", a, "*", b)
    return a * b

# Bind tool to LLM
llm_with_tools = llm.bind_tools([pomnozimacke])

# Define state
class MessagesState(TypedDict):
    messages: Annotated[list[HumanMessage | AIMessage], add_messages]

# Node 1: Calls LLM
def tool_calling_llm(state: MessagesState):
    """Calls LLM and returns response."""
    print("1. TOOL CALLING LLM")

    # Invoke LLM with tool binding
    response = llm_with_tools.invoke(state["messages"])
    

    return {"messages": state["messages"] + [response]}

# Route function: Determines next step
def route(state: MessagesState):
    """Routes based on whether the assistant message contains a tool call."""

    print("2. ROUTE CALLED")

    last_message = state["messages"][-1]

    tool_calls = last_message.additional_kwargs.get("tool_calls", [])
    
    if tool_calls:
        print("Detected tool call:", tool_calls)
        return "tools"  # If tool call exists, go to tools
    
    return "__end__"  # Otherwise, end

def execute_tools(state: MessagesState):
    """Executes the tool and returns the result."""
    last_message = state["messages"][-1]

    tool_calls = last_message.additional_kwargs.get("tool_calls", [])
    if not tool_calls:
        print("No tool calls found.")
        return state  # Return unchanged state

    tool_call = tool_calls[0]  # Assume single tool call for simplicity
    pprint(tool_call)  # Debugging print

    # Extract correct values based on OpenAI's new structure
    tool_name = tool_call["function"]["name"]
    tool_args = eval(tool_call["function"]["arguments"])  # Convert JSON string to dict

    if tool_name == "pomnozimacke":
        result = pomnozimacke(**tool_args)  # Execute tool
        return {"messages": state["messages"] + [AIMessage(content=f"Result: {result}")]}

    print("Unknown tool call:", tool_call)
    return state  # If tool call is unrecognized, return unchanged state

# Build the state graph
builder = StateGraph(MessagesState)
builder.add_node("node_1", tool_calling_llm)
builder.add_node("tools", execute_tools)

builder.add_edge(START, "node_1")
builder.add_edge("tools", END)

# Add conditional edges for routing
builder.add_conditional_edges("node_1", route)

# Compile the graph
graph = builder.compile()

# Test Execution
messages = graph.invoke({"messages": [HumanMessage(content="Multiply 5 and 6")]})  # Multiply 5 and 6 or Hi
# for m in messages['messages']:
#     pprint(m)

print("Final Result:", messages)