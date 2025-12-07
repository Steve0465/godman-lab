#!/bin/bash
# Quick launcher for receipt watcher

cd "$(dirname "$0")"

echo "🚀 Starting Receipt Watcher..."
echo ""

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies if needed
pip3 install -q watchdog pytesseract pillow 2>/dev/null

# Run watcher
python3 workflows/receipt_watcher.py
