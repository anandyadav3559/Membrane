# Core Runtime Engine

The `core` directory serves as the isolated memory, context, and storage engine for the Cognitive Chatbot ecosystem. Its primary design goal is **Decoupled Cognition**: separating the persistent memory operations, LLM context aggregation, and data storage logic away from the client applications (like the Chatbot UI and Context Management GUI). 

By isolating this logic, any frontend application can hook into the AI context without needing to understand how files are saved or how active context is injected into prompts.

---

## Directory Architecture & Data Flow

### 📂 `data/` (Persistent Storage Layer)
This subdirectory is the single source of truth for the RAG (Retrieval-Augmented Generation) memory state. It operates using flat JSON files to ensure extreme portability and lack of database overhead.
- **`context.json`**: The global database of all stored "Blocks" and their child "Chunks". Every piece of context ever saved by the user (and not explicitly deleted) lives here.
- **`active_context.json`**: The routing table. It holds a lightweight list of which specific `block_id`s and `chunk_id`s are currently "active". Only chunks referenced here will be injected into the LLM context string.
- **`trash.json`**: The soft-delete archive. When the user deletes a block or chunk via the Client GUI, it is moved here with a UNIX timestamp, allowing for safe recovery.

---

## Core Modules (In-Depth)

### 📄 `utils.py` (File I/O & Cryptography)
Handles low-level file interactions and identification.
- **Robust JSON Parsing**: Uses `load_json` and `save_json` to safely interact with the file system, handling `JSONDecodeError`s and returning default dictionaries if files do not exist.
- **`generate_id(prefix, content)`**: Replaces the old incremental ID system with a robust cryptographic approach. It encodes the `content` string alongside a UNIX `time.time()`, hashes it using **SHA-256 (`hashlib`)**, and extracts a 12-character hex digest. This guarantees globally unique, collision-resistant IDs (e.g., `block_a1b2c3d4e5f6`).

### 📄 `context.py` (Context Aggregation)
The bridge between storage and the LLM. 
- **`get_active_context_string()`**: Reads the `active_context.json` routing table, cross-references those IDs against the actual text data in `context.json`, and constructs the final, formatted string (`--- ACTIVE CONTEXT ---\n- [chunk 1]\n- [chunk 2]\n----------------------`). This string is passed via the API to be injected into the system prompt of the LLM.

### 📄 `memory.py` (Snippet Ingestion)
Responsible for capturing highlighted texts from the Chatbot UI and transforming them into persistent memory.
- **`save_selection_to_context(selected_text, user_prompt)`**: The ingestion pipeline. When a user highlights raw text in the frontend, this function generates a new SHA-256 `chunk_id` for the text, creates a new wrapper `block_id`, saves it to the permanent `context.json`, and **immediately** appends it to `active_context.json`. It returns the exact IDs to the frontend so the UI can build an "Undo" capability.

### 📄 `activation.py` (Granular State Control)
*(Currently used as an internal library or fallback)*
Provides deep-level state toggling.
- **`update_active_context(block_id, chunk_id, action)`**: A low-level engine utility designed to add or remove specific items from the `active_context.json` routing table safely without duplicating arrays.

### 📄 `chunking.py` (Legacy Support)
- Contains `split_text_into_chunks(text)` which was historically used to break LLM responses into 500+ word-level chunks for the old frontend grid system. 

---

## Inter-System Communication

The `core` engine does not expose endpoints directly from within this directory. Instead, the `main.py` file at the root of the project imports these core functions via `integrations/web/router.py` to expose them as RESTful endpoints (running on Port `5005` by default).

This strict separation ensures the `core` remains a pure logic layer, fully agnostic to whether it is being triggered by a FastAPI request, a CLI script, or an automated testing suite.
