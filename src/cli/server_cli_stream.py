
import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.markdown import Markdown
from rich.box import ROUNDED, SIMPLE
from src.cli.session import session_handshake

app = typer.Typer()
console = Console()

API_URL = "http://127.0.0.1:8000/chat/stream"
#  INTO THIS (Explicitly disable connect and read limits for heavy local processing):
timeout_config = httpx.Timeout(None, connect=None, read=None, write=None)

@app.command()
def ask():
    """
    Launches an interactive console client that handles live tool traces 
    and applies on-the-fly markdown syntax highlighting to streaming tokens.
    """
    console.print(Panel(
        Text("Markdown Live Stream Gateway Connected 📡\nWatching local tools compile with on-the-fly interactive cli.", justify="center", style="bold green"),
        box=ROUNDED,
        border_style="bright_blue"
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
                    console.print("\n[bold red]Closing stream terminal network connection. Bye!👋[/bold red]\n")
                    break

                console.print("\n[bold yellow] Real-Time Execution Event Pipeline Log:[/bold yellow]")
                
                accumulated_text = ""
                live_render = None
                
                # 1. Start the animated loading bar right before the network handshake opens
                with console.status("[bold green]Agent compiling execution pipeline...[/bold green]", spinner="dots") as status:
                    
                    inside_tool_output = False
                    tool_output_buffer = []

                    with client.stream("POST", API_URL, json={"message": question, "session_id": current_session_id}) as response:
                        for line in response.iter_lines():
                            if not line:
                                continue
                        
                            # A new tool initialization lands -> flush any old existing tool buffer first
                            if line.startswith("[TOOL_START]"):
                                status.stop()
                                if inside_tool_output and tool_output_buffer:
                                    final_log = "\n".join(tool_output_buffer)
                                    console.print(Panel(f"[bold white]✅ Tool Output Response Data:[/bold white]\n{final_log}", box=SIMPLE, border_style="bright_black"))
                                    tool_output_buffer = []
                                    inside_tool_output = False
                            
                                log_msg = line.replace("[TOOL_START]", "").strip()
                                console.print(Panel(f"[bold magenta]⚡ Tool Initiated:[/bold magenta] {log_msg}", box=SIMPLE, border_style="cyan"))
                                continue

                            # A new tool execution data stream begins
                            elif line.startswith("[TOOL_END]"):
                                status.stop()
                                # If a previous unclosed buffer exists, flush it
                                if tool_output_buffer:
                                    final_log = "\n".join(tool_output_buffer)
                                    console.print(Panel(f"[bold white]✅ Tool Output Response Data:[/bold white]\n{final_log}", box=SIMPLE, border_style="bright_black"))
                            
                                inside_tool_output = True
                                tool_output_buffer = [line.replace("[TOOL_END]", "").strip()]
                                continue
                            
                            # An incoming final assistant token lands -> flush tool data buffer completely
                            elif line.startswith("[TOKEN]"):
                                status.stop()
                                if inside_tool_output and tool_output_buffer:
                                    final_log = "\n".join(tool_output_buffer)
                                    console.print(Panel(f"[bold white]✅ Tool Output Response Data:[/bold white]\n{final_log}", box=SIMPLE, border_style="bright_black"))
                                    tool_output_buffer = []
                                    inside_tool_output = False
                                
                                token = line.replace("[TOKEN]", "")

                                accumulated_text += token
                                renderable_text = accumulated_text
                                if renderable_text.count("```") % 2 != 0:
                                    renderable_text += "\n```"
                                
                                markdown_node = Markdown(renderable_text, code_theme="monokai")
                                panel_frame = Panel(markdown_node, box=ROUNDED, border_style="green", padding=(1, 2))
                            
                                if live_render is None:
                                    console.print("\n[bold green]Assistant Streaming Output:[/bold green]")
                                    live_render = Live(panel_frame, console=console, refresh_per_second=12, auto_refresh=False)
                                    live_render.start()
                                else:
                                    live_render.update(panel_frame, refresh=True)
                                continue

                            # An error message lands -> shut down states
                            elif line.startswith("[ERROR]"):
                                status.stop()
                                inside_tool_output = False
                                console.print(f"[bold red]{line}[/bold red]")
                                continue

                            # ✔ THE CATCH-ALL ACCUMULATOR: If the server is sending raw lines of data 
                            # belonging to ANY tool, store it safely inside the buffer array
                            if inside_tool_output:
                                tool_output_buffer.append(line)
                                continue

                        # SAFETY CHECK FOR ALL TOOLS: Once the entire network connection ends,
                        # if there is still unprinted tool information remaining in memory, print it out.
                        if inside_tool_output and tool_output_buffer:
                            final_log = "\n".join(tool_output_buffer)
                            console.print(Panel(f"[bold white]✅ Tool Output Response Data:[/bold white]\n{final_log}", box=SIMPLE, border_style="bright_black"))

                        if live_render is not None:
                            live_render.stop()

            except httpx.ConnectError:
                console.print("\n[bold red]Critical Error: Cannot reach server. Did you start main.py?[/bold red]")
            except KeyboardInterrupt:
                if live_render is not None:
                    live_render.stop()
                console.print("\n\n[bold red]Stream connection broken via manual interrupt signal.[/bold red]\n")
                break

if __name__ == "__main__":
    app()

