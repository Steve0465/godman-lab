# Gemini Studio System Instructions - Godman-Lab AI Platform

**Version:** 1.0  
**Last Updated:** December 2025  
**Purpose:** System instructions for Google AI Studio when working on Godman-Lab projects

---

## Platform Overview

You are assisting with the **Godman-Lab** platform - an async orchestration system for AI workflows combining:
- Multi-agent coordination and routing
- Tool execution with function/CLI registration
- Distributed workflow engine with checkpointing
- Vision AI integration (GPT-4V, Claude, Gemini)
- Specialized integrations (tax receipts, Trello, AT&T billing, pool parts)

---

## Core Architecture Principles

### 1. Async-First Design
- All workflows, orchestrators, and distributed execution are async
- Use `async def` for workflow steps and agent actions
- Sync functions are automatically wrapped with `asyncio.to_thread`
- Always `await` workflow execution: `await workflow.run(context)`

### 2. Modular Structure
```
godman_ai/              # Core platform
├── orchestrator/       # Multi-agent coordination
├── workflows/          # Async workflow engine + DSL
├── models/            # Model routing and presets
├── tools/             # Tool registry and execution
├── capabilities/      # Capability mesh
├── skills/           # Reusable skill packages
├── plugins/          # Plugin discovery
└── server/           # FastAPI server + WebUI

libs/                  # Specialized integrations
├── tool_runner.py     # Decorator-based tool registration
├── tax_receipts_processor.py
├── trello/
├── att_scraper.py
└── security/
```

### 3. Public API Exports
All modules expose clean public APIs via `__all__` in `__init__.py`:
```python
from godman_ai import LocalModelRouter, TaskType, select_model
from godman_ai.orchestrator import Orchestrator, ToolRouter
from godman_ai.workflows import Workflow, Step, load_workflow_from_yaml
from godman_ai.tools import ToolRunner, register_tool
```

---

## Code Conventions

### Python Style

**Type Hints Required:**
```python
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

async def process_receipt(
    path: Path,
    category_rules: Dict[str, List[str]]
) -> Dict[str, Any]:
    """Process receipt with OCR and categorization.
    
    Args:
        path: Path to receipt file
        category_rules: Mapping of categories to keyword lists
        
    Returns:
        Dictionary with vendor, amount, category, confidence
        
    Raises:
        WorkflowError: If processing fails
    """
    pass
```

**Async Patterns:**
```python
# Good: Async workflow step
async def fetch_data(ctx: Context) -> Dict[str, Any]:
    result = await external_api.get()
    return {"data": result}

# Good: Sync step (auto-wrapped)
def validate_data(ctx: Context) -> bool:
    data = ctx.get("fetch_data")
    return len(data) > 0
```

**Error Handling:**
```python
from godman_ai.workflows import WorkflowError
from godman_ai.tools.vision import VisionError

try:
    result = await workflow.run(context)
except WorkflowError as e:
    logger.error(f"Workflow failed at step: {e.step_name}")
    # Handle gracefully
except VisionError as e:
    logger.error(f"Vision analysis failed: {e}")
    # Fallback to mock data
```

### Tool Registration

Use `@tool` decorator from `libs.tool_runner`:

```python
from libs.tool_runner import tool, runner

# Function-based tool
@tool(
    schema={"x": int, "y": int},
    description="Add two numbers"
)
def add(x: int, y: int) -> Dict[str, int]:
    return {"sum": x + y}

# CLI-based tool
@tool(
    schema={"path": str},
    command="ls -la {path}",
    description="List files in directory"
)
def list_files(path: str):
    pass

# Access registered tools
result = runner.run("add", {"x": 5, "y": 3})
```

### Workflow Construction

```python
from godman_ai.workflows import Workflow, Step, Context

async def fetch(ctx: Context) -> Dict[str, Any]:
    return {"items": [1, 2, 3]}

def process(ctx: Context) -> Dict[str, int]:
    items = ctx.get("fetch")["items"]
    return {"count": len(items)}

workflow = Workflow(
    steps=[
        Step("fetch", fetch),
        Step("process", process)
    ],
    before_all=lambda ctx: ctx.set("started", True),
    after_all=lambda ctx: logger.info("Complete"),
    on_error=lambda ctx: ctx.set("failed", True)
)

context = await workflow.run(Context())
result = context.get("process")
```

### Model Presets

Access specialized model presets for different tasks:

```python
from godman_ai.config.presets import get_preset_by_name

# Strategic reasoning
overmind = get_preset_by_name("Overmind")  # deepseek-r1:14b

# Code generation
forge = get_preset_by_name("Forge")  # qwen2.5-coder:7b

# Function calling
handler = get_preset_by_name("Handler")  # gorilla-openfunctions-v2

# Use preset
response = model_client.generate(
    prompt="Your task",
    model=overmind.model,
    temperature=overmind.temperature
)
```

---

## Vision AI Integration

### Supported Providers

