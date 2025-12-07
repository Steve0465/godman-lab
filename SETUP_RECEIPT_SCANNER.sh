#!/bin/bash
# Complete setup for receipt automation

echo "🧾 Receipt Scanner Automation Setup"
echo "===================================="
echo ""

cd ~/Desktop/godman-lab

# Install Python dependencies
echo "📦 Installing Python packages..."
pip3 install -q watchdog pytesseract pillow gspread oauth2client

# Check for Tesseract OCR
echo ""
echo "🔍 Checking OCR software..."
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract OCR not found"
    echo ""
    echo "To install (required for OCR):"
    echo "  brew install tesseract"
    echo ""
    read -p "Install now with Homebrew? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v brew &> /dev/null; then
            brew install tesseract
        else
            echo "❌ Homebrew not found. Install from: https://brew.sh"
        fi
    fi
else
    echo "✅ Tesseract OCR found: $(tesseract --version | head -1)"
fi

# Check OpenAI API key
echo ""
echo "🔑 Checking API keys..."
if grep -q "OPENAI_API_KEY" .env 2>/dev/null && ! grep -q "your_openai_api_key_here" .env; then
    echo "✅ OpenAI API key configured"
else
    echo "⚠️  OpenAI API key not configured"
    echo "   Edit .env file to add: OPENAI_API_KEY=sk-..."
    echo "   (Optional - system works without it, but data extraction is manual)"
fi

# Create folders
echo ""
echo "📁 Creating folders..."
mkdir -p scans
mkdir -p receipts/processed
echo "✅ Folders ready"

# Test import
echo ""
echo "🧪 Testing installation..."
python3 -c "
import sys
sys.path.insert(0, '.')
from workflows.receipt_watcher import ReceiptProcessor
print('✅ Receipt watcher ready')
" 2>&1

echo ""
echo "===================================="
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Configure scanner to save to:"
echo "      /Users/stephengodman/Desktop/godman-lab/scans"
echo "      (See SCANNER_PRINTER_SETUP.md for help)"
echo ""
echo "   2. Start the watcher:"
echo "      ./START_RECEIPT_WATCHER.sh"
echo ""
echo "   3. Scan away! Files auto-process"
echo ""
echo "📚 Guides:"
echo "   - RECEIPT_SCANNER_GUIDE.md - Full documentation"
echo "   - SCANNER_PRINTER_SETUP.md - Scanner configuration"
echo "===================================="
