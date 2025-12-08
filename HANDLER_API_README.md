# Handler API Endpoint

REST API endpoint for executing registered ToolRunner functions from the Handler preset (or any WebUI chat interface).

## Endpoint

### `POST /api/handler`

Execute a registered tool function by name with JSON parameters.

## Request Format

```json
{
  "function": "function_name",
  "parameters": {
    "param1": "value1",
    "param2": 123
  }
}
```

## Response Format

### Success (200)
```json
{
  "status": "success",
  "result": {"sum": 8},
  "error": null,
  "execution_time": 0.001,
  "timestamp": "2025-12-07T22:50:51"
}
```

### Error (400/500)
```json
{
  "detail": {
    "error": "Function not found",
    "function": "nonexistent",
    "message": "...",
    "available_tools": ["add", "greet"]
  }
}
```

## Usage Examples

### cURL
```bash
curl -X POST http://localhost:8000/api/handler \
  -H "Content-Type: application/json" \
  -d '{"function": "add", "parameters": {"x": 5, "y": 3}}'
```

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/handler",
    json={"function": "add", "parameters": {"x": 5, "y": 3}}
)
print(response.json()["result"])  # {"sum": 8}
```

### JavaScript
```javascript
const res = await fetch('/api/handler', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    function: 'add',
    parameters: {x: 5, y: 3}
  })
});
const data = await res.json();
console.log(data.result.sum); // 8
```

## Additional Endpoints

### `GET /api/handler/tools`

List all available tools.

```bash
curl http://localhost:8000/api/handler/tools
```

## WebUI Integration Flow

```
User: "Add 5 and 3"
  ↓
Handler LLM → {"function": "add", "parameters": {"x": 5, "y": 3}}
  ↓
POST /api/handler
  ↓
ToolRunner.run("add", {"x": 5, "y": 3})
  ↓
{"status": "success", "result": {"sum": 8}}
  ↓
WebUI: "The sum is 8"
```

## Error Handling

- **400**: Function not found (includes available tools list)
- **422**: Invalid request format
- **500**: Execution error (includes error details and execution time)

All errors logged to `~/godman-lab/logs/tool_runner.log`

## Testing

```bash
python3 test_handler_api.py  # 10 tests, all passing
```

## Status

✅ **Production Ready** - All tests passing, fully documented, comprehensive error handling
