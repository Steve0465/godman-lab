"""
Tests for maintenance log functionality
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from f250.scripts.maintenance import (
    init_csv,
    add_entry,
    get_history,
    sync_to_sqlite,
    init_sqlite_table
)
import pandas as pd


def test_init_csv(test_maintenance_csv):
    """Test maintenance CSV initialization."""
    init_csv(test_maintenance_csv)
    
    assert test_maintenance_csv.exists()
    
    # Verify CSV has correct columns
    df = pd.read_csv(test_maintenance_csv)
    expected_cols = ['date', 'mileage', 'type', 'description', 'cost', 'vendor', 'notes']
    assert list(df.columns) == expected_cols


def test_add_entry(test_maintenance_csv):
    """Test adding maintenance entry."""
    init_csv(test_maintenance_csv)
    
    success = add_entry(
        test_maintenance_csv,
        date='2024-12-04',
        mileage=50000,
        entry_type='oil_change',
        description='Full synthetic oil change',
        cost=75.00,
        vendor='Local Shop',
        notes='Used 5W-30'
    )
    
    assert success, "Entry should be added successfully"
    
    # Verify entry was added
    df = pd.read_csv(test_maintenance_csv)
    assert len(df) == 1
    assert df.iloc[0]['type'] == 'oil_change'
    assert df.iloc[0]['mileage'] == 50000


def test_get_history(test_maintenance_csv):
    """Test getting maintenance history."""
    init_csv(test_maintenance_csv)
    
    # Add multiple entries
    add_entry(test_maintenance_csv, '2024-12-01', 45000, 'oil_change', 'Oil change', 70.00)
    add_entry(test_maintenance_csv, '2024-12-02', 45100, 'tire_rotation', 'Rotated tires', 40.00)
    add_entry(test_maintenance_csv, '2024-12-03', 45200, 'oil_change', 'Oil change 2', 75.00)
    
    # Get all history
    df = get_history(test_maintenance_csv)
    assert len(df) == 3
    
    # Get filtered by type
    df_oil = get_history(test_maintenance_csv, entry_type='oil_change')
    assert len(df_oil) == 2
    
    # Get limited results
    df_limited = get_history(test_maintenance_csv, limit=2)
    assert len(df_limited) == 2


def test_sync_to_sqlite(test_maintenance_csv, test_db_path):
    """Test syncing CSV to SQLite."""
    init_csv(test_maintenance_csv)
    init_sqlite_table(test_db_path)
    
    # Add entries
    add_entry(test_maintenance_csv, '2024-12-01', 45000, 'oil_change', 'Oil change', 70.00)
    add_entry(test_maintenance_csv, '2024-12-02', 45100, 'tire_rotation', 'Tire rotation', 40.00)
    
    # Sync to database
    count = sync_to_sqlite(test_maintenance_csv, test_db_path)
    assert count == 2, "Should sync 2 entries"
    
    # Verify data in database
    import sqlite3
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM maintenance")
    db_count = cursor.fetchone()[0]
    conn.close()
    
    assert db_count == 2, "Database should have 2 entries"
