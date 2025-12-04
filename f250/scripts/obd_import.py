#!/usr/bin/env python3
"""
OBD Data Import Script
Robust CSV discovery, validation, and streaming import to parquet and SQLite.
"""
import os
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
DEFAULT_CSV_DIR = Path(__file__).parent.parent / "data" / "obd_csv"
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "f250.db"
DEFAULT_PARQUET_PATH = Path(__file__).parent.parent / "data" / "obd_logs.parquet"

REQUIRED_COLUMNS = ['timestamp', 'rpm', 'speed', 'engine_load']
DTC_COLUMNS = ['dtc_code', 'dtc_description']


def validate_csv(csv_path):
    """Validate CSV file has required columns and proper format."""
    try:
        df = pd.read_csv(csv_path, nrows=5)
        logger.info(f"CSV columns found: {list(df.columns)}")
        
        # Check for required columns (case-insensitive)
        df_columns_lower = [col.lower() for col in df.columns]
        missing_columns = []
        for req_col in REQUIRED_COLUMNS:
            if req_col.lower() not in df_columns_lower:
                missing_columns.append(req_col)
        
        if missing_columns:
            logger.warning(f"Missing required columns in {csv_path}: {missing_columns}")
            return False, f"Missing columns: {missing_columns}"
        
        return True, "Valid"
    except Exception as e:
        logger.error(f"Error validating {csv_path}: {e}")
        return False, str(e)


def normalize_dtc_columns(df):
    """Normalize DTC columns by combining variants and handling missing data."""
    # Create normalized DTC columns if they don't exist
    if 'dtc_code' not in df.columns:
        if 'dtc' in df.columns:
            df['dtc_code'] = df['dtc']
        elif 'diagnostic_code' in df.columns:
            df['dtc_code'] = df['diagnostic_code']
        else:
            df['dtc_code'] = None
    
    if 'dtc_description' not in df.columns:
        if 'dtc_desc' in df.columns:
            df['dtc_description'] = df['dtc_desc']
        elif 'code_description' in df.columns:
            df['dtc_description'] = df['code_description']
        else:
            df['dtc_description'] = None
    
    return df


def init_sqlite_db(db_path):
    """Initialize SQLite database with obd_logs table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obd_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            rpm REAL,
            speed REAL,
            engine_load REAL,
            coolant_temp REAL,
            intake_temp REAL,
            maf REAL,
            throttle_position REAL,
            fuel_trim_short REAL,
            fuel_trim_long REAL,
            dtc_code TEXT,
            dtc_description TEXT,
            misfire_detected INTEGER DEFAULT 0,
            source_file TEXT,
            imported_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE NOT NULL,
            imported_at TEXT NOT NULL,
            row_count INTEGER,
            status TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {db_path}")


def is_file_imported(db_path, file_name):
    """Check if a file has already been imported."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM import_log WHERE file_name = ?", (file_name,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def mark_file_imported(db_path, file_name, row_count, status="success"):
    """Mark a file as imported in the import log."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO import_log (file_name, imported_at, row_count, status)
        VALUES (?, ?, ?, ?)
    """, (file_name, datetime.now().isoformat(), row_count, status))
    conn.commit()
    conn.close()


def import_csv_to_sqlite(csv_path, db_path, dry_run=False):
    """Import CSV data to SQLite database."""
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Read {len(df)} rows from {csv_path}")
        
        # Normalize column names to lowercase
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Normalize DTC columns
        df = normalize_dtc_columns(df)
        
        # Add metadata columns
        df['source_file'] = csv_path.name
        df['imported_at'] = datetime.now().isoformat()
        
        # Detect misfires based on dtc_code
        if 'dtc_code' in df.columns:
            df['misfire_detected'] = df['dtc_code'].astype(str).str.contains(
                'P030[0-9]|misfire', case=False, na=False
            ).astype(int)
        else:
            df['misfire_detected'] = 0
        
        if dry_run:
            logger.info(f"[DRY RUN] Would import {len(df)} rows from {csv_path}")
            logger.info(f"[DRY RUN] Sample data:\n{df.head()}")
            return len(df)
        
        # Import to SQLite
        conn = sqlite3.connect(db_path)
        df.to_sql('obd_logs', conn, if_exists='append', index=False)
        conn.close()
        
        logger.info(f"Imported {len(df)} rows from {csv_path} to SQLite")
        return len(df)
    
    except Exception as e:
        logger.error(f"Error importing {csv_path} to SQLite: {e}")
        raise


