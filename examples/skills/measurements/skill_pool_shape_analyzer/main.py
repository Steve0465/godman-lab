import asyncio
from typing import Dict, List


async def run(ab_data: Dict[str, object], depth_profile: Dict[str, object] | None = None) -> Dict[str, object]:
    await asyncio.sleep(0)
    points: List[Dict[str, object]] = ab_data.get("points", []) if isinstance(ab_data, dict) else []
    labels = {p.get("label", "") for p in points}
    shape = "Rectangle" if labels.issuperset({"A", "B"}) or len(points) >= 4 else "Freeform"
    notes = []
    if depth_profile and depth_profile.get("hopper"):
        shape = f"{shape} (Hopper)"
    return {"shape": shape, "notes": notes}
