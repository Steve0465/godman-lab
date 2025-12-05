# GodmanAI Architecture

This document provides a detailed technical overview of GodmanAI's architecture, component interactions, and design patterns.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                     (cli/godman/main.py)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   API    │  │Dashboard │  │  Daemon  │  │  Tunnel  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                      OS Core Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │StateManager  │  │ModelRouter   │  │ToolGraph     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │PluginManager │  │Health        │                         │
│  └──────────────┘  └──────────────┘                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Agent Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Planner  │→ │ Executor │→ │ Reviewer │→ │AgentLoop │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  Orchestrator Layer                          │
│         (Input Detection & Tool Routing)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Tool Layer                               │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐    │
│  │ OCR │  │Vision│  │Sheets│  │Trello│  │Drive│  │Reports│  │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘    │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Infrastructure Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Memory  │  │  Queue   │  │Scheduler │                  │
│  │ (Vector, │  │ (SQLite) │  │  (Cron)  │                  │
│  │Episodic, │  └──────────┘  └──────────┘                  │
│  │ Working) │                                                │
│  └──────────┘                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### 1. CLI Layer (`cli/godman/`)

**Purpose**: User-facing command interface using Typer.

**Key Files**:
- `main.py` - Main CLI entrypoint
- `commands/` - Subcommand implementations

**Commands**:
```bash
godman run <input>           # Run orchestrator directly
godman agent <input>         # Run full agent loop
godman server                # Start API server
godman tunnel [url]          # Create secure tunnel
godman daemon start/stop     # Control background daemon
godman health                # System health check
godman queue enqueue/status  # Job queue management
godman schedule add/list     # Cron scheduler
godman skill new/package     # Skill development
godman store list/install    # Skill store
godman models list/run       # Local model management
```

**Design Pattern**: Command pattern with lazy imports to keep startup fast.

---

### 2. Service Layer (`godman_ai/service/`)

**Purpose**: HTTP API, web UI, and background services.

#### API Server (`api.py`)
- FastAPI-based REST API
- Token-based authentication
- Endpoints for orchestrator, agents, queue, memory, health

**Key Endpoints**:
```
POST /run           - Run orchestrator
POST /agent         - Run agent loop
POST /queue/enqueue - Add job to queue
GET  /queue/status  - Queue stats
GET  /os/state      - Global state snapshot
GET  /os/health     - Health metrics
GET  /tools         - List loaded tools
GET  /models        - List available models
POST /memory/add    - Add to episodic memory
POST /memory/search - Vector search
```

#### Dashboard (`dashboard.py`)
- Web UI at `/dashboard`
- Real-time system monitoring
- Tool and plugin viewer
- Queue and scheduler status
- Memory browser

#### Daemon Mode (`daemon.py`)
- Background process management
- Runs queue worker loop
- Runs scheduler loop
- Persistent across terminal sessions

#### Skill Store (`skill_store.py`)
- Install `.godmanskill` packages
- Validate and register plugins
- Manage local skill registry

---

### 3. OS Core Layer (`godman_ai/os_core/`)

**Purpose**: Global state, coordination, and system intelligence.

#### State Manager (`state_manager.py`)
Tracks runtime state:
```python
class GlobalState:
    settings: Settings
    memory: MemoryComponents
    queue: JobQueue
    scheduler: Scheduler
    active_models: dict
    runtime_stats: dict
```

Metrics tracked:
- Total tasks executed
- Success/failure rates
- Average execution time
- Tool usage frequencies
- Model routing decisions

#### Model Router (`model_router.py`)
Smart model selection:
```python
def choose_model(task_type: str) -> str:
    if task_type == "text_analysis":
        return "gpt-4o-mini"  # Fast, cheap
    elif task_type == "planning":
        return "gpt-4"        # Best reasoning
    elif task_type == "vision":
        return "gpt-4-vision" # Multimodal
```

Fallback logic:
- Cloud model unavailable → use local model
- Local model missing → download from Hugging Face
- Both unavailable → graceful error

#### Tool Graph (`tool_graph.py`)
Automatic tool chaining:
```python
# Build dependency graph
image → OCRTool → output: text
text  → ParserTool → output: structured_data
structured_data → SheetsTool → output: success

# Suggest chain for: "Extract receipt data and save to Sheets"
suggest_chain("receipt.jpg") 
# → ["ocr", "parser", "sheets"]
```

#### Plugin Manager (`plugin_manager.py`)
Dynamic plugin loading:
- Scan `godman_ai/plugins/`
- Import Python modules
- Detect `BaseTool` and `BaseAgent` subclasses
- Register with orchestrator
- Safe failure on bad plugins

#### Health Monitor (`health.py`)
System diagnostics:
```python
system_health() → {
    "queue_depth": 3,
    "worker_active": true,
    "scheduler_next_run": "2024-01-15T10:00:00",
    "memory_episodes": 142,
    "vector_count": 1523,
    "models_loaded": ["llama-7b", "gpt-4"],
    "recent_failures": 2,
    "uptime_hours": 47.3
}
```

