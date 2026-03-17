from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()

# A coding agent

model = ChatGroq(
    model="openai/gpt-oss-120b",
    max_tokens=1000
)

# state for both parent and subgraph
class CodeState(TypedDict):
    task: str         
    code: str 
    tests: str        
    error: str         
    attempts: int   
     
 
    
def task_node(state: CodeState):
    response = model.invoke(
         f"Break this coding task into clear requirements, specify language, complexity, and exact expected behavior: {state['task']}"
    )
    
    return {"task": response.content}

def worker_node(state: CodeState):
    response = model.invoke(
        f"Write code in the specified language only, no explanation, no markdown, no backticks: {state['task']}"
    )
    return {"code": response.content}

def test_creater(state: CodeState):
    response = model.invoke(
        f"Create ONLY unit tests and functional tests for this code: {state['code']}"
    )
    return {"tests": response.content}

def test_runner(state: CodeState):
    try:
        exec(state["code"] + "\n" + state["tests"])
        return {"error": ""}    # no error, code ran fine
    except Exception as e:
        return {"error": str(e), "attempts": state["attempts"] + 1}   # capture the error message + attempt

def review_node(state: CodeState):
    try:
        exec(state["code"])
        return {"error": ""}       # no error, code ran fine
    except Exception as e:
        return {"error": str(e), "attempts": state["attempts"] + 1}   # capture the error message
    
def bug_fixer(state: CodeState):
    response = model.invoke(
        f"Fix this code given these errors and tests. Return code only, no explanation, no markdown, no backticks.\nCode: {state['code']}\nError: {state['error']}\nTests: {state['tests']}"
    )
    return {"code": response.content}
    
def router(state: CodeState):
    if state["error"] == "":
        return "end"
    elif state["attempts"] >= 3:
        return "end"
    else:
        return "bug_fixer"
    

    

    

graph = StateGraph(CodeState)

graph.add_node("taskNode", task_node)
graph.add_node("workerNode", worker_node)
graph.add_node("reviewNode", review_node)

graph.set_entry_point("taskNode")

graph.add_edge("taskNode", "workerNode")
graph.add_edge("workerNode", "reviewNode")

graph.add_conditional_edges("reviewNode", router, {
    "worker_node": "workerNode",
    "end": END
})

app = graph.compile()
