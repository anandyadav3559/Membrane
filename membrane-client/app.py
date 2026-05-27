import sys
import os
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.utils import generate_id

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
CORS(app)

# Fallback to an absolute path relative to this script if not in env
default_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core', 'data'))
DATA_FOLDER_PATH = os.environ.get('DATA_FOLDER_PATH', default_data_path)
PORT = int(os.environ.get('PORT', 5007))
CONTEXT_FILE = os.path.join(DATA_FOLDER_PATH, 'context.json')
ACTIVE_CONTEXT_FILE = os.path.join(DATA_FOLDER_PATH, 'active_context.json')
TRASH_FILE = os.path.join(DATA_FOLDER_PATH, 'trash.json')

def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return default

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/context', methods=['GET'])
def get_context():
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    active_data = load_json(ACTIVE_CONTEXT_FILE, [])
    
    # Map active data for quick lookup and order
    active_map = {}
    for i, item in enumerate(active_data):
        active_map[item['block_id']] = {
            'chunks': set(item.get('active_chunks', [])),
            'index': i
        }
    
    # Enrich context data with active statuses
    enriched_blocks = []
    for block in context_data.get('blocks', []):
        b_id = block.get('block_id')
        if not b_id:
            continue
        is_active = b_id in active_map
        active_index = active_map[b_id]['index'] if is_active else 999999
        enriched_chunks = []
        for chunk in block.get('chunks', []):
            c_id = chunk['chunk_id']
            enriched_chunks.append({
                **chunk,
                "is_active": is_active and c_id in active_map[b_id]['chunks']
            })
        
        enriched_blocks.append({
            **block,
            "is_active": is_active,
            "active_index": active_index,
            "chunks": enriched_chunks
        })
        
    return jsonify({"blocks": enriched_blocks})

@app.route('/api/blocks', methods=['POST'])
def add_block():
    data = request.json
    user_prompt = data.get('user_prompt', '')
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    new_block = {
        "block_id": generate_id("block", user_prompt),
        "timestamp": int(time.time()),
        "user_prompt": user_prompt,
        "chunks": []
    }
    context_data.setdefault('blocks', []).append(new_block)
    save_json(CONTEXT_FILE, context_data)
    
    return jsonify({"message": "Block added", "block": new_block}), 201

@app.route('/api/blocks/<block_id>', methods=['PUT'])
def edit_block(block_id):
    data = request.json
    user_prompt = data.get('user_prompt')
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    for block in context_data.get('blocks', []):
        if block['block_id'] == block_id:
            block['user_prompt'] = user_prompt
            save_json(CONTEXT_FILE, context_data)
            return jsonify({"message": "Block updated", "block": block})
            
    return jsonify({"error": "Block not found"}), 404

@app.route('/api/blocks/<block_id>/chunks', methods=['POST'])
def add_chunk(block_id):
    data = request.json
    content = data.get('content', '')
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    for block in context_data.get('blocks', []):
        if block['block_id'] == block_id:
            new_chunk = {
                "chunk_id": generate_id("chunk", content),
                "content": content
            }
            block.setdefault('chunks', []).append(new_chunk)
            save_json(CONTEXT_FILE, context_data)
            return jsonify({"message": "Chunk added", "chunk": new_chunk}), 201
            
    return jsonify({"error": "Block not found"}), 404

@app.route('/api/blocks/<block_id>/chunks/<chunk_id>', methods=['PUT'])
def edit_chunk(block_id, chunk_id):
    data = request.json
    content = data.get('content')
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    for block in context_data.get('blocks', []):
        if block['block_id'] == block_id:
            for chunk in block.get('chunks', []):
                if chunk['chunk_id'] == chunk_id:
                    chunk['content'] = content
                    save_json(CONTEXT_FILE, context_data)
                    return jsonify({"message": "Chunk updated", "chunk": chunk})
                    
    return jsonify({"error": "Chunk not found"}), 404

