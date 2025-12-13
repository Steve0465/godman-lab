import asyncio
from typing import Dict, List


async def run(ab_points: List[Dict[str, float]]) -> Dict[str, List[Dict[str, float]]]:
    await asyncio.sleep(0)
    normalized = []
    for p in ab_points:
        normalized.append({"label": str(p.get("label", "")).upper(), "distance_a": float(p.get("distance_a", 0)), "distance_b": float(p.get("distance_b", 0))})
    return {"normalized": normalized}
