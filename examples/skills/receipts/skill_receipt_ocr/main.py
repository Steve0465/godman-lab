import asyncio
from pathlib import Path


async def run(path: str):
    content = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    await asyncio.sleep(0)
    return {"text": content or "mock receipt text"}
