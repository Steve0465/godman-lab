"""
Example FastAPI integration with diagnostics module.

This demonstrates how to integrate the async diagnostics module
into a FastAPI application.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from godman_ai.diagnostics import run_llm_health_check, install_all


class InstallRequest(BaseModel):
    """Request model for package installation"""

    pip_packages: Optional[List[str]] = None
    npm_packages: Optional[List[str]] = None
    npm_global: bool = False


# Example of using diagnostics in startup/shutdown events using lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    print("Running startup health check...")
    result = await run_llm_health_check()
    print(f"Health check complete: {result['overall_status']}")

    if result["overall_status"] == "critical":
        print("WARNING: All LLM services are unavailable!")

    yield

    # Shutdown
    print("Application shutting down...")


# Create app with lifespan
app = FastAPI(title="Diagnostics API Example", lifespan=lifespan)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Diagnostics API Example",
        "endpoints": {
            "/health": "Check LLM service health",
            "/health/openai": "Check only OpenAI",
            "/health/google": "Check only Google AI",
            "/install": "Install packages (POST)",
        },
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check for all LLM services.

    Returns health status, response times, and availability
    for all configured LLM services.
    """
    result = await run_llm_health_check()
    return result


@app.get("/health/openai")
async def health_check_openai():
    """Check only OpenAI API health"""
    result = await run_llm_health_check(check_openai=True, check_google=False)

    if result["overall_status"] == "critical":
        raise HTTPException(status_code=503, detail="OpenAI service unavailable")

    return result


@app.get("/health/google")
async def health_check_google():
    """Check only Google Generative AI health"""
    result = await run_llm_health_check(check_openai=False, check_google=True)

    if result["overall_status"] == "critical":
        raise HTTPException(status_code=503, detail="Google AI service unavailable")

    return result


@app.post("/install")
async def install_packages(request: InstallRequest):
    """
    Install packages via pip and/or npm.

    This endpoint allows installing Python and Node.js packages
    asynchronously. Both package managers can be used in a single request
    and will execute in parallel.
    """
    if not request.pip_packages and not request.npm_packages:
        raise HTTPException(
            status_code=400, detail="At least one of pip_packages or npm_packages must be provided"
        )

    result = await install_all(
        pip_packages=request.pip_packages,
        npm_packages=request.npm_packages,
        npm_global=request.npm_global,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Installation failed: {result['errors']}")

    return result


if __name__ == "__main__":
    import uvicorn

    print("\nStarting FastAPI server with diagnostics...")
    print("Endpoints:")
    print("  http://localhost:8000/health - Full health check")
    print("  http://localhost:8000/health/openai - OpenAI only")
    print("  http://localhost:8000/health/google - Google AI only")
    print("  http://localhost:8000/docs - API documentation\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
