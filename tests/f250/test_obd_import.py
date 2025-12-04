"""
Tests for OBD import functionality
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from f250.scripts.obd_import import (
    validate_csv,
    normalize_dtc_columns,
    init_sqlite_db,
    is_file_imported,
    mark_file_imported,
    import_csv_to_sqlite
)
import pandas as pd


def test_validate_csv(sample_csv_path):
    """Test CSV validation with valid file."""
    is_valid, message = validate_csv(sample_csv_path)
    assert is_valid, f"Valid CSV should pass: {message}"
    assert message == "Valid"


def test_validate_csv_missing_columns(temp_dir):
    """Test CSV validation with missing required columns."""
    invalid_csv = temp_dir / 'invalid.csv'
    invalid_csv.write_text("timestamp,rpm\n2024-01-01,1000\n")
    
    is_valid, message = validate_csv(invalid_csv)
    assert not is_valid, "CSV with missing columns should fail"
    assert "Missing columns" in message


def test_normalize_dtc_columns():
    """Test DTC column normalization."""
    # Test with various column name variants
    df = pd.DataFrame({
        'dtc': ['P0301', 'P0302'],
        'dtc_desc': ['Misfire Cyl 1', 'Misfire Cyl 2']
    })
    
    df = normalize_dtc_columns(df)
    
    assert 'dtc_code' in df.columns
    assert 'dtc_description' in df.columns
    assert df['dtc_code'].iloc[0] == 'P0301'


def test_init_sqlite_db(test_db_path):
    """Test SQLite database initialization."""
    init_sqlite_db(test_db_path)
    
    assert test_db_path.exists()
    
    # Verify tables exist
    import sqlite3
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert 'obd_logs' in tables
    assert 'import_log' in tables
    
    conn.close()


def test_is_file_imported(test_db_path):
    """Test import tracking."""
    init_sqlite_db(test_db_path)
    
    # File not imported yet
    assert not is_file_imported(test_db_path, 'test.csv')
    
    # Mark as imported
    mark_file_imported(test_db_path, 'test.csv', 100, 'success')
    
    # Should now be marked as imported
    assert is_file_imported(test_db_path, 'test.csv')


def test_import_csv_to_sqlite_dry_run(sample_csv_path, test_db_path):
    """Test CSV import in dry-run mode."""
    init_sqlite_db(test_db_path)
    
    # Import in dry-run mode
    row_count = import_csv_to_sqlite(sample_csv_path, test_db_path, dry_run=True)
    
    assert row_count == 5, "Should report 5 rows"
    
    # Verify no data was actually imported
    import sqlite3
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM obd_logs")
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 0, "Dry run should not import data"


def test_import_csv_to_sqlite(sample_csv_path, test_db_path):
    """Test actual CSV import."""
    init_sqlite_db(test_db_path)
    
    # Import data
    row_count = import_csv_to_sqlite(sample_csv_path, test_db_path, dry_run=False)
    
    assert row_count == 5, "Should import 5 rows"
    
    # Verify data was imported
    import sqlite3
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM obd_logs WHERE misfire_detected = 1")
    misfire_count = cursor.fetchone()[0]
    conn.close()
    
    assert misfire_count == 2, "Should detect 2 misfire events"
