# LLM Infrastructure Management Suite

Complete installation, monitoring, and health check system for Godman AI's LLM infrastructure.

## Components

### 1. Auto-Installer (`installer.py`)
Automatically installs all required LLM models and validates the system.

### 2. Health Monitor (`monitor.py`)
Cron-safe monitoring daemon that periodically checks LLM health.

### 3. Menu Bar Notifier (`menu_status.py`)
macOS menu bar integration with periodic status notifications.

### 4. Health CLI (`cli/godman/health.py`)
CLI commands for health checks and monitoring setup.

---

## Quick Start

### Install All Models

```bash
godman install
```

This will:
1. Check for installed models
2. Pull any missing models:
   - `deepseek-r1:14b`
   - `phi4:14b`
   - `llama3.1:8b`
   - `qwen2.5:7b`
3. Run full health check
4. Display results

### Run Health Check

```bash
godman health check
```

Performs comprehensive diagnostics on:
- Ollama server status
- Model availability
- Model performance
- Router functionality

### Setup Monitoring

```bash
# Preview cron job
godman health monitor --every 5

# Install cron job
godman health monitor --every 5 --install
```

### Run Menu Bar Monitor

```bash
python3 godman_ai/diagnostics/menu_status.py
```

Displays notifications every 5 minutes with LLM status.

---

## CLI Commands

### `godman install`

Auto-install all required models and run health check.

**Output:**
```
Godman AI — Auto Installer
--------------------------------------------------

→ Checking deepseek-r1:14b...
  ✓ deepseek-r1:14b already installed

→ Checking phi4:14b...
  Pulling phi4:14b...
  ✓ phi4:14b installed successfully

Model installation complete.

Running health check...

[Health check output...]

╭───────────────────────────────────────────╮
│ ✓ Installation OK — all systems ready    │
╰───────────────────────────────────────────╯
```

**Exit Codes:**
- `0` - All systems operational
- `1` - Installation failed or health check failed

---

### `godman health check`

Run full LLM infrastructure health check.

**Checks:**
- Ollama server running at `127.0.0.1:11434`
- All 4 models installed
- Model response times and tokens/sec
- Tool router functionality

**Output:**
```
Starting LLM Health Check...

→ Stopping existing Ollama processes...
✓ Stopped

→ Starting Ollama server...
✓ Server online at http://127.0.0.1:11434

→ Checking installed models...
✓ 4/4 models installed

→ Testing model performance...
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Model           ┃ Status ┃ Speed (tok/s)┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ deepseek-r1:14b │   ✓    │         15.23│
│ phi4:14b        │   ✓    │         18.45│
│ llama3.1:8b     │   ✓    │         25.67│
│ qwen2.5:7b      │   ✓    │         20.12│
└─────────────────┴────────┴──────────────┘

→ Testing tool router...
✓ Router returned: default_tool

✓ All systems operational
```

---

### `godman health monitor`

Setup periodic health monitoring via cron.

**Options:**
- `--every N` - Check every N minutes (default: 5)
- `--install` - Actually install the cron job (default: preview only)

**Examples:**

```bash
# Preview cron job (every 5 min)
godman health monitor

# Install check every 3 minutes
godman health monitor --every 3 --install

# Check every 10 minutes
godman health monitor --every 10 --install
```

**Cron Job Format:**
```
*/5 * * * * /usr/bin/python3 /path/to/godman_ai/diagnostics/monitor.py
```

**Logs Location:**
`~/godman-raw/monitor/llm_health.log`

**Log Format:**
```
2025-12-09T02:30:00 | {"ollama_online": true, "models_available": {...}, ...}
```

---

## Monitoring Scripts

### Cron Monitor (`monitor.py`)

**Purpose:** Cron-safe health monitoring with logging and notifications.

**Features:**
- Suppresses Rich color output for cron
- Logs results to `~/godman-raw/monitor/llm_health.log`
- Sends macOS notifications on failure
- Returns exit code 0/1 for cron job status

**Direct Usage:**
```bash
python3 godman_ai/diagnostics/monitor.py
```

**Manual Cron Setup:**
```bash
# Edit crontab
crontab -e

# Add line (check every 5 minutes):
*/5 * * * * /usr/bin/python3 ~/Desktop/godman-lab/godman_ai/diagnostics/monitor.py
```

---

### Menu Bar Notifier (`menu_status.py`)

**Purpose:** Long-running daemon with macOS notifications.

**Features:**
- Runs continuously in background
- Checks health every 5 minutes
- Displays notification with status
- Logs to `~/godman-raw/monitor/menu_status.json`

**Usage:**
```bash
python3 godman_ai/diagnostics/menu_status.py
```

