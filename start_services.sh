#!/bin/bash

# Kill all background processes started by this script when exiting
trap 'echo "Stopping all services..."; kill 0' SIGINT SIGTERM EXIT

echo "========================================="
echo " Starting Cognitive Chatbot Ecosystem"
echo "========================================="

echo "1. Starting LLM Proxy on port 8001..."
uvx llm-keypool proxy --port 8001 &

echo "2. Starting Core Runtime Engine on port 5005..."
uv run uvicorn main:app --port 5005 --reload &

echo "3. Starting Cognibot Client (Context Manager) on port 5007..."
uv run python cognibot-client/app.py &

echo "4. Starting Next.js Chatbot UI on port 3000..."
cd cognibot-chat-web && npm run dev &

echo ""
echo "All services are booting up!"
echo "-----------------------------------------"
echo "Chatbot UI:       http://localhost:3000"
echo "Context Manager:  http://localhost:5007"
echo "Core Engine API:  http://localhost:5005"
echo "LLM Proxy:        http://localhost:8001"
echo "-----------------------------------------"
echo "Press Ctrl+C at any time to stop all services."

# Wait infinitely so the script stays alive and keeps background processes running
wait
