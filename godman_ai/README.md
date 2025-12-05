# Godman AI - Intelligent Automation Agent

AI-powered automation agent for personal productivity and workflow orchestration.

## Overview

Godman AI is an intelligent agent system that dynamically loads tools and workflows to automate your personal and business tasks.

## Architecture

```
godman_ai/
├── engine.py              # Core agent engine
├── tools/                 # Pluggable tool modules
│   ├── ocr.py            # OCR extraction
│   ├── vision.py         # Vision API analysis
│   ├── sheets.py         # Google Sheets integration
│   ├── trello.py         # Trello board management
│   ├── drive.py          # Google Drive operations
│   └── reports.py        # Report generation
├── workflows/            # Multi-step workflows
│   ├── receipts_workflow.py    # Receipt processing
│   └── pooljob_workflow.py     # Pool job management
├── memory/               # Persistent storage
│   └── store.py         # Memory and context
├── config/              # Configuration
│   └── config.toml      # Agent configuration
└── logs/                # Execution logs
```

## Features

### Dynamic Tool Loading
- Automatically discovers and loads tools from `tools/` directory
- Each tool inherits from `BaseTool` class
- Call tools with: `engine.call_tool(name, **kwargs)`

### Workflow Orchestration
- Automatically discovers workflows from `workflows/` directory
- Workflows combine multiple tools into pipelines
- Run with: `engine.run_workflow(name, **kwargs)`

### Available Tools

**OCR Tools:**
- `ocr` - Extract text from images and PDFs
- `ocr_batch` - Batch process multiple files

**Vision Tools:**
- `vision` - Analyze images with OpenAI Vision
- `image_categorizer` - Auto-categorize images
- `receipt_analyzer` - Extract receipt data

**Sheets Tools:**
- `sheets` - Read/write Google Sheets
- `sheets_receipt_logger` - Log receipts to Sheets
- `sheets_report` - Generate reports

**Trello Tools:**
- `trello` - Manage Trello cards
- `trello_job_tracker` - Track pool jobs
- `trello_task_automation` - Auto-create tasks

**Drive Tools:**
- `drive` - Upload/download files
- `drive_organizer` - Auto-organize files
- `drive_backup` - Backup files
- `drive_scanner` - Index Drive contents

**Report Tools:**
- `reports` - Generate various reports
- `expense_analyzer` - Analyze spending
- `pool_job_reporter` - Pool job reports
- `automation_metrics` - Track automation performance

### Available Workflows

**Receipt Processing:**
- `receipts_workflow` - Complete receipt processing pipeline
- `quick_receipt` - Fast single receipt processing

**Pool Job Management:**
- `pooljob_workflow` - End-to-end job management
- `pooljob_completion` - Complete job and generate invoice

## Usage

### Basic Usage

```python
from engine import AgentEngine

# Initialize the engine
engine = AgentEngine()

# Check status
status = engine.status()
print(f"Loaded {status['tools_loaded']} tools")
print(f"Loaded {status['workflows_loaded']} workflows")

# Call a tool
result = engine.call_tool("ocr", file_path="receipt.pdf")
print(result)

# Run a workflow
result = engine.run_workflow(
    "receipts_workflow",
    input_dir="scans",
    use_vision=True,
    log_to_sheets=True,
    spreadsheet_id="your-sheet-id"
)
print(result)
```

### List Available Tools and Workflows

```python
# List all tools
tools = engine.list_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")

# List all workflows
workflows = engine.list_workflows()
for workflow in workflows:
    print(f"{workflow['name']}: {workflow['description']}")
```

### Using Memory Store

```python
from memory.store import MemoryStore

# Initialize memory
memory = MemoryStore()

# Store context
memory.set_context("current_project", "pool_business")
memory.set_preference("default_spreadsheet", "abc123")

# Retrieve context
project = memory.get_context("current_project")

# Log automation
memory.log_automation(
    workflow="receipts_workflow",
    status="success",
    details={"files_processed": 5}
)

# Get history
history = memory.get_automation_history(limit=10)
```

## Configuration

Edit `config/config.toml` to configure:
- OpenAI API settings
- Tool-specific parameters
- Workflow defaults
- Directory paths

## Creating Custom Tools

```python
from engine import BaseTool

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "Description of what my tool does"
    
    def execute(self, **kwargs):
        # Your tool logic here
        return {"result": "success"}
```

Place in `tools/` directory and it will be auto-loaded!

## Creating Custom Workflows

```python
from engine import BaseWorkflow

class MyWorkflow(BaseWorkflow):
    name = "my_workflow"
    description = "Description of workflow"
    
    def __init__(self, engine):
        self.engine = engine
    
    def run(self, **kwargs):
        # Use engine.call_tool() to orchestrate
        result1 = self.engine.call_tool("ocr", file_path="doc.pdf")
        result2 = self.engine.call_tool("sheets", action="write", ...)
        return {"status": "success"}
```

Place in `workflows/` directory and it will be auto-loaded!

## Logging

All execution logs are written to `logs/agent_YYYYMMDD.log`

## Requirements

```bash
pip install openai pillow pytesseract pdf2image tomli
```

## Future Enhancements

- [ ] OpenAI function calling integration
- [ ] Real-time streaming responses
- [ ] Web interface for agent control
- [ ] Scheduled automation triggers
- [ ] Multi-agent collaboration
- [ ] Voice interface integration

## License

MIT License - Stephen Godman
