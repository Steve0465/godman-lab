# Godman-Lab AI Agent Instructions

## Project Overview
Godman-Lab is an async orchestration platform for AI workflows, combining tool execution, skill packaging, plugin scaffolding, and distributed workflow coordination. The codebase follows a modular architecture where `godman_ai/` contains the core platform and `libs/` houses specialized integrations (tax, receipts, Trello, AT&T).

## Architecture Essentials

### Core Components
- **godman_ai/orchestrator**: Multi-agent coordination (`Orchestrator`, `ExecutorAgent`, `RouterV2`, `ToolRouter`)
- **godman_ai/workflows**: Async workflow engine with DSL loader, checkpointing, and distributed execution
- **godman_ai/models**: Model routing (`LocalModelRouter`, `TaskType`), presets system for specialized AI roles
- **godman_ai/tools**: Tool registry with `@tool` decorator pattern for function/CLI tool registration
- **godman_ai/capabilities**: Capability mesh for cross-component discovery and resolution
- **godman_ai/skills**: Skill packaging system for reusable workflow components
- **godman_ai/plugins**: Plugin discovery and registration for extensibility
- **godman_ai/server**: FastAPI server with WebUI, preset management, and handler endpoint

### Specialized Libraries (`libs/`)
- **tool_runner.py**: Decorator-based function registry with subprocess execution and schema validation
- **tax_receipts_processor.py**: OCR + category rules for tax document processing
- **trello/**: Trello automation (normalizer, metrics, export)
- **att_scraper.py**: AT&T billing automation with Playwright
- **security/**: Process safety wrappers for safe subprocess execution

## Critical Patterns

### Tool Registration
Use the `@tool` decorator from `libs.tool_runner` for registering functions or CLI commands:
```python
from libs.tool_runner import tool

@tool(schema={"x": int, "y": int}, description="Add two numbers")
def add(x: int, y: int):
    return {"sum": x + y}

@tool(schema={"path": str}, command="ls -la {path}")
def list_files(path: str):
    pass
```
The global `runner` instance in `libs.tool_runner` is used by the server API. See `register_tools.py` for examples.

### Workflow Construction
Workflows use async-first steps with shared context and hooks:
```python
from godman_ai.workflows import Workflow, Step, Context

async def fetch_data(ctx):
    return {"items": [1, 2, 3]}

wf = Workflow(
    steps=[Step("fetch", fetch_data)],
    before_all=lambda ctx: ctx.set("started", True),
    on_error=lambda ctx: ctx.set("failed", True)
)
ctx = await wf.run(Context())
```
Sync functions are automatically offloaded via `asyncio.to_thread`. Errors surface as `WorkflowError`.

### Model Presets
The project uses specialized model presets for different tasks (see `godman_ai/config/presets.py`):
- **Overmind** (`deepseek-r1:14b`): Strategic reasoning and multi-stage planning
- **Forge** (`qwen2.5-coder:7b`): Code generation and script automation
- **Handler** (`gorilla-openfunctions-v2`): Function calling interface

Access via REST API at `/api/presets` or Python API `get_preset_by_name("Overmind")`.

### Public API Exports
All modules expose public APIs via `__all__` in `__init__.py`. Import from package roots:
```python
from godman_ai import LocalModelRouter, TaskType, select_model
from godman_ai.orchestrator import Orchestrator, ToolRouter
from godman_ai.workflows import Workflow, Step, load_workflow_from_yaml
from godman_ai.tools import ToolRunner, register_tool
```

## Development Workflows

### Starting the Server
```bash
./START_GODMAN_SERVER.sh  # Launches FastAPI on port 8000
```
Activates `.venv` if present, sets `GODMAN_ENV=production`, serves WebUI at `/`, exposes presets/handler/tools APIs.

### Running Tests
```bash
pytest tests/  # All tests from repo root
pytest tests/workflows/  # Specific subdirectory
```
The `conftest.py` fixture ensures tests run from repo root with `GODMAN_LOG_DIR` and `HOME` env vars set.

### CLI Tools
```bash
godman tool list                                      # List registered tools
godman tool run -n add -p '{"x": 5, "y": 3}'         # Execute tool
python3 godman_tool_cli.py list                       # Alternative CLI entry
```

### Building Package
```bash
python3 -m build  # Creates dist/ with wheel and sdist
```
Package config in `pyproject.toml` (requires Python >=3.12).

## Project-Specific Conventions

### Logging
- All components log to `GODMAN_LOG_DIR` (defaults to `logs/` in repo root)
- `ToolRunner` logs to `tool_runner.log`, workflows to `workflow_engine.log`
- Use standard Python `logging` module with timestamps

### Error Handling
- Custom exceptions: `ModelRoutingError`, `WorkflowError`, `ValidationError`, `ToolExecutionError`
- Workflows propagate errors via `WorkflowError` with failing step name
- Tools return structured JSON: `{"status": "success"|"error", "result": ..., "error": {...}}`

### File Paths
- Use absolute paths from repo root in code
- Environment-aware paths via `Path(__file__).resolve().parents[N]`
- Data directories: `data/tax/`, `scans/`, `exports/`, `knowledge-base/`

### Async-First Design
- Workflows, orchestrators, and distributed execution are async
- Sync tool functions wrapped automatically with `asyncio.to_thread`
- Use `await` for workflow execution and step actions

### Security
- Process execution uses `libs.security.run_safe()` for sandboxing
- Subprocess timeouts enforced at step level
- Parameter validation via schema definitions

## Integration Points

### WebUI → Backend
- React WebUI served at `/` via FastAPI static mount at `/webui`
- REST APIs: `/api/presets`, `/handler`, `/health`
- CORS enabled for localhost development

### Workflow DSL
- YAML workflows loaded via `load_workflow_from_yaml(path)`
- Supports conditional steps, switch statements, and distributed execution
- See `docs/workflows_dsl.md` for syntax

### External Services
- AT&T scraper uses Playwright with cookie persistence (`att_browser_cookies.json`)
- Trello integration via `libs.trello/` with OAuth token management
- OCR processing via `ocr/` directory with measurement extraction workflows

## Key Files Reference
- [godman_ai/server/api.py](godman_ai/server/api.py): FastAPI server with presets, handler, and tool runner endpoints
- [libs/tool_runner.py](libs/tool_runner.py): Core tool registration and execution framework
- [godman_ai/workflows/engine.py](godman_ai/workflows/engine.py): Async workflow orchestration engine
- [godman_ai/config/presets.py](godman_ai/config/presets.py): Model preset definitions
- [register_tools.py](register_tools.py): Example tool registrations loaded by server
- [conftest.py](conftest.py): Pytest configuration with repo root setup
- [docs/index.md](docs/index.md): Documentation index with links to all guides

## Common Tasks

### Adding a New Tool
1. Define function with `@tool` decorator in a new file or `register_tools.py`
2. Specify schema with type annotations (e.g., `{"x": int, "text": str}`)
3. Return dict for structured output
4. Tool auto-registers on import via global `runner` instance

### Creating a Workflow
1. Import `Workflow`, `Step`, `Context` from `godman_ai.workflows`
2. Define step actions (sync or async functions)
3. Chain steps with shared context via `ctx.get(step_name)` and `ctx.set(key, value)`
4. Add hooks for lifecycle management (`before_all`, `after_all`, `on_error`)

### Adding a Preset
1. Edit `godman_ai/config/presets.py`
2. Add `Preset` instance to `PRESETS` list with model, temp, max_tokens, system prompt
3. Preset auto-exposed via `/api/presets/{name}` endpoint

## Specialized Integration Patterns

### Tax Receipt Processing
The `libs.tax_receipts_processor` module provides end-to-end receipt processing:
```python
from libs.tax_receipts_processor import extract_text_from_pdf, extract_vendor
from libs.tax_category_rules import classify_receipt

# Extract text from PDF using PyMuPDF
text = extract_text_from_pdf(Path("receipt.pdf"))

# Vendor detection with heuristics
vendor = extract_vendor(text)  # e.g., "Home Depot", "Amazon"

# Automatic tax categorization (vendor, text, amount)
category = classify_receipt(vendor, text, amount=100.0)
# Returns ReceiptClassification with category, subcategory, deductibility_rate, confidence
```
**Key patterns:**
- OCR fallback when text extraction yields <20 chars
- Vendor patterns use regex priority matching (building materials → pool supplies → groceries)
- Category rules in `libs.tax_category_rules` match vendor + keywords (e.g., lumber, paint, pool chemicals)
- Receipt workflows in `godman_ai.workflows.receipts` for batch processing

### Trello Automation
Trello integration uses normalized exports for O(1) lookups:
```python
from libs.trello_normalizer import normalize_trello_export

# Convert flat export to indexed structure
normalized = normalize_trello_export(raw_json)

# O(1) lookups instead of O(n) scans
complete_cards = normalized['cards_by_list_name']['Complete']
specific_card = normalized['cards_by_id']['card_abc123']
all_in_list = normalized['cards_by_list_id']['list_id_123']
```
**Enriched card data:**
- `comment_count`, `attachment_count`, `checklist_count`
- `checklist_items_total`, `checklist_items_complete`
- Pre-computed stats avoid repeated scanning

### AT&T Billing Automation
The `libs.att_scraper` uses Playwright for browser automation:
```python
from libs.att_scraper import ATTClient

client = ATTClient(headless=False)
client.login()  # Uses cookies from att_browser_cookies.json
bills = client.get_bills()
client.close()
```
**Key patterns:**
- Cookie persistence for session management
- Headless mode for automation, non-headless for interactive login
- Error handling for network failures and login issues

## Distributed Workflow Execution

The distributed engine (`godman_ai.workflows.distributed_engine`) adds checkpointing and worker coordination:

### Architecture
- **DistributedWorkflowRunner**: Submits workflows, checkpoints step state, coordinates concurrency
- **CheckpointStore**: Persistence API (in-memory or SQLite implementations)
- **JobServer**: HTTP server for workflow submission and status checks
- **Worker**: Polling worker that processes pending steps

### Usage
```bash
# Start distributed workflow
godman workflow start examples/workflows/sample.yml --distributed
godman workflow status <workflow_id>

# Worker management
godman worker start
godman job-server start
```

### Execution Modes
- **Local**: Compatible with v1.x `Workflow.run()` (default, no checkpointing)
- **Distributed**: Steps checkpointed, executed concurrently, resumable after failures
- **Agent-managed**: AgentLoop wraps distributed runs with critics/strategies for self-correction

### Checkpointing Pattern
```python
from godman_ai.workflows import DistributedWorkflowRunner, LocalSqliteCheckpointStore

runner = DistributedWorkflowRunner(
    checkpoint_store=LocalSqliteCheckpointStore("checkpoints.db")
)
workflow_id = await runner.submit_workflow(workflow, context)
status = await runner.get_workflow_status(workflow_id)
```

## Testing Patterns

### Test Structure
- All tests run from repo root via `conftest.py` fixture
- Environment vars set automatically: `GODMAN_LOG_DIR`, `HOME`
- Use `pytest.mark.asyncio` for async workflow tests

### Workflow Testing Example
```python
import asyncio
import pytest
from godman_ai.workflows import Workflow, Step, Context, WorkflowError

def test_workflow_hooks():
    order = []
    
    def before(ctx): order.append("before")
    def after(ctx): order.append("after")
    def action(ctx): order.append("action")
    
    wf = Workflow([Step("test", action)], before_all=before, after_all=after)
    ctx = asyncio.run(wf.run(Context()))
    assert order == ["before", "action", "after"]

def test_workflow_error_handling():
    def failing(ctx): raise ValueError("boom")
    wf = Workflow([Step("fail", failing)])
    
    with pytest.raises(WorkflowError):
        asyncio.run(wf.run(Context()))
```

### Tool Testing Pattern
```python
from libs.tool_runner import ToolRunner

def test_tool_execution():
    runner = ToolRunner()
    
    @runner.tool(schema={"x": int, "y": int})
    def add(x: int, y: int):
        return {"sum": x + y}
    
    result = runner.run("add", {"x": 5, "y": 3})
    assert result["status"] == "success"
    assert result["result"]["sum"] == 8
```

### Running Specific Test Suites
```bash
pytest tests/workflows/              # Workflow tests
pytest tests/orchestrator/           # Orchestrator tests
pytest tests/tools/                  # Tool runner tests
pytest tests/ -k "test_workflow"     # Filter by name
pytest tests/ -v                     # Verbose output
```
