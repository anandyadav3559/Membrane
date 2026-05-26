#!/bin/bash

echo "========================================="
echo " Stopping Cognitive Chatbot Ecosystem"
echo "========================================="

kill_port() {
  PORT=$1
  PID=$(lsof -ti tcp:$PORT)
  if [ ! -z "$PID" ]; then
    echo "Killing service on port $PORT (PID: $PID)..."
    kill -9 $PID
  else
    echo "No service running on port $PORT."
  fi
}

# Next.js UI
kill_port 3000

# Core Engine API
kill_port 5005

# Cognibot Client (Context Manager)
kill_port 5007

# LLM Proxy
kill_port 8001

echo ""
echo "All ecosystem services have been safely shut down!"
