from pathlib import Path
from langchain.tools import tool
import re
import ast
    
@tool
def find_todos(path: str = ".") -> str:
    """
    Scans the repository to identify developer annotations, technical debt, and bugs.
    It hunts specifically for 'TODO', 'FIXME', 'HACK', and 'BUG' comment markers inside files.
    Use this tool to spot uncompleted features, workarounds, or known problem areas.
    
    Args:
        path (str): The directory location to scan recursively from. Defaults to ".".
        
    Returns:
        str: Discovered code markers grouped cleanly with file paths and line numbers.
    """
    root = Path(path)
    if not root.exists():
        return f"Error: Path '{path}' does not exist."
        
    keywords = ["TODO", "FIXME", "HACK", "BUG"]
    pattern = re.compile(r"\b(" + "|".join(keywords) + r")\b[:\s\-]", re.IGNORECASE)
    ignore_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.uv'}
    
    # Explicitly restrict searches to code and documentation file types
    ALLOWED_EXTENSIONS = {'.py', '.md', '.txt', '.json', '.js', '.ts', '.ini', '.toml'}
    
    results = []

    for file_path in root.rglob('*'):
        # Check if the folder path is ignored
        if any(part in file_path.parts for part in ignore_dirs):
            continue
            
        # Skip directories, binary databases (.db), and files not in our safe extension list
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            results.append(f"{file_path}:{line_num} -> {line.strip()}")
            except Exception:
                continue

    return "\n".join(results) if results else "No developer annotations (TODO/FIXME/HACK/BUG) found."

@tool
def analyze_file(path: str) -> str:
    """
    Provides high-level static architecture metrics of a code file.
    Use this tool to parse structural items like line counts, classes, functions, and imports 
    before committing to reading the whole file via read_file. Prevents context bloating.
    
    Args:
        path (str): Path targeting a python script (e.g., 'utils/helpers.py').
        
    Returns:
        str: Structural metadata overview of the codebase file components.
    """
    target = Path(path)
    # Explicitly restrict searches to code file types
    ALLOWED_EXTENSIONS = {'.py', '.json', '.js', '.ts'}
    if not target.exists():
        return f"Error: File '{path}' not found."
    if not target.suffix in ALLOWED_EXTENSIONS:
        return f"Error: Static code analysis metrics are limited to Python (.py) files."

    try:
        content = target.read_text(encoding="utf-8")
        lines = content.splitlines()
        tree = ast.parse(content)
        
        imports = []
        classes = []
        functions = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                
        metrics = [
            f"File Name: {target.name}",
            f"Lines of Code: {len(lines)}",
            f"Imports: {', '.join(imports) if imports else 'None'}",
            f"Classes: {', '.join(classes) if classes else 'None'}",
            f"Functions: {', '.join(functions) if functions else 'None'}"
        ]
        return "\n".join(metrics)
        
    except SyntaxError:
        return f"Error: Could not parse syntax tree. '{path}' contains python structural syntax errors."
    except Exception as e:
        return f"Error analyzing structural components of '{path}': {str(e)}"
    
