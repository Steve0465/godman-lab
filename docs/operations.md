# GodmanAI Operations Guide

Complete reference for running and managing GodmanAI in production.

---

## Installation & Setup

### Prerequisites
```bash
# Python 3.9+
python --version

# Optional: cloudflared for tunneling
brew install cloudflare/cloudflare/cloudflared  # macOS
# or download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

### Install GodmanAI
```bash
# Clone repository
git clone https://github.com/Steve0465/godman-lab.git
cd godman-lab

# Install in editable mode
pip install -e .

# Verify installation
godman --help
```

### Configuration

Create `.env` file in repo root:
```bash
# OpenAI API Key (for cloud models)
OPENAI_API_KEY=sk-...

# GodmanAI API Token (for secure API access)
GODMAN_API_TOKEN=your-secure-token

# Optional: Local model directory
LOCAL_MODEL_DIR=/path/to/models

# Optional: Log level
GODMAN_LOG_LEVEL=INFO

# Optional: Enable/disable components
SCHEDULER_ENABLED=true
MEMORY_ENABLED=true
```

Or use environment variables:
```bash
export OPENAI_API_KEY="sk-..."
export GODMAN_API_TOKEN="your-secure-token"
```

### First Run
```bash
# Check system health
godman health

# Should show:
# - Settings loaded
# - Tools discovered
# - Models available
# - Queue/scheduler status
```

---

## Core Commands

### Running Tasks

#### Direct Orchestrator
```bash
# Run orchestrator on any input
godman run <input>

# Examples:
godman run "path/to/receipt.jpg"        # Process image
godman run "path/to/document.pdf"       # Process PDF
godman run "Analyze this text"          # Process text
godman run "path/to/data.csv"           # Process CSV
godman run "path/to/video.mp4"          # Process video

# Output: Structured JSON result from the appropriate tool
```

#### Full Agent Loop
```bash
# Run Planner → Executor → Reviewer loop
godman agent <input>

# Examples:
godman agent "Extract receipt data and save to Sheets"
godman agent "Organize documents in scans/ folder"
godman agent "Generate expense summary for November"
godman agent "Check pool job emails and update Trello"

# Output: Step-by-step execution trace + final result
```

---

## Server & API

### Start Local Server
```bash
# Start on default port 8000
godman server

# Server will start at: http://127.0.0.1:8000
# Dashboard at: http://127.0.0.1:8000/dashboard
```

### API Endpoints

#### Run Tasks
```bash
# Run orchestrator
curl -X POST http://127.0.0.1:8000/run \
  -H "Authorization: Bearer $GODMAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "path/to/file.jpg"}'

# Run agent loop
curl -X POST http://127.0.0.1:8000/agent \
  -H "Authorization: Bearer $GODMAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "Process receipts in scans/"}'
```

#### Queue Management
```bash
# Enqueue job
curl -X POST http://127.0.0.1:8000/queue/enqueue \
  -H "Authorization: Bearer $GODMAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task": "process receipt", "priority": 1}'

# Get queue status
curl http://127.0.0.1:8000/queue/status
```

#### System Information
```bash
# Get global state
curl http://127.0.0.1:8000/os/state

# Get health metrics
curl http://127.0.0.1:8000/os/health

# List tools
curl http://127.0.0.1:8000/tools

# List models
curl http://127.0.0.1:8000/models
```

#### Memory Operations
```bash
# Add to episodic memory
curl -X POST http://127.0.0.1:8000/memory/add \
  -H "Authorization: Bearer $GODMAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Processed receipt from Home Depot", "metadata": {"vendor": "Home Depot"}}'

# Search memory
curl -X POST http://127.0.0.1:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "home depot receipt", "top_k": 5}'
```

### Secure Tunneling
```bash
# Create Cloudflare tunnel to local server
godman tunnel

# Or specify custom URL
godman tunnel http://127.0.0.1:8000

# Output will show public URL like:
# https://random-subdomain.trycloudflare.com
```

---

## Background Services

### Daemon Mode

Start background daemon (runs queue worker + scheduler):
```bash
godman daemon start
```

Check daemon status:
```bash
godman daemon status

