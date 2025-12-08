# WebUI Presets Feature

## Overview
Three model presets have been added to the WebUI for specialized AI workflows:

### Presets

#### 1. Overmind
- **Model**: `deepseek-r1:14b`
- **Purpose**: Strategic reasoning engine
- **Capabilities**: 
  - Break down problems into steps
  - Uncover hidden dependencies
  - Design workflows
  - Detect required tools
  - Plan multi-stage operations
- **Output**: Structured plans with full reasoning

#### 2. Forge
- **Model**: `qwen2.5-coder:7b`
- **Purpose**: Execution engineer
- **Capabilities**:
  - Convert high-level plans into working code
  - Generate scripts, automations, pipelines
  - Output complete runnable code
  - Include file paths and dependencies
- **Output**: Ready-to-run code with setup instructions

#### 3. Handler
- **Model**: `gorilla-openfunctions-v2` (froehnerel/v2-q5_K_M)
- **Purpose**: Function calling interface
- **Capabilities**:
  - Convert user requests into structured function calls
  - Output JSON-formatted function calls
- **Output**: JSON only, no additional explanation

## API Endpoints

### List all presets
```
GET /api/presets
```

Response:
```json
{
  "presets": [
    {
      "id": "overmind",
      "name": "Overmind",
      "model": "deepseek-r1:14b",
      "prompt": "..."
    },
    ...
  ]
}
```

### Get specific preset
```
GET /api/presets/{name}
```

Example: `/api/presets/Overmind`

Response:
```json
{
  "id": "overmind",
  "name": "Overmind",
  "model": "deepseek-r1:14b",
  "prompt": "You are DeepSeek-R1 acting as my strategic reasoning engine..."
}
```

## File Structure
```
godman_ai/
├── models/
│   ├── __init__.py
│   └── preset.py          # Preset dataclass model
├── config/
│   └── presets.py         # Preset definitions and helpers
└── server/
    └── api.py             # FastAPI endpoints
```

## Usage

### Python
```python
from godman_ai.config.presets import get_all_presets, get_preset_by_name

# Get all presets
presets = get_all_presets()

# Get specific preset
overmind = get_preset_by_name("Overmind")
```

### WebUI Integration
The presets are available via REST API and can be integrated into any frontend:
1. Fetch presets from `/api/presets`
2. Display as dropdown or buttons
3. Load selected preset's model and prompt into chat interface

## Testing
Run the test scripts:
```bash
python3 test_presets.py  # Test preset configuration
python3 test_api.py      # Test API endpoints
```

## Branch
Created on branch: `feature/webui-presets`
