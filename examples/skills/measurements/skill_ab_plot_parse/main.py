import asyncio
from typing import Dict, List


async def run(text: str) -> Dict[str, object]:
    await asyncio.sleep(0)
    points = []
    gaps = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0].isalpha():
            label = parts[0].strip(":")
            try:
                a = float(parts[1])
                b = float(parts[2])
            except ValueError:
                continue
            points.append({"label": label, "distance_a": a, "distance_b": b, "notes": ""})
    if not points:
        gaps.append("no_points")
    ab_data = {"baseline": {"A": [0, 10], "B": [0, 10]}, "points": points}
    return {"ab_data": ab_data, "gaps": gaps}
