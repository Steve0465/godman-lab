"""
WebUI Router Module

FastAPI router for serving the WebUI dashboard.
Mounts static files and serves the index.html for the single-page application.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define paths
WEBUI_DIR = Path(__file__).parent.parent.parent / "webui"
INDEX_FILE = WEBUI_DIR / "index.html"

# Ensure webui directory exists
WEBUI_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/dashboard")
async def get_dashboard():
    """
    Serve the dashboard.
    
    Returns:
        FileResponse: The index.html file for the WebUI dashboard
    
    Raises:
        HTTPException: 404 if index.html not found
    """
    if not INDEX_FILE.exists():
        logger.error(f"index.html not found at {INDEX_FILE}")
        raise HTTPException(
            status_code=404,
            detail=f"WebUI index.html not found. Please create it at {WEBUI_DIR}/index.html"
        )
    
    logger.info(f"Serving dashboard from {INDEX_FILE}")
    return FileResponse(INDEX_FILE)


@router.get("/status")
async def get_webui_status():
    """
    Get WebUI status and configuration.
    
    Returns:
        dict: WebUI status information
    """
    return {
        "status": "operational",
        "webui_dir": str(WEBUI_DIR),
        "index_exists": INDEX_FILE.exists(),
        "static_files_mounted": "/webui",
        "root_route": "/",
        "routes": [
            {"path": "/", "description": "Main dashboard (root)", "method": "GET"},
            {"path": "/dashboard", "description": "Dashboard endpoint", "method": "GET"},
            {"path": "/status", "description": "WebUI status", "method": "GET"},
            {"path": "/webui/*", "description": "Static assets", "method": "GET"}
        ]
    }


def get_static_files_app():
    """
    Create and return the StaticFiles application.
    
    This should be mounted in the main app using:
    app.mount("/webui", get_static_files_app(), name="webui")
    
    Returns:
        StaticFiles: Configured static files application
    """
    return StaticFiles(directory=str(WEBUI_DIR))


# Export router and static files configuration
__all__ = ["router", "get_static_files_app", "WEBUI_DIR"]