@app.route('/api/toggle-block', methods=['POST'])
def toggle_block():
    data = request.json
    block_id = data.get('block_id')
    activate = data.get('activate', False) # True to activate, False to deactivate
    
    active_data = load_json(ACTIVE_CONTEXT_FILE, [])
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    # Remove if exists
    active_data = [item for item in active_data if item['block_id'] != block_id]
    
    if activate:
        # Find the block to get all its chunks and activate them by default
        target_block = next((b for b in context_data.get('blocks', []) if b['block_id'] == block_id), None)
        active_chunks = [c['chunk_id'] for c in target_block.get('chunks', [])] if target_block else []
        
        active_data.insert(0, {
            "block_id": block_id,
            "active_chunks": active_chunks
        })
        
    save_json(ACTIVE_CONTEXT_FILE, active_data)
    return jsonify({"message": f"Block {'activated' if activate else 'deactivated'}"})

@app.route('/api/toggle-chunk', methods=['POST'])
def toggle_chunk():
    data = request.json
    block_id = data.get('block_id')
    chunk_id = data.get('chunk_id')
    activate = data.get('activate', False)
    
    active_data = load_json(ACTIVE_CONTEXT_FILE, [])
    
    # Find the block in active_context
    target_item = next((item for item in active_data if item['block_id'] == block_id), None)
    
    if target_item:
        chunks = set(target_item.get('active_chunks', []))
        if activate:
            chunks.add(chunk_id)
        else:
            chunks.discard(chunk_id)
            
        if not chunks:
            # Remove the block entirely if no chunks remain
            active_data.remove(target_item)
        else:
            target_item['active_chunks'] = list(chunks)
    elif activate:
        # If block wasn't active, activate it with just this chunk
        active_data.append({
            "block_id": block_id,
            "active_chunks": [chunk_id]
        })
        
    save_json(ACTIVE_CONTEXT_FILE, active_data)
    return jsonify({"message": f"Chunk {'activated' if activate else 'deactivated'}"})

@app.route('/api/blocks/<block_id>', methods=['DELETE'])
def delete_block(block_id):
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    active_data = load_json(ACTIVE_CONTEXT_FILE, [])
    trash_data = load_json(TRASH_FILE, {"blocks": [], "chunks": []})
    
    block_to_delete = None
    new_blocks = []
    for block in context_data.get('blocks', []):
        if block['block_id'] == block_id:
            block_to_delete = block
        else:
            new_blocks.append(block)
            
    if block_to_delete:
        context_data['blocks'] = new_blocks
        save_json(CONTEXT_FILE, context_data)
        
        # Remove from active
        active_data = [item for item in active_data if item['block_id'] != block_id]
        save_json(ACTIVE_CONTEXT_FILE, active_data)
        
        # Add to trash
        trash_data.setdefault('blocks', []).append({
            **block_to_delete,
            "deleted_at": int(time.time())
        })
        save_json(TRASH_FILE, trash_data)
        
        return jsonify({"message": "Block deleted and moved to trash"})
    return jsonify({"error": "Block not found"}), 404

@app.route('/api/blocks/<block_id>/chunks/<chunk_id>', methods=['DELETE'])
def delete_chunk(block_id, chunk_id):
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    active_data = load_json(ACTIVE_CONTEXT_FILE, [])
    trash_data = load_json(TRASH_FILE, {"blocks": [], "chunks": []})
    
    chunk_to_delete = None
    for block in context_data.get('blocks', []):
        if block['block_id'] == block_id:
            new_chunks = []
            for chunk in block.get('chunks', []):
                if chunk['chunk_id'] == chunk_id:
                    chunk_to_delete = chunk
                else:
                    new_chunks.append(chunk)
            block['chunks'] = new_chunks
            
    if chunk_to_delete:
        save_json(CONTEXT_FILE, context_data)
        
        # Remove from active
        for item in active_data:
            if item['block_id'] == block_id:
                if chunk_id in item.get('active_chunks', []):
                    item['active_chunks'].remove(chunk_id)
        save_json(ACTIVE_CONTEXT_FILE, active_data)
        
        # Add to trash
        trash_data.setdefault('chunks', []).append({
            **chunk_to_delete,
            "parent_block_id": block_id,
            "deleted_at": int(time.time())
        })
        save_json(TRASH_FILE, trash_data)
        
        return jsonify({"message": "Chunk deleted and moved to trash"})
    return jsonify({"error": "Chunk not found"}), 404

