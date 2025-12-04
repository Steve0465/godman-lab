#!/usr/bin/env python3
"""
Maintenance Log Script - Manage maintenance history
Tracks maintenance entries in CSV and syncs to SQLite
"""

import argparse
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import csv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_CSV_PATH = Path('f250/data/maintenance_log.csv')
DEFAULT_DB_PATH = Path('f250/data/f250.db')

# CSV headers
CSV_HEADERS = ['date', 'mileage', 'type', 'description', 'cost', 'shop', 'notes']

# SQLite schema
MAINTENANCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    mileage INTEGER,
    type TEXT,
    description TEXT,
    cost REAL,
    shop TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

MAINTENANCE_INDEX = "CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance(date);"


def ensure_csv_exists(csv_path: Path) -> None:
    """
    Ensure CSV file exists with headers
    
    Args:
        csv_path: Path to CSV file
    """
    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        logger.info(f"Created new maintenance log: {csv_path}")


def add_entry(csv_path: Path, date: str, mileage: Optional[int], 
              entry_type: str, description: str, cost: Optional[float] = None,
              shop: Optional[str] = None, notes: Optional[str] = None) -> Dict:
    """
    Add a maintenance entry to the CSV log
    
    Args:
        csv_path: Path to CSV file
        date: Date of maintenance (YYYY-MM-DD format)
        mileage: Vehicle mileage at time of maintenance
        entry_type: Type of maintenance (oil_change, repair, inspection, etc.)
        description: Description of work performed
        cost: Cost of maintenance
        shop: Shop/location where work was done
        notes: Additional notes
        
    Returns:
        Dictionary with the added entry
    """
    ensure_csv_exists(csv_path)
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {date}. Use YYYY-MM-DD")
    
    entry = {
        'date': date,
        'mileage': mileage if mileage else '',
        'type': entry_type,
        'description': description,
        'cost': cost if cost else '',
        'shop': shop if shop else '',
        'notes': notes if notes else ''
    }
    
    # Append to CSV
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(entry)
    
    logger.info(f"Added maintenance entry: {entry_type} on {date}")
    return entry


def get_history(csv_path: Path, entry_type: Optional[str] = None, 
                start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get maintenance history from CSV
    
    Args:
        csv_path: Path to CSV file
        entry_type: Filter by maintenance type
        start_date: Filter by start date (YYYY-MM-DD)
        end_date: Filter by end date (YYYY-MM-DD)
        
    Returns:
        DataFrame with maintenance history
    """
    if not csv_path.exists():
        logger.warning(f"Maintenance log not found: {csv_path}")
        return pd.DataFrame(columns=CSV_HEADERS)
    
    df = pd.read_csv(csv_path)
    
    # Apply filters
    if entry_type:
        df = df[df['type'] == entry_type]
    
    if start_date:
        df = df[df['date'] >= start_date]
    
    if end_date:
        df = df[df['date'] <= end_date]
    
    # Sort by date descending
    df = df.sort_values('date', ascending=False)
    
    return df


def sync_to_sqlite(csv_path: Path, db_path: Path) -> int:
    """
    Sync maintenance entries from CSV to SQLite database
    
    Args:
        csv_path: Path to CSV file
        db_path: Path to SQLite database
        
    Returns:
        Number of entries synced
    """
    if not csv_path.exists():
        logger.warning(f"No CSV file to sync: {csv_path}")
        return 0
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    if df.empty:
        logger.info("No maintenance entries to sync")
        return 0
    
    # Connect to database
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    
    # Create table if not exists
    conn.execute(MAINTENANCE_SCHEMA)
    conn.execute(MAINTENANCE_INDEX)
    
    # Check existing entries to avoid duplicates
    existing_df = pd.read_sql_query(
        "SELECT date, mileage, type, description FROM maintenance",
        conn
    )
    
    # Find new entries (not already in database)
    if not existing_df.empty:
        # Create composite key for comparison
        df['key'] = df['date'] + '|' + df['type'] + '|' + df['description']
        existing_df['key'] = (existing_df['date'] + '|' + 
                             existing_df['type'] + '|' + 
                             existing_df['description'])
        
        new_df = df[~df['key'].isin(existing_df['key'])].drop('key', axis=1)
    else:
        new_df = df
    
    if new_df.empty:
        logger.info("All entries already synced to database")
        conn.close()
        return 0
    
    # Insert new entries
    new_df.to_sql('maintenance', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()
    
    logger.info(f"Synced {len(new_df)} new maintenance entries to database")
    return len(new_df)


def format_history_table(df: pd.DataFrame) -> str:
    """
    Format maintenance history as a readable table
    
    Args:
        df: DataFrame with maintenance history
        
    Returns:
        Formatted table string
    """
    if df.empty:
        return "No maintenance records found."
    
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"Maintenance History ({len(df)} records)")
    lines.append(f"{'='*80}\n")
    
    for idx, row in df.iterrows():
        lines.append(f"Date: {row['date']}")
        if pd.notna(row['mileage']) and row['mileage']:
            lines.append(f"Mileage: {row['mileage']:,}")
        lines.append(f"Type: {row['type']}")
        lines.append(f"Description: {row['description']}")
        if pd.notna(row['cost']) and row['cost']:
            lines.append(f"Cost: ${row['cost']:.2f}")
        if pd.notna(row['shop']) and row['shop']:
            lines.append(f"Shop: {row['shop']}")
        if pd.notna(row['notes']) and row['notes']:
            lines.append(f"Notes: {row['notes']}")
        lines.append('-' * 80)
    
    lines.append('')
    return '\n'.join(lines)


def main():
    """Main entry point for maintenance script"""
    parser = argparse.ArgumentParser(
        description='Manage F250 maintenance log',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add maintenance entry')
    add_parser.add_argument('--date', required=True, help='Date (YYYY-MM-DD)')
    add_parser.add_argument('--mileage', type=int, help='Vehicle mileage')
    add_parser.add_argument('--type', required=True, 
                           choices=['oil_change', 'tire_rotation', 'brake_service', 
                                   'inspection', 'repair', 'fluid_change', 'other'],
                           help='Type of maintenance')
    add_parser.add_argument('--description', required=True, 
                           help='Description of work performed')
    add_parser.add_argument('--cost', type=float, help='Cost of maintenance')
    add_parser.add_argument('--shop', help='Shop/location where work was done')
    add_parser.add_argument('--notes', help='Additional notes')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List maintenance history')
    list_parser.add_argument('--type', help='Filter by maintenance type')
    list_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync CSV to SQLite database')
    
    # Common arguments
    parser.add_argument(
        '--csv-path',
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f'Path to maintenance CSV (default: {DEFAULT_CSV_PATH})'
    )
    
    parser.add_argument(
        '--db-path',
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f'Path to SQLite database (default: {DEFAULT_DB_PATH})'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'add':
            entry = add_entry(
                args.csv_path,
                args.date,
                args.mileage,
                args.type,
                args.description,
                args.cost,
                args.shop,
                args.notes
            )
            print(f"\n✓ Added maintenance entry:")
            print(f"  Date: {entry['date']}")
            print(f"  Type: {entry['type']}")
            print(f"  Description: {entry['description']}")
            
        elif args.command == 'list':
            df = get_history(
                args.csv_path,
                entry_type=args.type,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            if args.limit:
                df = df.head(args.limit)
            
            table = format_history_table(df)
            print(table)
            
        elif args.command == 'sync':
            count = sync_to_sqlite(args.csv_path, args.db_path)
            print(f"\n✓ Synced {count} entries to database")
        
        return 0
        
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())