def import_csv_to_parquet(csv_path, parquet_path, dry_run=False):
    """Import CSV data to Parquet file."""
    try:
        df = pd.read_csv(csv_path)
        
        # Normalize column names
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Normalize DTC columns
        df = normalize_dtc_columns(df)
        
        if dry_run:
            logger.info(f"[DRY RUN] Would append {len(df)} rows to {parquet_path}")
            return len(df)
        
        # Append to existing parquet or create new one
        if parquet_path.exists():
            existing_df = pd.read_parquet(parquet_path)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_parquet(parquet_path, index=False)
            logger.info(f"Appended {len(df)} rows to existing parquet file")
        else:
            df.to_parquet(parquet_path, index=False)
            logger.info(f"Created new parquet file with {len(df)} rows")
        
        return len(df)
    
    except Exception as e:
        logger.error(f"Error importing {csv_path} to parquet: {e}")
        raise


def discover_csv_files(csv_dir):
    """Discover all CSV files in the directory."""
    csv_dir = Path(csv_dir)
    if not csv_dir.exists():
        logger.warning(f"CSV directory does not exist: {csv_dir}")
        return []
    
    csv_files = list(csv_dir.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV files in {csv_dir}")
    return csv_files


def main():
    parser = argparse.ArgumentParser(
        description="Import OBD CSV data to SQLite and Parquet"
    )
    parser.add_argument(
        '--csv-dir',
        type=Path,
        default=DEFAULT_CSV_DIR,
        help='Directory containing CSV files to import'
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        default=DEFAULT_DB_PATH,
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--parquet-path',
        type=Path,
        default=DEFAULT_PARQUET_PATH,
        help='Path to Parquet file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate files without importing'
    )
    parser.add_argument(
        '--run',
        action='store_true',
        help='Actually run the import'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-import of already imported files'
    )
    
    args = parser.parse_args()
    
    # Require explicit --run or --dry-run
    if not args.run and not args.dry_run:
        logger.error("Must specify --run or --dry-run")
        parser.print_help()
        sys.exit(1)
    
    # Discover CSV files
    csv_files = discover_csv_files(args.csv_dir)
    if not csv_files:
        logger.error(f"No CSV files found in {args.csv_dir}")
        sys.exit(1)
    
    # Initialize database if running
    if args.run and not args.dry_run:
        args.db_path.parent.mkdir(parents=True, exist_ok=True)
        args.parquet_path.parent.mkdir(parents=True, exist_ok=True)
        init_sqlite_db(args.db_path)
    
    # Process each CSV file
    total_rows = 0
    imported_count = 0
    skipped_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        logger.info(f"\nProcessing: {csv_file.name}")
        
        # Validate CSV
        is_valid, message = validate_csv(csv_file)
        if not is_valid:
            logger.error(f"Validation failed for {csv_file.name}: {message}")
            failed_count += 1
            continue
        
        # Check if already imported
        if not args.force and args.run and not args.dry_run:
            if is_file_imported(args.db_path, csv_file.name):
                logger.info(f"Skipping already imported file: {csv_file.name}")
                skipped_count += 1
                continue
        
        # Import to SQLite and Parquet
        try:
            row_count = import_csv_to_sqlite(csv_file, args.db_path, args.dry_run)
            import_csv_to_parquet(csv_file, args.parquet_path, args.dry_run)
            
            total_rows += row_count
            imported_count += 1
            
            # Mark as imported
            if args.run and not args.dry_run:
                mark_file_imported(args.db_path, csv_file.name, row_count)
        
        except Exception as e:
            logger.error(f"Failed to import {csv_file.name}: {e}")
            failed_count += 1
            if args.run and not args.dry_run:
                mark_file_imported(args.db_path, csv_file.name, 0, status="failed")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info(f"Import Summary:")
    logger.info(f"  Total files found: {len(csv_files)}")
    logger.info(f"  Successfully imported: {imported_count}")
    logger.info(f"  Skipped (already imported): {skipped_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Total rows imported: {total_rows}")
    logger.info("="*60)
    
    # Exit with appropriate code
    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