@app.route('/api/blocks/<source_block_id>/chunks/<chunk_id>/move', methods=['POST'])
def move_chunk(source_block_id, chunk_id):
    data = request.json
    target_block_id = data.get('target_block_id')
    activate = data.get('activate', False)
    
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    active_data = load_json(ACTIVE_CONTEXT_FILE, [])
    
    chunk_to_move = None
    
    # 1. Remove from source block
    for block in context_data.get('blocks', []):
        if block['block_id'] == source_block_id:
            new_chunks = []
            for chunk in block.get('chunks', []):
                if chunk['chunk_id'] == chunk_id:
                    chunk_to_move = chunk
                else:
                    new_chunks.append(chunk)
            block['chunks'] = new_chunks
            break
            
    if not chunk_to_move:
        return jsonify({"error": "Chunk not found"}), 404
        
    # 2. Add to target block
    target_found = False
    for block in context_data.get('blocks', []):
        if block['block_id'] == target_block_id:
            block.setdefault('chunks', []).append(chunk_to_move)
            target_found = True
            break
            
    if not target_found:
        return jsonify({"error": "Target block not found"}), 404
        
    save_json(CONTEXT_FILE, context_data)
    
    # 3. Handle active states
    for item in active_data:
        if item['block_id'] == source_block_id:
            if chunk_id in item.get('active_chunks', []):
                item['active_chunks'].remove(chunk_id)
            if not item.get('active_chunks'):
                active_data.remove(item)
            break
            
    if activate:
        target_item = next((item for item in active_data if item['block_id'] == target_block_id), None)
        if target_item:
            if chunk_id not in target_item.setdefault('active_chunks', []):
                target_item['active_chunks'].append(chunk_id)
        else:
            active_data.insert(0, {
                "block_id": target_block_id,
                "active_chunks": [chunk_id]
            })
            
    save_json(ACTIVE_CONTEXT_FILE, active_data)
    return jsonify({"message": "Chunk moved successfully"})

@app.route('/api/trash', methods=['GET'])
def get_trash():
    trash_data = load_json(TRASH_FILE, {"blocks": [], "chunks": []})
    return jsonify(trash_data)

@app.route('/api/trash/restore-block/<block_id>', methods=['POST'])
def restore_block(block_id):
    trash_data = load_json(TRASH_FILE, {"blocks": [], "chunks": []})
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    block_to_restore = None
    new_trash_blocks = []
    for block in trash_data.get('blocks', []):
        if block['block_id'] == block_id:
            block_to_restore = block
        else:
            new_trash_blocks.append(block)
            
    if block_to_restore:
        block_to_restore.pop('deleted_at', None)
        trash_data['blocks'] = new_trash_blocks
        save_json(TRASH_FILE, trash_data)
        
        context_data.setdefault('blocks', []).append(block_to_restore)
        save_json(CONTEXT_FILE, context_data)
        
        return jsonify({"message": "Block restored successfully"})
    return jsonify({"error": "Block not found in trash"}), 404

@app.route('/api/trash/restore-chunk/<chunk_id>', methods=['POST'])
def restore_chunk(chunk_id):
    trash_data = load_json(TRASH_FILE, {"blocks": [], "chunks": []})
    context_data = load_json(CONTEXT_FILE, {"blocks": []})
    
    chunk_to_restore = None
    new_trash_chunks = []
    for chunk in trash_data.get('chunks', []):
        if chunk['chunk_id'] == chunk_id:
            chunk_to_restore = chunk
        else:
            new_trash_chunks.append(chunk)
            
    if chunk_to_restore:
        parent_block_id = chunk_to_restore.pop('parent_block_id', None)
        chunk_to_restore.pop('deleted_at', None)
        trash_data['chunks'] = new_trash_chunks
        save_json(TRASH_FILE, trash_data)
        
        # Find parent block
        parent_block = next((b for b in context_data.get('blocks', []) if b['block_id'] == parent_block_id), None)
        
        if parent_block:
            parent_block.setdefault('chunks', []).append(chunk_to_restore)
        else:
            # Recreate skeleton block if parent is missing
            new_block = {
                "block_id": parent_block_id,
                "timestamp": int(time.time()),
                "user_prompt": "Restored Block (Parent was deleted)",
                "chunks": [chunk_to_restore]
            }
            context_data.setdefault('blocks', []).append(new_block)
            
        save_json(CONTEXT_FILE, context_data)
        return jsonify({"message": "Chunk restored successfully"})
        
    return jsonify({"error": "Chunk not found in trash"}), 404

if __name__ == '__main__':
    app.run(port=PORT, debug=True)
