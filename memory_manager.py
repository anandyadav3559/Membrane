import json
import os
import time

CONTEXT_FILE = 'context.json'
ACTIVE_CONTEXT_FILE = 'active_context.json'

def load_json(filepath, default_value):
    if not os.path.exists(filepath):
        return default_value
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_value

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_id(prefix):
    return f"{prefix}_{int(time.time() * 1000)}"

import re

def split_text_into_chunks(text):
    # Split by whitespace to make chunks word-level
    final_chunks = text.split()

    chunks = []
    for idx, c in enumerate(final_chunks):
        chunks.append({
            "chunk_id": generate_id(f"chunk_{idx}"),
            "index": idx,
            "content": c
        })
    return chunks

def save_selection_to_context(selected_indexes, llm_last_response, user_prompt=""):
    """
    selected_indexes: list of integers indicating which chunks the user clicked
    llm_last_response: full string response from the LLM
    user_prompt: the prompt that generated this response
    """
    if not selected_indexes:
        return None

    all_chunks = split_text_into_chunks(llm_last_response)
    selected_indexes = sorted(list(set(selected_indexes)))
    
    merged_chunks = []
    current_group = []
    
    for idx in selected_indexes:
        # Sanity check if index exists
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
            # Add all chunks in the block
            active_block_entry["active_chunks"] = list(set(active_block_entry["active_chunks"] + [c["chunk_id"] for c in full_block["chunks"]]))
            
    elif action == "remove":
        if active_block_entry:
            if chunk_id:
                if chunk_id in active_block_entry["active_chunks"]:
                    active_block_entry["active_chunks"].remove(chunk_id)
            else:
                # Remove entire block
                active_context = [b for b in active_context if b["block_id"] != block_id]
                
    # Cleanup blocks that have no active chunks left
    active_context = [b for b in active_context if b.get("active_chunks")]
    
    save_json(ACTIVE_CONTEXT_FILE, active_context)
    return True

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
