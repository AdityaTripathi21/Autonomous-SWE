from langchain_core.tools import tool
from pathlib import Path

# Note: This could be done with the FileManagementToolKit from LangChain, but I want to do it by myself for now

WORKSPACE = Path("workspace").resolve()

def _resolve_path(path:str) -> Path | str:
    try:
        full_path = (WORKSPACE / path).resolve()

        if not full_path.is_relative_to(WORKSPACE):
            return f"Error: '{path}' is outside the workspace"

        return full_path
    
    except Exception as e:
        return f"Error resolving path: {str(e)}"

@tool
def read_file(path:str) -> str:
    """Read the contents of a file inside the workspace"""
    
    full_path = _resolve_path(path)
    if isinstance(full_path, str):
        return full_path
    
    if not full_path.is_file():
        return f"Error: {path} is not a file"
    
    try:
        return full_path.read_text()
    
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool 
def write_file(path:str, content:str) -> str:
    """Write to this path inside the workspace"""
    
    full_path = _resolve_path(path)
    if isinstance(full_path, str):
        return full_path
    
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True) # make sure directory exists, if it doesn't, make it
    except Exception as e:
        return f"Error creating directory: {str(e)}"
    
    try:
        full_path.write_text(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
    
@tool
def list_files(directory: str = "") -> str:
    """List all files in the workspace (recursively)"""
    
    full_path = _resolve_path(directory)
    if isinstance(full_path, str):
        return full_path
    
    if not full_path.exists():
        return f"Error: {directory} does not exist"
    
    if not full_path.is_dir():
        return f"Error: {directory} is not a directory"
    
    files = []
    for p in full_path.rglob("*"):  # walk through paths recursively
        if p.is_file():
            files.append(str(p.relative_to(WORKSPACE))) # relative_to removes workspace/

    if not files:
        return "No files found"

    return "\n".join(files)
    
    
    
