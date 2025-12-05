# GodmanAI: Autonomous Terminal Intelligence

**A personal AI operating system running in your terminal.**

GodmanAI is a modular, extensible AI automation platform that combines intelligent agents, orchestration, memory systems, and tool routing to handle everything from receipt processing to document organization, job scheduling, and custom workflows.

---

## Key Features

- **🤖 Agent System**: Multi-phase agents (Planner → Executor → Reviewer) for autonomous task execution
- **🔀 Smart Orchestrator**: Dynamic input detection and tool routing (images, PDFs, text, CSVs, audio, video)
- **🧠 Memory Layer**: Vector store, episodic memory, and working memory for context retention
- **⚙️ Job Queue & Scheduler**: Background task processing with cron-based scheduling
- **🎯 OS Core**: State management, model routing, tool chaining, plugin system, and health monitoring
- **🌐 Service Layer**: Local API server, web dashboard, daemon mode, and secure tunneling
- **🧩 Skill SDK**: Build and package custom tools/agents with `.godmanskill` format
- **🏪 Private App Store**: Install skills from curated registry
- **🤖 Local Models**: Run LLMs locally with llama.cpp integration and smart routing

---

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/Steve0465/godman-lab.git
cd godman-lab

# Install in editable mode
pip install -e .
```

### Configuration

Set your API keys and tokens:

```bash
# OpenAI API Key (for cloud models)
export OPENAI_API_KEY="sk-..."

# GodmanAI API Token (for secure API access)
export GODMAN_API_TOKEN="your-secure-token"
```

Or create a `.env` file:

```
OPENAI_API_KEY=sk-...
GODMAN_API_TOKEN=your-secure-token
```

### Basic Usage

```bash
# Run a simple task through the orchestrator
godman run "path/to/receipt.pdf"

# Run the full agent loop (Planner → Executor → Reviewer)
godman agent "Extract vendor and total from this receipt"

# Start the local API server
godman server

# View system health and stats
godman health

# Start the background daemon (runs queue worker + scheduler)
godman daemon start
```

### Web Dashboard & Tunneling

```bash
# Start the server
godman server

# In another terminal, create a secure tunnel (requires cloudflared)
godman tunnel

# Access dashboard at: http://127.0.0.1:8000/dashboard
```

---

## Architecture Overview

GodmanAI is built in layers:

1. **Core Layer** (`godman_ai/`)
   - `engine.py` - BaseTool and BaseWorkflow abstractions
   - `orchestrator.py` - Input detection and tool routing
   - `tools/` - Individual tool implementations (OCR, vision, sheets, etc.)

2. **Agent Layer** (`godman_ai/agents/`)
   - `planner.py` - Generates structured task plans
   - `executor.py` - Executes individual steps using tools
   - `reviewer.py` - Validates outputs and triggers replanning
   - `agent_loop.py` - Coordinates the full agent cycle

3. **Memory Layer** (`godman_ai/memory/`)
   - `vector_store.py` - FAISS-based semantic search
   - `episodic_memory.py` - Task history and recall
   - `working_memory.py` - Short-term context between steps

4. **Infrastructure Layer** (`godman_ai/`)
   - `queue/` - Job queue engine with SQLite persistence
   - `scheduler/` - Cron-based task scheduling
   - `config/` - Settings and configuration management

5. **OS Core Layer** (`godman_ai/os_core/`)
   - `state_manager.py` - Global runtime state and metrics
   - `model_router.py` - Smart model selection (cloud vs. local)
   - `tool_graph.py` - Automatic tool chaining
   - `plugin_manager.py` - Dynamic plugin loading
   - `health.py` - System introspection and diagnostics

6. **Service Layer** (`godman_ai/service/`)
   - `api.py` - FastAPI REST endpoints
   - `server.py` - HTTP server runner
   - `dashboard.py` - Web UI for monitoring
   - `daemon.py` - Background service mode
   - `skill_store.py` - Skill installation system

7. **Skill SDK** (`godman_ai/sdk/`)
   - `skill_template/` - Starter templates for tools/agents
   - `builder.py` - Skill scaffolding and packaging
   - `validator.py` - Manifest and structure validation

8. **App Store** (`godman_ai/appstore/`)
   - `registry.py` - Skill catalog management
   - `fetcher.py` - Remote skill download
   - `index.json` - Curated skill registry

9. **CLI Interface** (`cli/godman/`)
   - `main.py` - Typer-based command-line interface
   - `commands/` - Subcommand implementations

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

---

## Use Cases

### Receipt Processing
```bash
# Scan receipt → OCR → parse → categorize → save to Sheets
godman agent "Process receipts in scans/ folder"
```

### Document Organization
```bash
# Auto-organize scanned documents by type and urgency
godman run scans/
```

### Job Scheduling
```bash
# Schedule recurring tasks
godman schedule add "0 9 * * *" "godman agent 'Generate daily expense report'"
godman daemon start
```

### Custom Skills
```bash
# Create a new skill
godman skill new my-analyzer

# Package it
godman skill package godman_ai/plugins/my-analyzer

# Install from store
godman store install ocr-pro
```

---

## Roadmap

### ✅ v0.1.0 (Current)
- Core orchestrator with input detection
- Agent system (Planner, Executor, Reviewer)
- Memory layer (vector + episodic)
- Job queue and scheduler
- OS Core with state management
- Service layer (API, dashboard, daemon)
- Skill SDK and private app store
- Local model support

### 🚧 v0.2.0 (Next)
- Voice command interface
- Mobile companion app
- Real-time notifications
- Advanced tool chaining rules
- Multi-model ensembles

### 🔮 v0.5.0
- Self-improvement loops
- Federated learning across instances
- Natural language workflow builder
- Integration marketplace

### 🎯 v1.0.0
- Production-ready stability
- Enterprise features
- Full documentation
- Community plugin ecosystem

---

## Documentation

- [Overview & Use Cases](docs/overview.md)
- [Architecture Deep Dive](docs/architecture.md)
- [Operations Guide](docs/operations.md)
- [Skills Development](docs/skills.md)
- [Model Configuration](docs/models.md)

---

## Contributing

This is a personal project, but contributions are welcome! Please open an issue before starting work on major features.

---

## License

MIT License - see LICENSE file for details.

---

## Legacy Tools

### Receipt Processing (Legacy)
See [docs/README_receipts.md](docs/README_receipts.md) for the original receipt processing scripts.

### GitHub Code Search
See [docs/README_github_search.md](docs/README_github_search.md) for GitHub search utilities.
