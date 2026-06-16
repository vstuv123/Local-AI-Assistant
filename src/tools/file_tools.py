from pathlib import Path
from langchain.tools import tool
import ast


@tool
def read_file(path: str) -> str:
    """
    Reads and returns the complete contents of a file.

    Use this tool whenever you need the actual source code,
    configuration, documentation, or text before performing
    analysis, explanation, debugging, review, or test generation.

    This tool should usually be called after analyze_file()
    when deeper inspection is required.
    
    Args:
        path (str): The exact file path relative to workspace root (e.g., 'src/main.py').
        
    Returns:
        str: Raw code text contents of the requested file.
    """
    target = Path(path)
    if not target.exists():
        return f"Error: File '{path}' not found."
    if target.is_dir():
        return f"Error: '{path}' is a directory. Use project_tree to check its files instead."
        
    try:
        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


@tool
def list_directory(path: str = ".") -> str:
    """
    Lists the immediate contents of a specified directory folder (shallow scan).
    Use this tool to peek inside a specific folder to check its files or subfolders 
    without generating a full recursive repository tree diagram.
    Also, you can Use this tool to verify the contents of the root running directory environment 
    without having to pass explicit directory string pathways.

    Args:
        path (str): The target directory folder path to look inside. Defaults to ".".

    Returns:
        str: A newline-separated text list of files and folders located inside the directory.
    """
    target = Path(path)
    if not target.exists():
        return f"Error: Directory '{path}' does not exist."
    if not target.is_dir():
        return f"Error: '{path}' is a file, not a directory. Use read_file to inspect it."

    try:
        return "\n".join(str(p) for p in target.iterdir())
    except Exception as e:
        return f"Error accessing directory '{path}': {str(e)}"


@tool
def search_files(keyword: str) -> str:
    """
    Searches recursively across the entire project directory tree to match files by name.
    Use this tool when you know the name (or part of the name) of a script, module, 
    or configuration file, but you do not know which directory it lives in.

    Args:
        keyword (str): A case-insensitive substring of the filename to search for (e.g., 'auth').

    Returns:
        str: A newline-separated text list of matching file paths (capped at 50 results).
    """
    matches = []
    clean_keyword = keyword.lower()

    # Define folders you want to completely skip
    IGNORE_DIRS = {".git", ".venv", "__pycache__", "node_modules"}

    for file in Path(".").rglob("*"):
        # Check if any parent folder of the file is in the ignore list
        if any(part in IGNORE_DIRS for part in file.parts):
            continue
        
        if clean_keyword in file.name.lower():
            matches.append(str(file))

    if not matches:
        return f"No matching files containing '{keyword}' found."

    return "\n".join(matches[:50])

@tool
def project_tree(path: str = ".") -> str:
    """
    Generates a full visual directory hierarchy tree mapping out the project structure.
    CRITICAL INTENT: Run this tool FIRST when encountering an unfamiliar or new project. 
    It gives you an immediate structural map of the workspace so you can locate where 
    source code, tests, and configs are managed. Automatically filters noise like .git or venv.

    Args:
        path (str): The root directory folder path to map out from. Defaults to ".".

    Returns:
        str: A text-based tree blueprint detailing the repository design.
    """

    root = Path(path)
    if not root.exists():
        return f"Error: Path '{path}' does not exist."
        
    ignore_patterns = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.DS_Store'}
    tree_lines = [f"{root.name}/"]
    
    def build_tree(dir_path: Path, prefix: str = ""):
        try:
            items = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
            
        items = [item for item in items if item.name not in ignore_patterns]
        count = len(items)
        
        for i, item in enumerate(items):
            is_last = (i == count - 1)
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{item.name}{'/' if item.is_dir() else ''}")
            
            if item.is_dir():
                next_prefix = prefix + ("    " if is_last else "│   ")
                build_tree(item, next_prefix)

    build_tree(root)
    return "\n".join(tree_lines)
