import requests

def call_llm(prompt, active_context_string="", config=None):
    """
    config is a dict:
    {
      "mode": "api_key", "proxy", or "simulate"
      "api_key": "...",
      "proxy_url": "http://localhost:8000/v1/chat/completions",
      "model": "llama-3.1-8b-instant"
    }
    """
    if config is None or config.get("mode") == "simulate":
        return (
            f"You asked: {prompt}\n\n"
            "Here is some information about your request.\n\n"
            "First point: AI has evolved significantly over the last decade. Neural networks are at the core.\n\n"
            "Second point: Context management is crucial for coherent long-term interactions in chatbots.\n\n"
            "Third point: Storing structured blocks and active contexts prevents token overflow."
        )
        
    messages = []
    if active_context_string:
        messages.append({"role": "system", "content": active_context_string})
    
    messages.append({"role": "user", "content": prompt})

    url = "https://api.groq.com/openai/v1/chat/completions" # Default direct API
    headers = {
        "Content-Type": "application/json"
    }
    
    if config["mode"] == "api_key":
        api_key = config.get("api_key", "").strip()
        if not api_key:
            return "Error: API Key is missing. Please provide a valid Groq/OpenAI key."
        headers["Authorization"] = f"Bearer {api_key}"
    elif config["mode"] == "proxy":
        url = config.get("proxy_url", "").strip() or "http://localhost:8000/v1/chat/completions"
        headers["Authorization"] = "Bearer dummy_proxy_key"
        
    model = config.get("model", "llama-3.1-8b-instant")
    if not model.strip():
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