**Output:**
```
Starting LLM Menu Bar Monitor...
Press Ctrl+C to stop

[Iteration 1] Running health check...
Status: OK | Models: 4/4
Sleeping 5 minutes...
```

**Notification Format:**
```
Title: LLM Status
Message: OK | Models: 4/4
```

**Background Daemon:**
```bash
# Run in background
nohup python3 godman_ai/diagnostics/menu_status.py > /dev/null 2>&1 &

# Stop
pkill -f menu_status.py
```

---

## Auto-Installer (`installer.py`)

**Purpose:** One-command installation of all required models.

**Features:**
- Checks which models are installed
- Pulls missing models automatically
- Shows progress for downloads
- Runs health check after installation
- Returns structured results

**Direct Usage:**
```bash
python3 godman_ai/diagnostics/installer.py
```

**Programmatic Usage:**
```python
from godman_ai.diagnostics.installer import install_all

result = install_all()

if result["all_systems_pass"]:
    print("✓ Ready to use")
else:
    print("✗ Some issues detected")
```

**Installation Process:**

1. Check each model with `ollama list`
2. If missing, run `ollama pull <model>`
3. Show progress indicator
4. After all models, run health check
5. Display results panel

---

## Integration Examples

### With CI/CD

```yaml
# GitHub Actions
- name: Install LLMs
  run: godman install

- name: Health Check
  run: godman health check
```

### With Systemd (Linux)

```ini
[Unit]
Description=LLM Health Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/menu_status.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### With Python

```python
from godman_ai.diagnostics.llm_health import run_llm_health_check

# Check before heavy LLM usage
result = run_llm_health_check()

if not result["all_systems_pass"]:
    # Reinstall or alert
    from godman_ai.diagnostics.installer import install_all
    install_all()
```

---

## Notifications

### macOS Notifications

All monitoring tools use `osascript` to send native macOS notifications.

**On Failure:**
```
Title: GodmanAI
Message: LLM Health FAIL
```

**Status Update:**
```
Title: LLM Status
Message: OK | Models: 4/4
```

### Slack/Email Integration

Extend `monitor.py`:

```python
def send_alert(result):
    if not result["all_systems_pass"]:
        # Send Slack webhook
        requests.post(SLACK_WEBHOOK, json={
            "text": f"LLM Health Failed: {result}"
        })

# In monitor_loop():
if not result["all_systems_pass"]:
    send_alert(result)
```

---

## Log Files

### Health Check Log
**Location:** `~/godman-raw/monitor/llm_health.log`

**Format:**
```
2025-12-09T02:30:00 | {"ollama_online": true, ...}
2025-12-09T02:35:00 | {"ollama_online": true, ...}
```

### Menu Status Log
**Location:** `~/godman-raw/monitor/menu_status.json`

**Content:** Latest health check result (JSON)

---

## Troubleshooting

### Installation Fails

```bash
# Check Ollama is installed
ollama --version

# Check Ollama is running
curl http://127.0.0.1:11434/api/tags

# Manually pull a model
ollama pull llama3.1:8b
```

### Cron Job Not Running

```bash
# Check cron logs (macOS)
log show --predicate 'process == "cron"' --last 1h

# Verify crontab
crontab -l

# Test script manually
python3 godman_ai/diagnostics/monitor.py
```

### Notifications Not Showing

```bash
# Check System Preferences > Notifications
# Ensure Terminal/Python has notification permissions

# Test notification manually
osascript -e 'display notification "Test" with title "Test"'
```

---

## File Structure

```
godman_ai/diagnostics/
├── __init__.py
├── llm_health.py          # Core health check function
├── installer.py           # Auto-installer
├── monitor.py             # Cron-safe monitor
├── menu_status.py         # Menu bar notifier
└── README.md

cli/godman/
├── health.py              # Health CLI commands
└── main.py                # Main CLI (includes install command)

~/godman-raw/monitor/
├── llm_health.log         # Monitor logs
└── menu_status.json       # Latest status
```

---

## Performance

- **Install:** 5-15 minutes per model (depending on download speed)
- **Health Check:** 20-30 seconds total
- **Monitor Check:** 20-30 seconds per iteration
- **Menu Bar Check:** 20-30 seconds per iteration (every 5 min)

---

## Dependencies

- `rich` - Terminal formatting
- `typer` - CLI framework
- `subprocess` - Process management (stdlib)
- `ollama` - CLI tool (must be installed)

---

## Platform Support

- **macOS:** Full support (all features including notifications)
- **Linux:** Full support (modify notifications for Linux)
- **Windows:** Partial support (process management may need changes)
