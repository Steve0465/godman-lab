import asyncio
from typing import Dict, List


async def run(ab_points: List[Dict[str, float]]) -> Dict[str, List[Dict[str, float]]]:
    await asyncio.sleep(0)
    return {"boundaries": [{"start": p.get("label"), "end": p.get("label"), "len": p.get("distance_a", 0)} for p in ab_points]}
