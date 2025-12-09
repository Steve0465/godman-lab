# LLM Health Check Diagnostics

Comprehensive health check system for the local Ollama LLM infrastructure.

## Overview

The `run_llm_health_check()` function performs a full diagnostic test of the LLM stack, including:
- Ollama server management
- Model availability verification
- Performance benchmarking
- Router integration testing

## Function Signature

```python
def run_llm_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for Ollama LLM infrastructure.
    
    Returns:
        Dictionary with health check results
    """
```

## Return Schema

```python
{
    "ollama_online": bool,              # Server reachable at 127.0.0.1:11434
    "models_available": {                # Per-model installation status
        "deepseek-r1:14b": bool,
        "phi4:14b": bool,
        "llama3.1:8b": bool,
        "qwen2.5:7b": bool
    },
    "model_speeds": {                    # Tokens/sec for each model
        "deepseek-r1:14b": 15.23,
        "phi4:14b": 18.45,
        "llama3.1:8b": 25.67,
        "qwen2.5:7b": 20.12
    },
    "router_selected": str,              # Tool router test result
    "all_systems_pass": bool,            # Overall health status
    "error": str                         # Optional error message
}
```

## Health Check Process

### 1. Process Management
- Kills all existing `ollama` processes using `SIGTERM`
- Waits 2 seconds for clean shutdown
- Starts fresh `ollama serve` in background

### 2. Server Availability
- Polls `http://127.0.0.1:11434/api/tags` every 1 second
- Maximum wait time: 30 seconds
- Sets `ollama_online: true` when reachable

### 3. Model Verification
- Queries `/api/tags` for installed models
- Checks presence of all 4 required models
- Records availability in `models_available` dict

### 4. Performance Testing
- For each installed model:
  - Sends tiny prompt: "Say OK."
  - Limits generation to 5 tokens
  - Measures `tokens_per_second`
  - Uses 30-second timeout
- Records speeds in `model_speeds` dict

### 5. Router Integration
- Imports `ToolRouter` from orchestrator
- Calls `router.route("health check routing test")`
- Records returned tool name in `router_selected`

### 6. Final Assessment
- `all_systems_pass` = true if:
  - Ollama server is online
  - At least 3/4 models installed
  - All installed models responded successfully

## Usage

### Programmatic

```python
from godman_ai.diagnostics.llm_health import run_llm_health_check

result = run_llm_health_check()

if result["all_systems_pass"]:
    print("✓ LLM infrastructure healthy")
else:
    print("✗ LLM infrastructure has issues")
    print(f"Details: {result}")
```

### Direct Execution

```bash
cd godman_ai/diagnostics
python3 llm_health.py
```

## Output Format

The function uses Rich for colored terminal output:

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

## Error Handling

### Graceful Failures

The function catches all exceptions and returns a valid result dict with:
- `all_systems_pass: false`
- Optional `error` field with exception details
- Partial results for completed steps

### Common Issues

**Server won't start:**
```python
{
    "ollama_online": false,
    "models_available": {},
    "model_speeds": {},
    "router_selected": null,
    "all_systems_pass": false
}
```

**Models not installed:**
```python
{
    "ollama_online": true,
    "models_available": {
        "deepseek-r1:14b": false,
        "phi4:14b": true,
        "llama3.1:8b": true,
        "qwen2.5:7b": false
    },
    "model_speeds": {
        "phi4:14b": 18.45,
        "llama3.1:8b": 25.67
    },
    "all_systems_pass": false
}
```

**Model performance failure:**
```python
{
    "ollama_online": true,
    "models_available": {"llama3.1:8b": true},
    "model_speeds": {"llama3.1:8b": null},  # Failed to respond
    "all_systems_pass": false
}
```

## Performance Characteristics

- **Fast execution:** ~5 seconds per model (with tiny prompts)
- **Total runtime:** ~20-30 seconds for all checks
- **Minimal resource usage:** 5-token generations only
- **Safe cleanup:** Proper process termination

## Integration Points

### With CLI

Can be wrapped in a CLI command:

```python
@app.command("health")
def llm_health():
    """Check LLM infrastructure health."""
    result = run_llm_health_check()
    sys.exit(0 if result["all_systems_pass"] else 1)
```

### With Monitoring

Can be called periodically:

```python
import schedule

def check_health():
    result = run_llm_health_check()
    if not result["all_systems_pass"]:
        alert_admins(result)

schedule.every(5).minutes.do(check_health)
```

### With API

Can power a health endpoint:

```python
@app.get("/health/llm")
def health_endpoint():
    return run_llm_health_check()
```

## Dependencies

- `rich` - Terminal formatting
- `urllib` - HTTP requests (stdlib)
- `subprocess` - Process management (stdlib)
- `godman_ai.orchestrator.tool_router` - Router testing

## Security Notes

- Uses `SIGTERM` for graceful process termination
- Never uses `SIGKILL` or forced termination
- Waits for server ready state before proceeding
- Timeouts prevent hanging indefinitely

## Platform Compatibility

- **macOS/Linux:** Full support (uses `pgrep`)
- **Windows:** May need modification for process killing

## Future Enhancements

- [ ] Add GPU/VRAM monitoring
- [ ] Test streaming responses
- [ ] Benchmark larger generations
- [ ] Check model update availability
- [ ] Verify API version compatibility
- [ ] Test concurrent requests
