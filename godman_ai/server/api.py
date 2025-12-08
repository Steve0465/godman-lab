from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from pathlib import Path
from godman_ai.config.presets import get_all_presets, get_preset_by_name
from libs.tool_runner import runner as tool_runner

# Import WebUI router and static files
from godman_ai.server.webui import router as webui_router, get_static_files_app, WEBUI_DIR

# Import to register sample tools
try:
    import register_tools
except ImportError:
    pass  # Tools can be registered separately

app = FastAPI(
    title="Godman AI API",
    description="API for WebUI presets, Handler endpoint, and ToolRunner execution",
    version="1.0.0"
)

# Add CORS middleware for localhost and WebUI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",  # Common dev port
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files at /webui
app.mount("/webui", get_static_files_app(), name="webui")

# Include WebUI router
app.include_router(webui_router, tags=["WebUI"])


# Root route - serve index.html
@app.get("/", include_in_schema=False)
async def root():
    """
    Serve the main WebUI dashboard at root path.
    
    Returns:
        FileResponse: The index.html file from webui folder
    """
    index_path = Path(WEBUI_DIR) / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"index.html not found at {index_path}"
        )
    return FileResponse(index_path)


class HandlerRequest(BaseModel):
    """Request model for handler endpoint"""
    function: str = Field(..., description="Name of the function to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Function parameters")


class HandlerResponse(BaseModel):
    """Response model for handler endpoint"""
    status: str = Field(..., description="Execution status: 'success' or 'error'")
    result: Optional[Any] = Field(None, description="Function result if successful")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: str = Field(..., description="ISO timestamp of execution")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/presets")
def list_presets():
    """Get all available model presets"""
    return {"presets": get_all_presets()}


@app.get("/api/presets/{name}")
def get_preset(name: str):
    """Get a specific preset by name"""
    preset = get_preset_by_name(name)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    return preset


@app.post("/api/handler", response_model=HandlerResponse)
def execute_handler(request: HandlerRequest):
    """
    Execute a registered function from Handler preset.
    
    Accepts JSON with function name and parameters, validates that the function
    exists, executes it via ToolRunner, and returns structured output.
    
    Args:
        request: HandlerRequest with function name and parameters
    
    Returns:
        HandlerResponse with execution result or error details
    
    Raises:
        HTTPException: 400 if function not found, 500 if execution fails
    """
    # Validate function exists
    tool_info = tool_runner.get_tool_info(request.function)
    if tool_info is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Function not found",
                "function": request.function,
                "message": f"Function '{request.function}' is not registered in ToolRunner",
                "available_tools": list(tool_runner.list_tools().keys())
            }
        )
    
    # Execute the function
    try:
        result = tool_runner.run(request.function, request.parameters)
        
        # Return result directly if successful
        if result["status"] == "success":
            return HandlerResponse(**result)
        
        # If tool execution returned error status, return 500
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Execution failed",
                "function": request.function,
                "error_details": result.get("error"),
                "execution_time": result.get("execution_time"),
                "timestamp": result.get("timestamp")
            }
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error",
                "function": request.function,
                "message": str(e),
                "type": type(e).__name__
            }
        )


@app.get("/api/handler/tools")
def list_handler_tools():
    """
    List all available tools registered in ToolRunner.
    
    Returns:
        Dictionary of tool names and their metadata (description, schema, etc.)
    """
    return {
        "tools": tool_runner.list_tools(),
        "count": len(tool_runner.list_tools())
    }
