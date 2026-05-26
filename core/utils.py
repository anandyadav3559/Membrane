import json
import os
import time

CONTEXT_FILE = os.path.join(os.path.dirname(__file__), 'data', 'context.json')
ACTIVE_CONTEXT_FILE = os.path.join(os.path.dirname(__file__), 'data', 'active_context.json')

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

import hashlib

def generate_id(prefix, content=""):
    hash_input = f"{content}_{time.time()}".encode('utf-8')
    hash_str = hashlib.sha256(hash_input).hexdigest()[:12]
    return f"{prefix}_{hash_str}"
