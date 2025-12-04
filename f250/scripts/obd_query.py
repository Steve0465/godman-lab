#!/usr/bin/env python3
"""
OBD Query Script
Robust query CLI for parquet/SQLite with analysis and diagnostic reports.
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
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "f250.db"
DEFAULT_PARQUET_PATH = Path(__file__).parent.parent / "data" / "obd_logs.parquet"
DEFAULT_REPORT_DIR = Path(__file__).parent.parent / "data" / "notes"


def query_sqlite(db_path, dtc=None, date_range=None, misfire_only=False):
    """Query SQLite database with filters."""
    try:
        conn = sqlite3.connect(db_path)
        
        # Build query
        query = "SELECT * FROM obd_logs WHERE 1=1"
        params = []
        
        if dtc:
            query += " AND dtc_code LIKE ?"
            params.append(f"%{dtc}%")
        
        if date_range:
            start_date, end_date = date_range
            query += " AND timestamp BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        if misfire_only:
            query += " AND misfire_detected = 1"
        
        query += " ORDER BY timestamp DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        logger.info(f"Query returned {len(df)} rows")
        return df
    
    except Exception as e:
        logger.error(f"Error querying SQLite: {e}")
        raise


def query_parquet(parquet_path, dtc=None, date_range=None, misfire_only=False):
    """Query Parquet file with filters."""
    try:
        df = pd.read_parquet(parquet_path)
        logger.info(f"Loaded {len(df)} rows from parquet")
        
        # Apply filters
        if dtc:
            df = df[df['dtc_code'].astype(str).str.contains(dtc, case=False, na=False)]
        
        if date_range:
            start_date, end_date = date_range
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        if misfire_only:
            if 'misfire_detected' in df.columns:
                df = df[df['misfire_detected'] == 1]
            else:
                # Fallback: detect from dtc_code
                df = df[df['dtc_code'].astype(str).str.contains(
                    'P030[0-9]|misfire', case=False, na=False
                )]
        
        logger.info(f"Filtered to {len(df)} rows")
        return df
    
    except Exception as e:
        logger.error(f"Error querying Parquet: {e}")
        raise


def analyze_misfires(df):
    """Analyze misfire patterns in the data."""
    if df.empty:
        return "No misfire data found."
    
    analysis = []
    analysis.append("\n=== MISFIRE ANALYSIS ===")
    
    # Count by DTC code
    if 'dtc_code' in df.columns:
        dtc_counts = df['dtc_code'].value_counts()
        analysis.append("\nMisfires by DTC Code:")
        for dtc, count in dtc_counts.items():
            analysis.append(f"  {dtc}: {count} occurrences")
    
    # Correlations with engine metrics
    numeric_cols = ['rpm', 'speed', 'engine_load', 'fuel_trim_short', 'fuel_trim_long']
    available_cols = [col for col in numeric_cols if col in df.columns]
    
    if available_cols:
        analysis.append("\nAverage values during misfires:")
        for col in available_cols:
            avg = df[col].mean()
            analysis.append(f"  {col}: {avg:.2f}")
    
    return "\n".join(analysis)


def classify_fuel_trim(df):
    """Classify fuel trim status."""
    if df.empty or 'fuel_trim_short' not in df.columns:
        return "No fuel trim data available."
    
    classification = []
    classification.append("\n=== FUEL TRIM CLASSIFICATION ===")
    
    # Average fuel trims
    avg_short = df['fuel_trim_short'].mean() if 'fuel_trim_short' in df.columns else None
    avg_long = df['fuel_trim_long'].mean() if 'fuel_trim_long' in df.columns else None
    
    if avg_short is not None:
        classification.append(f"Average Short-Term Fuel Trim: {avg_short:.2f}%")
        if abs(avg_short) > 10:
            classification.append("  ⚠️  WARNING: High deviation (>10%)")
        else:
            classification.append("  ✓ Within normal range")
    
    if avg_long is not None:
        classification.append(f"\nAverage Long-Term Fuel Trim: {avg_long:.2f}%")
        if abs(avg_long) > 10:
            classification.append("  ⚠️  WARNING: High deviation (>10%)")
        else:
            classification.append("  ✓ Within normal range")
    
    # Interpretation
    if avg_short is not None and avg_long is not None:
        classification.append("\nInterpretation:")
        if avg_short > 10 and avg_long > 10:
            classification.append("  Engine running LEAN (possible vacuum leak or fuel delivery issue)")
        elif avg_short < -10 and avg_long < -10:
            classification.append("  Engine running RICH (possible sensor or injector issue)")
        else:
            classification.append("  Fuel trim values within acceptable range")
    
    return "\n".join(classification)


def generate_summary_table(df):
    """Generate a summary table of the query results."""
    if df.empty:
        return "No data to summarize."
    
    summary = []
    summary.append("\n=== SUMMARY TABLE ===")
    summary.append(f"Total Records: {len(df)}")
    
    if 'timestamp' in df.columns:
        summary.append(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # DTC summary
    if 'dtc_code' in df.columns:
        unique_dtcs = df['dtc_code'].nunique()
        summary.append(f"Unique DTC Codes: {unique_dtcs}")
    
    # Key metrics
    numeric_cols = ['rpm', 'speed', 'engine_load', 'coolant_temp']
    for col in numeric_cols:
        if col in df.columns:
            summary.append(f"{col.upper()}: min={df[col].min():.2f}, max={df[col].max():.2f}, avg={df[col].mean():.2f}")
    
    return "\n".join(summary)


def write_diagnostic_report(df, output_path, dtc=None):
    """Write a diagnostic markdown report."""
    try:
        report = []
        report.append(f"# Diagnostic Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if dtc:
            report.append(f"\n## DTC Code: {dtc}")
        
        # Summary
        report.append(generate_summary_table(df))
        
        # Misfire analysis
        if 'misfire_detected' in df.columns:
            misfire_df = df[df['misfire_detected'] == 1]
            if not misfire_df.empty:
                report.append(analyze_misfires(misfire_df))
        
        # Fuel trim analysis
        report.append(classify_fuel_trim(df))
        
        # Recent events
        report.append("\n=== RECENT EVENTS (Last 10) ===")
        if not df.empty:
            # Only include columns that exist in the dataframe
            display_cols = ['timestamp', 'dtc_code', 'rpm', 'speed', 'engine_load']
            available_cols = [col for col in display_cols if col in df.columns]
            if available_cols:
                recent = df.head(10)[available_cols].to_string(index=False)
                report.append(f"\n{recent}")
            else:
                report.append("\nNo displayable columns available.")
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("\n".join(report))
        
        logger.info(f"Diagnostic report written to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error writing diagnostic report: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Query OBD data and generate diagnostic reports"
    )
    parser.add_argument(
        '--source',
        choices=['sqlite', 'parquet'],
        default='sqlite',
        help='Data source to query'
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
        '--dtc',
        type=str,
        help='Filter by DTC code (partial match)'
    )
    parser.add_argument(
        '--range',
        nargs=2,
        metavar=('START', 'END'),
        help='Date range filter (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--misfire-only',
        action='store_true',
        help='Show only misfire events'
    )
    parser.add_argument(
        '--report',
        type=Path,
        help='Generate diagnostic report at specified path'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Limit number of results shown (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.source == 'sqlite' and not args.db_path.exists():
        logger.error(f"SQLite database not found: {args.db_path}")
        sys.exit(1)
    
    if args.source == 'parquet' and not args.parquet_path.exists():
        logger.error(f"Parquet file not found: {args.parquet_path}")
        sys.exit(1)
    
    # Query data
    try:
        if args.source == 'sqlite':
            df = query_sqlite(args.db_path, args.dtc, args.range, args.misfire_only)
        else:
            df = query_parquet(args.parquet_path, args.dtc, args.range, args.misfire_only)
        
        if df.empty:
            logger.warning("No data found matching query criteria")
            print("No results found.")
            sys.exit(0)
        
        # Display summary
        print(generate_summary_table(df))
        
        # Display misfire analysis if requested
        if args.misfire_only or (args.dtc and 'P030' in args.dtc.upper()):
            print(analyze_misfires(df))
        
        # Display fuel trim classification
        print(classify_fuel_trim(df))
        
        # Show sample data
        print(f"\n=== SAMPLE DATA (showing {min(args.limit, len(df))} of {len(df)} records) ===")
        print(df.head(args.limit).to_string(index=False))
        
        # Generate report if requested
        if args.report:
            write_diagnostic_report(df, args.report, args.dtc)
        
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error during query: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
