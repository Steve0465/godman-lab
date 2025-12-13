import pytest
from typer.testing import CliRunner
from pathlib import Path
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from cli.godman.tax import app
from libs.tax.filename_schema import build_tax_filename, TaxFilenameParts, OwnerTag, IntentTag

runner = CliRunner()

def test_init_year(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    
    result = runner.invoke(app, ["init-year", str(archive), "--year", "2024"])
    assert result.exit_code == 0
    
    year_dir = archive / "2024"
    assert year_dir.exists()
    assert (year_dir / "00_INCOME").exists()
    assert (year_dir / "_SUMMARY").exists()
    assert (archive / "_RULES" / "TAX_DEDUCTION_RULES.md").exists()

def test_intake_scan_valid_file(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    
    # Init year
    runner.invoke(app, ["init-year", str(archive), "--year", "2024"])
    
    # Create inbox file
    inbox = archive / "_inbox"
    inbox.mkdir()
    
    parts = TaxFilenameParts(
        date=date(2024, 1, 1),
        owner=OwnerTag.STEVE,
        intent=IntentTag.BIZ,
        category="EXPENSE",
        source="TEST",
        description="ITEM",
        ext="pdf",
        amount=Decimal("10.00")
    )
    filename = build_tax_filename(parts)
    (inbox / filename).touch()
    
    result = runner.invoke(app, ["intake-scan", str(archive), "--year", "2024"])
    assert result.exit_code == 0
    
    # Check moved
    target = archive / "2024" / "01_EXPENSES" / filename
    assert target.exists()
    assert not (inbox / filename).exists()
    
    # Check log
    log_files = list((archive / "2024" / "_SUMMARY").glob("intake_log_*.jsonl"))
    assert len(log_files) == 1

def test_intake_scan_interactive(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    runner.invoke(app, ["init-year", str(archive), "--year", "2024"])
    
    inbox = archive / "_inbox"
    inbox.mkdir()
    (inbox / "scan.pdf").touch()
    
    # Mock inputs: Date, Owner, Intent, Category, Source, Amount, Description, Status
    inputs = [
        "2024-02-01", # Date
        "STEVE",      # Owner
        "BIZ",        # Intent
        "EXPENSE",    # Category
        "VENDOR",     # Source
        "20.00",      # Amount
        "STUFF",      # Description
        "OK"          # Status
    ]
    
    with patch('typer.prompt', side_effect=inputs):
        result = runner.invoke(app, ["intake-scan", str(archive), "--year", "2024"])
        
    assert result.exit_code == 0
    
    expected_name = "2024-02-01__STEVE__BIZ__EXPENSE__VENDOR__20.00__STUFF__OK.pdf"
    target = archive / "2024" / "01_EXPENSES" / expected_name
    assert target.exists()

def test_healthcare_report(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    runner.invoke(app, ["init-year", str(archive), "--year", "2024"])
    
    hc_dir = archive / "2024" / "02_HEALTHCARE"
    (hc_dir / "2024-01-01__JOINT__PERSONAL__HEALTHCARE__MKT__1095A.pdf").touch()
    (hc_dir / "2024-01-01__JOINT__PERSONAL__HEALTHCARE__INS__PREMIUM_JAN.pdf").touch()
    
    result = runner.invoke(app, ["healthcare-report", str(archive), "--year", "2024"])
    assert result.exit_code == 0
    
    report = archive / "2024" / "_SUMMARY" / "2024__HEALTHCARE_READINESS.md"
    assert report.exists()
    content = report.read_text()
    assert "✅ Found" in content  # 1095-A
    assert "1 found" in content   # Premium proofs

def test_allocations_report(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    runner.invoke(app, ["init-year", str(archive), "--year", "2024"])
    
    misc_dir = archive / "2024" / "99_SUPPORTING_MISC"
    
    # Match rule
    parts = TaxFilenameParts(
        date=date(2024, 1, 1),
        owner=OwnerTag.JOINT,
        intent=IntentTag.MIXED,
        category="MISC",
        source="ATT",
        description="BILL",
        ext="pdf",
        amount=Decimal("100.00")
    )
    (misc_dir / build_tax_filename(parts)).touch()
    
    # No match
    parts2 = TaxFilenameParts(
        date=date(2024, 1, 2),
        owner=OwnerTag.JOINT,
        intent=IntentTag.MIXED,
        category="MISC",
        source="OTHER",
        description="STUFF",
        ext="pdf",
        amount=Decimal("50.00")
    )
    (misc_dir / build_tax_filename(parts2)).touch()
    
    result = runner.invoke(app, ["allocations", str(archive), "--year", "2024"])
    assert result.exit_code == 0
    
    report = archive / "2024" / "_SUMMARY" / "2024__JOINT_ALLOCATIONS.md"
    assert report.exists()
    content = report.read_text()
    assert "ATT" in content
    assert "STEVE: 60%" in content
    assert "OTHER" in content
