from pathlib import Path
from langchain.tools import tool
import os
import getpass
import subprocess
import ctypes
from send2trash import send2trash
import shutil

@tool
def current_directory() -> str:
    """
    Retrieves the absolute pathway of the agent's current active system working directory.
    Use this tool when you need to check where the agent process is running on the machine, 
    or when formatting relative file structures into full path specifications.

    Returns:
        str: The absolute path string of the current execution directory.
    """
    try:
        return str(Path.cwd().resolve())
    except Exception as e:
        return f"Error resolving current directory path: {str(e)}"


@tool
def current_user() -> str:
    """
    Retrieves the system username profile under which this agent instance is running.
    Use this tool to learn environmental context permissions, find home directories, 
    or personalize terminal outputs safely without executing low-level shell commands.

    Returns:
        str: The operating system user identification name.
    """
    try:
        return getpass.getuser()
    except Exception:
        # Fallback layer for unique system environments
        return os.environ.get("USER", os.environ.get("USERNAME", "unknown_user"))

@tool
def modify_file(path: str, new_content: str) -> str:
    """
    Overwrites or creates a target text or code file safely with newly provided text content payloads.
    CRITICAL INTENT: Use this tool ONLY when you need to save code files, build config files, 
    or apply complete script updates. Always double check code syntax internally before overwriting.

    Args:
        path (str): File destination path relative to execution directory.
        new_content (str): The complete file string payload to write into the target file.

    Returns:
        str: A confirmation response message indicating successful file writing or system error.
    """
    target = Path(path)
    if target.is_dir():
        return f"Error: Target '{path}' is a directory folder structure. File contents cannot overwrite directories."
        
    try:
        # Build missing subdirectories safely if the agent requests a nested file structure path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_content, encoding="utf-8")
        return f"Success: File successfully updated and written to target path: '{path}'."
    except Exception as e:
        return f"File System Modification Error writing to '{path}': {str(e)}"


@tool
def delete_file(path: str, confirmed: bool = False) -> str:
    """
    Permanently destroys a target file on disk.
    SAFETY REQUIRED: You MUST call current_directory() or search_files() first 
    to verify the exact file location before invoking this tool. Also, This tool requires `confirmed=True` to run. If `confirmed` is False, 
    the file will not be deleted, and you must ask the user for permission first.

    Args:
        path (str): File destination path to erase.
        confirmed (bool): Must be explicitly set to True by the agent after checking with the user.
    """
    target = Path(path)
    # Inside your delete_file tool in your tools module:
    if not target.is_absolute() and not (Path.cwd() / target).exists():
        return (
            f"CRITICAL ERROR FOR AGENT: The path '{path}' does not exist in the working directory ({Path.cwd()}). "
            "AGENT INSTRUCTION: Do not ask the user to find it. You must immediately call your own `search_files` "
            f"tool with keyword='{path}' to find its exact location yourself right now."
        )
        
    if not confirmed:
        return f"Aborted: Deletion of '{path}' requires confirmation. Ask the user 'Do you want me to delete {path}?' in text first."

    try:
        if target.is_dir():
            # ✔ FIX: Use rmtree to delete folders cleanly on Windows
            shutil.rmtree(target)
            return f"Success: Folder directory '{path}' and all its contents have been permanently deleted."
        else:
            # Delete individual files
            target.unlink()
            return f"Success: File '{path}' has been permanently deleted from disk."
            
    except PermissionError as pe:
        return (
            f"Error deleting '{path}': [Permission Denied]. The file/folder might be locked by another program "
            "(like VS Code or your terminal) or requires Administrator privileges to delete."
        )
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@tool
def system_power_sleep() -> str:
    """
    Puts the laptop or desktop computer immediately into low-power Sleep mode.
    CRITICAL BEHAVIOR: If the hardware or OS configuration fails or blocks the Sleep transition, 
    this tool automatically triggers a secure system Shutdown fallback to turn off the device.

    Returns:
        str: Status logging string showing power operation state changes.
    """
    try:
        print("\n⚠️ Power Alert: LLM Agent triggered Sleep command. Suspending system...")
        
        # 1. Attempt Native Windows API Sleep (SetSuspendState: 0=Sleep, 1=Force, 0=Disable Wake)
        # Using ctypes ensures it tries to sleep without messing with global hibernation variables.
        success = ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        
        if success:
            return "Success: Computer state changed to Sleep mode."
            
        # 2. Fallback Verification: If the function returned 0, sleep failed. Trigger Shutdown.
        raise RuntimeError("Windows API rejected the low-power sleep suspension state transition.")
        
    except Exception as error_log:
        print(f"Sleep failed ({str(error_log)}). Activating fallback Shutdown immediately...")
        try:
            # Executes a graceful Windows shutdown with a 10-second delay so you don't lose files
            # /s = shutdown, /t 10 = 10 second countdown tracker
            subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
            return "Warning: Sleep execution failed. Fallback triggered: System shutting down in 10 seconds."
        except Exception as e:
            return f"Critical System Error: Failed to execute both Sleep and Shutdown commands. Error: {str(e)}"


@tool
def remove_file(path: str) -> str:
    """
    Removes a file or directory from the workspace (Equivalent to Linux 'rm' / 'rm -rf').
    SAFETY NOTE: This tool does NOT permanently delete files from disk. It safely 
    moves them to the system Recycle Bin (Trash) so they can be recovered if needed.
    
    CRITICAL INTENT: Use this for automatic, low-risk cleanup of temporary or duplicate files because it saves them to the Recycle Bin..

    Args:
        path (str): The file or folder path relative to the workspace root to be removed.

    Returns:
        str: Status logging confirmation string indicating success or system error.
    """
    target = Path(path)
    if not target.exists():
        return f"Error executing rm: Target path '{path}' does not exist."

    try:
        # Resolve to absolute path to guarantee exact file targeting
        absolute_path = target.resolve()
        
        # Safe execution: Moves the item directly to the Windows Recycle Bin
        send2trash(str(absolute_path))
        
        return f"Success: '{path}' was safely moved to the system Recycle Bin."
    except Exception as e:
        return f"Error executing rm operation on '{path}': {str(e)}"