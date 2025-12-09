# Godman AI CLI - Router Integration

The `godman ai route` command provides CLI access to the intelligent LLM router.

## Command

```bash
godman ai route <prompt> [OPTIONS]
```

## Options

- `--model, -m TEXT` - Force a specific model (bypasses automatic routing)
- `--raw` - Print raw JSON output instead of formatted display

## Usage Examples

### Auto-routing (recommended)

Let the router choose the best model based on prompt analysis:

```bash
# Reasoning task → deepseek-r1:14b
godman ai route "Analyze why my server keeps crashing under high load"

# Math task → phi4:14b
godman ai route "Calculate the derivative of x^2 + 5x + 3"

# Quick chat → llama3.1:8b
godman ai route "What is the capital of France?"

# Long-form writing → qwen2.5:7b
godman ai route "Write a comprehensive guide to Docker containers"
```

### Force specific model

Override routing logic to use a specific model:

```bash
godman ai route "Hello there!" --model llama3.1:8b

godman ai route "Explain neural networks" -m deepseek-r1:14b
```

### Raw JSON output

Get structured JSON response for programmatic use:

```bash
godman ai route "Calculate 5 + 3" --raw
```

Output:
```json
{
  "model": "phi4:14b",
  "prompt": "Calculate 5 + 3",
  "response": "5 + 3 = 8",
  "category": "math",
  "duration": 2.145,
  "success": true,
  "tokens_generated": 12,
  "tokens_per_second": 5.59
}
```

## Output Format

### Standard (formatted) output:

```
Model: phi4:14b
Category: math
Duration: 2.145s
Speed: 5.59 tok/s

╭─ Response ────────────────────────────────────────╮
│ The answer is 8                                   │
╰───────────────────────────────────────────────────╯
```

### Raw JSON output:

Complete structured data including:
- `model` - Model used
- `category` - Detected task category
- `prompt` - Input prompt
- `response` - Generated text
- `duration` - Execution time in seconds
- `success` - Boolean success flag
- `tokens_generated` - Number of tokens
- `tokens_per_second` - Generation speed
- `fallback_used` - Whether fallback model was used (if applicable)

## Routing Categories

The router automatically classifies prompts into four categories:

1. **Reasoning** - Analysis, troubleshooting, architecture, planning
2. **Math** - Calculations, equations, formulas
3. **Conversational** - Quick questions, chat, simple queries
4. **Writing** - Long-form content, essays, summaries

## Error Handling

The command handles:
- Router module not available
- Model not installed
- Network/timeout errors
- HTTP errors from Ollama
- JSON parsing errors

Failed requests will:
1. Attempt fallback models automatically
2. Display error details
3. Exit with non-zero status code

## Integration with Main CLI

The route command is part of the `ai` subcommand group:

```bash
godman ai route "..."      # Router (new)
godman ai local "..."      # Direct Ollama
godman ai local-file path  # File analysis
godman ai shell            # Interactive shell
```

## Requirements

- Python 3.7+
- Ollama running locally
- Router module at `~/godman-raw/llm/router/model_router.py`
- At least one model installed
- Dependencies: typer, rich

## Logging

All routing decisions are automatically logged to:
`~/godman-raw/llm/router/router_logs/route_<timestamp>.json`

## Direct Execution

The ai module can also be run directly:

```bash
python3 -m cli.godman.ai route "What is Python?"
```

Or:

```bash
cd cli/godman
python3 ai.py route "What is Python?"
```
