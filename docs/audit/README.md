# Audit Snapshot Documentation

## Overview

The audit snapshot system captures a comprehensive, point-in-time snapshot of the godman-lab repository architecture.

## Usage

```bash
# From repository root
python3 scripts/audit_snapshot.py

# Custom output directory  
python3 scripts/audit_snapshot.py --out-dir custom/path

# Adjust max lines per search section
python3 scripts/audit_snapshot.py --max-lines-per-section 300
```

## Output Files

- **snapshot.txt** - Human-readable text format
- **snapshot.json** - Structured JSON for programmatic analysis

## Using with Codex Runner

### Review Current State
```bash
PYTHONPATH=. python cli/codex_runner.py "Read docs/audit/snapshot.txt and summarize the architecture"
```

### Identify Gaps
```bash
PYTHONPATH=. python cli/codex_runner.py "Analyze docs/audit/snapshot.json and list critical gaps"
```

### Plan Implementation
```bash
PYTHONPATH=. python cli/codex_runner.py "Based on docs/audit/snapshot.txt, create implementation plan for orchestrator"
```

### Generate Diagrams
```bash
PYTHONPATH=. python cli/codex_runner.py "Using docs/audit/snapshot.json, generate Mermaid diagram of tool systems"
```

### Compare Snapshots
```bash
python3 scripts/audit_snapshot.py --out-dir docs/audit/baseline
# Make changes...
python3 scripts/audit_snapshot.py --out-dir docs/audit/current
PYTHONPATH=. python cli/codex_runner.py "Compare docs/audit/baseline and docs/audit/current snapshots"
```

## Requirements

- Python 3.8+
- Git
- ripgrep (optional) - `brew install ripgrep`