# Output:
# Daemon: running
# PID: 12345
# Uptime: 2h 34m
# Queue depth: 3
# Next scheduled run: 2024-01-15 09:00:00
```

Stop daemon:
```bash
godman daemon stop
```

### Queue Operations

#### CLI Management
```bash
# Add job to queue
godman queue enqueue "Process receipt: scans/receipt_001.jpg"

# Check queue status
godman queue status

# Output:
# Jobs pending: 5
# Jobs running: 1
# Jobs completed: 142
# Jobs failed: 3
```

#### Programmatic Usage
```python
from godman_ai.queue import JobQueue

queue = JobQueue()
queue.enqueue({"task": "process receipt", "file": "receipt.jpg"}, priority=1)
job = queue.dequeue()
```

### Scheduler Operations

#### Add Scheduled Tasks
```bash
# Run daily at 9 AM
godman schedule add "0 9 * * *" "godman agent 'Generate daily report'"

# Run every 30 minutes
godman schedule add "*/30 * * * *" "godman agent 'Check pool emails'"

# Run on weekdays at 6 PM
godman schedule add "0 18 * * 1-5" "godman agent 'Send expense summary'"
```

#### List Schedules
```bash
godman schedule list

# Output:
# ID  Cron          Command                                  Enabled
# 1   0 9 * * *     godman agent 'Generate daily report'    Yes
# 2   */30 * * * *  godman agent 'Check pool emails'        Yes
```

#### Remove Schedule
```bash
godman schedule remove <id>
```

#### Cron Expression Reference
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, Sunday=0)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)

Examples:
0 9 * * *       - 9:00 AM daily
*/15 * * * *    - Every 15 minutes
0 */2 * * *     - Every 2 hours
0 9 * * 1       - 9 AM every Monday
0 0 1 * *       - Midnight on 1st of month
```

---

## System Monitoring

### Health Check
```bash
godman health

# Output:
{
  "queue_depth": 3,
  "worker_active": true,
  "scheduler_next_run": "2024-01-15T09:00:00",
  "memory_episodes": 142,
  "vector_count": 1523,
  "models_loaded": ["llama-7b", "gpt-4"],
  "recent_failures": 2,
  "uptime_hours": 47.3,
  "tool_usage": {
    "ocr": 87,
    "sheets": 52,
    "vision": 34
  }
}
```

### View Global State
```bash
godman os state

# Shows:
# - Settings snapshot
# - Loaded tools
# - Active models
# - Runtime statistics
```

### Logs

Logs are stored in `.godman/logs/`:
```bash
# View recent logs
tail -f .godman/logs/godman.log

# Search for errors
grep ERROR .godman/logs/godman.log

# View agent execution logs
cat .godman/logs/agent_loop.log
```

---

## Memory Management

### Episodic Memory
```bash
# Add episode manually (usually done automatically)
curl -X POST http://127.0.0.1:8000/memory/add \
  -H "Authorization: Bearer $GODMAN_API_TOKEN" \
  -d '{"text": "Processed receipt", "metadata": {"vendor": "Target"}}'

# Search episodes
curl -X POST http://127.0.0.1:8000/memory/search \
  -d '{"query": "target receipt", "top_k": 5}'
```

### Vector Store
Location: `.godman/state/vector_store/`

```bash
# Check vector store size
ls -lh .godman/state/vector_store/

# Clear vector store (caution: deletes all semantic search data)
rm -rf .godman/state/vector_store/
```

### Working Memory
Working memory is ephemeral and cleared between agent runs. No manual management needed.

---

## Tool Management

### List Available Tools
```bash
godman tools list

# Output:
# - ocr: OCR tool for text extraction
# - vision: Image analysis tool
# - sheets: Google Sheets integration
# - trello: Trello card management
# - drive: Google Drive file operations
# - reports: Generate summaries and reports
```

### Tool Usage Stats
```bash
godman health | grep tool_usage

# Shows how many times each tool has been called
```

---

## Model Management

### List Models
```bash
godman models list

# Output:
# Cloud Models:
#   - gpt-4
#   - gpt-4o
#   - gpt-4o-mini
# 
# Local Models:
#   - llama-7b (7B parameters, 4.2 GB)
#   - mistral-7b-instruct (7B parameters, 4.1 GB)
```

