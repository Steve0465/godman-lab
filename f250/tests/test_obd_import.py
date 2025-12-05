"""Tests for obd_import.py script."""

import pytest
import sys
from pathlib import Path
import tempfile
import csv
import pandas as pd

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from obd_import import validate_csv, normalize_dtc_columns


def test_validate_csv_valid():
    """Test validation of a valid OBD CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'engine_rpm', 'vehicle_speed'])
        writer.writerow(['2024-12-04 10:00:00', '2500', '55'])
    
    try:
        is_valid, msg = validate_csv(csv_path)
        assert is_valid
        if msg:
            assert 'valid' in msg.lower()
    finally:
        csv_path.unlink(missing_ok=True)


def test_validate_csv_missing_required_column():
    """Test validation fails when required column is missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)
        writer = csv.writer(f)
        writer.writerow(['engine_rpm', 'vehicle_speed'])  # Missing 'timestamp'
        writer.writerow(['2500', '55'])
    
    try:
        is_valid, msg = validate_csv(csv_path)
        assert not is_valid
        assert 'timestamp' in msg.lower()
    finally:
        csv_path.unlink(missing_ok=True)


def test_normalize_dtc_columns():
    """Test DTC column normalization."""
    test_df = pd.DataFrame({
        'timestamp': ['2024-12-04 10:00:00'],
        'dtc': ['P0300'],
        'engine_rpm': [2500]
    })
    
    normalized = normalize_dtc_columns(test_df)
    
    # Should have 'dtc_code' field
    assert 'dtc_code' in normalized.columns
    # Should have added dtc_description
    assert 'dtc_description' in normalized.columns
    # Original column is kept by the function
    assert normalized.iloc[0]['dtc_code'] == 'P0300'


def test_validate_csv_empty_file():
    """Test validation of empty CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)
        # Write nothing
    
    try:
        is_valid, msg = validate_csv(csv_path)
        assert not is_valid
    finally:
        csv_path.unlink(missing_ok=True)
