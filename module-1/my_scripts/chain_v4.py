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
from langgraph.prebuilt import  ToolNode, tools_condition

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
    print("1. TOOL DEVIDE ARGS", a, "and", b)
    print("2. TOOL DEVIDE Resolving ", a / b, "\n\n")
    return a / b

llm_with_tools = llm.bind_tools([pomnozimacke, divide])

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def custom_tools_condition(state: MessagesState) -> str:
    """Routes execution based on whether the last message contains a tool call."""

    last_message = state["messages"][-1]

    print("1. custom_tools_condition",last_message)
    print("2. custom_tools_condition AIMessage",AIMessage)
    print("3. custom_tools_condition isinstance(last_message, AIMessage)",isinstance(last_message, AIMessage))


    
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_call = last_message.tool_calls[0]
        tool_call_id = tool_call["id"]
        function_name = tool_call["name"]
        args = tool_call["args"]

        print("4. custom_tools_condition tool_call", tool_call)
        print("5. custom_tools_condition tool_call_id", tool_call_id)
        print("6. custom_tools_condition function_name", function_name)
        print("7. custom_tools_condition args", args)
        print("8. custom_tools_condition - Returning tools \n\n")
        return "tools"
    
    print("10. custom_tools_condition - Returning node_1")
    return END #'process_tool_response'

def calling_llm(state: MessagesState):
    print("1. calling_llm :", state["messages"])
    tool_response = state["messages"][-1]

    print("2. calling_llm  TOOL_RESPONSE:", tool_response)
  
    if hasattr(tool_response, "tool_call_id") and tool_response.tool_call_id:
        print("4. calling_llm ENTERING \n\n")
        return {"messages": [tool_response.content]}
    

    responseFromLLm = llm_with_tools.invoke(state["messages"])
    print("10. calling_llm BASIC RESPONSE FROM LLM: ",responseFromLLm,"\n\n")
    return {"messages": [responseFromLLm]}

def process_tool_response(state: MessagesState):
    """Passes tool results back to the LLM for further processing."""
    tool_response = state["messages"][-1]
    print("1. process_tool_response", tool_response)
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("node_1", calling_llm) # this is a 1 call, this is a 4 call
builder.add_node("tools", ToolNode([pomnozimacke, divide])) # this is a 3 call
builder.add_node("process_tool_response", process_tool_response)

builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", custom_tools_condition) # this is a 2 call, this is a 5 call
builder.add_edge("tools", "node_1")
#builder.add_edge("node_1", "process_tool_response")
#builder.add_edge("node_1", END)

graph = builder.compile()

messages = graph.invoke({"messages": HumanMessage(content="Divide 5 by 6")})  # Divide 5 by 6 or Multiply 5 and 6 or Hi
for m in messages['messages']:
    m.pretty_print()
