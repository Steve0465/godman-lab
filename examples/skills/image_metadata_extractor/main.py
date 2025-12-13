from pathlib import Path


def extract(path: str):
    p = Path(path)
    return {"metadata": {"name": p.name, "exists": p.exists()}}
