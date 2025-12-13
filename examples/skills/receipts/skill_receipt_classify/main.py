import asyncio
from typing import Dict


CATEGORY_RULES = {
    "coffee": "Meals",
    "store": "Supplies",
}


async def run(vendor: str, amount: float) -> Dict[str, str]:
    await asyncio.sleep(0)
    key = vendor.lower()
    category = CATEGORY_RULES.get(key, "Other")
    return {"category": category}