---

### 4. Agent Layer (`godman_ai/agents/`)

**Purpose**: Autonomous task execution with planning and feedback.

#### Planner Agent (`planner.py`)
Converts high-level goals into structured plans:

```python
task = "Process receipts in scans/ folder"

plan = [
    {
        "id": 1,
        "action_type": "list_files",
        "input": {"path": "scans/"},
        "expected_output": "list of file paths"
    },
    {
        "id": 2,
        "action_type": "ocr",
        "input": {"file": "$1.output[0]"},
        "expected_output": "text content"
    },
    {
        "id": 3,
        "action_type": "parse",
        "input": {"text": "$2.output"},
        "expected_output": "vendor, total, date"
    },
    ...
]
```

#### Executor Agent (`executor.py`)
Runs individual plan steps:

```python
def execute_step(step):
    if step["action_type"] == "ocr":
        return orchestrator.run_task(step["input"])
    elif step["action_type"] == "parse":
        return llm.extract_fields(step["input"])
    else:
        return run_custom_function(step)
```

#### Reviewer Agent (`reviewer.py`)
Validates execution quality:

```python
def review_output(step, output):
    if step["expected_output"] == "vendor, total, date":
        if not all(k in output for k in ["vendor", "total", "date"]):
            return {
                "approved": False,
                "feedback": "Missing required fields",
                "needs_revision": True
            }
    return {"approved": True}
```

#### Agent Loop (`agent_loop.py`)
Coordinates the full cycle:

```python
def run(task_input):
    plan = planner.generate_plan(task_input)
    results = []
    
    for step in plan:
        output = executor.execute_step(step)
        review = reviewer.review_output(step, output)
        
        if not review["approved"]:
            # Replan this step
            new_step = planner.revise_step(step, review["feedback"])
            output = executor.execute_step(new_step)
        
        results.append(output)
    
    return aggregate_results(results)
```

---

### 5. Orchestrator Layer (`godman_ai/orchestrator.py`)

**Purpose**: Input detection and tool routing.

**Flow**:
```python
def run_task(input_obj):
    # 1. Detect input type
    input_type = detect_input_type(input_obj)
    
    # 2. Select tool
    tool = select_tool_for_type(input_type)
    
    # 3. Execute
    result = tool.run(input=input_obj)
    
    # 4. Log and return
    log_execution(tool, result)
    return result
```

**Input Detection**:
```python
def detect_input_type(input_obj):
    if input_obj.endswith(('.jpg', '.png')):
        return "image"
    elif input_obj.endswith('.pdf'):
        return "pdf"
    elif input_obj.endswith('.csv'):
        return "csv"
    elif input_obj.endswith(('.mp4', '.mov')):
        return "video"
    elif os.path.isfile(input_obj):
        return detect_by_content(input_obj)
    else:
        return "text"
```

**Lazy Imports**: Heavy libraries loaded only when needed:
```python
def run_ocr(image_path):
    from PIL import Image  # Import here, not at top
    import pytesseract
    
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)
```

---

### 6. Tool Layer (`godman_ai/tools/`)

**Purpose**: Individual capabilities (OCR, vision, integrations).

**BaseTool Contract**:
```python
class BaseTool:
    name: str
    description: str
    
    def run(self, **kwargs):
        raise NotImplementedError
```

**Example Tools**:
- `OCRTool` - Tesseract OCR
- `VisionTool` - OpenAI vision or local CLIP
- `SheetsTool` - Google Sheets API
- `TrelloTool` - Trello API
- `DriveTool` - Google Drive API
- `ReportsTool` - Generate summaries

**Auto-Discovery**:
```python
# tools/auto_loader.py
def discover_tool_classes(package_path):
    tools = {}
    for module in pkgutil.iter_modules([package_path]):
        mod = importlib.import_module(f"{package_path}.{module.name}")
        for name, obj in inspect.getmembers(mod):
            if isinstance(obj, type) and issubclass(obj, BaseTool):
                tools[obj.name] = obj
    return tools
```

---

### 7. Infrastructure Layer

#### Memory System (`godman_ai/memory/`)

**Vector Store** (`vector_store.py`):
- FAISS-based semantic search
- Stores text + metadata
- Persistent to disk

```python
store = VectorStore()
store.add("Process receipt for Home Depot", {"vendor": "Home Depot", "total": 45.67})
results = store.search("home improvement store receipt")
```

**Episodic Memory** (`episodic_memory.py`):
- Complete task histories
- Stores: input, plan, results, timestamp

```python
memory.add_episode(
    task_input="receipt.jpg",
    plan=[...],
    results={...}
)

similar_tasks = memory.recall("receipt processing")
```

**Working Memory** (`working_memory.py`):
- Short-lived key-value store
- Shared between agent steps

```python
working_memory.push("extracted_text", ocr_result)
text = working_memory.get("extracted_text")
```

#### Job Queue (`godman_ai/queue/`)

**Queue Implementation** (`job_queue.py`):
- SQLite-backed persistence
- Priority-based ordering
- Status tracking (pending, running, complete, failed)

