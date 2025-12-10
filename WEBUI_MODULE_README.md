# WebUI Dashboard Module

FastAPI router for serving the Godman AI WebUI dashboard with static file support.

## Overview

The `godman_ai/server/webui.py` module provides a FastAPI router that:
- Serves the main `index.html` dashboard at `/`
- Mounts static files from the `webui/` directory at `/static`
- Provides WebUI status and configuration endpoints
- Integrates seamlessly with the existing Handler API

## Files Created

```
godman_ai/server/webui.py     # WebUI router module
webui/index.html               # Main dashboard HTML
```

## Integration

The WebUI router is automatically integrated into the main API:

```python
# In godman_ai/server/api.py
from godman_ai.server.webui import router as webui_router, get_static_files_app

# Mount static files
app.mount("/static", get_static_files_app(), name="static")

# Include WebUI router
app.include_router(webui_router, tags=["WebUI"])
```

## Endpoints

### `GET /`
Serves the main dashboard (index.html)

**Response:** HTML file

**Example:**
```bash
curl http://localhost:8000/
# Returns the full dashboard HTML
```

### `GET /dashboard`
Alias for `/` - serves the same dashboard

**Response:** HTML file

### `GET /status`
Get WebUI status and configuration

**Response:**
```json
{
  "status": "operational",
  "webui_dir": "/path/to/webui",
  "index_exists": true,
  "static_files_mounted": true,
  "routes": [
    {"path": "/", "description": "Main dashboard"},
    {"path": "/dashboard", "description": "Dashboard alias"},
    {"path": "/status", "description": "WebUI status"},
    {"path": "/static/*", "description": "Static assets"}
  ]
}
```

### `GET /static/{filepath}`
Serves static files (CSS, JS, images, etc.) from the `webui/` directory

**Example:**
```bash
# Access static files
curl http://localhost:8000/static/style.css
curl http://localhost:8000/static/app.js
curl http://localhost:8000/static/logo.png
```

## Dashboard Features

The included `index.html` dashboard provides:

### Visual Design
- Modern gradient background
- Card-based layout
- Responsive design
- Clean, professional styling

### Information Display
- Live server status indicator
- Feature highlights (Handler API, Presets, ToolRunner)
- API endpoint documentation
- Interactive test button

### Interactive Testing
- Built-in API test functionality
- Tests multiple Handler endpoints
- Displays results in terminal-style output
- Real-time execution feedback

### Tested Functions
1. **add(42, 58)** - Math operation
2. **create_user("Alice", 28)** - User creation
3. **calculate_stats([10,20,30])** - Data processing
4. **List tools** - Tool discovery

## Usage

### Start the Server
```bash
cd ~/Desktop/godman-lab
uvicorn godman_ai.server.api:app --reload
```

### Access the Dashboard
Open your browser to:
```
http://localhost:8000/
```

### Test the API
Click the "🧪 Test Handler API" button on the dashboard to run automated tests.

## Adding Static Assets

Place files in the `webui/` directory:

```
webui/
├── index.html          # Main dashboard
├── style.css          # Additional styles
├── app.js             # JavaScript code
├── images/            # Images
│   └── logo.png
└── fonts/             # Custom fonts
```

Access them at:
```
http://localhost:8000/static/style.css
http://localhost:8000/static/app.js
http://localhost:8000/static/images/logo.png
```

## CORS Configuration

CORS is enabled to allow frontend development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**⚠️ Production Note:** Update `allow_origins` to specify your domain instead of `"*"`.

## Module API

### `router`
FastAPI router with WebUI endpoints. Include in main app with:
```python
app.include_router(router, tags=["WebUI"])
```

### `get_static_files_app()`
Returns configured StaticFiles application. Mount with:
```python
app.mount("/static", get_static_files_app(), name="static")
```

### `WEBUI_DIR`
Path to the webui directory. Use for reference or file operations:
```python
from godman_ai.server.webui import WEBUI_DIR
print(f"WebUI files at: {WEBUI_DIR}")
```

## Error Handling

### Index Not Found
If `index.html` doesn't exist, returns 404 with helpful message:
```json
{
  "detail": "WebUI index.html not found. Please create it at /path/to/webui/index.html"
}
```

### Static File Not Found
Returns 404 for missing static files with standard error response.

## Development Workflow

1. **Edit HTML/CSS/JS** in `webui/` directory
2. **Refresh browser** - Changes are immediately visible
3. **No restart needed** - Static files served directly
4. **Test with dashboard button** - Verify API integration

## Testing

### Manual Testing
```bash
# Test dashboard
curl http://localhost:8000/

# Test status
curl http://localhost:8000/status

# Test API integration
curl -X POST http://localhost:8000/api/handler \
  -H "Content-Type: application/json" \
  -d '{"function": "add", "parameters": {"x": 5, "y": 3}}'
```

### Browser Testing
1. Open http://localhost:8000/
2. Click "🧪 Test Handler API" button
3. Verify all tests pass
4. Check console for any errors

## Integration with Handler API

The dashboard seamlessly integrates with the Handler API:

```javascript
// Example: Call Handler API from dashboard
async function executeFunction(funcName, params) {
    const response = await fetch('/api/handler', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            function: funcName,
            parameters: params
        })
    });
    return await response.json();
}

// Usage
const result = await executeFunction('add', {x: 5, y: 3});
console.log(result.result.sum); // 8
```

## Production Deployment

### Security Considerations
1. **CORS**: Configure specific origins
2. **HTTPS**: Always use HTTPS in production
3. **Static Files**: Consider CDN for better performance
4. **Rate Limiting**: Add rate limiting middleware
5. **Authentication**: Add auth for sensitive operations

### Performance
- Static files cached by browser
- FastAPI serves efficiently
- Consider nginx for production static file serving

## Status

✅ **Operational**
- Router module created and tested
- Dashboard HTML created and styled
- Static file mounting configured
- API integration verified
- All endpoints tested and working

## Next Steps

1. **Enhance Dashboard**
   - Add real-time chat interface
   - Implement preset selector
   - Add tool execution history
   - Create visualization components

2. **Add Features**
   - File upload functionality
   - WebSocket for real-time updates
   - User authentication
   - Settings management

3. **Polish UI**
   - Add animations
   - Improve responsive design
   - Add dark mode
   - Create additional pages
