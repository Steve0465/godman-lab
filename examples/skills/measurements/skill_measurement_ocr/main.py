import asyncio
from pathlib import Path
from typing import Dict


async def run(path: str) -> Dict[str, str]:
    text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else "A=0 B=0"
    await asyncio.sleep(0)
    return {"text": text}
