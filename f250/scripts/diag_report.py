#!/usr/bin/env python3
"""
Diagnostic Report Generator
Generate comprehensive diagnostic sheets for DTCs or maintenance jobs.
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
DEFAULT_REPORT_DIR = Path(__file__).parent.parent / "data" / "notes"
DEFAULT_PHOTOS_DIR = Path(__file__).parent.parent / "data" / "photos"


def get_obd_events(db_path, dtc=None, date_range=None, limit=50):
    """Retrieve relevant OBD events from database."""
    try:
        conn = sqlite3.connect(db_path)
        
        query = "SELECT * FROM obd_logs WHERE 1=1"
        params = []
        
        if dtc:
            query += " AND dtc_code LIKE ?"
            params.append(f"%{dtc}%")
        
        if date_range:
            start_date, end_date = date_range
            query += " AND timestamp BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        logger.info(f"Retrieved {len(df)} OBD events")
        return df
    
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.warning("OBD logs table not found")
            return pd.DataFrame()
        raise
    except Exception as e:
        logger.error(f"Error retrieving OBD events: {e}")
        raise


def get_maintenance_entries(db_path, entry_type=None, date_range=None, limit=20):
    """Retrieve relevant maintenance entries from database."""
    try:
        conn = sqlite3.connect(db_path)
        
        query = "SELECT * FROM maintenance WHERE 1=1"
        params = []
        
        if entry_type:
            query += " AND type LIKE ?"
            params.append(f"%{entry_type}%")
        
        if date_range:
            start_date, end_date = date_range
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        logger.info(f"Retrieved {len(df)} maintenance entries")
        return df
    
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.warning("Maintenance table not found")
            return pd.DataFrame()
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance entries: {e}")
        raise


def find_related_photos(photos_dir, dtc=None, job_name=None):
    """Find photos related to the diagnostic issue."""
    if not photos_dir.exists():
        logger.warning(f"Photos directory not found: {photos_dir}")
        return []
    
    photo_patterns = []
    if dtc:
        # Remove any DTC prefix (P, C, B, U) and convert to lowercase
        dtc_without_prefix = dtc[1:] if len(dtc) > 1 and dtc[0].upper() in ['P', 'C', 'B', 'U'] else dtc
        photo_patterns.append(dtc_without_prefix.lower())
    if job_name:
        photo_patterns.append(job_name.lower())
    
    related_photos = []
    for photo_file in photos_dir.glob("*"):
        if photo_file.is_file() and photo_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']:
            file_name_lower = photo_file.name.lower()
            if any(pattern in file_name_lower for pattern in photo_patterns):
                related_photos.append(photo_file)
    
    logger.info(f"Found {len(related_photos)} related photos")
    return related_photos


def analyze_dtc(dtc_code):
    """Provide basic analysis of DTC code."""
    analysis = []
    
    # DTC format: [P/C/B/U][0-3][0-9][0-9][0-9]
    if not dtc_code or len(dtc_code) < 5:
        return "Invalid DTC code format"
    
    prefix = dtc_code[0].upper()
    system_type = dtc_code[1] if len(dtc_code) > 1 else ''
    
    # System identification
    systems = {
        'P': 'Powertrain',
        'C': 'Chassis',
        'B': 'Body',
        'U': 'Network/Communication'
    }
    analysis.append(f"System: {systems.get(prefix, 'Unknown')}")
    
    # Generic vs manufacturer specific
    if system_type in ['0', '2']:
        analysis.append("Type: Generic (SAE)")
    elif system_type in ['1', '3']:
        analysis.append("Type: Manufacturer-specific")
    
    # Misfire detection
    if dtc_code.startswith('P030'):
        cylinder = dtc_code[-1] if dtc_code[-1].isdigit() else 'Unknown'
        if cylinder == '0':
            analysis.append("⚠️  MISFIRE: Random/Multiple Cylinders")
        else:
            analysis.append(f"⚠️  MISFIRE: Cylinder {cylinder}")
        
        analysis.append("\nCommon causes:")
        analysis.append("  - Spark plugs or ignition coils")
        analysis.append("  - Fuel injectors")
        analysis.append("  - Vacuum leaks")
        analysis.append("  - Low compression")
    
    return "\n".join(analysis)


def generate_diagnostic_report(db_path, photos_dir, dtc=None, job_name=None, date_range=None):
    """Generate comprehensive diagnostic report."""
    report = []
    
    # Header
    report.append("# Diagnostic Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Vehicle: Ford F-250")
    
    if dtc:
        report.append(f"\n## Issue: DTC {dtc}")
        report.append(f"\n{analyze_dtc(dtc)}")
    elif job_name:
        report.append(f"\n## Issue: {job_name}")
    
    # OBD Events
    report.append("\n## OBD Scan Data")
    obd_df = get_obd_events(db_path, dtc, date_range)
    
    if not obd_df.empty:
        report.append(f"\nTotal events: {len(obd_df)}")
        report.append(f"Date range: {obd_df['timestamp'].min()} to {obd_df['timestamp'].max()}")
        
        # Key statistics
        numeric_cols = ['rpm', 'speed', 'engine_load', 'coolant_temp', 'fuel_trim_short', 'fuel_trim_long']
        available_cols = [col for col in numeric_cols if col in obd_df.columns]
        
        if available_cols:
            report.append("\n### Key Metrics")
            for col in available_cols:
                if obd_df[col].notna().any():
                    report.append(f"- {col.upper()}: min={obd_df[col].min():.2f}, max={obd_df[col].max():.2f}, avg={obd_df[col].mean():.2f}")
        
        # Recent events table
        report.append("\n### Recent Events")
        display_cols = ['timestamp', 'dtc_code', 'rpm', 'speed', 'engine_load']
        available_display = [col for col in display_cols if col in obd_df.columns]
        
        if available_display:
            report.append("\n```")
            report.append(obd_df[available_display].head(10).to_string(index=False))
            report.append("```")
    else:
        report.append("\nNo OBD events found for this issue.")
    
    # Maintenance History
    report.append("\n## Related Maintenance History")
    maint_df = get_maintenance_entries(db_path, date_range=date_range)
    
    if not maint_df.empty:
        report.append(f"\nTotal entries: {len(maint_df)}")
        report.append("\n### Recent Maintenance")
        
        for idx, row in maint_df.head(10).iterrows():
            report.append(f"\n**{row['date']} - {row['type']}**")
            if pd.notna(row['mileage']):
                report.append(f"- Mileage: {row['mileage']:,.0f} miles")
            if pd.notna(row['description']):
                report.append(f"- Description: {row['description']}")
            if pd.notna(row['cost']) and row['cost']:
                report.append(f"- Cost: ${row['cost']:.2f}")
            if pd.notna(row['vendor']) and row['vendor']:
                report.append(f"- Vendor: {row['vendor']}")
    else:
        report.append("\nNo maintenance records found.")
    
    # Related Photos
    report.append("\n## Photos")
    photos = find_related_photos(photos_dir, dtc, job_name)
    
    if photos:
        report.append(f"\nFound {len(photos)} related photo(s):")
        for photo in photos:
            report.append(f"- `{photo.relative_to(photos_dir.parent)}`")
    else:
        report.append("\nNo related photos found.")
        report.append(f"\n_Note: Add photos to `{photos_dir.relative_to(photos_dir.parent.parent)}` with relevant naming._")
    
    # Recommendations
    report.append("\n## Recommendations")
    report.append("\n_Add diagnostic recommendations and next steps here._")
    
    # Notes
    report.append("\n## Additional Notes")
    report.append("\n_Add any additional observations or notes here._")
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Generate diagnostic report for F250 issues"
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        default=DEFAULT_DB_PATH,
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--photos-dir',
        type=Path,
        default=DEFAULT_PHOTOS_DIR,
        help='Directory containing related photos'
    )
    parser.add_argument(
        '--report-dir',
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help='Directory to save reports'
    )
    parser.add_argument(
        '--dtc',
        type=str,
        help='DTC code to investigate'
    )
    parser.add_argument(
        '--job',
        type=str,
        help='Job or issue name'
    )
    parser.add_argument(
        '--range',
        nargs=2,
        metavar=('START', 'END'),
        help='Date range filter (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.dtc and not args.job:
        logger.error("Must specify either --dtc or --job")
        parser.print_help()
        sys.exit(1)
    
    if not args.db_path.exists():
        logger.warning(f"Database not found: {args.db_path}")
        logger.warning("Report will be generated with limited data")
    
    # Generate report
    try:
        report_content = generate_diagnostic_report(
            args.db_path,
            args.photos_dir,
            args.dtc,
            args.job,
            args.range
        )
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if args.dtc:
                filename = f"diagnostics_{args.dtc}_{timestamp}.md"
            else:
                job_slug = args.job.lower().replace(' ', '_')
                filename = f"diagnostics_{job_slug}_{timestamp}.md"
            output_path = args.report_dir / filename
        
        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Diagnostic report generated: {output_path}")
        print(f"\nDiagnostic report generated successfully:")
        print(f"  {output_path}")
        print(f"\nReport preview:")
        print("=" * 80)
        print(report_content[:500] + "...")
        print("=" * 80)
        
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error generating report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
