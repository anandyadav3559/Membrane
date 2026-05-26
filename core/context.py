from core.utils import load_json, CONTEXT_FILE, ACTIVE_CONTEXT_FILE

def get_active_context_string():
    """Builds the string to be injected into the next LLM prompt."""
    active_context = load_json(ACTIVE_CONTEXT_FILE, [])
    if not isinstance(active_context, list):
        active_context = []
        
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    if not isinstance(context_data, dict):
        context_data = {"blocks": []}
    if "blocks" not in context_data:
        context_data["blocks"] = []
    
    if not active_context:
        return ""
        
    context_string = "--- ACTIVE CONTEXT ---\n"
    
    chunk_lookup = {}
    for b in context_data["blocks"]:
        for c in b["chunks"]:
            chunk_lookup[c["chunk_id"]] = c["content"]
            
    for active_b in active_context:
        for cid in active_b["active_chunks"]:
            if cid in chunk_lookup:
                context_string += f"- {chunk_lookup[cid]}\n"
                
    context_string += "----------------------\n"
    return context_string
