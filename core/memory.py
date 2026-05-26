import time
from core.utils import load_json, save_json, generate_id, CONTEXT_FILE, ACTIVE_CONTEXT_FILE
from core.chunking import split_text_into_chunks

def save_selection_to_context(selected_indexes, llm_last_response, user_prompt=""):
    """
    Commits selected chunks to persistent storage and active memory.
    """
    if not selected_indexes:
        return None

    all_chunks = split_text_into_chunks(llm_last_response)
    selected_indexes = sorted(list(set(selected_indexes)))
    
    merged_chunks = []
    current_group = []
    
    for idx in selected_indexes:
        if idx < 0 or idx >= len(all_chunks):
            continue
            
        if not current_group:
            current_group.append(idx)
        else:
            if idx == current_group[-1] + 1:
                current_group.append(idx)
            else:
                content = " ".join([all_chunks[i]['content'] for i in current_group])
                merged_chunks.append({
                    "chunk_id": generate_id(f"chunk_{current_group[0]}"),
                    "content": content
                })
                current_group = [idx]
                
    if current_group:
        content = " ".join([all_chunks[i]['content'] for i in current_group])
        merged_chunks.append({
            "chunk_id": generate_id(f"chunk_{current_group[0]}"),
            "content": content
        })
    
    if not merged_chunks:
        return None
    
    block_id = generate_id("block")
    new_block = {
        "block_id": block_id,
        "timestamp": int(time.time()),
        "user_prompt": user_prompt,
        "chunks": merged_chunks
    }
    
    # Update persistent block storage
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    if "blocks" not in context_data:
        context_data["blocks"] = []
    context_data["blocks"].append(new_block)
    save_json(CONTEXT_FILE, context_data)
    
    # Add to active context array
    active_context = load_json(ACTIVE_CONTEXT_FILE, [])
    if not isinstance(active_context, list):
        active_context = []
        
    active_context.append({
        "block_id": block_id,
        "active_chunks": [c["chunk_id"] for c in merged_chunks]
    })
    save_json(ACTIVE_CONTEXT_FILE, active_context)
    
    return block_id
