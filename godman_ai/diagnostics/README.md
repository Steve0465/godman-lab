# Diagnostics Module

The `godman_ai.diagnostics` module provides async-powered diagnostic tools for checking system health and installing dependencies.

## Features

- **Async Subprocess Execution**: Uses `asyncio.create_subprocess_exec` for non-blocking subprocess calls
- **FastAPI Compatible**: All functions are async and can be directly used in FastAPI endpoints
- **CLI Integration**: Sync wrappers available via `godman` CLI commands
- **Parallel Execution**: Multiple installations or health checks run concurrently for efficiency
- **Comprehensive Health Checks**: Check availability of OpenAI, Google AI, Anthropic, and custom services

## Installation

The diagnostics module is included with `godman-lab`:

```bash
pip install godman-lab
```

## Usage

### CLI Usage

#### Check LLM Service Health

```bash
# Check all configured services
godman diagnostics-health

# Check only specific services
godman diagnostics-health --no-openai --anthropic

# Check only Google AI
godman diagnostics-health --no-openai
```

#### Install Dependencies

```bash
# Install Python packages
godman diagnostics-install --pip "requests,beautifulsoup4"

# Install npm packages locally
godman diagnostics-install --npm "typescript,eslint"

# Install npm packages globally
godman diagnostics-install --npm "typescript" --npm-global

# Install both pip and npm packages
godman diagnostics-install --pip "fastapi,uvicorn" --npm "typescript"
```

### Python API Usage

#### Async Usage (Recommended for FastAPI/async code)

```python
import asyncio
from godman_ai.diagnostics import run_llm_health_check, install_all

# Health check
async def check_health():
    result = await run_llm_health_check(
        check_openai=True,
        check_google=True,
        check_anthropic=False
    )
    print(f"Status: {result['overall_status']}")
    return result

# Install dependencies
async def install_deps():
    result = await install_all(
        pip_packages=['requests', 'beautifulsoup4'],
        npm_packages=['typescript'],
        npm_global=False
    )
    return result

# Run from async context
asyncio.run(check_health())
```

#### Sync Usage (for compatibility with sync code)

```python
import asyncio
from godman_ai.diagnostics import run_llm_health_check, install_all

# Wrap async calls with asyncio.run()
result = asyncio.run(run_llm_health_check())
print(f"Status: {result['overall_status']}")

# Install dependencies synchronously
result = asyncio.run(install_all(pip_packages=['requests']))
```

### FastAPI Integration

```python
from fastapi import FastAPI
from godman_ai.diagnostics import run_llm_health_check, install_all

app = FastAPI()

@app.get("/health")
async def health_check():
    """Async health check endpoint"""
    result = await run_llm_health_check()
    return result

@app.post("/install")
async def install_packages(pip_packages: list[str], npm_packages: list[str] = None):
    """Async package installation endpoint"""
    result = await install_all(
        pip_packages=pip_packages,
        npm_packages=npm_packages
    )
    return result
```

## API Reference

### `run_llm_health_check()`

Check the health and availability of LLM services.

**Parameters:**
- `check_openai` (bool): Whether to check OpenAI API (default: True)
- `check_google` (bool): Whether to check Google Generative AI (default: True)
- `check_anthropic` (bool): Whether to check Anthropic API (default: False)
- `external_commands` (list[list[str]], optional): External commands to run as health checks

**Returns:**
```python
{
    "timestamp": 1234567890.0,
    "overall_status": "healthy" | "degraded" | "critical",
    "services": {
        "openai": {
            "available": True,
            "response_time_ms": 123.45,
            "models_count": 10,
            "error": None
        },
        # ... more services
    },
    "python_info": {
        "python_version": "3.12.3",
        "platform": "linux"
    },
    "summary": {
        "total_services": 2,
        "available_services": 1,
        "unavailable_services": 1
    },
    "execution_time_ms": 250.0
}
```

### `install_all()`

Install dependencies using package managers.

**Parameters:**
- `pip_packages` (list[str], optional): Python packages to install via pip
- `npm_packages` (list[str], optional): Node.js packages to install via npm
- `npm_global` (bool): Install npm packages globally (default: False)

**Returns:**
```python
{
    "success": True,
    "pip": {
        "success": True,
        "returncode": 0,
        "installed": ["requests", "beautifulsoup4"],
        "failed": []
    },
    "npm": {
        "success": True,
        "returncode": 0,
        "installed": ["typescript"],
        "failed": []
    },
    "errors": []
}
```

## Implementation Details

### Async Subprocess

The module uses `asyncio.create_subprocess_exec()` for all subprocess operations:

```python
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)

stdout, stderr = await asyncio.wait_for(
    process.communicate(),
    timeout=timeout
)
```

### Parallel Execution

Multiple operations run concurrently using `asyncio.gather()`:

```python
results = await asyncio.gather(
    _install_pip_packages(pip_packages),
    _install_npm_packages(npm_packages),
    return_exceptions=True
)
```

### Error Handling

- Timeouts are configurable (default: 300s for installations, 30s for health checks)
- Exceptions are caught and returned in the result dictionary
- Failed operations don't block successful ones

## Testing

Run the test suite:

```bash
# Run all diagnostics tests
pytest tests/test_diagnostics*.py -v

# Run with coverage
pytest tests/test_diagnostics*.py --cov=godman_ai.diagnostics -v
```

## Contributing

When adding new diagnostic features:

1. Keep functions async using `asyncio.create_subprocess_exec()`
2. Add comprehensive tests with mocked subprocesses
3. Update this documentation
4. Ensure FastAPI compatibility
5. Run linting: `black godman_ai/diagnostics/ && ruff check godman_ai/diagnostics/`
