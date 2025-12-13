import asyncio
from pathlib import Path
from typing import Dict


async def run(metadata: Dict[str, object]) -> Dict[str, str]:
    await asyncio.sleep(0)
    name = Path(str(metadata.get("name", "file"))).stem.replace(" ", "_").lower()
    ext = Path(str(metadata.get("name", "file.txt"))).suffix or ".txt"
    return {"filename": f"{name}{ext}"}
