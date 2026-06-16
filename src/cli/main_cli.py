
import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.markdown import Markdown
from rich.box import ROUNDED, SIMPLE
from src.agent.assistant import agent_executor
from src.db.db import save_message, init_db, get_chat_history
from src.cli.session import session_handshake
import os
from dotenv import load_dotenv

# Explicitly load the environmental keys from your local .env file
load_dotenv()

app = typer.Typer()
console = Console()

init_db() # creating message table if not exists already

async def async_chat_loop():
    """Handles direct local engine streaming, tool logs, and markdown highlights."""

    console.print(Panel(
        Text("Local Direct CLI Engine Connected (Offline) 💻\nType 'exit' or 'quit' to close the session.", justify="center", style="bold green"),
        box=ROUNDED,
        border_style="bright_blue"
    ))

    # Step 1: Enforce a Session ID verification handshake on startup
    current_session_id = session_handshake()

    # Fetch initial history once to load context into memory if needed
    chat_history = get_chat_history(current_session_id)

    while True:
        try:
            console.print("\n[bold cyan]User[/bold cyan]")
            question = input(" └──> ").strip()

            if not question:
                continue

            if question.lower() in ["exit", "quit"]:
                console.print("\n[bold red]Shutting down local session. Goodbye! 👋[/bold red]\n")
                break

            # Core Database Event: Log the new raw inquiry before pipeline compilation
            save_message(session_id=current_session_id, role="user", content=question)

            console.print("\n[bold yellow]⚙️ Local Execution Event Pipeline Log:[/bold yellow]")
            
            full_response = ""
            live_render = None

            # ✔ SPINNER GATEWAY: Start the status loading animation before hitting the generator stream loop
            with console.status("[bold green]Agent compiling local execution pipeline...[/bold green]", spinner="dots") as status:
                
                # Stream every background engine processing layer directly from your local Llama model
                async for chunk in agent_executor.astream_events(
                    {"input": question, "chat_history": chat_history}, 
                    config={"metadata": {"session_id": current_session_id}},
                    version="v2"
                ):
                    event = chunk["event"]
                    
                    # 1. Capture the exact moment the Chat Model finishes its processing loop
                    if event == "on_chat_model_end":
                        try:
                            output_msg = chunk["data"]["output"] # Fixed dictionary selector layout
            
                            # Extract reasoning thought text if present
                            thought = getattr(output_msg, "content", "")
            
                            # Check if the model has requested to invoke a tool/subtool
                            if hasattr(output_msg, "tool_calls") and output_msg.tool_calls:
                                status.stop() # Clear spinner before writing layout tracks
                                for tool_call in output_msg.tool_calls:
                                    name = tool_call.get("name")
                                    args = tool_call.get("args")
                    
                                # Print a clean trace log showing the tool intercept event
                                console.print(Panel(
                                    f"[bold yellow]🧠 Model Decision:[/bold yellow] Routing request to subtool [bold cyan]{name}[/bold cyan] with args: {args}",
                                    box=SIMPLE, 
                                    border_style="yellow"
                                ))
            
                            # If there are no tool calls, it's a direct textual thought response
                            elif thought.strip() and not live_render:
                                pass
                
                        except Exception as e:
                            pass
                            
                    # 2. Catch the exact moment the LLM starts calling a tool
                    elif event == "on_tool_start":
                        status.stop() # ✔ Clear loading line so panels print cleanly
                        tool_name = chunk['name']
                        tool_input = chunk['data'].get('input', {})
                        console.print(Panel(f"[bold magenta]⚡ Tool Initiated:[/bold magenta] Running {tool_name} with: {tool_input}", box=SIMPLE, border_style="cyan"))
                        
                    # 3. Catch the moment your local Python tool finishes execution
                    elif event == "on_tool_end":
                        status.stop() # ✔ Clear loading line so tool data panels print cleanly
                        tool_name = chunk['name']
                        tool_output = chunk['data'].get('output', '')
                        console.print(Panel(f"[bold white]✅ Tool Output Response Data:[/bold white]\n{tool_output}", box=SIMPLE, border_style="bright_black"))
                    
                    # 4. Stream out the final answer text tokens word-by-word
                    elif event == "on_chat_model_stream":
                        # ✔ THE REAL SPINNER OVERRIDE: Dropped instant token land
                        status.stop()
                        
                        token = chunk["data"]["chunk"].content
                        full_response += token
                        
                        renderable_text = full_response
                        if renderable_text.count("```") % 2 != 0:
                            renderable_text += "\n```"

                        markdown_node = Markdown(renderable_text, code_theme="monokai")
                        panel_frame = Panel(markdown_node, box=ROUNDED, border_style="green", padding=(1, 2))
                        
                        # Initialize the Live viewport on the very first text token chunk
                        if live_render is None:
                            console.print("\n[bold green]Assistant Streaming Output:[/bold green]")
                            live_render = Live(panel_frame, console=console, refresh_per_second=12, auto_refresh=False)
                            live_render.start()
                        else:
                            live_render.update(panel_frame, refresh=True)

            # Safely shut down the refresh thread engine frame when processing ends
            if live_render is not None:
                live_render.stop()

            # Core Database Event: Append the finalized streaming answer to the persistent session row
            if full_response:
                save_message(session_id=current_session_id, role="assistant", content=full_response)
            
            # Refresh internal history cache state variable for subsequent prompts
            chat_history = get_chat_history(current_session_id)

        except KeyboardInterrupt:
            console.print("\n\n[bold red]Session interrupted via terminal command. Exiting...[/bold red]\n")
            break

@app.command()
def ask():
    """
    Launches an interactive, beautiful local terminal chat session 
    with your autonomous developer agent assistant featuring syntax highlighting.
    """
    asyncio.run(async_chat_loop())

if __name__ == "__main__":
    app()
