import random
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv() 

#llm = ChatOpenAI()
#llm.invoke("Hello, world!")


# Define the state class
class State:
    def __init__(self, mood=None):
        self.mood = mood

# Define nodes (returning a dict instead of State)
def node_1(state):
    print("Processing node_1...")
    return {"graph_state": state['graph_state'] +" I am"}
    #return {"mood": state["mood"]}  # Ensure it returns a dict

def node_2(state):
    print("Processing node_2...")
    return {"graph_state": state['graph_state'] +" happy!"}
    #return {"mood": state["mood"]}

def node_3(state):
    print("Processing node_3...")
    return {"graph_state": state['graph_state'] +" sad!"}
    #return {"mood": state["mood"]}

# Define conditional logic (expects dict input)
#def decide_mood(state) -> Literal["node_2", "node_3"]:
def decide_mood(state):
    user_input = state['graph_state']
    print("user_input", user_input)

    random_number = random.random()
    print("Random number:", random_number)

    if random_number < 0.5:
        return "node_2"
    return "node_3"

# Build graph
builder = StateGraph(dict)  # Use dict instead of State
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Define edges
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# Compile graph
graph = builder.compile()

# View - how to display the graph [TODO]
#display(Image(graph.get_graph().draw_mermaid_png()))


# Correct invocation
result = graph.invoke({"graph_state" : "Hi, this is Lance."})
print("Final Result:", result)
