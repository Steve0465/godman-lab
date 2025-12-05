# GodmanAI Installation Guide

## Quick Install (Core Only)

```bash
pip install -e .
```

This installs the core CLI with basic agent functionality.

## Optional Features

### Install Service Layer (API Server + Dashboard)
```bash
pip install -e ".[service]"
```

### Install Vision & OCR
```bash
pip install -e ".[vision]"
```

### Install Memory & Vector Store
```bash
pip install -e ".[memory]"
```

### Install Everything
```bash
pip install -e ".[all]"
```

## Configuration

### Required Environment Variables

```bash
# OpenAI API Key (for agent planning and reasoning)
export OPENAI_API_KEY="sk-..."

# Optional: API Security Token
export GODMAN_API_TOKEN="your-secret-token"

# Optional: Local Models Directory
export GODMAN_MODELS_DIR="/path/to/models"
```

Add to `~/.zshrc` or `~/.bashrc` for persistence.

### Create Config Directory

```bash
mkdir -p ~/.godman/{state,logs,registry,tmp}
```

## Verify Installation

```bash
# Check CLI is available
godman --help

# Check system health
godman os-health

# View available skills
godman store-list
```

## Running the System

### Run a simple task
```bash
godman run "Analyze this text"
```

### Run full agent loop
```bash
godman agent "Process my receipts"
```

### Start API server
```bash
godman server
```

### Start background daemon
```bash
godman daemon-start
```

## Troubleshooting

### FastAPI not installed
If you see "FastAPI not installed" errors:
```bash
pip install -e ".[service]"
```

### OCR not working
Install vision dependencies:
```bash
pip install -e ".[vision]"
# Also install system tesseract:
# macOS: brew install tesseract
# Ubuntu: sudo apt install tesseract-ocr
```

### Tests failing
Install dev dependencies:
```bash
pip install -e ".[dev]"
pytest tests/
```
