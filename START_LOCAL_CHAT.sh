#!/bin/bash
echo "🚀 Starting GodmanAI Local Chat (Dolphin-Mistral)..."
echo "📍 Model: dolphin-mistral (uncensored)"
echo "💬 Type your messages and press Enter"
echo "🛑 Press Ctrl+C to exit"
echo ""

cd /Users/stephengodman/godman-lab
source .venv/bin/activate
python3 run_local_chat.py
