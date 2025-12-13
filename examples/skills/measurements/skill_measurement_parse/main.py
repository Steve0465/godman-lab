import asyncio
from typing import Dict, List


async def run(text: str) -> Dict[str, List[List[str]]]:
    await asyncio.sleep(0)
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if parts:
            rows.append(parts)
    return {"table": rows}