```python
from godman_ai.tools.vision import VisionAnalyzer, VisionError

# OpenAI GPT-4V (best for complex analysis)
analyzer = VisionAnalyzer(provider="openai", model="gpt-4o")

# Anthropic Claude 3 (cost-effective)
analyzer = VisionAnalyzer(provider="claude", model="claude-3-sonnet-20240229")

# Coming: Google Gemini (native video support)
# analyzer = VisionAnalyzer(provider="gemini", model="gemini-1.5-pro")
```

### Image Analysis Patterns

```python
# Generic analysis
result = analyzer.analyze(
    image="pool_part.jpg",
    prompt="Identify this pool part. Return JSON with part_number, manufacturer, confidence.",
    max_tokens=1000,
    temperature=0.2
)

# Specialized pool part identification
result = analyzer.analyze_pool_part(
    image="pump_housing.jpg",
    include_alternatives=True
)

# Returns:
{
    "part_number": "SPX1091Z2",
    "manufacturer": "Hayward",
    "description": "Super Pump Housing Assembly",
    "confidence": 0.95,
    "alternatives": [...],
    "equivalents": [...]
}
```

### Error Handling

```python
try:
    result = analyzer.analyze_pool_part(image)
except VisionError as e:
    logger.error(f"Vision analysis failed: {e}")
    # Fallback to mock data or manual entry
    result = {
        "part_number": "UNKNOWN",
        "confidence": 0.0,
        "description": "Manual identification required"
    }
```

### Video Support (Gemini)

When adding Gemini video support:

```python
# Frame extraction approach
import cv2

def extract_frames(video_path: Path, interval_seconds: int = 5) -> List[bytes]:
    """Extract frames from video at regular intervals."""
    cap = cv2.VideoCapture(str(video_path))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frames = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if frame_num % (fps * interval_seconds) == 0:
            _, buffer = cv2.imencode('.jpg', frame)
            frames.append(buffer.tobytes())
    
    cap.release()
    return frames

# Analyze each frame
for frame in extract_frames(video_path):
    result = analyzer.analyze(frame, "Describe equipment visible")
```

```python
# Native video with Gemini (future)
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')

video = genai.upload_file(str(video_path))
result = model.generate_content([
    "Analyze this pool inspection video. Identify equipment, note conditions.",
    video
])
```

---

## Testing Patterns

### Workflow Tests

```python
import pytest
import asyncio
from godman_ai.workflows import Workflow, Step, Context, WorkflowError

@pytest.mark.asyncio
async def test_workflow_execution():
    """Test basic workflow execution."""
    executed = []
    
    def step1(ctx): executed.append("step1")
    def step2(ctx): executed.append("step2")
    
    workflow = Workflow([Step("s1", step1), Step("s2", step2)])
    await workflow.run(Context())
    
    assert executed == ["step1", "step2"]

@pytest.mark.asyncio
async def test_workflow_error_handling():
    """Test error propagation."""
    def failing(ctx): raise ValueError("boom")
    
    workflow = Workflow([Step("fail", failing)])
    
    with pytest.raises(WorkflowError):
        await workflow.run(Context())
```

### Tool Tests

```python
from libs.tool_runner import ToolRunner

def test_tool_execution():
    """Test tool registration and execution."""
    runner = ToolRunner()
    
    @runner.tool(schema={"x": int, "y": int})
    def add(x: int, y: int):
        return {"sum": x + y}
    
    result = runner.run("add", {"x": 5, "y": 3})
    
    assert result["status"] == "success"
    assert result["result"]["sum"] == 8
```

### Vision Tests (with mocking)

```python
from unittest.mock import patch, MagicMock
from godman_ai.tools.vision import VisionAnalyzer

def test_vision_analysis_with_mock():
    """Test vision analyzer with mocked API."""
    with patch('requests.post') as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{
                    "message": {
                        "content": '{"part_number": "TEST123", "confidence": 0.95}'
                    }
                }]
            }
        )
        
        analyzer = VisionAnalyzer(provider="openai")
        result = analyzer.analyze_pool_part("test.jpg")
        
        assert result["part_number"] == "TEST123"
        assert result["confidence"] == 0.95
```

---

## File Organization

### Naming Conventions

**Python Files:**
- Modules: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`

**Test Files:**
- Mirror source structure: `tests/workflows/test_engine.py` for `godman_ai/workflows/engine.py`
- Test functions: `test_<feature>_<scenario>()`

### Directory Structure

```
godman-lab/
├── godman_ai/              # Core package
│   ├── __init__.py        # Public API exports
│   ├── orchestrator/
│   ├── workflows/
│   ├── tools/
│   └── config/
├── libs/                   # Integrations
│   ├── tool_runner.py
│   ├── tax/
│   └── trello/
├── tests/                  # Test suite
│   ├── conftest.py        # Pytest fixtures
│   └── workflows/
├── examples/               # Demo scripts
├── docs/                   # Documentation
├── requirements.txt        # Dependencies
├── pyproject.toml         # Package config
└── *.md                   # Project docs
```

---

## Logging and Debugging

### Logging Setup

```python
import logging
from pathlib import Path

# Get logger
logger = logging.getLogger(__name__)

# Configure (done in main modules)
log_dir = Path(os.environ.get("GODMAN_LOG_DIR", "logs"))
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)

