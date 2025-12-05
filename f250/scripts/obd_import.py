#!/usr/bin/env python3
"""
OBD Import Script - Robust CSV discovery and validation
Streams imports to parquet and SQLite database (f250/data/f250.db)
"""

import sys
import argparse
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required columns for OBD data
REQUIRED_COLUMNS = ['timestamp', 'device_time']
# Optional DTC columns that may appear
DTC_COLUMNS = ['dtc', 'dtc_code', 'dtc_description', 'trouble_codes']

# Schema for obd_logs table
OBD_LOGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS obd_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_time TEXT,
    session_id TEXT,
    dtc_code TEXT,
    dtc_description TEXT,
    engine_rpm REAL,
    vehicle_speed REAL,
    coolant_temp REAL,
    intake_temp REAL,
    maf REAL,
    throttle_pos REAL,
    fuel_pressure REAL,
    fuel_level REAL,
    o2_sensor_1 REAL,
    o2_sensor_2 REAL,
    stft_bank1 REAL,
    ltft_bank1 REAL,
    stft_bank2 REAL,
    ltft_bank2 REAL,
    misfire_count REAL,
    raw_data TEXT,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# Index for efficient queries
OBD_LOGS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_timestamp ON obd_logs(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_dtc_code ON obd_logs(dtc_code);",
    "CREATE INDEX IF NOT EXISTS idx_session_id ON obd_logs(session_id);"
]


def discover_csv_files(csv_dir: Path) -> List[Path]:
    """
    Discover all CSV files in the given directory
    
    Args:
        csv_dir: Directory to search for CSV files
        
    Returns:
        List of Path objects for CSV files found
    """
    csv_files = list(csv_dir.glob("*.csv"))
    logger.info(f"Discovered {len(csv_files)} CSV files in {csv_dir}")
    return sorted(csv_files)


def validate_csv(csv_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate CSV file has required columns
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Read just the header
        df_sample = pd.read_csv(csv_path, nrows=0)
        columns = set(df_sample.columns.str.lower())
        
        # Check for at least one required column
        has_required = any(col in columns for col in REQUIRED_COLUMNS)
        
        if not has_required:
            return False, f"Missing required columns. Need at least one of: {REQUIRED_COLUMNS}"
        
        logger.debug(f"Validated {csv_path.name}: {len(df_sample.columns)} columns")
        return True, None
        
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}"


def normalize_dtc_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DTC-related columns to standard dtc_code and dtc_description
    
    Args:
        df: DataFrame to normalize
        
    Returns:
        Normalized DataFrame
    """
    # Normalize column names to lowercase
    df.columns = df.columns.str.lower().str.strip()
    
    # Map various DTC column names to standard names
    if 'dtc' in df.columns and 'dtc_code' not in df.columns:
        df['dtc_code'] = df['dtc']
    elif 'trouble_codes' in df.columns and 'dtc_code' not in df.columns:
        df['dtc_code'] = df['trouble_codes']
    
    # Ensure dtc_code and dtc_description exist
    if 'dtc_code' not in df.columns:
        df['dtc_code'] = None
    if 'dtc_description' not in df.columns:
        df['dtc_description'] = None
    
    return df


def create_database(db_path: Path) -> sqlite3.Connection:
    """
    Create SQLite database with schema
    
    Args:
        db_path: Path to database file
        
    Returns:
        Database connection
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    
    # Create table
    conn.execute(OBD_LOGS_SCHEMA)
    
    # Create indexes
    for idx_sql in OBD_LOGS_INDEXES:
        conn.execute(idx_sql)
    
    conn.commit()
    logger.info(f"Database initialized at {db_path}")
    
    return conn


