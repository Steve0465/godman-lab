import asyncio
from datetime import date
from typing import Dict


async def run(text: str) -> Dict[str, object]:
    await asyncio.sleep(0)
    vendor = "Unknown"
    amount = 0.0
    for token in text.split():
        if token.lower() in {"coffee", "store"}:
            vendor = token.capitalize()
        if token.replace(".", "", 1).isdigit():
            amount = float(token)
    return {"vendor": vendor, "amount": amount, "date": str(date.today())}
