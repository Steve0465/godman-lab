#!/bin/bash
# Quick Install Script - Essential Power Tools

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      🚀 Installing Essential Mac Power Tools! 🚀          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Essential Mac Apps (FREE!)
echo "📱 Installing Mac Apps..."
brew install --cask raycast rectangle stats appcleaner

# Command Line Tools (FREE!)
echo ""
echo "⚡ Installing Command Line Tools..."
brew install fzf bat exa fd tree ripgrep imagemagick ffmpeg

# Setup fzf
echo ""
echo "🔧 Setting up fzf..."
$(brew --prefix)/opt/fzf/install --all

# Python AI Tools
echo ""
echo "🤖 Installing Python AI Tools..."
pip3 install openai-whisper pillow opencv-python

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ✅ INSTALLATION COMPLETE! ✅              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 What's New:"
echo "  • Raycast - Press Cmd+Space"
echo "  • Rectangle - Ctrl+Opt+Arrow to snap windows"
echo "  • Stats - Check menu bar"
echo "  • fzf - Ctrl+R for command history"
echo ""
