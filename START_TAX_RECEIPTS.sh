#!/bin/bash
# Tax-ready receipt watcher with OpenAI integration

cd "$(dirname "$0")"

echo "💼 Starting Tax-Ready Receipt Processor..."
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for OpenAI key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  No OpenAI API key found"
    echo "   To enable auto-extraction, add your key to .env:"
    echo "   echo 'OPENAI_API_KEY=sk-your-key' >> .env"
    echo ""
fi

# Install dependencies
pip3 install -q watchdog pytesseract pillow openai 2>/dev/null

# Run tax-ready watcher
python3 workflows/receipt_watcher_tax.py