```python
queue.enqueue({"task": "process receipt"}, priority=1)
job = queue.dequeue()
```

**Worker** (`job_worker.py`):
- Continuous polling
- Feeds jobs to AgentLoop
- Stores results in episodic memory

#### Scheduler (`godman_ai/scheduler/`)

**Scheduler** (`scheduler.py`):
- Cron expression parsing
- Enqueues jobs at scheduled times
- Persistent schedule storage

```python
scheduler.add_schedule("0 9 * * *", "godman agent 'Daily report'")
scheduler.run_pending()
```

---

## Data Flow Examples

### Example 1: Simple Task

```
User: godman run receipt.jpg

CLI → Orchestrator.run_task("receipt.jpg")
  → detect_input_type → "image"
  → select_tool → OCRTool
  → OCRTool.run(image_path="receipt.jpg")
    → pytesseract.image_to_string()
  → return {"text": "..."}
CLI → print result
```

### Example 2: Agent Loop

```
User: godman agent "Extract receipt data and save to Sheets"

CLI → AgentLoop.run("Extract receipt data and save to Sheets")
  → Planner.generate_plan()
    → LLM creates: [list_files, ocr, parse, sheets]
  → For each step:
    → Executor.execute_step()
      → Orchestrator.run_task()
    → Reviewer.review_output()
      → If failed → Planner.revise_step()
  → EpisodicMemory.add_episode()
  → return final_output
CLI → print summary
```

### Example 3: Scheduled Job

```
Scheduler: every hour at :00

Scheduler.run_pending()
  → check cron matches
  → JobQueue.enqueue("Check pool emails")
  
JobWorker (running in daemon):
  → JobQueue.dequeue()
  → AgentLoop.run("Check pool emails")
    → Planner → [read_email, extract_job_details, update_trello]
    → Executor → EmailTool, ParserTool, TrelloTool
    → Reviewer → validate
  → EpisodicMemory.add_episode()
  → mark job complete
```

---

## Design Principles

### 1. Lazy Imports
Heavy libraries imported only when needed to keep startup fast.

### 2. Dependency Injection
Components receive dependencies via constructor, not global singletons.

### 3. Interface Segregation
Small, focused interfaces (`BaseTool`, `BaseWorkflow`, `BaseAgent`).

### 4. Open/Closed Principle
Extensible via plugins without modifying core code.

### 5. Fail-Safe Design
Plugins, tools, and agents can fail without crashing the system.

### 6. Local-First
All data stays local unless explicitly configured otherwise.

### 7. Observable
Logs, metrics, and health checks at every layer.

---

## Extension Points

### Add a New Tool
```python
# godman_ai/tools/my_tool.py
from godman_ai.engine import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something"
    
    def run(self, **kwargs):
        return {"result": "success"}
```

### Add a New Agent Type
```python
# godman_ai/agents/optimizer.py
class OptimizerAgent:
    def optimize_plan(self, plan):
        # Remove redundant steps
        return optimized_plan
```

### Add a Custom Workflow
```python
# godman_ai/workflows/invoice_flow.py
from godman_ai.engine import BaseWorkflow

class InvoiceWorkflow(BaseWorkflow):
    name = "invoice"
    
    def run(self, **kwargs):
        ocr = self.engine.call_tool("ocr", ...)
        parse = self.engine.call_tool("parser", ...)
        return parse
```

### Add a Plugin
Drop any `.py` file in `godman_ai/plugins/` with a `BaseTool` subclass and it will auto-load.

---

## Performance Considerations

### Startup Time
- Lazy imports keep CLI responsive
- Plugin discovery deferred until first use

### Memory Usage
- Vector store paginated for large datasets
- Episodic memory prunable by age/relevance

### Concurrency
- Queue worker runs in separate process
- Scheduler non-blocking
- API server uses async FastAPI

### Scalability
- SQLite queue suitable for single-user workloads
- For multi-user: swap to PostgreSQL
- For distributed: use Redis queue + Celery

---

## Security Model

### API Authentication
- Bearer token required for mutating endpoints
- Token stored in settings, loaded from env

### Tunnel Security
- Cloudflare tunnels provide HTTPS
- No port forwarding required

### Local Execution
- No telemetry or external calls unless configured
- All data stays on disk

### Plugin Safety
- Plugins run in same process (no sandbox)
- Review code before installing third-party skills

---

## Future Architecture Enhancements

### v0.2.0
- Multi-agent collaboration (agents spawn sub-agents)
- Streaming responses for long tasks
- Webhook triggers

### v0.5.0
- Distributed queue (Redis/RabbitMQ)
- Multi-user support (per-user state)
- Remote skill registry (private npm-style registry)

### v1.0.0
- Sandboxed plugin execution
- GraphQL API
- Real-time WebSocket dashboard
- Federated episodic memory

---

For operational details, see [operations.md](operations.md).
For skill development, see [skills.md](skills.md).
For model configuration, see [models.md](models.md).
