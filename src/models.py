from langchain_ollama import ChatOllama

def get_llm():
    return ChatOllama(
        model="llama3.2:3b",
        temperature=0,
        num_ctx=32768,     # Give it room to look at history
    )