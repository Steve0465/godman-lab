#!/bin/bash

# Start Godman AI Server
# Launches the FastAPI server with the persistent kernel

echo "======================================================================"
echo "Starting Godman AI Server v0.3"
echo "======================================================================"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables
export GODMAN_ENV=production
export GODMAN_LOG_LEVEL=INFO

# Start the server
echo ""
echo "Starting FastAPI server on http://0.0.0.0:8000"
echo ""
echo "Available endpoints:"
echo "  - Chat: POST /chat"
echo "  - Streaming: POST /chat/stream"
echo "  - Memory Search: POST /memory/search"
echo "  - Tasks: POST /tasks/create"
echo "  - Health: GET /admin/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================================"

python -m uvicorn godman_ai.server.api:app --host 0.0.0.0 --port 8000 --reload
