"""
Server runner for GodmanAI API

Starts FastAPI server with Uvicorn.
"""

import logging
import socket

logger = logging.getLogger(__name__)


def _find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")


def run_server(host: str = "127.0.0.1", port: int = 8000, auto_port: bool = True):
    """
    Start the GodmanAI API server
    
    Args:
        host: Host to bind to
        port: Port to bind to (will auto-detect if busy and auto_port=True)
        auto_port: Automatically find available port if specified port is busy
    """
    try:
        import uvicorn
    except ImportError:
        raise ImportError("Uvicorn not installed. Run: pip install uvicorn")
    
    # Find available port if requested
    if auto_port:
        try:
            port = _find_available_port(port)
        except RuntimeError as e:
            logger.error(f"Could not find available port: {e}")
            raise
    
    logger.info(f"Starting GodmanAI API server at http://{host}:{port}")
    print(f"\n🚀 GodmanAI API Server starting...")
    print(f"📡 URL: http://{host}:{port}")
    print(f"📖 Docs: http://{host}:{port}/docs")
    print(f"🔧 Health: http://{host}:{port}/os/health")
    print(f"📊 Dashboard: http://{host}:{port}/dashboard")
    print(f"\nPress CTRL+C to stop\n")
    
    from godman_ai.service.api import app
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
