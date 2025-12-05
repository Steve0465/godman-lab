#!/usr/bin/env python3
"""Demo script for Godman AI Agent Engine."""
import sys
from pathlib import Path

# Add godman-ai to path
sys.path.insert(0, str(Path(__file__).parent))

from engine import AgentEngine
from memory.store import MemoryStore


def main():
    print("=" * 70)
    print("🤖 Godman AI - Agent Engine Demo")
    print("=" * 70)
    print()
    
    # Initialize engine
    print("Initializing Agent Engine...")
    engine = AgentEngine()
    print()
    
    # Show status
    status = engine.status()
    print("📊 Engine Status:")
    print(f"  • Tools loaded: {status['tools_loaded']}")
    print(f"  • Workflows loaded: {status['workflows_loaded']}")
    print(f"  • Config loaded: {status['config_loaded']}")
    print(f"  • OpenAI ready: {status['openai_ready']}")
    print()
    
    # List available tools
    print("🛠️  Available Tools:")
    tools = engine.list_tools()
    for tool in tools:
        print(f"  • {tool['name']}: {tool['description']}")
    print()
    
    # List available workflows
    print("⚙️  Available Workflows:")
    workflows = engine.list_workflows()
    for workflow in workflows:
        print(f"  • {workflow['name']}: {workflow['description']}")
    print()
    
    # Demo: Call a tool
    print("=" * 70)
    print("Demo 1: Calling OCR Tool")
    print("=" * 70)
    try:
        result = engine.call_tool("ocr", file_path="test.pdf")
        print("✓ Tool executed successfully")
        print(f"  Result: {result}")
    except Exception as e:
        print(f"✗ Tool execution failed: {e}")
    print()
    
    # Demo: Run a workflow
    print("=" * 70)
    print("Demo 2: Running Receipt Workflow")
    print("=" * 70)
    try:
        result = engine.run_workflow(
            "receipts_workflow",
            input_dir="scans",
            use_vision=False
        )
        print("✓ Workflow executed successfully")
        print(f"  Status: {result.get('status')}")
        print(f"  Files processed: {result.get('processed', 0)}")
    except Exception as e:
        print(f"✗ Workflow execution failed: {e}")
    print()
    
    # Demo: Memory store
    print("=" * 70)
    print("Demo 3: Memory Store")
    print("=" * 70)
    memory = MemoryStore()
    
    # Set some context
    memory.set_context("demo_run", True)
    memory.set_preference("favorite_tool", "ocr")
    
    # Add conversation
    memory.add_conversation("user", "Hello, agent!")
    memory.add_conversation("assistant", "Hello! How can I help you today?")
    
    # Log automation
    memory.log_automation(
        workflow="receipts_workflow",
        status="success",
        details={"demo": True}
    )
    
    print("✓ Memory operations completed")
    print(f"  Context keys: {list(memory._context_cache.keys())}")
    print(f"  Conversation entries: {len(memory.get_conversation_history())}")
    print()
    
    # Demo: Query LLM (placeholder)
    print("=" * 70)
    print("Demo 4: LLM Query (Placeholder)")
    print("=" * 70)
    response = engine.query_llm("What is the best way to organize receipts?")
    print(f"  Response: {response}")
    print()
    
    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  • Configure OpenAI API key in config.toml")
    print("  • Add your Google Sheets ID")
    print("  • Set up Trello board ID")
    print("  • Run actual workflows with real data")
    print()
    print("Documentation: godman-ai/README.md")
    print()


if __name__ == "__main__":
    main()
