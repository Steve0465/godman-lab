#!/bin/bash

# Fun Playground Script
figlet "Tool Playground" | lolcat

echo ""
echo "🎮 Interactive Tool Playground"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Choose your adventure:"
echo ""
echo "1. 🎨 View Tools as Beautiful JSON (fx)"
echo "2. 📊 System Monitor (btop)"
echo "3. 🌈 Create Rainbow Text"
echo "4. 🔥 Test All Math Functions"
echo "5. 📝 Test All String Functions"
echo "6. 📈 Run Stats Analysis"
echo "7. 🎪 Hollywood Hacker Mode"
echo "8. 🌐 Open WebUI Dashboard"
echo "9. 🤖 Interactive Handler Chat"
echo "0. 🚪 Exit"
echo ""
read -p "Enter choice [0-9]: " choice

case $choice in
    1)
        echo "📦 Fetching tools..."
        curl -s http://localhost:8000/api/handler/tools | fx
        ;;
    2)
        echo "📊 Launching btop..."
        btop
        ;;
    3)
        read -p "Enter text for rainbow: " text
        figlet "$text" | lolcat
        ;;
    4)
        echo "🔢 Testing Math Functions..."
        echo ""
        echo "42 + 58 ="
        curl -s -X POST http://localhost:8000/api/handler \
          -H "Content-Type: application/json" \
          -d '{"function": "add", "parameters": {"x": 42, "y": 58}}' | jq '.result'
        echo ""
        echo "100 - 35 ="
        curl -s -X POST http://localhost:8000/api/handler \
          -H "Content-Type: application/json" \
          -d '{"function": "subtract", "parameters": {"x": 100, "y": 35}}' | jq '.result'
        echo ""
        echo "12 × 8 ="
        curl -s -X POST http://localhost:8000/api/handler \
          -H "Content-Type: application/json" \
          -d '{"function": "multiply", "parameters": {"x": 12, "y": 8}}' | jq '.result'
        ;;
    5)
        echo "📝 Testing String Functions..."
        echo ""
        echo "Uppercase 'hello world':"
        curl -s -X POST http://localhost:8000/api/handler \
          -H "Content-Type: application/json" \
          -d '{"function": "uppercase", "parameters": {"text": "hello world"}}' | jq '.result'
        echo ""
        echo "Lowercase 'HELLO WORLD':"
        curl -s -X POST http://localhost:8000/api/handler \
          -H "Content-Type: application/json" \
          -d '{"function": "lowercase", "parameters": {"text": "HELLO WORLD"}}' | jq '.result'
        echo ""
        echo "Reverse 'Godman AI':"
        curl -s -X POST http://localhost:8000/api/handler \
          -H "Content-Type: application/json" \
          -d '{"function": "reverse_text", "parameters": {"text": "Godman AI"}}' | jq '.result'
        ;;
    6)
        echo "�� Running Stats Analysis..."
        curl -s -X POST http://localhost:8000/api/handler \
          -H "Content-Type: application/json" \
          -d '{"function": "calculate_stats", "parameters": {"items": [10, 25, 30, 45, 50, 75, 90]}}' | jq '.'
        ;;
    7)
        echo "🎬 Launching Hollywood Mode..."
        echo "Press Ctrl+C to exit"
        sleep 2
        hollywood
        ;;
    8)
        echo "🌐 Opening WebUI Dashboard..."
        open http://localhost:8000
        ;;
    9)
        echo "🤖 Interactive Handler Chat"
        echo "Type your natural language requests (or 'exit' to quit)"
        echo "Example: 'add 5 and 3', 'reverse hello', 'create user Alice age 25'"
        echo ""
        while true; do
            read -p "You: " input
            if [ "$input" = "exit" ]; then
                break
            fi
            echo "$input" | ollama run froehnerel/gorilla-openfunctions:v2-q5_K_M
            echo ""
        done
        ;;
    0)
        figlet "Goodbye!" | lolcat
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac
