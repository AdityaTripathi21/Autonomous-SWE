import subprocess
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict
from dotenv import load_dotenv
from tools.file_tools import list_files, read_file, write_file
from langchain_core.tools import tool


load_dotenv()

# A coding agent

model = ChatGroq(
    model="openai/gpt-oss-120b",
    max_tokens=4000
)

tools = [list_files, read_file, write_file]
tools_by_name = {t.name: t for t in tools}

model_with_tools = model.bind_tools(tools)

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
        f"Write a simple, minimal Python implementation only. No helper utilities, no optional parameters, no benchmarks, no tests, no explanation, no markdown, no backticks. Just the core function(s): {state['task']}"    
        )
    write_file.invoke({"path": "src/main.py", "content": response.content})
    return {"code": response.content}

def test_creator(state: CodeState):
    response = model.invoke(
        f"Write Python unit tests only using the unittest module. No explanation, no markdown, no backticks, no imports other than unittest and 'from src.main import *'. Tests only. Here is the code:\n{state['code']}"
        )
    return {"tests": response.content}

def test_runner(state: CodeState):
    write_file.invoke({"path": "tests/test_main.py", "content": state["tests"]})
    result = subprocess.run(
        ["python3", "workspace/tests/test_main.py"],
        capture_output=True,
        text=True
        )
    if result.returncode != 0:
        return {"error": result.stderr, "attempts": state["attempts"] + 1}
    return {"error": ""}

    
def bug_fixer(state: CodeState):
    response = model.invoke(
        f"Fix this code given these errors and tests. Return code only, no explanation, no markdown, no backticks.\nCode: {state['code']}\nError: {state['error']}\nTests: {state['tests']}"
    )
    write_file.invoke({"path": "src/main.py", "content": response.content})
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

    
while True:
    task = input("Enter task (or 'quit' to exit): ")
    if task.lower() == "quit":
        break
    result = app.invoke({
        "task": task,
        "code": "",
        "tests": "",
        "error": "",
        "attempts": 0
    })
