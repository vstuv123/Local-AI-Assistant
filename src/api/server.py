
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from src.agent.assistant import agent_executor
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from src.db.db import init_db, save_message, get_chat_history
import os
from dotenv import load_dotenv

# Explicitly load the environmental keys from your local .env file
load_dotenv()

# 1. Define the lifecycle logic inside an async context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This block triggers upon API app server boot runtime (Startup)
    init_db() 
    
    yield  # The application serves requests while frozen here
    
    # Optional but we can Put our cleanup/shutdown code here (e.g., close_db()). In our case, we not need it

# 2. Pass the lifespan manager directly into the FastAPI instance
app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session" # Added session tracker key argument

# Upgraded response structure to include the tool trace history array
class DetailedChatResponse(BaseModel):
    tool_steps: list[dict]
    final_output: str
    session_id: str


@app.post("/chat", response_model=DetailedChatResponse)
async def detailed_chat(request: ChatRequest):
    """
    Standard synchronous chat gateway. Receives a user string query,
    executes background agent tools dynamically, and returns the final response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message context content cannot be empty.")
        
    try:
        # 1. Fetch previous session logs to build short-term memory context
        history_context = get_chat_history(request.session_id)
        
        # Invoke the agent executor
        result = agent_executor.invoke(
            {
                "input": request.message,
                "chat_history": history_context  # Feeds past context directly to prompt
            },
            config={
                "metadata": {
                    "session_id": request.session_id
                }
            }
        )

        final_answer = result["output"]
        # 3. Commit this current conversational turn into the SQLite db
        save_message(request.session_id, "user", request.message)
        save_message(request.session_id, "assistant", final_answer)
        
        # Parse the intermediate steps tracker list
        # result["intermediate_steps"] contains a list of tuples: (AgentAction, ToolOutput)
        steps_log = []
        for action, observation in result.get("intermediate_steps", []):
            steps_log.append({
                "tool_called": action.tool,
                "tool_input": action.tool_input,
                "log_thought": action.log, # The LLM's raw reasoning text
                "tool_output": str(observation)
            })
            
        return DetailedChatResponse(
            tool_steps=steps_log,
            final_output=final_answer,
            session_id=request.session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Service Error: {str(e)}")

@app.post("/chat/stream")
async def stream_agent_events(request: ChatRequest):
    """
    Advanced streaming gateway. Pumps tokens down an active HTTP connection stream
    as soon as they emerge from the local model pipeline.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message context content cannot be empty.")
    
    async def event_generator():
        try:
            history_context = get_chat_history(request.session_id)
            accumulated_output = ""
            
            async for event in agent_executor.astream_events(
                {
                    "input": request.message, 
                    "chat_history": history_context
                },
                config={
                    "metadata": {
                        "session_id": request.session_id
                    }
                },
                version="v2"
            ):
                kind = event["event"]
                
                # 1. Tool Call Initialization Layer
                if kind == "on_tool_start":
                    tool_name = event['name']
                    tool_input = event['data'].get('input', {})
                    yield f"[TOOL_START] Running {tool_name} with: {tool_input}\n"
                    
                # 2. Tool Completion Return Data Layer
                elif kind == "on_tool_end":
                    tool_name = event['name']
                    tool_output = event['data'].get('output', '')
                    # Escape internal raw newlines so they don't break client-side line-by-line streaming
                    clean_output = str(tool_output).strip()
                    yield f"[TOOL_END] Result from {tool_name}: {clean_output}\n"
                    
                # 3. ✔ FIX: Match chat model stream events correctly
                elif kind == "on_chat_model_stream":
                    chunk_data = event["data"].get("chunk")
                    if chunk_data and hasattr(chunk_data, "content"):
                        content = chunk_data.content
                        if content:
                            accumulated_output += content
                            # Print directly without adding spaces so words stay joined naturally
                            yield f"[TOKEN]{content}\n"
            
            # Commit the session records after successful model exhaustion
            save_message(request.session_id, "user", request.message)
            save_message(request.session_id, "assistant", accumulated_output)
                        
        except Exception as e:
            yield f"\n[ERROR] Streaming System Error: {str(e)}\n"

    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    # 0.0.0.0 tells your computer to listen to your entire local home network!
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)