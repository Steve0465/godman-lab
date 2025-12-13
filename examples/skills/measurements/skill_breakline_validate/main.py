import asyncio
from typing import Dict, List


async def run(boundaries: List[Dict[str, float]]) -> Dict[str, List[str]]:
    await asyncio.sleep(0)
    issues = []
    if not boundaries:
        issues.append("no_boundaries")
    elif len(boundaries) < 2:
        issues.append("insufficient_boundaries")
    return {"issues": issues}
