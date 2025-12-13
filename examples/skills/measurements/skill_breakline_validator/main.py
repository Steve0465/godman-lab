import asyncio
from typing import Dict, List


async def run(ab_data: Dict[str, object], shape: str | None = None) -> Dict[str, List[str]]:
    await asyncio.sleep(0)
    issues = []
    points = ab_data.get("points", []) if isinstance(ab_data, dict) else []
    if not points:
        issues.append("missing_points")
    labels = [p.get("label", "") for p in points if isinstance(p, dict)]
    if labels and len(set(labels)) != len(labels):
        issues.append("duplicate_labels")
    if shape and "Rectangle" in shape and len(points) < 4:
        issues.append("insufficient_points_for_rectangle")
    return {"issues": issues}
