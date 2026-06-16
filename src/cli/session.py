import uuid
from rich.console import Console
from src.db.db import get_session_ids 

console = Console()

def session_handshake():
    # Initialize a tracking variable to manage the user's active thread state
    current_session_id = None 
    
    while not current_session_id:
        console.print("\n[bold magenta]🔑 Session Configuration Required[/bold magenta]")
        
        # input() already returns a string, no need for .strip() on the prompt itself
        user_input = input("└──> Enter an existing Session ID (or press Enter to create a new one): ").strip()
        
        if user_input:
            current_session_id = user_input
            if current_session_id in get_session_ids():
                console.print(f"[green]✔ Loaded existing session profile: [bold]{current_session_id}[/bold][/green]")
            else:
                console.print(f"[red]❌ Session profile not found: [bold]{current_session_id}[/bold][/red]")
                current_session_id = None  # Reset loop if invalid
        else:
            current_session_id = str(uuid.uuid4())[:8]  # Generate clean 8-char unique hash
            console.print(f"[bright_yellow]✨ Initialized a brand new chat session ID: [bold]{current_session_id}[/bold][/bright_yellow]")
            console.print("[dim]Use this ID next time to resume this precise conversation timeline.[/dim]")
            
    return current_session_id
