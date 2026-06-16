import sqlite3
from pathlib import Path
from typing import List, Dict
from langchain_core.messages import HumanMessage, AIMessage

# Pinpoints the exact folder where this specific script file sits on disk,
# then creates 'chat_history.db' right next to it.
DB_PATH = Path(__file__).parent / "chat_history.db"

def init_db():
    """Initializes the database table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_message(session_id: str, role: str, content: str):
    """Saves a single chat message (user or assistant) to the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.commit()

def get_chat_history(session_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """Retrieves the recent history formatted for your LLM client."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Fetch latest messages first, ordered chronologically
        cursor.execute("""
            SELECT role, content FROM (
                SELECT role, content, id FROM messages 
                WHERE session_id = ? 
                ORDER BY id DESC LIMIT ?
            ) ORDER BY id ASC
        """, (session_id, limit))
        
        langchain_history = []
        for role, content in cursor.fetchall():
            if role == "user":
                langchain_history.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_history.append(AIMessage(content=content))
        return langchain_history
    
def get_session_ids() -> List[str]:
    """Fetches all existing session ids from database"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        session_ids = []
        # Fetch latest messages first, ordered chronologically
        cursor.execute("""
            SELECT DISTINCT session_id FROM messages
        """)
        for row in cursor.fetchall():
            session_ids.append(row[0])
        return session_ids
