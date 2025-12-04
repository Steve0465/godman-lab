#!/usr/bin/env python3
"""
Diagnostic Report Generator - Create comprehensive diagnostic sheets
Pulls OBD events, maintenance history, and photo references
"""

import argparse
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_obd_events(db_path: Path, dtc: Optional[str] = None, 
                   start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve OBD events from database
    
    Args:
        db_path: Path to SQLite database
        dtc: Optional DTC code to filter by
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        DataFrame with OBD events
    """
    if not db_path.exists():
        logger.warning(f"Database not found: {db_path}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(str(db_path))
    
    query = "SELECT * FROM obd_logs WHERE 1=1"
    params = []
    
    if dtc:
        query += " AND dtc_code LIKE ?"
        params.append(f"%{dtc}%")
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    query += " ORDER BY timestamp DESC"
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error querying OBD events: {str(e)}")
        df = pd.DataFrame()
    finally:
        conn.close()
    
    return df


def get_maintenance_entries(db_path: Path, csv_path: Path,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            entry_type: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve maintenance entries from database or CSV
    
    Args:
        db_path: Path to SQLite database
        csv_path: Path to maintenance CSV (fallback)
        start_date: Optional start date
        end_date: Optional end date
        entry_type: Optional maintenance type filter
        
    Returns:
        DataFrame with maintenance entries
    """
    # Try database first
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        
        query = "SELECT * FROM maintenance WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        if entry_type:
            query += " AND type = ?"
            params.append(entry_type)
        
        query += " ORDER BY date DESC"
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            logger.warning(f"Could not query maintenance from database: {str(e)}")
            conn.close()
    
    # Fallback to CSV
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        if entry_type:
            df = df[df['type'] == entry_type]
        
        return df.sort_values('date', ascending=False)
    
    logger.warning("No maintenance data found")
    return pd.DataFrame()


def find_related_photos(photo_dir: Path, dtc: Optional[str] = None,
                       job_id: Optional[str] = None) -> List[Path]:
    """
    Find photos related to a diagnostic issue or job
    
    Args:
        photo_dir: Directory containing photos
        dtc: DTC code to match in filename
        job_id: Job ID to match in filename
        
    Returns:
        List of photo paths
    """
    if not photo_dir.exists():
        return []
    
    photos = []
    
    # Search for matching photos
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.heic']:
        for photo in photo_dir.glob(f"**/{ext}"):
            filename = photo.name.lower()
            
            # Check if filename contains DTC or job_id
            if dtc and dtc.lower() in filename:
                photos.append(photo)
            elif job_id and job_id.lower() in filename:
                photos.append(photo)
    
    return sorted(photos)


def generate_report(output_path: Path, dtc: Optional[str] = None,
                   job_id: Optional[str] = None, title: Optional[str] = None,
                   obd_data: pd.DataFrame = None,
                   maintenance_data: pd.DataFrame = None,
                   photos: List[Path] = None) -> None:
    """
    Generate comprehensive diagnostic report
    
    Args:
        output_path: Path to write report
        dtc: DTC code being diagnosed
        job_id: Job/case ID
        title: Custom title for report
        obd_data: DataFrame with OBD events
        maintenance_data: DataFrame with maintenance entries
        photos: List of related photo paths
    """
    report = []
    
    # Header
    report.append("# Diagnostic Report")
    
    if title:
        report.append(f"## {title}")
    
    if dtc:
        report.append(f"### DTC: {dtc}")
    
    if job_id:
        report.append(f"### Job ID: {job_id}")
    
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n---\n")
    
    # Issue Summary
    report.append("## Issue Summary")
    report.append("")
    report.append("*Document the primary symptoms and concerns here*")
    report.append("")
    
    # OBD Events Section
    if obd_data is not None and not obd_data.empty:
        report.append("## OBD Diagnostic Data")
        report.append("")
        report.append(f"Total events logged: {len(obd_data)}")
        
        if 'timestamp' in obd_data.columns:
            report.append(f"Date range: {obd_data['timestamp'].min()} to {obd_data['timestamp'].max()}")
        
        report.append("")
        
        # DTC Summary
        if 'dtc_code' in obd_data.columns:
            dtc_counts = obd_data['dtc_code'].value_counts()
            report.append("### Diagnostic Trouble Codes")
            report.append("")
            for code, count in dtc_counts.items():
                if pd.notna(code):
                    report.append(f"- **{code}**: {count} occurrences")
            report.append("")
        
        # Key Readings
        report.append("### Key Sensor Readings")
        report.append("")
        
        if 'engine_rpm' in obd_data.columns:
            rpm_stats = obd_data['engine_rpm'].describe()
            report.append(f"- **Engine RPM**: min={rpm_stats.get('min', 0):.0f}, "
                         f"avg={rpm_stats.get('mean', 0):.0f}, max={rpm_stats.get('max', 0):.0f}")
        
        if 'vehicle_speed' in obd_data.columns:
            speed_stats = obd_data['vehicle_speed'].describe()
            report.append(f"- **Vehicle Speed**: min={speed_stats.get('min', 0):.0f}, "
                         f"avg={speed_stats.get('mean', 0):.0f}, max={speed_stats.get('max', 0):.0f}")
        
        if 'coolant_temp' in obd_data.columns:
            temp_stats = obd_data['coolant_temp'].describe()
            report.append(f"- **Coolant Temp**: min={temp_stats.get('min', 0):.0f}, "
                         f"avg={temp_stats.get('mean', 0):.0f}, max={temp_stats.get('max', 0):.0f}")
        
        # Fuel Trim Analysis
        if 'ltft_bank1' in obd_data.columns or 'ltft_bank2' in obd_data.columns:
            report.append("")
            report.append("### Fuel Trim Analysis")
            report.append("")
            
            if 'ltft_bank1' in obd_data.columns:
                ltft1_avg = obd_data['ltft_bank1'].mean()
                report.append(f"- **Bank 1 LTFT**: {ltft1_avg:.2f}%")
                if ltft1_avg > 10:
                    report.append("  - ⚠️ Running lean (high positive)")
                elif ltft1_avg < -10:
                    report.append("  - ⚠️ Running rich (high negative)")
            
            if 'ltft_bank2' in obd_data.columns:
                ltft2_avg = obd_data['ltft_bank2'].mean()
                report.append(f"- **Bank 2 LTFT**: {ltft2_avg:.2f}%")
                if ltft2_avg > 10:
                    report.append("  - ⚠️ Running lean (high positive)")
                elif ltft2_avg < -10:
                    report.append("  - ⚠️ Running rich (high negative)")
        
        report.append("")
    else:
        report.append("## OBD Diagnostic Data")
        report.append("")
        report.append("*No OBD data available for this issue*")
        report.append("")
    
    # Maintenance History Section
    if maintenance_data is not None and not maintenance_data.empty:
        report.append("## Related Maintenance History")
        report.append("")
        
        for idx, row in maintenance_data.head(10).iterrows():
            report.append(f"### {row['date']} - {row['type']}")
            if pd.notna(row.get('mileage')):
                report.append(f"**Mileage:** {row['mileage']:,}")
            report.append(f"**Description:** {row['description']}")
            if pd.notna(row.get('cost')):
                report.append(f"**Cost:** ${row['cost']:.2f}")
            if pd.notna(row.get('shop')):
                report.append(f"**Shop:** {row['shop']}")
            if pd.notna(row.get('notes')) and row['notes']:
                report.append(f"**Notes:** {row['notes']}")
            report.append("")
    else:
        report.append("## Related Maintenance History")
        report.append("")
        report.append("*No related maintenance records found*")
        report.append("")
    
    # Photos Section
    if photos and len(photos) > 0:
        report.append("## Related Photos")
        report.append("")
        for photo in photos:
            # Use relative path from notes directory
            rel_path = photo.relative_to(output_path.parent.parent) if photo.is_relative_to(output_path.parent.parent) else photo
            report.append(f"- `{rel_path}`")
        report.append("")
    else:
        report.append("## Related Photos")
        report.append("")
        report.append("*No related photos found*")
        report.append("")
    
    # Analysis Section
    report.append("## Analysis and Findings")
    report.append("")
    report.append("*Document your diagnostic findings here*")
    report.append("")
    report.append("1. ")
    report.append("2. ")
    report.append("3. ")
    report.append("")
    
    # Recommendations Section
    report.append("## Recommendations")
    report.append("")
    report.append("*List recommended actions*")
    report.append("")
    report.append("- [ ] ")
    report.append("- [ ] ")
    report.append("- [ ] ")
    report.append("")
    
    # Parts Section
    report.append("## Parts Needed")
    report.append("")
    report.append("| Part | Part Number | Qty | Est. Cost |")
    report.append("|------|-------------|-----|-----------|")
    report.append("|      |             |     |           |")
    report.append("")
    
    # Notes Section
    report.append("## Additional Notes")
    report.append("")
    report.append("*Additional observations, references, or follow-up items*")
    report.append("")
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))
    
    logger.info(f"Diagnostic report written to {output_path}")