# Use in code
logger.info("Workflow started")
logger.error(f"Step failed: {e}", exc_info=True)
logger.debug(f"Context state: {ctx.data}")
```

### Environment Variables

```bash
# Core settings
export GODMAN_ENV=production  # or development
export GODMAN_LOG_DIR=logs/

# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."

# Integration keys
export TRELLO_API_KEY="..."
export TRELLO_TOKEN="..."
```

---

## Integration Patterns

### Tax Receipt Processing

```python
from libs.tax_receipts_processor import extract_text_from_pdf, extract_vendor
from libs.tax_category_rules import classify_receipt

# Extract and classify
text = extract_text_from_pdf(Path("receipt.pdf"))
vendor = extract_vendor(text)
category = classify_receipt(vendor, text, amount=100.0)

print(f"Vendor: {vendor}")
print(f"Category: {category.category}")
print(f"Deductibility: {category.deductibility_rate:.0%}")
```

### Trello Automation

```python
from libs.trello_normalizer import normalize_trello_export

# Normalize for O(1) lookups
normalized = normalize_trello_export(raw_export)

# Fast access
complete_cards = normalized['cards_by_list_name']['Complete']
card = normalized['cards_by_id']['card_123']
```

### AT&T Billing

```python
from libs.att_scraper import ATTClient

client = ATTClient(headless=False)
client.login()  # Uses saved cookies
bills = client.get_bills()
client.close()
```

---

## Common Tasks

### Adding a New Tool

1. Define with `@tool` decorator
2. Specify schema with types
3. Return dict for structured output
4. Auto-registers on import

```python
from libs.tool_runner import tool

@tool(schema={"text": str, "max_length": int}, description="Truncate text")
def truncate(text: str, max_length: int) -> Dict[str, str]:
    return {"result": text[:max_length]}
```

### Creating a Workflow

1. Import workflow components
2. Define step actions (sync/async)
3. Chain with shared context
4. Add lifecycle hooks

```python
from godman_ai.workflows import Workflow, Step, Context

async def fetch(ctx): return {"data": [1, 2, 3]}
def process(ctx): return {"count": len(ctx.get("fetch")["data"])}

workflow = Workflow([Step("fetch", fetch), Step("process", process)])
result = await workflow.run(Context())
```

### Adding a Model Preset

Edit `godman_ai/config/presets.py`:

```python
Preset(
    name="CustomAnalyzer",
    model="mixtral-8x7b",
    temperature=0.3,
    max_tokens=2048,
    system_prompt="You are a specialized analyzer...",
    description="Custom analysis preset"
)
```

---

## Response Guidelines

### When Generating Code

1. **Follow conventions** above strictly
2. **Include type hints** for all functions
3. **Add docstrings** with Args, Returns, Raises
4. **Provide tests** using pytest patterns
5. **Handle errors** with custom exceptions
6. **Use async** for workflows and I/O operations
7. **Log appropriately** with Python logging

### When Explaining

1. **Be concise** - code speaks
2. **Show examples** from actual codebase
3. **Reference files** - "See `godman_ai/workflows/engine.py`"
4. **Link patterns** - "Similar to PartIdentifierWorkflow"

### When Debugging

1. **Check logs** first - all components log to `GODMAN_LOG_DIR`
2. **Verify environment** - API keys, paths, venv activation
3. **Run tests** - `pytest tests/ -v`
4. **Reproduce** - minimal example that shows issue

---

## Current Focus: Video Analysis with Gemini

### Goals

1. Add Google Gemini as vision provider
2. Support native video analysis (not just frames)
3. Maintain compatibility with existing VisionAnalyzer API
4. Handle video files (MP4, MOV, AVI)
5. Provide frame extraction fallback

### Implementation Checklist

- [ ] Add `gemini` provider to VisionAnalyzer
- [ ] Install `google-generativeai` package
- [ ] Add video upload/analysis methods
- [ ] Frame extraction utility (OpenCV)
- [ ] Update tests with Gemini mocks
- [ ] Update documentation
- [ ] Add video examples to `examples/`

### API Design (Draft)

```python
# Native video analysis
analyzer = VisionAnalyzer(provider="gemini")
result = analyzer.analyze_video(
    video="pool_inspection.mp4",
    prompt="Identify all pool equipment and note conditions"
)

# Frame extraction fallback
frames = analyzer.extract_frames(video="video.mp4", interval=5)
for frame in frames:
    result = analyzer.analyze(frame, prompt)
```

---

## Quick Reference

**Start server:** `./START_GODMAN_SERVER.sh`  
**Run tests:** `pytest tests/ -v`  
**List tools:** `godman tool list`  
**Execute tool:** `godman tool run -n <name> -p '<json>'`  
**Build package:** `python3 -m build`

**Key files:**
- API server: `godman_ai/server/api.py`
- Tool runner: `libs/tool_runner.py`
- Workflow engine: `godman_ai/workflows/engine.py`
- Vision tools: `godman_ai/tools/vision.py`
- Presets: `godman_ai/config/presets.py`

---

**Last updated:** December 18, 2025  
**Platform version:** 1.0+  
**Python requirement:** ≥3.12
