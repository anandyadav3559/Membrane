# Setup Instructions

This guide provides detailed steps on how to set up and run the Membrane Ecosystem.

## Environment Variables (`.env`)

The application utilizes a `.env` file in the root directory to manage the LLM endpoint configuration. There are two primary modes you can use:

1. **Proxy Mode (Default & Recommended for Local Testing):**
   ```env
   LLM_ENDPOINT="proxy"
   ```
   In this mode, the system expects a local LLM proxy (such as `llm-keypool`) running on `http://127.0.0.1:8001`. The `start_services.sh` script automatically starts this proxy for you.

2. **Direct API Mode:**
   ```env
   LLM_ENDPOINT="api"
   GROQ_API_KEY="your_groq_api_key_here"
   ```
   In this mode, the system bypasses the proxy and sends requests directly to the Groq API. You must provide a valid `GROQ_API_KEY`.

## Running the Ecosystem

1. **Install Prerequisites**: Ensure you have `uv` and Node.js (`npm`) installed.
2. **Install Dependencies**:
   ```bash
   # Install Python dependencies
   uv add fastapi uvicorn pydantic jinja2 python-multipart requests tiktoken pytest python-dotenv

   # Install Next.js frontend dependencies
   cd membrane-chat-web && npm install
   ```
3. **Start All Services**:
   The ecosystem consists of multiple microservices. You can start all of them simultaneously using the provided bash script from the root directory:
   ```bash
   bash start_services.sh
   ```
   This will concurrently boot up:
   - **LLM Proxy** on port `8001`
   - **Core Runtime Engine** on port `5005`
   - **Context Manager Client** on port `5007`
   - **Next.js UI** on port `3000`

## Stopping the Ecosystem

To cleanly shut down all background processes across the ecosystem, run:
```bash
bash stop_services.sh
```
