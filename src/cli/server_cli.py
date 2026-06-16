
import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.box import ROUNDED, SIMPLE
from src.cli.session import session_handshake

app = typer.Typer()
console = Console()

API_URL = "http://127.0.0.1:8000/chat"
#  INTO THIS (Explicitly disable connect and read limits for heavy local processing):
timeout_config = httpx.Timeout(None, connect=None, read=None, write=None)

@app.command()
def ask():
    """
    Launches an interactive developer console interface. Displays full background 
    tool execution trace tracking histories sent down from the API backend framework.
    """
    console.print(Panel(
        Text("Developer Debug Client Connected 🛠️\nExposing full background agent tool-calling execution traces.", justify="center", style="bold yellow"),
        box=ROUNDED,
        border_style="orange3"
    ))

    # Step 1: Enforce a Session ID verification handshake on startup
    current_session_id = session_handshake()

    with httpx.Client(timeout=timeout_config) as client:
        while True:
            try:
                console.print("\n[bold cyan]User[/bold cyan]")
                question = input(" └──> ").strip()

                if not question:
                    continue

                if question.lower() in ["exit", "quit"]:
                    console.print("\n[bold red]Closing debug gateway. Goodbye!👋[/bold red]\n")
                    break

                with console.status("[bold yellow]Executing agent framework loops...[/bold yellow]", spinner="dots"):
                    payload = {"message": question, "session_id": current_session_id}
                    response = client.post(API_URL, json=payload)
                    
                    if response.status_code != 200:
                        console.print(f"[bold red]Server Error ({response.status_code}): {response.text}[/bold red]")
                        continue
                        
                    data = response.json()

                # 1. Parse and print the tool-calling trace blocks cleanly
                tool_steps = data.get("tool_steps", [])
                if tool_steps:
                    console.print("\n[bold yellow]⚙️ Background Tool Execution Trace Timeline:[/bold yellow]")
                    for index, step in enumerate(tool_steps, 1):
                        trace_text = (
                            f"[bold magenta]Step {index}:[/bold magenta] Fired Tool -> [bold green]{step['tool_called']}[/bold green]\n"
                            f"[bold blue]Arguments Passed:[/bold blue] {step['tool_input']}\n"
                            f"[bold cyan]LLM Reasoning Thought:[/bold cyan] {step['log_thought'].strip()}\n"
                            f"[bold white]Returned Data Content Output:[/bold white]\n{step['tool_output']}"
                        )
                        console.print(Panel(trace_text, box=SIMPLE, border_style="bright_black"))

                # 2. Render the final markdown payload
                final_answer = data.get("final_output", "No response content generated.")
                highlighted_output = Markdown(final_answer, code_theme="monokai")

                console.print("\n[bold green]Final Assistant Response[/bold green]")
                console.print(Panel(
                    highlighted_output, 
                    box=ROUNDED, 
                    border_style="green",
                    padding=(1, 2)
                ))

            except httpx.ConnectError:
                console.print("\n[bold red]Critical Error: Cannot connect to FastAPI server. Did you remember to start main.py?[/bold red]")
            except KeyboardInterrupt:
                console.print("\n\n[bold red]Session disconnected via manual interrupt command.[/bold red]\n")
                break

if __name__ == "__main__":
    app()
