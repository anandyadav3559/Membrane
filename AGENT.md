# Membrane - Agent Architecture Guide

Welcome, AI Agent. This document contains the source of truth for the architecture of the Membrane project. You **must** read this before making any modifications to the codebase. Update this document whenever significant structural changes occur.

## 1. High-Level Architecture

The project is divided into strictly decoupled layers:

### A. The Core Runtime Engine (`/core`)
- **Port:** `5005` (FastAPI) via `main.py`
- **Purpose:** Acts as the pure logic and state-management engine. It does **not** handle UI.
- **Key Modules:**
  - `memory.py`: Handles saving specific text "chunks" into overarching "blocks". Controls active context routing.
  - `context.py`: Compiles the `active_context.json` into a plain string formatted for LLM injection.
  - `utils.py`: Manages cryptographic hashing (SHA-256 based on timestamp and content) to ensure globally unique identifiers for chunks and blocks.
- **Data Layer (`/core/data/`):**
  - Uses simple JSON files as databases (`context.json`, `active_context.json`, `trash.json`).

### B. The External Integrations (`/integrations`)
- **Web Router (`integrations/web/router.py`):** Exposes the API endpoints for the Next.js frontend to consume. 
  - Exposes `/chat`, `/api/core/context/active`, `/api/core/context/save_selection`, and `/api/core/context/clear_active`.
- **LLM Client (`integrations/llm_client.py`):** Connects to the external LLM providers.
  - Relies **strictly** on the root `.env` file for configuration (`LLM_ENDPOINT`, `GROQ_API_KEY`).
  - Never place LLM logic directly inside the `/core` directory.

### C. The Chatbot UI (`/membrane-chat-web`)
- **Port:** `3000` (Next.js 14+ App Router)
- **Purpose:** The main interface for the user to interact with the bot and save memory context.
- **Architecture Rules:**
  - Uses a **Split-Screen Layout**: Chat on the right, persistent Memory Context sidebar on the left.
  - **Ephemeral UI Context**: The left sidebar only acts as a temporary "tray" for snippets collected during the current turn. When the user sends a new message (`handleSend`), the frontend sidebar array is wiped so it doesn't get cluttered.
  - **Persistent Backend Context**: The `active_context.json` on the backend is **NEVER** automatically wiped by the Chatbot UI. It continuously collects all snippets. Blocks are only removed from the active context if the user explicitly deletes them via the Context Management Client (Port 5007) or by manually clicking the trash icon on a recently collected snippet.

### D. The Context Management Client (`/membrane-client`)
- **Port:** `5007` (Flask)
- **Purpose:** A graphical GUI to manage long-term memory. It allows users to view active chunks and drag-and-drop them into permanent knowledge blocks.

## 2. Important Conventions

- **ID Generation:** Never use sequential IDs (e.g., `1`, `2`). Always use `core.utils.generate_id(prefix, content)` to create collision-proof SHA-256 hashes.
- **CORS:** The core engine (`main.py`) must have CORS wildcarded (`*`) to allow the Next.js frontend to communicate with it.
- **Dependencies:** Managed strictly via `uv`. The root `pyproject.toml` is the source of truth for python packages. `npm` is used inside `membrane-chat-web`.
- **Configuration:** No hardcoded LLM keys. The project uses `dotenv`.

## 3. How to Run the Ecosystem

Refer to `commands.txt` for the current run commands. Currently, the stack requires 4 terminal windows:
1. LLM Proxy (Port `8001`)
2. Core Runtime Engine (Port `5005`)
3. Next.js Chatbot UI (Port `3000`)
4. Membrane Client GUI (Port `5007`)