@tool
def find_possible_bugs(path: str) -> str:
    """
    Performs lightweight static analysis of python files.

    Use this tool before asking for a full bug review.
    It quickly identifies common code smells such as:

    - Mutable default arguments
    - Empty exception handlers
    - Silent error suppression

    This is a fast pre-analysis tool and does not replace
    full source code inspection.
    
    Args:
        path (str): Path targeting a python script (e.g., 'app/server.py').
        
    Returns:
        str: A summary of flagged code structural anomalies or warnings.
    """
    target = Path(path)
    if not target.exists():
        return f"Error: File '{path}' not found."
    if target.suffix != '.py':
        return f"Error: Bug isolation linting is currently limited to Python (.py) files."

    warnings = []
    try:
        tree = ast.parse(target.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            # Check for dangerous mutable default arguments: def func(x=[])
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        warnings.append(f"Line {node.lineno}: Function '{node.name}' uses a mutable default argument.")
            
            # Check for silent generic exception handling: except: pass
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    warnings.append(f"Line {node.lineno}: Dangerous empty 'except:' block suppresses errors silently.")
                    
        return "\n".join(warnings) if warnings else "No obvious structural code anti-patterns flagged."
    except Exception as e:
        return f"Parser failure while scanning for anomalies: {str(e)}"

@tool
def search_code(keyword: str, path: str = ".") -> str:
    """
    Searches recursively across all text files in the project for a specific raw code string or keyword.
    CRITICAL INTENT: Call this tool when you know a specific code snippet, class initialization, 
    variable name, or error string (e.g., "ChatOllama", "def authentication"), but you do not know 
    which exact file or line number contains it.

    Args:
        keyword (str): The text phrase, class, or function name to search for (case-insensitive).
        path (str): The root folder directory to start searching from. Defaults to ".".

    Returns:
        str: A text list of matching instances showing the exact file path and line number (capped at 50 results).
    """
                
    root = Path(path)
    if not root.exists():
        return f"Error: Path '{path}' does not exist."
        
    ignore_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.idea', '.vscode', '.uv'}
    
    # ✔ EXTENSION GUARD: Restrict code searching to readable source files only
    ALLOWED_EXTENSIONS = {'.py', '.md', '.txt', '.json', '.js', '.ts', '.ini', '.toml', '.cfg', '.yaml', '.yml'}
    
    matches = []
    clean_keyword = keyword.lower()
    
    for file_path in root.rglob('*'):
        if any(part in file_path.parts for part in ignore_dirs):
            continue
            
        # ✔ FILTER OUT BINARIES: Verify file type suffix before opening
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if clean_keyword in line.lower():
                            matches.append(f"{file_path} line {line_num}: {line.strip()}")
            except Exception:
                continue # Gracefully skip locked files
                
    if not matches:
        return f"No occurrences of code keyword '{keyword}' found in the project repository."
        
    return "\n".join(matches[:50]) # Caps output string size to protect LLM context window limits

@tool
def generate_tests(path: str) -> str:
    """
    Scans a source file and extracts the public testable function signatures (interfaces).
    It returns function names, arguments, type hints, return types, and docstrings.
    CRITICAL INTENT: Call this tool when you need to know WHAT functions exist, WHAT arguments
    they take, and WHAT they return, so you can plan and write a complete unit test suite.

    Args:
        path (str): Target implementation script file path (e.g., 'src/auth.py').
        
    Returns:
        str: A detailed structural map of public functions and their input/output contracts.
    """
    target = Path(path)
    if not target.exists():
        return f"Error: File '{path}' not found."
        
    if target.suffix != '.py':
        return f"Error: Static code analysis metrics are limited to Python (.py) files."
        
    try:
        tree = ast.parse(target.read_text(encoding="utf-8"))
        interfaces = []
        
        for node in ast.walk(tree):
            # Find functions, ignoring private ones starting with '_'
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                # 1. Extract and format the input arguments
                args_list = []
                for arg in node.args.args:
                    arg_str = arg.arg
                    # Capture type hint if it exists (e.g., amount: float)
                    if arg.annotation:
                        arg_str += f": {ast.unparse(arg.annotation)}"
                    args_list.append(arg_str)
                
                # 2. Capture return type hint if it exists (e.g., -> float)
                return_type = "Any"
                if node.returns:
                    return_type = ast.unparse(node.returns)
                    
                # 3. Extract the function's docstring for behavioral context
                docstring = ast.get_docstring(node)
                doc_text = f"\n    Docstring: \"{docstring}\"" if docstring else "\n    Docstring: None"
                
                # Combine into a clean interface contract
                signature = f"- def {node.name}({', '.join(args_list)}) -> {return_type}:{doc_text}"
                interfaces.append(signature)
                
        if not interfaces:
            return f"No top-level public functions discovered to target for tests in {target.name}."
            
        return f"File: {target.name}\nTest Target Interfaces Identified:\n" + "\n\n".join(interfaces)
        
    except Exception as e:
        return f"Failed to map test target structure: {str(e)}"
