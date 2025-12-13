import asyncio
from typing import Dict


async def run(file: str, route: str) -> Dict[str, str]:
    await asyncio.sleep(0)
    return {"stored": f"{route}/{file}"}