### Run Model Directly
```bash
# Run inference with specific model
godman models run "Explain quantum computing" --model llama-7b

# Use cloud model
godman models run "Analyze this contract" --model gpt-4
```

### Model Router Config
Edit settings or set environment variables:
```bash
export PREFER_LOCAL_MODELS=true  # Prefer local over cloud
export FALLBACK_TO_CLOUD=true    # Use cloud if local fails
```

See [models.md](models.md) for detailed model configuration.

---

## Troubleshooting

### Command Not Found
```bash
# Ensure installation completed
pip install -e .

# Check PATH
which godman

# If not found, add to PATH:
export PATH="$HOME/.local/bin:$PATH"
```

### API Token Errors
```bash
# Error: "401 Unauthorized"
# Fix: Set GODMAN_API_TOKEN
export GODMAN_API_TOKEN="your-token"

# Verify it's set
echo $GODMAN_API_TOKEN
```

### OpenAI API Errors
```bash
# Error: "OpenAI API key not found"
# Fix: Set OPENAI_API_KEY
export OPENAI_API_KEY="sk-..."

# Or use local models exclusively
export PREFER_LOCAL_MODELS=true
```

### Queue Not Processing
```bash
# Check daemon status
godman daemon status

# If not running, start it
godman daemon start

# Check logs
tail -f .godman/logs/daemon.log
```

### Memory Issues
```bash
# Clear old episodes (keeps last 1000)
python -c "from godman_ai.memory import EpisodicMemory; EpisodicMemory().prune(max_episodes=1000)"

# Reset vector store
rm -rf .godman/state/vector_store/
```

### Plugin Load Failures
```bash
# Check logs for plugin errors
grep "plugin" .godman/logs/godman.log

# List loaded plugins
godman os state | grep plugins

# Remove bad plugin
rm godman_ai/plugins/bad_plugin.py
```

---

## Performance Tuning

### Startup Time
- Most imports are lazy - startup should be <1s
- If slow, check for plugins with heavy top-level imports

### Execution Speed
- Use local models for simple tasks (faster, no API calls)
- Use cloud models for complex reasoning
- Adjust `max_workers` in queue settings for parallelism

### Memory Usage
- Vector store grows over time - prune periodically
- Episodic memory stored in SQLite - vacuum occasionally:
  ```bash
  sqlite3 .godman/state/memory.db "VACUUM;"
  ```

### Disk Space
- Logs rotate automatically (keeps 7 days)
- Vector store can be cleared safely
- Episodic memory can be pruned by date

---

## Production Deployment

### Systemd Service (Linux)
```ini
# /etc/systemd/system/godman.service
[Unit]
Description=GodmanAI Daemon
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/godman-lab
Environment="OPENAI_API_KEY=sk-..."
Environment="GODMAN_API_TOKEN=your-token"
ExecStart=/path/to/venv/bin/godman daemon start
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable godman
sudo systemctl start godman
sudo systemctl status godman
```

### macOS launchd
```xml
<!-- ~/Library/LaunchAgents/com.godman.daemon.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.godman.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/godman</string>
        <string>daemon</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/godman.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/godman.out</string>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.godman.daemon.plist
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

ENV GODMAN_API_TOKEN=your-token
EXPOSE 8000

CMD ["godman", "server"]
```

Build and run:
```bash
docker build -t godman .
docker run -p 8000:8000 -v $(pwd)/.godman:/app/.godman godman
```

---

## Backup & Restore

### What to Backup
- `.godman/state/` - Queue, memory, vector store
- `.env` - Configuration
- `godman_ai/plugins/` - Custom plugins
- `.godman/installed_skills.json` - Skill registry

### Backup Script
```bash
#!/bin/bash
tar -czf godman-backup-$(date +%Y%m%d).tar.gz \
  .godman/state/ \
  .env \
  godman_ai/plugins/ \
  .godman/installed_skills.json
```

### Restore
```bash
tar -xzf godman-backup-20240115.tar.gz
```

---

## Next Steps

- [Skills Development](skills.md) - Build custom tools and plugins
- [Model Configuration](models.md) - Set up local LLMs
- [Architecture](architecture.md) - Understand internals
