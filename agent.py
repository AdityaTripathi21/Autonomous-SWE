import ast
import subprocess
import sys
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict
from dotenv import load_dotenv
from tools.file_tools import list_files, read_file, write_file
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer




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
    error: str  # latest error
    errors: list
    dependencies: list       
    attempts: int   
     
 
# planner code and returns task state    
def task_node(state: CodeState):
    writer = get_stream_writer()
    writer(f"Starting planning for task: {state['task']}")
    response = model.invoke([
        SystemMessage(content="You are a software requirements analyst. Break coding tasks into clear requirements, specify language, complexity, and exact expected behavior."),
        HumanMessage(content=state["task"])
    ])
    writer(f"Finished planning for task: {response.content}")
    return {"task": response.content}

# extracts dependencies from code using AST
def extract_dependencies(code: str) -> list[str]:
    tree = ast.parse(code)
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    # remove standard library modules
    return [m for m in imports if m not in sys.stdlib_module_names]

# installs dependencies in main and test file
def dependency_node(state: CodeState):
    writer = get_stream_writer()

    combined_code = state["code"] + "\n" + state["tests"]
    
    writer("Starting extraction for dependencies from combined code")
    
    try:
        packages = extract_dependencies(combined_code)
    except Exception:
        writer("No dependencies found.")
        return {"dependencies": []}
    
    writer("Finished extraction successfully, starting install...")
    
    installed = []
    for package in packages:
        result = subprocess.run(
            ["pip", "install", "--quiet", package],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            installed.append(package)
    if len(installed) == 0:
        writer("Installed 0 packages.")
    else:
        writer(f"Finished installation successfully. Packages installed: {installed}")

    return {"dependencies": installed}

# writes code given task and writes code to main.py and returns code state
def worker_node(state: CodeState):
    writer = get_stream_writer()
    
    writer("Writing code for task...")
    
    response = model.invoke([
        SystemMessage(content="You are an expert Python engineer. You write clean, minimal, correct code. You never include explanations, markdown, backticks, or tests in your output. Code only."),   # SysMessage for instructions
        HumanMessage(content=f"Write code for this task: {state['task']}")  # The input
    ])
    write_file.invoke({"path": "src/main.py", "content": response.content})
    
    writer("Finished writing and successfully wrote to file main.py")
    
    return {"code": response.content}

# tests get created here, however they aren't written, instead they are stored in state and given to the test_runner
def test_creator(state: CodeState):
    writer = get_stream_writer()
    
    writer("Writing tests for code...")
    
    response = model.invoke([
        SystemMessage(content="You are an expert Python test engineer. You write unit tests using only the unittest module. No explanation, no markdown, no backticks. Only import unittest and 'from src.main import *'. Tests only."),
        HumanMessage(content=f"Write unit tests for this code:\n{state['code']}")
    ])
    writer("Finished writing tests for code.")
    
    return {"tests": response.content}

# tests are written using write_file, and then they're run, if errors, error, errors, attempt is returned, otherwise, just empty error
def test_runner(state: CodeState):
    writer = get_stream_writer()
    
    writer("Writing tests to file...")

    write_file.invoke({"path": "tests/test_main.py", "content": state["tests"]})
    
    writer("Successfully wrote tests to file. Running tests...")
    
    result = subprocess.run(
        ["python3", "workspace/tests/test_main.py"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        if state["attempts"] >= 3:
            writer(f"Error encountered. Max number of attempts reached, try again.")
        else:
            writer(f"Error encountered. The error is {result.stderr}. Attempt no. {state['attempts'] + 1 } unsuccessful. Retrying...")
        return {"error": result.stderr, "errors": state["errors"] + [result.stderr], "attempts": state["attempts"] + 1}
    writer("Tests ran successfully with no error. Program is correct.")
    return {"error": ""}

# Fixes code given the code, errors, error (latest), and tests, writes to main.py, and returns code as state
def bug_fixer(state: CodeState):
    writer = get_stream_writer()
    
    writer(f"Attempting to fix bugs...\nLatest bug: {state['error']} All bugs: {state['errors']}")
    
    response = model.invoke([
        SystemMessage(content="You are an expert Python debugger. You fix code based on errors and failing tests. Return fixed code only, no explanation, no markdown, no backticks."),
        HumanMessage(content=f"Fix this code.\nCode: {state['code']}\nAll previous errors in order: {state['errors']}\nLatest error: {state['error']}\nTests: {state['tests']}")    ])
    
    writer("Finished bug fixing. Writing code to main.py...")
    
    write_file.invoke({"path": "src/main.py", "content": response.content})
    
    writer("Finished writing code to main.py")
    
    return {"code": response.content}

# router for conditional edge, if no error, end the loop, if attempts >= 3, end the loop, otherwise loop to bug_fixer    
def router(state: CodeState):
    if state["error"] == "":
        return "end"
    elif state["attempts"] >= 3:
        return "end"
    else:
        
        return "bug_fixer"
    

subgraph = StateGraph(CodeState)

subgraph.add_node("dependency_node", dependency_node)
subgraph.add_node("worker_node", worker_node)
subgraph.add_node("test_creator", test_creator)
subgraph.add_node("test_runner", test_runner)
subgraph.add_node("bug_fixer", bug_fixer)

subgraph.set_entry_point("worker_node")

subgraph.add_edge("worker_node", "test_creator")
subgraph.add_edge("test_creator", "dependency_node")
subgraph.add_edge("dependency_node", "test_runner")

subgraph.add_conditional_edges("test_runner", router, {
    "bug_fixer": "bug_fixer",
    "end": END
})

subgraph.add_edge("bug_fixer", "test_runner")

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
    for chunk in app.stream(
        {
            "task": task,
            "code": "",
            "tests": "",
            "error": "",
            "errors": [],
            "dependencies": [],
            "attempts": 0
        },
        stream_mode="custom",
        subgraphs=True,
        version="v2"
    ):
        if chunk["type"] == "custom":
            print(chunk["data"])
