import pytest
from datetime import date
from decimal import Decimal
from libs.tax.filename_schema import (
    TaxFilenameParts, OwnerTag, IntentTag, StatusTag,
    build_tax_filename, parse_tax_filename, sanitize_token
)

def test_sanitize_token():
    assert sanitize_token("Hello World") == "HELLO_WORLD"
    assert sanitize_token("foo-bar") == "FOO_BAR"
    assert sanitize_token("a.b.c") == "A_B_C"
    assert sanitize_token("  test  ") == "TEST"
    assert sanitize_token("___test___") == "TEST"
    assert sanitize_token("") == "UNKNOWN"

def test_roundtrip_full():
    parts = TaxFilenameParts(
        date=date(2024, 1, 15),
        owner=OwnerTag.STEVE,
        intent=IntentTag.BIZ,
        category="EXPENSE",
        source="AMAZON",
        description="OFFICE_SUPPLIES",
        ext="pdf",
        amount=Decimal("123.45"),
        status=StatusTag.OK
    )
    filename = build_tax_filename(parts)
    assert filename == "2024-01-15__STEVE__BIZ__EXPENSE__AMAZON__123.45__OFFICE_SUPPLIES__OK.pdf"
    
    parsed = parse_tax_filename(filename)
    assert parsed == parts

def test_roundtrip_minimal():
    parts = TaxFilenameParts(
        date=date(2024, 1, 15),
        owner=OwnerTag.JOINT,
        intent=IntentTag.PERSONAL,
        category="INCOME",
        source="WORK",
        description="SALARY",
        ext="png"
    )
    filename = build_tax_filename(parts)
    assert filename == "2024-01-15__JOINT__PERSONAL__INCOME__WORK__SALARY.png"
    
    parsed = parse_tax_filename(filename)
    assert parsed == parts

def test_parse_invalid():
    assert parse_tax_filename("invalid.pdf") is None
    assert parse_tax_filename("2024-01-15__STEVE.pdf") is None
    assert parse_tax_filename("2024-01-15__INVALID__BIZ__CAT__SRC__DESC.pdf") is None

def test_parse_with_status_only():
    filename = "2024-01-15__ASHLEIGH__MIXED__HEALTHCARE__DOCTOR__CHECKUP__REVIEW.jpg"
    parsed = parse_tax_filename(filename)
    assert parsed.status == StatusTag.REVIEW
    assert parsed.amount is None
    assert parsed.description == "CHECKUP"

def test_parse_with_amount_only():
    filename = "2024-01-15__ASHLEIGH__MIXED__HEALTHCARE__DOCTOR__50.00__CHECKUP.jpg"
    parsed = parse_tax_filename(filename)
    assert parsed.status is None
    assert parsed.amount == Decimal("50.00")
    assert parsed.description == "CHECKUP"
