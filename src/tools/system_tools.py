import psutil
from pathlib import Path
from langchain.tools import tool

@tool
def memory_usage() -> str:
    """
    Retrieves the current RAM (Random Access Memory) utilization metrics of the host system.
    Use this tool to track memory strain or verify if the machine has enough resources 
    available to run heavy local tasks like initializing large models or compiling code.

    Returns:
        str: A formatted breakdown displaying total percentage used and total bytes available.
    """
    mem = psutil.virtual_memory()
    return f"Used: {mem.percent}% | Available: {mem.available / (1024**3):.2f} GB"


@tool
def cpu_usage() -> str:
    """
    Retrieves the real-time CPU utilization percentage across all system cores.
    Use this tool to inspect active processing workloads or diagnose if background tasks 
    are bottlenecking hardware execution performance.

    Returns:
        str: The current aggregated processor utilization percentage.
    """
    return f"Current CPU Utilization: {psutil.cpu_percent(interval=0.5)}%"


@tool
def disk_usage() -> str:
    """
    Retrieves storage metrics and remaining capacity for the primary system root partition.
    Use this tool to verify available hard drive space before downloading massive model datasets, 
    cloning large repositories, or writing heavy log binaries to disk.

    Returns:
        str: Total storage percentage currently consumed on the root hard drive.
    """
    try:
        disk = psutil.disk_usage("/")
        return f"Root Disk Space Used: {disk.percent}%"
    except Exception as e:
        return f"Error gathering disk drive metrics: {str(e)}"


@tool
def running_processes() -> str:
    """
    Lists active system processes running on the machine, detailing names and Process IDs (PIDs).
    Use this tool to discover running background programs, locate target services, or check 
    if specific development environments are actively running on the host system.

    Returns:
        str: A newline-separated text index list of the first 50 active system process records.
    """
    processes = []
    try:
        for p in psutil.process_iter(["pid", "name"]):
            processes.append(f"PID {p.info['pid']} - {p.info['name']}")
    except Exception as e:
        return f"Error compiling active system processes: {str(e)}"
        
    return "\n".join(processes[:50])


from pathlib import Path

@tool
def largest_files(directory: str = ".") -> str:
    """
    Scans a directory tree recursively to isolate and sort the top 10 heaviest files by storage size.
    Use this tool to perform drive cleanup, uncover bloated cache files, or identify where 
    massive assets (like downloaded model blobs or databases) are consuming space.
    Ignores common virtual environments and system folders like .venv and .git.

    Args:
        directory (str): The root folder directory to start scanning from. Defaults to ".".

    Returns:
        str: A sorted list displaying the top 10 largest files mapped out alongside their sizes in Megabytes (MB).
    """
    root_path = Path(directory)
    if not root_path.exists():
        return f"Error: Target path '{directory}' does not exist."

    # Folders to completely skip during the scan
    IGNORE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".uv"}

    files = []
    # Recursively hunt down sizes while gracefully skipping locked or system-protected files
    for path in root_path.rglob("*"):
        # Check if any parent folder of the file matches our ignore list
        if any(part in IGNORE_DIRS for part in path.parts):
            continue

        if path.is_file():
            try:
                size = path.stat().st_size
                files.append((path, size))
            except (PermissionError, FileNotFoundError):
                continue

    if not files:
        return f"No readable files discovered within directory structure: '{directory}'."

    # Sort largest files to the top of the stack
    files.sort(key=lambda x: x[1], reverse=True)

    result = []
    for path, size in files[:10]:
        size_in_mb = size / (1024 * 1024)
        result.append(f"{path} : {size_in_mb:.2f} MB")

    return f"Top 10 Largest Files in '{directory}':\n" + "\n".join(result)