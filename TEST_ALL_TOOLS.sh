#!/bin/bash

echo "=========================================="
echo "🧪 GodmanAI Tool Testing Suite"
echo "=========================================="
echo ""

echo "📦 Installed Tools:"
ls -1 godman_ai/tools/*.py | grep -v __pycache__ | sed 's/godman_ai\/tools\//  • /' | sed 's/.py//'
echo ""

echo "🤖 Local Model Status:"
ollama list | grep qwen
echo ""

echo "✅ Python Dependencies:"
python3 -c "import requests; print('  ✓ requests')" 2>/dev/null || echo "  ✗ requests (missing)"
python3 -c "from duckduckgo_search import DDGS; print('  ✓ duckduckgo_search')" 2>/dev/null || echo "  ✗ duckduckgo_search (missing)"
echo ""

echo "📁 Project Structure:"
echo "  • $(find godman_ai/tools -name '*.py' | wc -l | tr -d ' ') tool files"
echo "  • $(find libs -name '*.py' 2>/dev/null | wc -l | tr -d ' ') library files"
echo "  • $(find cli -name '*.py' 2>/dev/null | wc -l | tr -d ' ') CLI files"
echo ""

echo "🚀 Ready to launch!"
echo ""
echo "Run your AI:"
echo "  python3 run_local_godman.py"
echo ""

