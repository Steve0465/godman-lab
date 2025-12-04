#!/usr/bin/env python3
"""
Maintenance Log Management Script
Manage CSV-based maintenance log with SQLite sync.
"""
import sys
import argparse
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CSV_PATH = Path(__file__).parent.parent / "data" / "maintenance_log.csv"
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "f250.db"

CSV_COLUMNS = ['date', 'mileage', 'type', 'description', 'cost', 'vendor', 'notes']


def init_csv(csv_path):
    """Initialize maintenance log CSV if it doesn't exist."""
    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(csv_path, index=False)
        logger.info(f"Created new maintenance log: {csv_path}")
    else:
        logger.info(f"Using existing maintenance log: {csv_path}")


def init_sqlite_table(db_path):
    """Initialize SQLite maintenance table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            mileage INTEGER,
            type TEXT NOT NULL,
            description TEXT,
            cost REAL,
            vendor TEXT,
            notes TEXT,
            synced_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Maintenance table initialized in {db_path}")


def add_entry(csv_path, date, mileage, entry_type, description, cost=None, vendor=None, notes=None):
    """Add a new maintenance entry to the CSV."""
    try:
        # Load existing entries
        if csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(columns=CSV_COLUMNS)
        
        # Create new entry
        new_entry = {
            'date': date,
            'mileage': mileage,
            'type': entry_type,
            'description': description,
            'cost': cost if cost is not None else '',
            'vendor': vendor if vendor else '',
            'notes': notes if notes else ''
        }
        
        # Append and save
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Added maintenance entry: {entry_type} - {description}")
        return True
    
    except Exception as e:
        logger.error(f"Error adding entry: {e}")
        return False


def get_history(csv_path, entry_type=None, limit=None):
    """Get maintenance history from CSV."""
    try:
        if not csv_path.exists():
            logger.warning(f"Maintenance log not found: {csv_path}")
            return pd.DataFrame(columns=CSV_COLUMNS)
        
        df = pd.read_csv(csv_path)
        
        # Filter by type if specified
        if entry_type:
            df = df[df['type'].str.lower() == entry_type.lower()]
        
        # Sort by date descending
        df = df.sort_values('date', ascending=False)
        
        # Apply limit if specified
        if limit:
            df = df.head(limit)
        
        return df
    
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return pd.DataFrame(columns=CSV_COLUMNS)


def sync_to_sqlite(csv_path, db_path):
    """Sync maintenance entries from CSV to SQLite."""
    try:
        # Read CSV
        if not csv_path.exists():
            logger.warning(f"No CSV file to sync: {csv_path}")
            return 0
        
        df = pd.read_csv(csv_path)
        
        if df.empty:
            logger.info("No entries to sync")
            return 0
        
        # Initialize database
        init_sqlite_table(db_path)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add synced_at column to dataframe
        df['synced_at'] = datetime.now().isoformat()
        
        # Clear existing entries and insert new ones
        # (For simplicity, we replace all entries; a more sophisticated approach would track changes)
        cursor.execute("DELETE FROM maintenance")
        
        # Insert all entries
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO maintenance (date, mileage, type, description, cost, vendor, notes, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['date'],
                row['mileage'] if pd.notna(row['mileage']) else None,
                row['type'],
                row['description'] if pd.notna(row['description']) else None,
                row['cost'] if pd.notna(row['cost']) else None,
                row['vendor'] if pd.notna(row['vendor']) else None,
                row['notes'] if pd.notna(row['notes']) else None,
                row['synced_at']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Synced {len(df)} entries to SQLite")
        return len(df)
    
    except Exception as e:
        logger.error(f"Error syncing to SQLite: {e}")
        raise


def display_entries(df):
    """Display maintenance entries in a formatted way."""
    if df.empty:
        print("No maintenance entries found.")
        return
    
    print(f"\n{'='*80}")
    print(f"MAINTENANCE HISTORY ({len(df)} entries)")
    print(f"{'='*80}\n")
    
    for idx, row in df.iterrows():
        print(f"Date: {row['date']}")
        if pd.notna(row['mileage']):
            print(f"Mileage: {row['mileage']:,.0f} miles")
        print(f"Type: {row['type']}")
        print(f"Description: {row['description']}")
        if pd.notna(row['cost']) and row['cost']:
            print(f"Cost: ${row['cost']:.2f}")
        if pd.notna(row['vendor']) and row['vendor']:
            print(f"Vendor: {row['vendor']}")
        if pd.notna(row['notes']) and row['notes']:
            print(f"Notes: {row['notes']}")
        print(f"{'-'*80}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage F250 maintenance log"
    )
    parser.add_argument(
        '--csv-path',
        type=Path,
        default=DEFAULT_CSV_PATH,
        help='Path to maintenance log CSV'
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        default=DEFAULT_DB_PATH,
        help='Path to SQLite database'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add entry command
    add_parser = subparsers.add_parser('add', help='Add a maintenance entry')
    add_parser.add_argument('--date', required=True, help='Date (YYYY-MM-DD)')
    add_parser.add_argument('--mileage', type=int, required=True, help='Mileage at service')
    add_parser.add_argument('--type', required=True, help='Type of maintenance (e.g., oil_change, tire_rotation)')
    add_parser.add_argument('--description', required=True, help='Description of work performed')
    add_parser.add_argument('--cost', type=float, help='Cost of service')
    add_parser.add_argument('--vendor', help='Vendor/shop name')
    add_parser.add_argument('--notes', help='Additional notes')
    
    # List entries command
    list_parser = subparsers.add_parser('list', help='List maintenance entries')
    list_parser.add_argument('--type', help='Filter by maintenance type')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync CSV to SQLite database')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize maintenance log')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'init':
            init_csv(args.csv_path)
            init_sqlite_table(args.db_path)
            print(f"Initialized maintenance log at {args.csv_path}")
            print(f"Initialized SQLite table in {args.db_path}")
        
        elif args.command == 'add':
            init_csv(args.csv_path)
            success = add_entry(
                args.csv_path,
                args.date,
                args.mileage,
                args.type,
                args.description,
                args.cost,
                args.vendor,
                args.notes
            )
            if success:
                print("Maintenance entry added successfully.")
                print("\nRemember to run 'sync' to update the SQLite database.")
            else:
                print("Failed to add maintenance entry.")
                sys.exit(1)
        
        elif args.command == 'list':
            df = get_history(args.csv_path, args.type, args.limit)
            display_entries(df)
        
        elif args.command == 'sync':
            count = sync_to_sqlite(args.csv_path, args.db_path)
            print(f"Synced {count} entries to SQLite database.")
        
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
