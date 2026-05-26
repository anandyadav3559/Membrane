from core.utils import load_json, save_json, CONTEXT_FILE, ACTIVE_CONTEXT_FILE

def update_active_context(block_id, chunk_id=None, action="add"):
    """
    Updates active status of a block or a chunk.
    action: "add" or "remove"
    """
    active_context = load_json(ACTIVE_CONTEXT_FILE, [])
    if not isinstance(active_context, list):
        active_context = []
        
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    full_block = next((b for b in context_data["blocks"] if b["block_id"] == block_id), None)
    if not full_block:
        return False
        
    active_block_entry = next((b for b in active_context if b["block_id"] == block_id), None)
    
    if action == "add":
        if not active_block_entry:
            active_block_entry = {"block_id": block_id, "active_chunks": []}
            active_context.append(active_block_entry)
            
        if chunk_id:
            if chunk_id not in active_block_entry["active_chunks"]:
                active_block_entry["active_chunks"].append(chunk_id)
        else:
            active_block_entry["active_chunks"] = list(set(active_block_entry["active_chunks"] + [c["chunk_id"] for c in full_block["chunks"]]))
            
    elif action == "remove":
        if active_block_entry:
            if chunk_id:
                if chunk_id in active_block_entry["active_chunks"]:
                    active_block_entry["active_chunks"].remove(chunk_id)
            else:
                active_context = [b for b in active_context if b["block_id"] != block_id]
                
    active_context = [b for b in active_context if b.get("active_chunks")]
    save_json(ACTIVE_CONTEXT_FILE, active_context)
    return True
