import unittest
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory_manager import (
    save_selection_to_context, 
    update_active_context, 
    get_active_context_string,
    CONTEXT_FILE,
    ACTIVE_CONTEXT_FILE,
    split_text_into_chunks
)

def count_tokens(text):
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback approximation: 1 token ~= 4 chars
        return int(len(text) / 4)

class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        # Cleanup files before each test
        for f in [CONTEXT_FILE, ACTIVE_CONTEXT_FILE]:
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        for f in [CONTEXT_FILE, ACTIVE_CONTEXT_FILE]:
            if os.path.exists(f):
                os.remove(f)

    def test_split_chunks(self):
        text = "Hello world."
        chunks = split_text_into_chunks(text)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["content"], "Hello")
        self.assertEqual(chunks[1]["content"], "world.")

    def test_save_selection(self):
        text = "word0 word1 word2 word3"
        # We select indices 0 and 2. Because they are not contiguous, they form two blocks.
        block_id = save_selection_to_context([0, 2], text)
        self.assertIsNotNone(block_id)
        
        # Check active context
        context_str = get_active_context_string()
        self.assertIn("word0", context_str)
        self.assertIn("word2", context_str)
        self.assertNotIn("word1", context_str)

    def test_update_active_context_remove_chunk(self):
        text = "word0 word1 word2 word3"
        # contiguous selection -> merged into 1 chunk
        block_id = save_selection_to_context([0, 1], text)
        
        # Read the generated chunk_id for the merged chunk
        with open(CONTEXT_FILE, 'r') as f:
            data = json.load(f)
            block = data["blocks"][0]
            chunk_0_id = block["chunks"][0]["chunk_id"]
            
        update_active_context(block_id, chunk_0_id, action="remove")
        
        context_str = get_active_context_string()
        self.assertNotIn("word0 word1", context_str)

    def test_update_active_context_remove_block(self):
        text = "wordA wordB"
        block_id = save_selection_to_context([0, 1], text)
        
        # Remove entire block
        update_active_context(block_id, action="remove")
        
        context_str = get_active_context_string()
        self.assertEqual(context_str, "")

    def test_llm_token_usage(self):
        # Simulate standard LLM test
        base_prompt = "Summarize the history of AI."
        text = "AI started in 1956."
        save_selection_to_context([0, 1, 2, 3], text) # Select all

        
        context_str = get_active_context_string()
        final_prompt = f"{context_str}\n\nUser: {base_prompt}"
        
        tokens = count_tokens(final_prompt)
        print(f"\n[Token Test] Estimated Prompt Tokens: {tokens}")
        self.assertGreater(tokens, 10) 

if __name__ == '__main__':
    unittest.main()
