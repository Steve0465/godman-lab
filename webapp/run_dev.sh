#!/bin/bash

# Development runner script for OCR Thread Analyzer
# Starts both FastAPI and Streamlit in the background

set -e

echo "🚀 Starting OCR Thread Analyzer Development Environment"
echo "========================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements-enhanced.txt
fi

# Create necessary directories
mkdir -p webapp/uploads
mkdir -p webapp/results
mkdir -p webapp/templates

# Kill any existing processes on these ports
echo "🔄 Checking for existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

# Start FastAPI server
echo -e "${BLUE}Starting FastAPI server on http://localhost:8000${NC}"
cd webapp
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!
cd ..

# Wait a moment for FastAPI to start
sleep 2

# Start Streamlit dashboard
echo -e "${BLUE}Starting Streamlit dashboard on http://localhost:8501${NC}"
streamlit run webapp/dashboard/streamlit_app.py --server.port 8501 > /tmp/streamlit.log 2>&1 &
STREAMLIT_PID=$!

# Wait a moment for services to start
sleep 3

echo ""
echo -e "${GREEN}✅ Services started successfully!${NC}"
echo ""
echo "📝 Access the services at:"
echo "   - FastAPI Web UI: http://localhost:8000"
echo "   - Streamlit Dashboard: http://localhost:8501"
echo ""
echo "📋 Process IDs:"
echo "   - FastAPI: $FASTAPI_PID"
echo "   - Streamlit: $STREAMLIT_PID"
echo ""
echo "📄 Logs:"
echo "   - FastAPI: tail -f /tmp/fastapi.log"
echo "   - Streamlit: tail -f /tmp/streamlit.log"
echo ""
echo "🛑 To stop services:"
echo "   kill $FASTAPI_PID $STREAMLIT_PID"
echo ""
echo "Press Ctrl+C to stop all services..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $FASTAPI_PID 2>/dev/null || true
    kill $STREAMLIT_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Wait for user interrupt
wait
