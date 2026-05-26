import os
import requests
from dotenv import load_dotenv

load_dotenv()

def call_llm(prompt, active_context_string="", config=None):
    """
    Calls the LLM based on .env configuration:
    - LLM_ENDPOINT="proxy" or "api"
    - GROQ_API_KEY="..."
    """
    messages = []
    if active_context_string:
        messages.append({"role": "system", "content": active_context_string})
    
    messages.append({"role": "user", "content": prompt})

    endpoint_mode = os.getenv("LLM_ENDPOINT", "proxy").lower().strip()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if endpoint_mode == "api":
        url = "https://api.groq.com/openai/v1/chat/completions"
        if not api_key:
            return "Error: LLM_ENDPOINT is 'api' but GROQ_API_KEY is not set in .env."
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        # Default to proxy
        url = "http://127.0.0.1:8001/v1/chat/completions"
        headers["Authorization"] = "Bearer dummy_proxy_key"
        
    model = "llama-3.1-8b-instant"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error calling LLM: {str(e)}"
