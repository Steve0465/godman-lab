#!/usr/bin/env python3
"""
Maintenance Log Management - CSV and SQLite maintenance tracking
"""

import argparse
import csv
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Get the project root directory.
    Searches up from script location for a directory containing 'f250' subdirectory.
    """
    script_path = Path(__file__).resolve()
    # Start from script directory and go up
    current = script_path.parent
    
    # Try to find project root by looking for f250 directory
    for _ in range(5):  # Limit search depth
        if (current / 'f250').exists():
            return current
        current = current.parent
    
    # If not found, assume we're already in f250/scripts and go up two levels
    return script_path.parent.parent.parent


class MaintenanceManager:
    """Manage maintenance log in CSV and SQLite"""
    
    def __init__(self, csv_path: Path, db_path: Path):
        self.csv_path = csv_path
        self.db_path = db_path
        self._ensure_csv_exists()
        
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.csv_path.exists():
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'date', 'mileage', 'type', 'description', 
                    'cost', 'shop', 'notes'
                ])
                writer.writeheader()
            logger.info(f"Created maintenance log at {self.csv_path}")
    
    def init_db(self):
        """Initialize SQLite maintenance table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    mileage INTEGER,
                    type TEXT NOT NULL,
                    description TEXT,
                    cost REAL,
                    shop TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create index on date
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_maintenance_date 
                ON maintenance(date)
            """)
            
            # Create index on type
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_maintenance_type 
                ON maintenance(type)
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"Maintenance table initialized in {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def add_entry(
        self,
        date: str,
        mileage: Optional[int],
        entry_type: str,
        description: str,
        cost: Optional[float] = None,
        shop: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Add a maintenance entry to CSV"""
        try:
            entry = {
                'date': date,
                'mileage': mileage if mileage else '',
                'type': entry_type,
                'description': description,
                'cost': cost if cost else '',
                'shop': shop if shop else '',
                'notes': notes if notes else ''
            }
            
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'date', 'mileage', 'type', 'description',
                    'cost', 'shop', 'notes'
                ])
                writer.writerow(entry)
            
            logger.info(f"Added maintenance entry: {entry_type} on {date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add entry: {e}")
            return False
    
    def get_history(
        self,
        entry_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get maintenance history from CSV"""
        try:
            df = pd.read_csv(self.csv_path)
            
            # Filter by type if specified
            if entry_type:
                df = df[df['type'] == entry_type]
            
            # Filter by date range
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to read history: {e}")
            return pd.DataFrame()
    
    def sync_to_sqlite(self) -> bool:
        """Sync CSV entries to SQLite database"""
        try:
            # Read CSV
            df = pd.read_csv(self.csv_path)
            
            if df.empty:
                logger.warning("No entries to sync")
                return True
            
            # Add timestamps
            now = datetime.now().isoformat()
            df['created_at'] = now
            df['updated_at'] = now
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Clear existing data and insert
            cursor = conn.cursor()
            cursor.execute("DELETE FROM maintenance")
            
            # Insert all records
            df.to_sql('maintenance', conn, if_exists='append', index=False)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Synced {len(df)} entries to SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False
    
    def list_entries(
        self,
        limit: Optional[int] = None,
        entry_type: Optional[str] = None
    ) -> str:
        """List maintenance entries in a formatted table"""
        df = self.get_history(entry_type=entry_type)
        
        if df.empty:
            return "No maintenance entries found."
        
        # Sort by date descending
        df = df.sort_values('date', ascending=False)
        
        if limit:
            df = df.head(limit)
        
        output = []
        output.append(f"\n{'='*80}")
        output.append(f"Maintenance History")
        output.append(f"{'='*80}")
        output.append(f"Total Entries: {len(df)}")
        
        if not df.empty:
            output.append(f"\n{df.to_string(index=False)}")
        
        output.append(f"{'='*80}\n")
        
        return "\n".join(output)
    
    def export_to_sqlite_query(self) -> List[Dict]:
        """Export maintenance entries as list of dicts for SQLite insertion"""
        try:
            df = pd.read_csv(self.csv_path)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return []


def main():
    """Main entry point"""
    # Get project root for robust default paths
    project_root = get_project_root()
    
    parser = argparse.ArgumentParser(
        description="Manage F250 maintenance log"
    )
    parser.add_argument(
        '--csv',
        type=Path,
        default=project_root / 'f250/data/maintenance_log.csv',
        help='Path to maintenance CSV file'
    )
    parser.add_argument(
        '--db',
        type=Path,
        default=project_root / 'f250/data/f250.db',
        help='Path to SQLite database'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add entry command
    add_parser = subparsers.add_parser('add', help='Add a maintenance entry')
    add_parser.add_argument('--date', required=True, help='Date (YYYY-MM-DD)')
    add_parser.add_argument('--mileage', type=int, help='Mileage')
    add_parser.add_argument('--type', required=True, help='Type (e.g., oil_change, repair)')
    add_parser.add_argument('--description', required=True, help='Description')
    add_parser.add_argument('--cost', type=float, help='Cost in dollars')
    add_parser.add_argument('--shop', help='Shop name')
    add_parser.add_argument('--notes', help='Additional notes')
    
    # List entries command
    list_parser = subparsers.add_parser('list', help='List maintenance entries')
    list_parser.add_argument('--limit', type=int, help='Limit number of entries')
    list_parser.add_argument('--type', help='Filter by type')
    list_parser.add_argument('--format', choices=['table', 'csv', 'json'], 
                           default='table', help='Output format')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync CSV to SQLite')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Get maintenance history')
    history_parser.add_argument('--type', help='Filter by type')
    history_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    history_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    history_parser.add_argument('--format', choices=['table', 'csv', 'json'],
                               default='table', help='Output format')
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        manager = MaintenanceManager(args.csv, args.db)
        
        if args.command == 'add':
            success = manager.add_entry(
                date=args.date,
                mileage=args.mileage,
                entry_type=args.type,
                description=args.description,
                cost=args.cost,
                shop=args.shop,
                notes=args.notes
            )
            if not success:
                sys.exit(1)
                
        elif args.command == 'list':
            if args.format == 'table':
                print(manager.list_entries(limit=args.limit, entry_type=args.type))
            else:
                df = manager.get_history(entry_type=args.type)
                if args.limit:
                    df = df.head(args.limit)
                if args.format == 'csv':
                    print(df.to_csv(index=False))
                else:
                    print(df.to_json(orient='records', indent=2))
                    
        elif args.command == 'sync':
            manager.init_db()
            if not manager.sync_to_sqlite():
                sys.exit(1)
                
        elif args.command == 'history':
            df = manager.get_history(
                entry_type=args.type,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            if args.format == 'table':
                print(df.to_string(index=False))
            elif args.format == 'csv':
                print(df.to_csv(index=False))
            else:
                print(df.to_json(orient='records', indent=2))
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
