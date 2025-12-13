import asyncio
from typing import Dict, List


async def run(normalized: List[Dict[str, float]], boundaries: List[Dict[str, float]]) -> Dict[str, str]:
    await asyncio.sleep(0)
    if not normalized or not boundaries:
        return {"fitment": "UNKNOWN"}
    return {"fitment": "READY"}
