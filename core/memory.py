import time
from core.utils import load_json, save_json, generate_id, CONTEXT_FILE, ACTIVE_CONTEXT_FILE

def save_selection_to_context(selected_text, user_prompt=""):
    """
    Commits selected text to persistent storage and active memory as a new block.
    """
    if not selected_text or not selected_text.strip():
        return None, None

    chunk_id = generate_id("chunk")
    new_chunk = {
        "chunk_id": chunk_id,
        "content": selected_text.strip()
    }
    
    block_id = generate_id("block")
    new_block = {
        "block_id": block_id,
        "timestamp": int(time.time()),
        "user_prompt": user_prompt,
        "chunks": [new_chunk]
    }
    
    # Update persistent block storage
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    context_data.setdefault("blocks", []).append(new_block)
    save_json(CONTEXT_FILE, context_data)
    
    # Add to active context array
    active_context = load_json(ACTIVE_CONTEXT_FILE, [])
    if not isinstance(active_context, list):
        active_context = []
        
    active_context.append({
        "block_id": block_id,
        "active_chunks": [chunk_id]
    })
    save_json(ACTIVE_CONTEXT_FILE, active_context)
    
    return block_id, chunk_id
