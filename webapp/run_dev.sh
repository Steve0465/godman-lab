#!/bin/bash
# Development startup script for Enhanced OCR/Thread Analyzer
# Runs FastAPI backend and Streamlit dashboard

set -e

echo "=========================================="
echo "Enhanced OCR/Thread Analyzer Dev Server"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "webapp/main.py" ]; then
    echo "Error: Please run this script from the repository root"
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

echo "✓ Python version: $(python --version)"

# Check if required packages are installed
echo ""
echo "Checking dependencies..."

MISSING_DEPS=()

python -c "import fastapi" 2>/dev/null || MISSING_DEPS+=("fastapi")
python -c "import uvicorn" 2>/dev/null || MISSING_DEPS+=("uvicorn")
python -c "import streamlit" 2>/dev/null || MISSING_DEPS+=("streamlit")
python -c "import cv2" 2>/dev/null || MISSING_DEPS+=("opencv-python")
python -c "import PIL" 2>/dev/null || MISSING_DEPS+=("pillow")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "⚠ Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "Install with:"
    echo "  pip install -r requirements-enhanced.txt"
    exit 1
fi

echo "✓ Core dependencies installed"

# Check optional dependencies
echo ""
echo "Checking optional dependencies..."

python -c "import pytesseract" 2>/dev/null && echo "✓ Tesseract available" || echo "⚠ Tesseract not available (install: pip install pytesseract)"
python -c "from google.cloud import vision" 2>/dev/null && echo "✓ Google Vision available" || echo "⚠ Google Vision not available (install: pip install google-cloud-vision)"
python -c "import boto3" 2>/dev/null && echo "✓ AWS Textract available" || echo "⚠ AWS Textract not available (install: pip install boto3)"
python -c "from sentence_transformers import SentenceTransformer" 2>/dev/null && echo "✓ Sentence Transformers available" || echo "⚠ Sentence Transformers not available (install: pip install sentence-transformers)"

echo ""
echo "=========================================="
echo "Starting servers..."
echo "=========================================="
echo ""

# Create log directory
mkdir -p logs

# Start FastAPI in background
echo "Starting FastAPI backend on http://localhost:8000"
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "  PID: $FASTAPI_PID"

# Wait a moment for FastAPI to start
sleep 2

# Start Streamlit in background
echo "Starting Streamlit dashboard on http://localhost:8501"
python -m streamlit run webapp/dashboard/streamlit_app.py --server.port 8501 > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "  PID: $STREAMLIT_PID"

echo ""
echo "=========================================="
echo "✓ Servers started successfully!"
echo "=========================================="
echo ""
echo "Access points:"
echo "  📱 Web UI:        http://localhost:8000"
echo "  📊 Dashboard:     http://localhost:8501"
echo "  📚 API Docs:      http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  FastAPI:    logs/fastapi.log"
echo "  Streamlit:  logs/streamlit.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=========================================="

# Handle Ctrl+C
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $FASTAPI_PID 2>/dev/null || true
    kill $STREAMLIT_PID 2>/dev/null || true
    echo "✓ Stopped"
    exit 0
}

trap cleanup INT TERM

# Wait for both processes
wait $FASTAPI_PID $STREAMLIT_PID
