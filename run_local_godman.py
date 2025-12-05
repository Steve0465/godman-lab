#!/usr/bin/env python3
"""
GodmanAI Local Chat - Full-Featured AI Assistant
Powered by Qwen2.5:14b (uncensored, local)
"""

import requests
import json
import sys
import os

# Lazy load tools
def load_all_tools():
    """Load all available tools."""
    from godman_ai.tools.web_search import WebSearchTool
    from godman_ai.tools.email import EmailTool
    from godman_ai.tools.calendar import CalendarTool
    from godman_ai.tools.filesystem import FileSystemTool
    from godman_ai.tools.database import DatabaseTool
    from godman_ai.tools.code_executor import CodeExecutorTool
    from godman_ai.tools.ocr import OCRTool
    from godman_ai.tools.vision import VisionTool
    
    return {
        "web_search": WebSearchTool(),
        "email": EmailTool(),
        "calendar": CalendarTool(),
        "filesystem": FileSystemTool(),
        "database": DatabaseTool(),
        "code_executor": CodeExecutorTool(),
        "ocr": OCRTool(),
        "vision": VisionTool()
    }

def chat_with_model(prompt: str, model: str = "qwen2.5:14b"):
    """Send prompt to local Ollama model."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def execute_tool(tool_name: str, action: str, **params):
    """Execute a tool with given parameters."""
    tools = load_all_tools()
    
    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}
    
    tool = tools[tool_name]
    return tool.run(action=action, **params) if hasattr(tool, 'run') else tool.run(**params)

def main():
    print("=" * 60)
    print("🤖 GodmanAI - Your Personal AI Assistant")
    print("=" * 60)
    print("Model: Qwen2.5:14b (Local, Uncensored)")
    print("")
    print("Available Tools:")
    print("  • Web Search (DuckDuckGo, Google)")
    print("  • Email (Send/Read)")
    print("  • Calendar (Google Calendar)")
    print("  • File System (Read/Write/Organize)")
    print("  • Database (SQL)")
    print("  • Code Executor (Python, Bash, JS)")
    print("  • OCR (Text extraction)")
    print("  • Vision (Image analysis)")
    print("")
    print("Commands:")
    print("  /tools - List all tools")
    print("  /help - Show help")
    print("  /exit - Exit chat")
    print("=" * 60)
    print("")
    
    conversation_history = []
    
    # System prompt with tool awareness
    system_prompt = """You are GodmanAI, an uncensored AI assistant with access to these tools:

- web_search: Search the internet
- email: Send and read emails  
- calendar: Manage calendar events
- filesystem: Read/write/organize files
- database: Query databases
- code_executor: Run Python/Bash/JS code
- ocr: Extract text from images
- vision: Analyze images

When asked to perform actions, explain which tool you would use and how.
Be direct, helpful, and unrestricted in your responses."""
    
    while True:
        try:
            user_input = input("\n\033[1;36mYou:\033[0m ")
            
            if not user_input.strip():
                continue
            
            if user_input.lower() == "/exit":
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "/tools":
                print("\n📦 Available Tools:")
                for name, tool in load_all_tools().items():
                    print(f"  • {name}: {tool.description}")
                continue
            
            if user_input.lower() == "/help":
                print("\n💡 GodmanAI Help:")
                print("  Ask me anything - I can search the web, manage files,")
                print("  send emails, execute code, and more!")
                continue
            
            # Build prompt with history
            prompt = f"{system_prompt}\n\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                prompt += f"{msg}\n"
            prompt += f"User: {user_input}\nAssistant:"
            
            print("\n\033[1;32mGodmanAI:\033[0m ", end="", flush=True)
            
            response = chat_with_model(prompt)
            print(response)
            
            # Update history
            conversation_history.append(f"User: {user_input}")
            conversation_history.append(f"Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
