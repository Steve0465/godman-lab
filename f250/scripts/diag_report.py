#!/usr/bin/env python3
"""
Diagnostic Report Generator - Create comprehensive diagnostic sheets
"""

import argparse
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


class DiagnosticReportGenerator:
    """Generate diagnostic reports from OBD and maintenance data"""
    
    def __init__(self, db_path: Path, notes_dir: Path, photos_dir: Optional[Path] = None):
        self.db_path = db_path
        self.notes_dir = notes_dir
        # If photos_dir is not provided, compute relative to notes_dir
        if photos_dir is None:
            self.photos_dir = self.notes_dir.parent / 'photos'
        else:
            self.photos_dir = photos_dir
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        
    def get_obd_events(self, dtc: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """Get OBD events from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if dtc:
                query = "SELECT * FROM obd_logs WHERE dtc = ? ORDER BY timestamp DESC"
                params = (dtc,)
            else:
                query = "SELECT * FROM obd_logs ORDER BY timestamp DESC"
                params = ()
            
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
            
        except sqlite3.Error as e:
            logger.error(f"Failed to query OBD events: {e}")
            return pd.DataFrame()
    
    def get_maintenance_entries(
        self,
        entry_type: Optional[str] = None,
        start_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get maintenance entries from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM maintenance"
            conditions = []
            params = []
            
            if entry_type:
                conditions.append("type = ?")
                params.append(entry_type)
            
            if start_date:
                conditions.append("date >= ?")
                params.append(start_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY date DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
            
        except sqlite3.Error as e:
            logger.error(f"Failed to query maintenance entries: {e}")
            return pd.DataFrame()
    
    def find_related_photos(self, job_name: str) -> List[Path]:
        """Find photos related to a job or DTC"""
        if not self.photos_dir.exists():
            return []
        
        # Look for photos matching the job name pattern
        photo_patterns = [
            f"*{job_name}*",
            f"*{job_name.lower()}*",
            f"*{job_name.upper()}*"
        ]
        
        photos = []
        for pattern in photo_patterns:
            photos.extend(self.photos_dir.glob(pattern + ".jpg"))
            photos.extend(self.photos_dir.glob(pattern + ".png"))
            photos.extend(self.photos_dir.glob(pattern + ".jpeg"))
        
        return list(set(photos))  # Remove duplicates
    
    def generate_dtc_report(self, dtc: str, output_path: Optional[Path] = None) -> Path:
        """Generate a diagnostic report for a specific DTC"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.notes_dir / f"diagnostics_{dtc}_{timestamp}.md"
        
        # Get OBD events
        obd_df = self.get_obd_events(dtc=dtc, limit=50)
        
        # Get recent maintenance
        maintenance_df = self.get_maintenance_entries()
        
        # Find related photos
        photos = self.find_related_photos(dtc)
        
        # Generate report
        with open(output_path, 'w') as f:
            f.write(f"# Diagnostic Report: {dtc}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # DTC Information
            f.write(f"## DTC Code: {dtc}\n\n")
            
            if obd_df.empty:
                f.write("No OBD events found for this DTC.\n\n")
            else:
                f.write(f"**Total Occurrences:** {len(obd_df)}\n")
                f.write(f"**First Seen:** {obd_df['timestamp'].min()}\n")
                f.write(f"**Last Seen:** {obd_df['timestamp'].max()}\n\n")
                
                # Summary statistics
                f.write("### Event Statistics\n\n")
                
                if 'rpm' in obd_df.columns:
                    f.write(f"- **RPM Range:** {obd_df['rpm'].min():.0f} - {obd_df['rpm'].max():.0f}\n")
                    f.write(f"- **Average RPM:** {obd_df['rpm'].mean():.0f}\n")
                
                if 'speed' in obd_df.columns:
                    f.write(f"- **Speed Range:** {obd_df['speed'].min():.0f} - {obd_df['speed'].max():.0f} mph\n")
                
                if 'coolant_temp' in obd_df.columns:
                    f.write(f"- **Coolant Temp Range:** {obd_df['coolant_temp'].min():.0f} - {obd_df['coolant_temp'].max():.0f}°F\n")
                
                if 'misfire_count' in obd_df.columns and obd_df['misfire_count'].sum() > 0:
                    f.write(f"- **Total Misfires:** {obd_df['misfire_count'].sum():.0f}\n")
                
                # Recent events table
                f.write("\n### Recent Events\n\n")
                f.write("| Timestamp | RPM | Speed | Coolant | Misfires | Source |\n")
                f.write("|-----------|-----|-------|---------|----------|--------|\n")
                
                for _, row in obd_df.head(10).iterrows():
                    f.write(f"| {row.get('timestamp', 'N/A')} | ")
                    f.write(f"{row.get('rpm', 'N/A')} | ")
                    f.write(f"{row.get('speed', 'N/A')} | ")
                    f.write(f"{row.get('coolant_temp', 'N/A')} | ")
                    f.write(f"{row.get('misfire_count', 'N/A')} | ")
                    f.write(f"{Path(row.get('source_file', 'N/A')).name} |\n")
            
            # Related maintenance
            f.write("\n## Related Maintenance History\n\n")
            
            if maintenance_df.empty:
                f.write("No maintenance entries found.\n\n")
            else:
                f.write(f"**Total Entries:** {len(maintenance_df)}\n\n")
                f.write("| Date | Mileage | Type | Description | Cost |\n")
                f.write("|------|---------|------|-------------|------|\n")
                
                for _, row in maintenance_df.head(10).iterrows():
                    cost = row.get('cost', 0)
                    cost_str = f"${float(cost):.2f}" if pd.notna(cost) and cost is not None else "N/A"
                    f.write(f"| {row.get('date', 'N/A')} | ")
                    f.write(f"{row.get('mileage', 'N/A')} | ")
                    f.write(f"{row.get('type', 'N/A')} | ")
                    f.write(f"{row.get('description', 'N/A')} | ")
                    f.write(f"{cost_str} |\n")
            
            # Photos
            f.write("\n## Related Photos\n\n")
            
            if photos:
                f.write(f"Found {len(photos)} related photos:\n\n")
                for photo in photos:
                    f.write(f"- `{photo}`\n")
            else:
                f.write("No related photos found.\n")
            
            # Notes section
            f.write("\n## Technician Notes\n\n")
            f.write("_Add your diagnostic notes here_\n\n")
            
            # Action items
            f.write("## Action Items\n\n")
            f.write("- [ ] Review OBD event patterns\n")
            f.write("- [ ] Check related maintenance history\n")
            f.write("- [ ] Inspect related components\n")
            f.write("- [ ] Test repairs\n")
            f.write("- [ ] Clear codes and monitor\n\n")
            
            # Conclusion
            f.write("## Conclusion\n\n")
            f.write("_Add final diagnosis and resolution here_\n\n")
        
        logger.info(f"Generated diagnostic report at {output_path}")
        return output_path
    
    def generate_job_report(
        self,
        job_name: str,
        job_type: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """Generate a diagnostic report for a maintenance job"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_job_name = job_name.replace(' ', '_').lower()
            output_path = self.notes_dir / f"diagnostics_{safe_job_name}_{timestamp}.md"
        
        # Get relevant OBD data (last 30 days)
        obd_df = self.get_obd_events(limit=100)
        
        # Get maintenance history
        maintenance_df = self.get_maintenance_entries(entry_type=job_type)
        
        # Find related photos
        photos = self.find_related_photos(job_name)
        
        # Generate report
        with open(output_path, 'w') as f:
            f.write(f"# Diagnostic Report: {job_name}\n\n")
            f.write(f"**Type:** {job_type}\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Job information
            f.write(f"## Job Details\n\n")
            f.write(f"**Job Name:** {job_name}\n")
            f.write(f"**Job Type:** {job_type}\n\n")
            
            # Recent OBD activity
            f.write("## Recent OBD Activity\n\n")
            
            if obd_df.empty:
                f.write("No recent OBD events.\n\n")
            else:
                # Count DTCs
                dtc_counts = obd_df['dtc'].value_counts()
                if not dtc_counts.empty:
                    f.write("### Active DTCs\n\n")
                    for dtc, count in dtc_counts.items():
                        if pd.notna(dtc):
                            f.write(f"- **{dtc}**: {count} occurrences\n")
                    f.write("\n")
                
                # Misfire summary
                if 'misfire_count' in obd_df.columns and obd_df['misfire_count'].sum() > 0:
                    f.write("### Misfire Activity\n\n")
                    misfire_events = len(obd_df[obd_df['misfire_count'] > 0])
                    f.write(f"- **Total misfire events:** {misfire_events}\n")
                    f.write(f"- **Total misfires:** {obd_df['misfire_count'].sum():.0f}\n\n")
            
            # Maintenance history
            f.write("## Maintenance History\n\n")
            
            if maintenance_df.empty:
                f.write(f"No previous {job_type} entries found.\n\n")
            else:
                f.write(f"**Previous {job_type} entries:** {len(maintenance_df)}\n\n")
                f.write("| Date | Mileage | Description | Cost | Shop |\n")
                f.write("|------|---------|-------------|------|------|\n")
                
                for _, row in maintenance_df.head(5).iterrows():
                    cost = row.get('cost', 0)
                    cost_str = f"${float(cost):.2f}" if pd.notna(cost) and cost is not None else "N/A"
                    f.write(f"| {row.get('date', 'N/A')} | ")
                    f.write(f"{row.get('mileage', 'N/A')} | ")
                    f.write(f"{row.get('description', 'N/A')} | ")
                    f.write(f"{cost_str} | ")
                    f.write(f"{row.get('shop', 'N/A')} |\n")
                f.write("\n")
            
            # Photos
            f.write("## Related Photos\n\n")
            
            if photos:
                f.write(f"Found {len(photos)} related photos:\n\n")
                for photo in photos:
                    f.write(f"- `{photo}`\n")
            else:
                f.write("No related photos found.\n")
            
            # Work performed
            f.write("\n## Work Performed\n\n")
            f.write("_Document the work performed here_\n\n")
            
            # Parts used
            f.write("## Parts Used\n\n")
            f.write("| Part Number | Description | Quantity | Cost |\n")
            f.write("|-------------|-------------|----------|------|\n")
            f.write("| | | | |\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            f.write("_Add recommendations for future maintenance_\n\n")
        
        logger.info(f"Generated job report at {output_path}")
        return output_path


def main():
    """Main entry point"""
    # Get script directory and compute default paths relative to it
    script_dir = Path(__file__).parent.resolve()
    f250_data_dir = script_dir.parent / 'data'
    
    parser = argparse.ArgumentParser(
        description="Generate diagnostic reports for F250"
    )
    parser.add_argument(
        '--db',
        type=Path,
        default=f250_data_dir / 'f250.db',
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--notes-dir',
        type=Path,
        default=f250_data_dir / 'notes',
        help='Directory for diagnostic reports'
    )
    parser.add_argument(
        '--photos-dir',
        type=Path,
        default=f250_data_dir / 'photos',
        help='Directory containing related photos'
    )
    parser.add_argument(
        '--dtc',
        type=str,
        help='Generate report for a specific DTC'
    )
    parser.add_argument(
        '--job-name',
        type=str,
        help='Generate report for a maintenance job'
    )
    parser.add_argument(
        '--job-type',
        type=str,
        help='Type of maintenance job (required with --job-name)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (optional)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not args.dtc and not args.job_name:
        parser.error("Must specify either --dtc or --job-name")
    
    if args.job_name and not args.job_type:
        parser.error("--job-type is required when using --job-name")
    
    try:
        generator = DiagnosticReportGenerator(
            args.db,
            args.notes_dir,
            args.photos_dir
        )
        
        if args.dtc:
            report_path = generator.generate_dtc_report(args.dtc, args.output)
            print(f"Generated DTC report: {report_path}")
        else:
            report_path = generator.generate_job_report(
                args.job_name,
                args.job_type,
                args.output
            )
            print(f"Generated job report: {report_path}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
