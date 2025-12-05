#!/usr/bin/env python3
"""
OBD Query Script - Robust query CLI for parquet and SQLite
Supports filtering, analysis, and diagnostic report generation
"""

import argparse
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Misfire DTC patterns (P030x codes indicate cylinder misfires)
MISFIRE_DTC_PATTERN = 'P030'


def query_sqlite(db_path: Path, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Query SQLite database with filters
    
    Args:
        db_path: Path to SQLite database
        filters: Dictionary of filter parameters
        
    Returns:
        DataFrame with query results
    """
    conn = sqlite3.connect(str(db_path))
    
    # Build query
    query = "SELECT * FROM obd_logs WHERE 1=1"
    params = []
    
    if filters.get('dtc'):
        query += " AND dtc_code LIKE ?"
        params.append(f"%{filters['dtc']}%")
    
    if filters.get('start_date'):
        query += " AND timestamp >= ?"
        params.append(filters['start_date'])
    
    if filters.get('end_date'):
        query += " AND timestamp <= ?"
        params.append(filters['end_date'])
    
    if filters.get('misfire_only'):
        query += " AND (misfire_count > 0 OR dtc_code LIKE ?)"
        params.append(f"%{MISFIRE_DTC_PATTERN}%")
    
    query += " ORDER BY timestamp"
    
    logger.debug(f"Query: {query}")
    logger.debug(f"Params: {params}")
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def query_parquet(parquet_dir: Path, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Query parquet files with filters
    
    Args:
        parquet_dir: Directory containing parquet files
        filters: Dictionary of filter parameters
        
    Returns:
        DataFrame with query results
    """
    parquet_files = list(parquet_dir.glob("*.parquet"))
    
    if not parquet_files:
        logger.warning(f"No parquet files found in {parquet_dir}")
        return pd.DataFrame()
    
    # Read all parquet files
    dfs = []
    for pf in parquet_files:
        try:
            df = pd.read_parquet(pf)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Error reading {pf.name}: {str(e)}")
    
    if not dfs:
        return pd.DataFrame()
    
    # Combine all dataframes
    df = pd.concat(dfs, ignore_index=True)
    
    # Apply filters
    if filters.get('dtc') and 'dtc_code' in df.columns:
        df = df[df['dtc_code'].str.contains(filters['dtc'], case=False, na=False)]
    
    if filters.get('start_date') and 'timestamp' in df.columns:
        df = df[df['timestamp'] >= filters['start_date']]
    
    if filters.get('end_date') and 'timestamp' in df.columns:
        df = df[df['timestamp'] <= filters['end_date']]
    
    if filters.get('misfire_only'):
        if 'misfire_count' in df.columns:
            df = df[(df['misfire_count'] > 0) | 
                   (df['dtc_code'].str.contains(MISFIRE_DTC_PATTERN, case=False, na=False))]
        else:
            df = df[df['dtc_code'].str.contains(MISFIRE_DTC_PATTERN, case=False, na=False)]
    
    # Sort by timestamp
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')
    
    return df


def analyze_misfires(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze misfire data from OBD logs
    
    Args:
        df: DataFrame with OBD data
        
    Returns:
        Dictionary with misfire analysis
    """
    analysis = {
        'total_misfire_events': 0,
        'total_misfire_count': 0,
        'misfire_dtc_count': 0,
        'affected_cylinders': set(),
        'avg_rpm_during_misfire': None,
        'avg_load_during_misfire': None,
    }
    
    if df.empty:
        return analysis
    
    # Count misfire events
    if 'misfire_count' in df.columns:
        misfire_df = df[df['misfire_count'] > 0]
        analysis['total_misfire_events'] = len(misfire_df)
        analysis['total_misfire_count'] = misfire_df['misfire_count'].sum()
        
        if 'engine_rpm' in df.columns and not misfire_df.empty:
            analysis['avg_rpm_during_misfire'] = misfire_df['engine_rpm'].mean()
    
    # Count misfire DTCs
    if 'dtc_code' in df.columns:
        misfire_dtcs = df[df['dtc_code'].str.contains(MISFIRE_DTC_PATTERN, case=False, na=False)]
        analysis['misfire_dtc_count'] = len(misfire_dtcs)
        
        # Extract cylinder numbers from DTC codes (P0301 = cylinder 1, etc.)
        for dtc in misfire_dtcs['dtc_code'].dropna().unique():
            if dtc.upper().startswith(MISFIRE_DTC_PATTERN) and len(dtc) >= 5:
                cyl = dtc[4]
                if cyl.isdigit() and cyl != '0':
                    analysis['affected_cylinders'].add(int(cyl))
    
    analysis['affected_cylinders'] = sorted(list(analysis['affected_cylinders']))
    
    return analysis


def classify_fuel_trim(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Classify fuel trim status (rich, lean, normal)
    
    Args:
        df: DataFrame with OBD data
        
    Returns:
        Dictionary with fuel trim classification
    """
    classification = {
        'bank1_status': 'unknown',
        'bank2_status': 'unknown',
        'bank1_avg_stft': None,
        'bank1_avg_ltft': None,
        'bank2_avg_stft': None,
        'bank2_avg_ltft': None,
        'concerns': []
    }
    
    if df.empty:
        return classification
    
    # Bank 1 analysis
    if 'stft_bank1' in df.columns and 'ltft_bank1' in df.columns:
        stft1 = df['stft_bank1'].dropna()
        ltft1 = df['ltft_bank1'].dropna()
        
        if not stft1.empty:
            classification['bank1_avg_stft'] = stft1.mean()
        if not ltft1.empty:
            classification['bank1_avg_ltft'] = ltft1.mean()
        
        if classification['bank1_avg_ltft'] is not None:
            if classification['bank1_avg_ltft'] > 10:
                classification['bank1_status'] = 'lean'
                classification['concerns'].append('Bank 1 running lean (high positive LTFT)')
            elif classification['bank1_avg_ltft'] < -10:
                classification['bank1_status'] = 'rich'
                classification['concerns'].append('Bank 1 running rich (high negative LTFT)')
            else:
                classification['bank1_status'] = 'normal'
    
    # Bank 2 analysis
    if 'stft_bank2' in df.columns and 'ltft_bank2' in df.columns:
        stft2 = df['stft_bank2'].dropna()
        ltft2 = df['ltft_bank2'].dropna()
        
        if not stft2.empty:
            classification['bank2_avg_stft'] = stft2.mean()
        if not ltft2.empty:
            classification['bank2_avg_ltft'] = ltft2.mean()
        
        if classification['bank2_avg_ltft'] is not None:
            if classification['bank2_avg_ltft'] > 10:
                classification['bank2_status'] = 'lean'
                classification['concerns'].append('Bank 2 running lean (high positive LTFT)')
            elif classification['bank2_avg_ltft'] < -10:
                classification['bank2_status'] = 'rich'
                classification['concerns'].append('Bank 2 running rich (high negative LTFT)')
            else:
                classification['bank2_status'] = 'normal'
    
    return classification


def generate_summary_table(df: pd.DataFrame) -> str:
    """
    Generate summary table of query results
    
    Args:
        df: DataFrame with query results
        
    Returns:
        Formatted summary table string
    """
    if df.empty:
        return "No data found."
    
    summary = []
    summary.append(f"\n{'='*60}")
    summary.append(f"OBD Query Results Summary")
    summary.append(f"{'='*60}")
    summary.append(f"Total records: {len(df)}")
    
    if 'timestamp' in df.columns:
        summary.append(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    if 'dtc_code' in df.columns:
        unique_dtcs = df['dtc_code'].dropna().unique()
        summary.append(f"Unique DTCs: {len(unique_dtcs)}")
        if len(unique_dtcs) > 0:
            summary.append(f"  {', '.join(unique_dtcs[:10])}")
            if len(unique_dtcs) > 10:
                summary.append(f"  ... and {len(unique_dtcs) - 10} more")
    
    # Key statistics
    if 'engine_rpm' in df.columns:
        rpm_stats = df['engine_rpm'].describe()
        summary.append(f"\nEngine RPM: min={rpm_stats['min']:.0f}, "
                      f"avg={rpm_stats['mean']:.0f}, max={rpm_stats['max']:.0f}")
    
    if 'vehicle_speed' in df.columns:
        speed_stats = df['vehicle_speed'].describe()
        summary.append(f"Vehicle Speed: min={speed_stats['min']:.0f}, "
                      f"avg={speed_stats['mean']:.0f}, max={speed_stats['max']:.0f}")
    
    summary.append(f"{'='*60}\n")
    
    return '\n'.join(summary)


def generate_diagnostic_report(df: pd.DataFrame, output_path: Path, 
                               dtc: Optional[str] = None) -> None:
    """
    Generate diagnostic markdown report
    
    Args:
        df: DataFrame with OBD data
        output_path: Path to write report
        dtc: Optional specific DTC to focus on
    """
    report = []
    report.append(f"# OBD Diagnostic Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    if dtc:
        report.append(f"## Focus: DTC {dtc}")
        report.append("")
    
    # Summary section
    report.append(f"## Data Summary")
    report.append(f"- Total records: {len(df)}")
    if 'timestamp' in df.columns and not df.empty:
        report.append(f"- Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    report.append("")
    
    # DTC Analysis
    if 'dtc_code' in df.columns:
        unique_dtcs = df['dtc_code'].dropna().unique()
        report.append(f"## Diagnostic Trouble Codes")
        report.append(f"Found {len(unique_dtcs)} unique DTCs:")
        report.append("")
        for code in unique_dtcs:
            count = len(df[df['dtc_code'] == code])
            report.append(f"- **{code}**: {count} occurrences")
        report.append("")
    
    # Misfire Analysis
    misfire_analysis = analyze_misfires(df)
    if misfire_analysis['total_misfire_events'] > 0 or misfire_analysis['misfire_dtc_count'] > 0:
        report.append(f"## Misfire Analysis")
        report.append(f"- Total misfire events: {misfire_analysis['total_misfire_events']}")
        report.append(f"- Total misfire count: {misfire_analysis['total_misfire_count']}")
        report.append(f"- Misfire DTCs logged: {misfire_analysis['misfire_dtc_count']}")
        if misfire_analysis['affected_cylinders']:
            report.append(f"- Affected cylinders: {', '.join(map(str, misfire_analysis['affected_cylinders']))}")
        if misfire_analysis['avg_rpm_during_misfire']:
            report.append(f"- Average RPM during misfires: {misfire_analysis['avg_rpm_during_misfire']:.0f}")
        report.append("")
    
    # Fuel Trim Analysis
    fuel_trim = classify_fuel_trim(df)
    report.append(f"## Fuel Trim Analysis")
    report.append(f"- Bank 1 status: **{fuel_trim['bank1_status']}**")
    if fuel_trim['bank1_avg_ltft'] is not None:
        report.append(f"  - Average LTFT: {fuel_trim['bank1_avg_ltft']:.2f}%")
    if fuel_trim['bank1_avg_stft'] is not None:
        report.append(f"  - Average STFT: {fuel_trim['bank1_avg_stft']:.2f}%")
    
    report.append(f"- Bank 2 status: **{fuel_trim['bank2_status']}**")
    if fuel_trim['bank2_avg_ltft'] is not None:
        report.append(f"  - Average LTFT: {fuel_trim['bank2_avg_ltft']:.2f}%")
    if fuel_trim['bank2_avg_stft'] is not None:
        report.append(f"  - Average STFT: {fuel_trim['bank2_avg_stft']:.2f}%")
    report.append("")
    
    if fuel_trim['concerns']:
        report.append(f"### Concerns")
        for concern in fuel_trim['concerns']:
            report.append(f"- {concern}")
        report.append("")
    
    # Recommendations
    report.append(f"## Recommendations")
    report.append("")
    report.append(f"Based on the analysis, consider:")
    report.append(f"- Review maintenance history for related repairs")
    report.append(f"- Check for pending DTCs")
    report.append(f"- Verify sensor readings are within normal ranges")
    report.append("")
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))
    
    logger.info(f"Diagnostic report written to {output_path}")


def main():
    """Main entry point for OBD query script"""
    parser = argparse.ArgumentParser(
        description='Query OBD data from SQLite or Parquet files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--source',
        choices=['sqlite', 'parquet'],
        default='sqlite',
        help='Data source to query (default: sqlite)'
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
        help='Directory containing parquet files (default: f250/data/parquet)'
    )
    
    parser.add_argument(
        '--dtc',
        type=str,
        help='Filter by DTC code (partial match supported)'
    )
    
    parser.add_argument(
        '--range',
        nargs=2,
        metavar=('START', 'END'),
        help='Date range filter (format: YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--misfire-only',
        action='store_true',
        help='Show only misfire-related records'
    )
    
    parser.add_argument(
        '--report',
        type=Path,
        help='Generate diagnostic report at specified path'
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
    
    # Build filters
    filters = {}
    if args.dtc:
        filters['dtc'] = args.dtc
    if args.range:
        filters['start_date'] = args.range[0]
        filters['end_date'] = args.range[1]
    if args.misfire_only:
        filters['misfire_only'] = True
    
    # Query data
    try:
        if args.source == 'sqlite':
            if not args.db_path.exists():
                logger.error(f"Database not found: {args.db_path}")
                return 1
            df = query_sqlite(args.db_path, filters)
        else:
            if not args.parquet_dir.exists():
                logger.error(f"Parquet directory not found: {args.parquet_dir}")
                return 1
            df = query_parquet(args.parquet_dir, filters)
        
        # Display summary
        summary = generate_summary_table(df)
        print(summary)
        
        # Generate report if requested
        if args.report:
            generate_diagnostic_report(df, args.report, dtc=args.dtc)
        
        return 0
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())
