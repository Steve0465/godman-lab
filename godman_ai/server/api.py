from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from godman_ai.config.presets import get_all_presets, get_preset_by_name
from godman_ai.config.settings import settings
from godman_ai.services.trello_client import TRELLO_BOARDS
from libs.tool_runner import runner as tool_runner

# Routers
from godman_ai.server.webui import router as webui_router, get_static_files_app, WEBUI_DIR
from godman_ai.server.spotify_router import router as spotify_router
from godman_ai.server.trello_router import router as trello_router

# Security (NO circular imports)
from godman_ai.server.security import get_api_key

# -------------------------------------------------------------------
# App setup
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tool registration (safe imports)
try:
    import register_tools
    import godman_ai.tools.spotify
    import godman_ai.tools.trello
except ImportError:
    pass

app = FastAPI(
    title="Godman AI API",
    description="API for WebUI presets, Handler endpoint, and ToolRunner execution",
    version="1.0.0",
)

# -------------------------------------------------------------------
# Startup validation (FAIL FAST)
# -------------------------------------------------------------------

@app.on_event("startup")
def validate_required_secrets():
    missing = []

    # Core
    if not settings.GODMAN_API_KEY:
        missing.append("GODMAN_API_KEY")

    # Trello global
    if not settings.TRELLO_API_KEY:
        missing.append("TRELLO_API_KEY")
    if not settings.TRELLO_TOKEN:
        missing.append("TRELLO_TOKEN")

    # Trello boards
    for name, board_id in TRELLO_BOARDS.items():
        if not board_id:
            missing.append(f"TRELLO_BOARD_{name.upper()}")

    # Spotify (only enforce if client ID exists)
    if settings.SPOTIFY_CLIENT_ID and not settings.SPOTIFY_CLIENT_SECRET:
        missing.append("SPOTIFY_CLIENT_SECRET")

    if missing:
        raise RuntimeError(
            "Missing required secrets:\n" + "\n".join(f" - {m}" for m in missing)
        )

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Static + Routers
# -------------------------------------------------------------------

app.mount("/webui", get_static_files_app(), name="webui")

app.include_router(webui_router, tags=["WebUI"])
app.include_router(spotify_router)
app.include_router(trello_router)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    index_path = Path(WEBUI_DIR) / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"index.html not found at {index_path}",
        )
    return FileResponse(index_path)


class HandlerRequest(BaseModel):
    function: str = Field(..., description="Name of the function to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class HandlerResponse(BaseModel):
    status: str
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    execution_time: float
    timestamp: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/presets")
def list_presets():
    return {"presets": get_all_presets()}


@app.get("/api/presets/{name}")
def get_preset(name: str):
    preset = get_preset_by_name(name)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    return preset


@app.post(
    "/api/handler",
    response_model=HandlerResponse,
    dependencies=[Depends(get_api_key)],
)
async def execute_handler(request: HandlerRequest):
    tool_info = tool_runner.get_tool_info(request.function)
    if tool_info is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Function not found",
                "function": request.function,
                "available_tools": list(tool_runner.list_tools().keys()),
            },
        )

    try:
        result = await tool_runner.run_async(
            request.function,
            request.parameters,
        )

        if result["status"] == "success":
            return HandlerResponse(**result)

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Execution failed",
                "function": request.function,
                "details": str(result.get("error")),
            },
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error executing handler")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


@app.get(
    "/api/handler/tools",
    dependencies=[Depends(get_api_key)],
)
def list_handler_tools():
    return {
        "tools": tool_runner.list_tools(),
        "count": len(tool_runner.list_tools()),
    }

