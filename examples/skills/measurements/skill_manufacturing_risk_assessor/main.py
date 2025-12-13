import asyncio
from typing import Dict, List


async def run(ab_data: Dict[str, object], shape: str, issues: List[str]) -> Dict[str, object]:
    await asyncio.sleep(0)
    risk = "LOW"
    reasons = []
    if issues:
        risk = "MEDIUM"
        reasons.extend(issues)
    if "Freeform" in shape and "missing_points" in issues:
        risk = "HIGH"
        reasons.append("freeform_missing_points")
    return {"risk_level": risk, "reasons": reasons}
