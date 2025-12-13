import asyncio
from pathlib import Path

from examples.skills.receipts.skill_receipt_classify import main as classify_main
from examples.skills.receipts.skill_receipt_normalize import main as normalize_main
from examples.skills.receipts.skill_receipt_ocr import main as ocr_main
from examples.skills.receipts.skill_receipt_parse import main as parse_main


def test_receipt_skills_roundtrip(tmp_path):
    sample = tmp_path / "receipt.txt"
    sample.write_text("coffee 12.50", encoding="utf-8")
    ocr = asyncio.run(ocr_main.run(str(sample)))
    parsed = asyncio.run(parse_main.run(ocr["text"]))
    cat = asyncio.run(classify_main.run(parsed["vendor"], parsed["amount"]))
    norm = asyncio.run(normalize_main.run(str(sample.name)))
    assert "text" in ocr
    assert parsed["vendor"] == "Coffee"
    assert cat["category"] in {"Meals", "Other"}
    assert norm["filename"].endswith(".pdf")
