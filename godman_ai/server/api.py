from fastapi import FastAPI, HTTPException
from godman_ai.config.presets import get_all_presets, get_preset_by_name

app = FastAPI()

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
