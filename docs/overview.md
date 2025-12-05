# GodmanAI Overview

## What is GodmanAI?

GodmanAI is a personal AI operating system designed to run entirely in your terminal. It combines intelligent agents, memory systems, task orchestration, and extensible tools to automate complex workflows without requiring cloud services or external platforms.

Think of it as your personal AI assistant that can:
- **See** (process images, PDFs, videos)
- **Remember** (store and recall task history)
- **Plan** (break down complex tasks)
- **Execute** (run tools and workflows)
- **Learn** (improve from feedback)
- **Schedule** (run recurring tasks)
- **Integrate** (connect to Google Sheets, Trello, Drive, etc.)

---

## Core Concepts

### Orchestrator
The orchestrator is the traffic controller of GodmanAI. It:
- Detects input types (image, PDF, text, CSV, audio, video)
- Routes to the appropriate tool
- Handles errors gracefully
- Returns structured results

### Agent System
The agent system enables autonomous task execution through three phases:

1. **Planner** - Breaks tasks into structured steps
2. **Executor** - Runs each step using tools
3. **Reviewer** - Validates outputs and triggers replanning if needed

This loop continues until the task is complete or max iterations are reached.

### Memory
GodmanAI has three types of memory:

- **Vector Store** - Semantic search across past tasks and documents
- **Episodic Memory** - Complete task histories with plans and results
- **Working Memory** - Short-term context shared between steps

### Tools
Tools are modular components that perform specific actions:
- `OCRTool` - Extract text from images
- `VisionTool` - Analyze image content
- `SheetsTool` - Read/write Google Sheets
- `TrelloTool` - Manage Trello cards
- `DriveTool` - Upload/download Drive files
- `ReportsTool` - Generate summaries and reports

Tools implement the `BaseTool` interface and can be dynamically loaded.

---

## Real-World Use Cases

### 1. Receipt Processing Pipeline

**Problem**: Manually entering receipt data is tedious and error-prone.

**Solution**:
```bash
# Scan receipts into scans/ folder
godman agent "Process all receipts in scans/ and add to expense tracker"
```

**What happens**:
1. Planner creates steps: scan folder → OCR each file → parse vendor/total/date → classify category → append to Google Sheet
2. Executor runs OCRTool → custom parser → SheetsTool
3. Reviewer validates data quality
4. Results saved to episodic memory

### 2. Pool Job Management

**Problem**: Tracking pool maintenance jobs across multiple properties with paper records.

**Solution**:
```bash
# Create a workflow that monitors email, extracts job details, updates Trello
godman schedule add "*/30 * * * *" "godman agent 'Check pool job emails and update board'"
godman daemon start
```

**What happens**:
- Every 30 minutes, daemon triggers the scheduled task
- Agent reads new emails
- Extracts job details (address, chemicals needed, completion status)
- Creates or updates Trello cards
- Sends notifications for urgent issues

### 3. F-250 Truck Diagnostics

**Problem**: Recording and analyzing truck maintenance patterns.

**Solution**:
```bash
# Take a photo of dashboard warning light
godman run photos/check_engine.jpg
```

**What happens**:
1. VisionTool identifies the warning symbol
2. Agent searches episodic memory for similar past issues
3. Generates diagnostic report with likely causes
4. Creates maintenance reminder in calendar

### 4. Document Organization

**Problem**: Random scanned documents need to be categorized and prioritized.

**Solution**:
```bash
# Point to a folder of mixed documents
godman agent "Organize documents in scans/ by type and urgency"
```

**What happens**:
1. Orchestrator detects file types (PDF, images, etc.)
2. OCRTool extracts text
3. VisionTool analyzes layout/content
4. Classifier determines: bill, invoice, personal doc, junk mail
5. Files moved to organized folders
6. Bills flagged for payment tracking
7. Summary report generated

---

## Why Terminal-First?

GodmanAI is designed for developers, power users, and automation enthusiasts who prefer:

- **Speed** - No GUI overhead, just commands
- **Automation** - Easy to script and chain commands
- **Privacy** - Runs locally with optional cloud models
- **Flexibility** - Pipe outputs, compose workflows, integrate with existing tools
- **Transparency** - See exactly what's happening with logs and debug output

---

## Extensibility

GodmanAI is built to grow with you:

### Custom Tools
```python
from godman_ai.engine import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    
    def run(self, **kwargs):
        # Your logic here
        return {"result": "success"}
```

### Custom Workflows
```python
from godman_ai.engine import BaseWorkflow

class MyWorkflow(BaseWorkflow):
    name = "my_workflow"
    
    def run(self, **kwargs):
        ocr_result = self.engine.call_tool("ocr", image_path=kwargs["image"])
        sheet_result = self.engine.call_tool("sheets", data=ocr_result)
        return sheet_result
```

### Custom Skills
```bash
# Scaffold a new skill
godman skill new invoice-analyzer

# Add your logic to the generated files
# Package it
godman skill package godman_ai/plugins/invoice-analyzer

# Share with your team or install on other machines
godman skill install invoice-analyzer.godmanskill
```

---

## Privacy & Security

- **Local-first** - All data stays on your machine unless you explicitly use cloud services
- **Optional cloud** - Use OpenAI, Google, etc. only when needed
- **Token-based auth** - Secure your API endpoints with bearer tokens
- **Encrypted tunnels** - Use Cloudflare tunnels for remote access
- **No telemetry** - No data sent to external servers except your configured integrations

---

## Next Steps

- [Architecture Deep Dive](architecture.md) - Understand how GodmanAI works internally
- [Operations Guide](operations.md) - Learn all CLI commands and workflows
- [Skills Development](skills.md) - Build custom tools and plugins
- [Model Configuration](models.md) - Set up local LLMs and model routing
