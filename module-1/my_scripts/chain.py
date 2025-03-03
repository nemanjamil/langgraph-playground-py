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
# from langgraph.prebuilt import  tools_condition # [todo Maybe it's removed from library I do not know how to import tools_condition from langgraph.prebuilt]

load_dotenv()

# Ensure the API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing. Please check your .env file.")

llm = ChatOpenAI(model="gpt-4o")

def mulitply(a: int, b: int) -> int:
    """Multiplies two numbers and returns the result."""
    print("mulitply ARGS", a, "and", b)
    print("mulitply Resolving ", a * b)
    return a * b

llm_with_tools = llm.bind_tools([mulitply])

class MessagesState(TypedDict):
    print("MessagesState")
    messages: Annotated[list[AnyMessage], add_messages]

def tool_calling_llm(state: MessagesState):
    print("1. Tool calling LLM:", state["messages"])
    
    # Invoke LLM with tool binding
    response = llm_with_tools.invoke(state["messages"])

    print("2. Tool calling LLM response: ", response.additional_kwargs)

    # Check if the response contains a tool call
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_call = response.tool_calls[0]  # Assume only one tool call

        print("3. Tool calling LLM - We have tool_calls: ", tool_call)

        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name == "mulitply":

            print("4. Tool calling LLM - mulitply")

            result = mulitply(**tool_args)  # Call the tool

            print("5. Tool calling LLM - mulitply response", result)

            return {"messages": [response, AIMessage(content=f"Result: {result}")]}
        

    print("6. Tool calling LLM - NOT ENTERING TOOK CALL")

    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("node_1", tool_calling_llm)
builder.add_node("tools", tool(mulitply))

builder.add_edge(START, "node_1")
builder.add_edge("node_1", END)

graph = builder.compile()



messages = graph.invoke({"messages": HumanMessage(content="Multiply 5 and 6")})  # Multiply 5 and 6 or Hi
for m in messages['messages']:
    m.pretty_print()
