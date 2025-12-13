import asyncio
from pathlib import Path


async def run(filename: str):
    await asyncio.sleep(0)
    stem = Path(filename).stem.replace(" ", "_").lower()
    return {"filename": f"{stem}.pdf"}
