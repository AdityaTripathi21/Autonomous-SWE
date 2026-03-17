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

def test_creator(state: CodeState):
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
    

subgraph = StateGraph(CodeState)

subgraph.add_node("worker_node", worker_node)
subgraph.add_node("test_creator", test_creator)
subgraph.add_node("test_runner", test_runner)
subgraph.add_node("bug_fixer", bug_fixer)

subgraph.set_entry_point("worker_node")

subgraph.add_edge("worker_node", "test_creator")
subgraph.add_edge("test_creator", "test_runner")

subgraph.add_conditional_edges("test_runner", router, {
    "bug_fixer": "bug_fixer",
    "end": END
})

subgraph.add_edge("bug_fixer", "test_creator")

engineer_agent = subgraph.compile()

parent = StateGraph(CodeState)

parent.add_node("task_node", task_node)
parent.add_node("engineer_agent", engineer_agent)   # subgraph is a node

parent.set_entry_point("task_node")
parent.add_edge("task_node", "engineer_agent")
parent.add_edge("engineer_agent", END)

app = parent.compile()

    
result = app.invoke({
    "task": "Write a function in Java that reverses a String",
    "code": "",
    "tests": "",
    "error": "",
    "attempts": 0
})

print(result["code"])