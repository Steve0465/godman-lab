# 🚀 GodmanAI Quickstart Guide

## What You Just Built

You created **GodmanAI** - a personal AI operating system that runs entirely on your computer with these capabilities:

### Core Features
- 🤖 **Local AI Models** - Run uncensored AI models with no data leaving your machine
- 📁 **Smart File Organization** - AI automatically categorizes and organizes files
- 📄 **OCR & Document Processing** - Extract text from receipts, invoices, PDFs
- 🧠 **Personal AI Assistant** - Learns about YOU and makes decisions your way
- 🔄 **Task Automation** - Queue jobs, schedule tasks, run workflows
- 🌐 **API Server** - RESTful API + web dashboard
- 🔌 **Plugin System** - Extend with custom tools and skills

---

## Step 1: Analyze Your System

Let GodmanAI learn about you:

```bash
# Full system analysis
godman profile analyze --full

# See what questions it has
godman profile questions

# Answer them interactively
godman profile answer
```

This creates a profile at `~/.godman/profile/profile.json` that the AI uses to understand your preferences, business, and habits.

---

## Step 2: Test the Local AI Model

```bash
# Check if Ollama is running
ollama list

# Test the local model
python -c "
from godman_ai.models.local_model import LocalModel
model = LocalModel()
response = model.query('What can you help me with?')
print(response)
"
```

---

## Step 3: Organize Your Files

```bash
# Analyze and organize Desktop
godman organize ~/Desktop

# Organize Documents with AI categorization
godman organize ~/Documents --mode ai

# Dry run first (see what would happen)
godman organize ~/Downloads --dry-run
```

---

## Step 4: Process Documents

```bash
# Process a receipt
godman run scans/receipt.pdf

# Use the full agent system (plan → execute → review)
godman agent scans/receipt.pdf

# Check system status
godman status
```

---

## Step 5: Start the Server & Dashboard

```bash
# Start API server
godman server

# In another terminal, expose it publicly
godman tunnel

# Or run in background
godman daemon start
```

Access dashboard at: http://127.0.0.1:8000/dashboard

---

## Understanding Your System

### Directory Structure

```
godman-lab/
├── cli/godman/              # CLI commands
├── libs/                    # Core business logic
├── godman_ai/              # AI engine
│   ├── agents/             # Agent system (planner/executor/reviewer)
│   ├── memory/             # Vector store, episodic memory
│   ├── models/             # Local model integration
│   ├── os_core/            # State manager, model router, plugins
│   ├── profiler/           # Personal data collector
│   ├── queue/              # Job queue system
│   ├── scheduler/          # Task scheduler
│   ├── sdk/                # Skill development kit
│   └── service/            # API server, daemon
└── ~/.godman/              # Your personal data
    ├── profile/            # AI profile about you
    ├── state/              # Runtime state, vector store
    ├── logs/               # System logs
    └── plugins/            # Installed skills
```

### Key Concepts

**Orchestrator** - Routes tasks to the right tool based on input type (PDF → OCR, image → vision, etc.)

**Agent Loop** - Multi-phase autonomous system:
1. **Planner** - Creates step-by-step execution plan
2. **Executor** - Runs each step using tools
3. **Reviewer** - Validates outputs, triggers replanning if needed

**Memory System**:
- **Working Memory** - Short-term context during task execution
- **Episodic Memory** - Remembers past tasks and results
- **Vector Store** - Semantic search over your data

**Model Router** - Automatically chooses:
- Big models for planning (GPT-4)
- Small models for simple tasks (local models)
- Vision models for images
- Local fallback if OpenAI unavailable

---

## What Makes This Special

### vs ChatGPT/Claude
- ✅ Runs 24/7 in background
- ✅ No data leaves your computer
- ✅ Train it on YOUR data
- ✅ No censorship or restrictions
- ✅ Integrates with your filesystem
- ✅ Can execute actions automatically

### vs GitHub Copilot (me!)
- ✅ I help you BUILD the system
- ✅ Your system RUNS the system
- ✅ I'm corporate-hosted, GodmanAI is yours
- ✅ I assist, GodmanAI operates autonomously

---

## Next Steps

### Make It Smarter

Train your AI on your data:

```bash
# Export profile for fine-tuning
godman profile export training_data.json

# Add your communication style
# (Export messages from Messages.app or Mail)
```

### Add Custom Skills

```bash
# Create new skill
godman skill new my-custom-tool --author "Your Name"

# Develop it, then package
godman skill package ./my-custom-tool

# Install it
godman skills install ./my-custom-tool.godmanskill
```

### Automate Everything

```bash
# Schedule daily receipt processing
godman schedule add "0 9 * * *" "godman agent 'Process yesterday receipts'"

# Queue background tasks
godman queue enqueue "Organize Downloads folder"

# Run worker to process queue
godman queue worker
```

---

## Troubleshooting

### Check System Health
```bash
godman os-health
```

### View Logs
```bash
tail -f ~/.godman/logs/godman.log
```

### Reset Profile
```bash
godman profile reset
```

### Check What's Running
```bash
godman daemon status
godman queue status
godman schedule list
```

---

## Privacy & Ethics

**Your data stays local:**
- Profile stored in `~/.godman/profile/`
- Nothing uploaded to cloud (unless you configure it)
- OpenAI API only used if you provide key
- Local models never send data anywhere

**Boundaries:**
- System analyzes files you explicitly give it access to
- Won't access iCloud/online accounts without credentials
- Respects standard privacy practices

**You have full control:**
- View profile anytime: `godman profile show`
- Delete everything: `rm -rf ~/.godman`
- Configure model preferences in `~/.godman/config.yaml`

---

## Getting Help

```bash
# General help
godman --help

# Command-specific help
godman profile --help
godman organize --help
godman agent --help
```

---

## What's Next?

You now have a **personal AI OS** that can:
- Learn about you
- Organize your life
- Process documents
- Run autonomously
- Extend with custom skills
- Operate completely offline

The system grows smarter the more you use it. Start with simple tasks and gradually give it more autonomy as you build trust.

**Welcome to the future of personal AI!** 🎉
