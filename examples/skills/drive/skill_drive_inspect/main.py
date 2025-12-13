import asyncio
from typing import Dict


async def run(file: str) -> Dict[str, object]:
    await asyncio.sleep(0)
    return {"metadata": {"name": file, "size": len(file), "mime": "application/pdf" if file.endswith(".pdf") else "text/plain"}}