def main():
    """Main entry point for diagnostic report generator"""
    parser = argparse.ArgumentParser(
        description='Generate comprehensive diagnostic reports',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--dtc',
        type=str,
        help='DTC code to generate report for'
    )
    
    parser.add_argument(
        '--job-id',
        type=str,
        help='Job/case ID for the diagnostic'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        help='Custom title for the report'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for report (auto-generated if not specified)'
    )
    
    parser.add_argument(
        '--db-path',
        type=Path,
        default=Path('f250/data/f250.db'),
        help='Path to SQLite database (default: f250/data/f250.db)'
    )
    
    parser.add_argument(
        '--maintenance-csv',
        type=Path,
        default=Path('f250/data/maintenance_log.csv'),
        help='Path to maintenance CSV (default: f250/data/maintenance_log.csv)'
    )
    
    parser.add_argument(
        '--photo-dir',
        type=Path,
        default=Path('f250/data/photos'),
        help='Directory containing photos (default: f250/data/photos)'
    )
    
    parser.add_argument(
        '--date-range',
        nargs=2,
        metavar=('START', 'END'),
        help='Date range for data (format: YYYY-MM-DD)'
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
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if args.dtc:
            filename = f"diagnostics_{args.dtc.replace('/', '_')}_{timestamp}.md"
        elif args.job_id:
            filename = f"diagnostics_{args.job_id}_{timestamp}.md"
        else:
            filename = f"diagnostics_{timestamp}.md"
        output_path = Path(f'f250/data/notes/{filename}')
    
    # Get date range
    start_date = args.date_range[0] if args.date_range else None
    end_date = args.date_range[1] if args.date_range else None
    
    # Gather data
    logger.info("Gathering diagnostic data...")
    
    obd_data = get_obd_events(args.db_path, dtc=args.dtc, 
                              start_date=start_date, end_date=end_date)
    logger.info(f"Found {len(obd_data)} OBD events")
    
    maintenance_data = get_maintenance_entries(args.db_path, args.maintenance_csv,
                                               start_date=start_date, end_date=end_date)
    logger.info(f"Found {len(maintenance_data)} maintenance entries")
    
    photos = find_related_photos(args.photo_dir, dtc=args.dtc, job_id=args.job_id)
    logger.info(f"Found {len(photos)} related photos")
    
    # Generate report
    generate_report(
        output_path,
        dtc=args.dtc,
        job_id=args.job_id,
        title=args.title,
        obd_data=obd_data,
        maintenance_data=maintenance_data,
        photos=photos
    )
    
    print(f"\n✓ Diagnostic report generated: {output_path}")
    return 0


if __name__ == '__main__':
    exit(main())
