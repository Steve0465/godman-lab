"""Tests for maintenance.py script."""

import pytest
import sys
from pathlib import Path
import tempfile
import csv
from datetime import datetime
import pandas as pd

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from maintenance import add_entry, get_history


def test_add_entry():
    """Test adding a maintenance entry to CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)
    
    try:
        # Add entry
        result = add_entry(
            csv_path=csv_path,
            date='2024-12-04',
            mileage=50000,
            entry_type='oil_change',
            description='5W-30 synthetic oil change',
            cost=75.00,
            shop='Quick Lube'
        )
        
        # Verify entry was returned
        assert result['date'] == '2024-12-04'
        assert result['type'] == 'oil_change'
        assert result['cost'] == 75.00
        
        # Verify file was created
        assert csv_path.exists()
    finally:
        csv_path.unlink(missing_ok=True)


def test_get_history():
    """Test retrieving maintenance history."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)
        writer = csv.DictWriter(f, fieldnames=['date', 'mileage', 'type', 'description', 'cost', 'shop', 'notes'])
        writer.writeheader()
        writer.writerow({
            'date': '2024-12-01',
            'mileage': 49500,
            'type': 'inspection',
            'description': 'Annual inspection',
            'cost': 50.00,
            'shop': 'Main Garage',
            'notes': ''
        })
    
    try:
        history = get_history(csv_path)
        assert len(history) == 1
        assert history.iloc[0]['type'] == 'inspection'
    finally:
        csv_path.unlink(missing_ok=True)


def test_get_history_with_type_filter():
    """Test filtering history by maintenance type."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)
        writer = csv.DictWriter(f, fieldnames=['date', 'mileage', 'type', 'description', 'cost', 'shop', 'notes'])
        writer.writeheader()
        writer.writerow({
            'date': '2024-12-01',
            'mileage': 49500,
            'type': 'oil_change',
            'description': 'Oil change',
            'cost': 75.00,
            'shop': 'Quick Lube',
            'notes': ''
        })
        writer.writerow({
            'date': '2024-11-01',
            'mileage': 49000,
            'type': 'repair',
            'description': 'Brake pads',
            'cost': 200.00,
            'shop': 'Main Garage',
            'notes': ''
        })
    
    try:
        history = get_history(csv_path, entry_type='oil_change')
        assert len(history) == 1
        assert history.iloc[0]['type'] == 'oil_change'
    finally:
        csv_path.unlink(missing_ok=True)
