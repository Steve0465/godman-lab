#!/usr/bin/env python3
"""
OBD Import Script - Robust CSV discovery, validation, and import to SQLite and Parquet
"""

import argparse
import csv
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required columns for OBD CSV files
REQUIRED_COLUMNS = ['timestamp', 'rpm', 'speed', 'coolant_temp']
DTC_COLUMNS = ['dtc', 'dtc_code', 'trouble_code']


class OBDImporter:
    """Handles OBD CSV import to SQLite and Parquet"""
    
    def __init__(self, db_path: Path, parquet_dir: Path):
        self.db_path = db_path
        self.parquet_dir = parquet_dir
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        
    def init_db(self):
        """Initialize SQLite database with required schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create obd_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obd_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    rpm REAL,
                    speed REAL,
                    coolant_temp REAL,
                    dtc TEXT,
                    fuel_trim_st REAL,
                    fuel_trim_lt REAL,
                    misfire_count INTEGER,
                    source_file TEXT,
                    import_date TEXT NOT NULL
                )
            """)
            
            # Create imported_files table for idempotency
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS imported_files (
                    file_path TEXT PRIMARY KEY,
                    import_date TEXT NOT NULL,
                    row_count INTEGER,
                    status TEXT
                )
            """)
            
            # Create index on timestamp
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_obd_timestamp 
                ON obd_logs(timestamp)
            """)
            
            # Create index on dtc
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_obd_dtc 
                ON obd_logs(dtc)
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def is_file_imported(self, file_path: Path) -> bool:
        """Check if file has already been imported"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status FROM imported_files WHERE file_path = ?",
                (str(file_path),)
            )
            result = cursor.fetchone()
            conn.close()
            return result is not None and result[0] == 'success'
        except sqlite3.Error as e:
            logger.error(f"Error checking import status: {e}")
            return False
    
    def mark_file_imported(self, file_path: Path, row_count: int, status: str):
        """Mark file as imported in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO imported_files 
                (file_path, import_date, row_count, status)
                VALUES (?, ?, ?, ?)
            """, (str(file_path), datetime.now().isoformat(), row_count, status))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Error marking file as imported: {e}")
            raise
    
    def validate_csv(self, file_path: Path) -> tuple[bool, List[str]]:
        """Validate CSV file has required columns"""
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                
            missing = [col for col in REQUIRED_COLUMNS if col not in headers]
            
            if missing:
                return False, missing
            return True, []
            
        except Exception as e:
            logger.error(f"Error validating {file_path}: {e}")
            return False, [str(e)]
    
    def normalize_dtc_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DTC columns to a single 'dtc' column"""
        dtc_col = None
        for col in DTC_COLUMNS:
            if col in df.columns:
                dtc_col = col
                break
        
        if dtc_col and dtc_col != 'dtc':
            df['dtc'] = df[dtc_col]
            if dtc_col != 'dtc':
                df = df.drop(columns=[dtc_col])
        elif 'dtc' not in df.columns:
            df['dtc'] = None
            
        return df
    
    def import_csv(self, file_path: Path, dry_run: bool = False) -> bool:
        """Import a single CSV file"""
        logger.info(f"Processing {file_path}")
        
        # Check if already imported
        if self.is_file_imported(file_path):
            logger.info(f"Skipping {file_path} - already imported")
            return True
        
        # Validate
        valid, errors = self.validate_csv(file_path)
        if not valid:
            logger.error(f"Validation failed for {file_path}: {errors}")
            self.mark_file_imported(file_path, 0, 'validation_failed')
            return False
        
        if dry_run:
            logger.info(f"[DRY RUN] Would import {file_path}")
            return True
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            logger.info(f"Read {len(df)} rows from {file_path}")
            
            # Normalize DTC column
            df = self.normalize_dtc_column(df)
            
            # Add metadata
            df['source_file'] = str(file_path)
            df['import_date'] = datetime.now().isoformat()
            
            # Ensure optional columns exist
            for col in ['fuel_trim_st', 'fuel_trim_lt', 'misfire_count']:
                if col not in df.columns:
                    df[col] = None
            
            # Write to Parquet
            parquet_path = self.parquet_dir / f"{file_path.stem}.parquet"
            df.to_parquet(parquet_path, index=False)
            logger.info(f"Wrote Parquet to {parquet_path}")
            
            # Write to SQLite
            conn = sqlite3.connect(self.db_path)
            df.to_sql('obd_logs', conn, if_exists='append', index=False)
            conn.close()
            logger.info(f"Imported {len(df)} rows to SQLite")
            
            # Mark as imported
            self.mark_file_imported(file_path, len(df), 'success')
            
            return True
            
        except Exception as e:
            logger.error(f"Import failed for {file_path}: {e}")
            self.mark_file_imported(file_path, 0, f'error: {str(e)}')
            return False
    
    def discover_csvs(self, csv_dir: Path) -> List[Path]:
        """Discover all CSV files in directory"""
        csv_files = list(csv_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files in {csv_dir}")
        return csv_files
    
    def import_all(self, csv_dir: Path, dry_run: bool = False) -> tuple[int, int]:
        """Import all CSV files from directory"""
        csv_files = self.discover_csvs(csv_dir)
        
        if not csv_files:
            logger.warning(f"No CSV files found in {csv_dir}")
            return 0, 0
        
        success_count = 0
        fail_count = 0
        
        for csv_file in csv_files:
            if self.import_csv(csv_file, dry_run):
                success_count += 1
            else:
                fail_count += 1
        
        return success_count, fail_count


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Import OBD CSV files to SQLite and Parquet"
    )
    parser.add_argument(
        '--csv-dir',
        type=Path,
        default=Path('f250/data/obd_csv'),
        help='Directory containing CSV files to import'
    )
    parser.add_argument(
        '--db',
        type=Path,
        default=Path('f250/data/f250.db'),
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--parquet-dir',
        type=Path,
        default=Path('f250/data/parquet'),
        help='Directory for Parquet files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate files without importing'
    )
    parser.add_argument(
        '--run',
        action='store_true',
        help='Run the import'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Require explicit --run or --dry-run
    if not args.run and not args.dry_run:
        parser.error("Must specify either --run or --dry-run")
    
    try:
        importer = OBDImporter(args.db, args.parquet_dir)
        
        # Initialize database
        if not args.dry_run:
            importer.init_db()
        
        # Import files
        success, failed = importer.import_all(args.csv_dir, args.dry_run)
        
        logger.info(f"Import complete: {success} successful, {failed} failed")
        
        if failed > 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