def import_csv_to_db(csv_path: Path, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """
    Import CSV data to SQLite database
    
    Args:
        csv_path: Path to CSV file
        conn: Database connection
        dry_run: If True, only validate without importing
        
    Returns:
        Number of rows imported
    """
    try:
        # Read CSV in chunks for memory efficiency
        chunk_size = 1000
        total_rows = 0
        
        for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size):
            # Normalize DTC columns
            chunk_df = normalize_dtc_columns(chunk_df)
            
            # Map columns to database schema, checking for existence
            db_columns = {}
            column_map = [
                ('timestamp', ['timestamp', 'device_time']),
                ('device_time', ['device_time', 'timestamp']),
                ('session_id', ['session_id']),
                ('dtc_code', ['dtc_code']),
                ('dtc_description', ['dtc_description']),
                ('engine_rpm', ['engine_rpm', 'rpm']),
                ('vehicle_speed', ['vehicle_speed', 'speed']),
                ('coolant_temp', ['coolant_temp', 'coolant_temperature']),
                ('intake_temp', ['intake_temp', 'intake_air_temp']),
                ('maf', ['maf', 'mass_air_flow']),
                ('throttle_pos', ['throttle_pos', 'throttle_position']),
                ('fuel_pressure', ['fuel_pressure']),
                ('fuel_level', ['fuel_level']),
                ('o2_sensor_1', ['o2_sensor_1', 'o2_b1s1']),
                ('o2_sensor_2', ['o2_sensor_2', 'o2_b1s2']),
                ('stft_bank1', ['stft_bank1', 'short_ft_1']),
                ('ltft_bank1', ['ltft_bank1', 'long_ft_1']),
                ('stft_bank2', ['stft_bank2', 'short_ft_2']),
                ('ltft_bank2', ['ltft_bank2', 'long_ft_2']),
                ('misfire_count', ['misfire_count', 'misfires']),
            ]
            for key, col_names in column_map:
                for col_name in col_names:
                    if col_name in chunk_df.columns:
                        db_columns[key] = chunk_df[col_name]
                        break
            
            # Create DataFrame for import with only available columns
            import_df = pd.DataFrame(db_columns)
            
            if not dry_run:
                # Import to database
                import_df.to_sql('obd_logs', conn, if_exists='append', index=False)
            
            total_rows += len(chunk_df)
        
        logger.info(f"{'Would import' if dry_run else 'Imported'} {total_rows} rows from {csv_path.name}")
        return total_rows
        
    except Exception as e:
        logger.error(f"Error importing {csv_path.name}: {str(e)}")
        raise


def import_csv_to_parquet(csv_path: Path, output_dir: Path, dry_run: bool = False) -> Path:
    """
    Convert CSV to Parquet format
    
    Args:
        csv_path: Path to CSV file
        output_dir: Directory for output parquet files
        dry_run: If True, only validate without converting
        
    Returns:
        Path to created parquet file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / f"{csv_path.stem}.parquet"
    
    try:
        df = pd.read_csv(csv_path)
        df = normalize_dtc_columns(df)
        
        if not dry_run:
            df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
            logger.info(f"Converted {csv_path.name} to {parquet_path.name}")
        else:
            logger.info(f"Would convert {csv_path.name} to {parquet_path.name}")
        
        return parquet_path
        
    except Exception as e:
        logger.error(f"Error converting {csv_path.name} to parquet: {str(e)}")
        raise


def main():
    """Main entry point for OBD import script"""
    parser = argparse.ArgumentParser(
        description='Import OBD CSV data to SQLite and Parquet',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--csv-dir',
        type=Path,
        default=Path('f250/data/csv'),
        help='Directory containing CSV files (default: f250/data/csv)'
    )
    
    parser.add_argument(
        '--db-path',
        type=Path,
        default=Path('f250/data/f250.db'),
        help='Path to SQLite database (default: f250/data/f250.db)'
    )
    
    parser.add_argument(
        '--parquet-dir',
        type=Path,
        default=Path('f250/data/parquet'),
        help='Directory for parquet files (default: f250/data/parquet)'
    )
    
    parser.add_argument(
        '--run',
        action='store_true',
        help='Execute the import'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate files without importing'
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
    
    # Validate arguments
    if not args.run and not args.dry_run:
        parser.error("Must specify either --run or --dry-run")
    
    if not args.csv_dir.exists():
        logger.error(f"CSV directory does not exist: {args.csv_dir}")
        sys.exit(1)
    
    # Discover CSV files
    csv_files = discover_csv_files(args.csv_dir)
    
    if not csv_files:
        logger.warning(f"No CSV files found in {args.csv_dir}")
        sys.exit(0)
    
    # Validate all CSV files first
    valid_files = []
    for csv_file in csv_files:
        is_valid, error_msg = validate_csv(csv_file)
        if is_valid:
            valid_files.append(csv_file)
            logger.info(f"✓ Valid: {csv_file.name}")
        else:
            logger.warning(f"✗ Invalid: {csv_file.name} - {error_msg}")
    
    if not valid_files:
        logger.error("No valid CSV files to import")
        return 1
    
    logger.info(f"Found {len(valid_files)} valid CSV files")
    
    # Initialize database if not dry run
    conn = None
    if args.run:
        conn = create_database(args.db_path)
    
    # Import files
    total_imported = 0
    try:
        for csv_file in valid_files:
            try:
                # Import to database
                if conn:
                    rows = import_csv_to_db(csv_file, conn, dry_run=args.dry_run)
                    total_imported += rows
                
                # Convert to parquet
                import_csv_to_parquet(csv_file, args.parquet_dir, dry_run=args.dry_run)
                
            except Exception as e:
                logger.error(f"Failed to process {csv_file.name}: {str(e)}")
                continue
        
        if conn:
            conn.commit()
        
        logger.info(f"Import complete: {total_imported} total rows")
        return 0
        
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
