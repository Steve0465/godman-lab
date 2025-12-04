#!/usr/bin/env python3
"""
OBD Query Script - Query OBD data from SQLite or Parquet with diagnostic analysis
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


class OBDQueryEngine:
    """Query and analyze OBD data"""
    
    def __init__(self, db_path: Path, parquet_dir: Optional[Path] = None):
        self.db_path = db_path
        self.parquet_dir = parquet_dir
        
    def query_sqlite(self, query: str) -> pd.DataFrame:
        """Execute query against SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            logger.error(f"SQLite query failed: {e}")
            raise
    
    def query_parquet(self, filters: Dict) -> pd.DataFrame:
        """Query Parquet files with filters"""
        if not self.parquet_dir or not self.parquet_dir.exists():
            raise ValueError("Parquet directory not specified or doesn't exist")
        
        parquet_files = list(self.parquet_dir.glob("*.parquet"))
        if not parquet_files:
            logger.warning("No parquet files found")
            return pd.DataFrame()
        
        dfs = []
        for pf in parquet_files:
            df = pd.read_parquet(pf)
            dfs.append(df)
        
        combined = pd.concat(dfs, ignore_index=True)
        
        # Apply filters
        for col, val in filters.items():
            if col in combined.columns:
                combined = combined[combined[col] == val]
        
        return combined
    
    def query_by_dtc(self, dtc: str, use_parquet: bool = False) -> pd.DataFrame:
        """Query all logs with a specific DTC"""
        if use_parquet:
            return self.query_parquet({'dtc': dtc})
        else:
            query = "SELECT * FROM obd_logs WHERE dtc = ? ORDER BY timestamp"
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=(dtc,))
            conn.close()
            return df
    
    def query_by_date_range(
        self, 
        start_date: str, 
        end_date: str,
        use_parquet: bool = False
    ) -> pd.DataFrame:
        """Query logs within date range"""
        if use_parquet:
            df = self.query_parquet({})
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
            return df
        else:
            query = """
                SELECT * FROM obd_logs 
                WHERE timestamp >= ? 
                AND timestamp <= ?
                ORDER BY timestamp
            """
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            conn.close()
            return df
    
    def query_misfires(self, use_parquet: bool = False) -> pd.DataFrame:
        """Query logs with misfire events"""
        if use_parquet:
            df = self.query_parquet({})
            return df[df['misfire_count'] > 0]
        else:
            query = """
                SELECT * FROM obd_logs 
                WHERE misfire_count > 0 
                ORDER BY timestamp
            """
            return self.query_sqlite(query)
    
    def analyze_misfires(self, df: pd.DataFrame) -> Dict:
        """Analyze misfire patterns"""
        if df.empty:
            return {'total_events': 0, 'total_misfires': 0}
        
        analysis = {
            'total_events': len(df),
            'total_misfires': df['misfire_count'].sum(),
            'avg_misfires_per_event': df['misfire_count'].mean(),
            'max_misfires': df['misfire_count'].max(),
            'date_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            }
        }
        
        # Analyze by RPM ranges
        if 'rpm' in df.columns:
            df['rpm_range'] = pd.cut(
                df['rpm'], 
                bins=[0, 1000, 2000, 3000, 4000, 10000],
                labels=['idle', 'low', 'mid', 'high', 'very_high']
            )
            analysis['misfires_by_rpm'] = df.groupby('rpm_range')['misfire_count'].sum().to_dict()
        
        return analysis
    
    def classify_fuel_trim(self, fuel_trim: float) -> str:
        """Classify fuel trim status"""
        if pd.isna(fuel_trim):
            return 'unknown'
        elif fuel_trim > 10:
            return 'rich'
        elif fuel_trim < -10:
            return 'lean'
        else:
            return 'normal'
    
    def analyze_fuel_trim(self, df: pd.DataFrame) -> Dict:
        """Analyze fuel trim patterns"""
        if df.empty or 'fuel_trim_st' not in df.columns:
            return {}
        
        df['ft_st_class'] = df['fuel_trim_st'].apply(self.classify_fuel_trim)
        
        analysis = {
            'short_term_avg': df['fuel_trim_st'].mean(),
            'short_term_std': df['fuel_trim_st'].std(),
            'classification_counts': df['ft_st_class'].value_counts().to_dict()
        }
        
        if 'fuel_trim_lt' in df.columns:
            df['ft_lt_class'] = df['fuel_trim_lt'].apply(self.classify_fuel_trim)
            analysis['long_term_avg'] = df['fuel_trim_lt'].mean()
            analysis['long_term_std'] = df['fuel_trim_lt'].std()
        
        return analysis
    
    def generate_summary_table(self, df: pd.DataFrame) -> str:
        """Generate a text summary table of the data"""
        if df.empty:
            return "No data found."
        
        summary = []
        summary.append(f"\n{'='*60}")
        summary.append(f"OBD Data Summary")
        summary.append(f"{'='*60}")
        summary.append(f"Total Records: {len(df)}")
        
        if 'timestamp' in df.columns:
            summary.append(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # DTC summary
        if 'dtc' in df.columns:
            dtc_counts = df['dtc'].value_counts()
            if not dtc_counts.empty:
                summary.append(f"\nDTC Codes Found: {len(dtc_counts)}")
                summary.append(f"Top DTCs:")
                for dtc, count in dtc_counts.head(5).items():
                    summary.append(f"  {dtc}: {count} occurrences")
        
        # Misfire summary
        if 'misfire_count' in df.columns:
            misfire_df = df[df['misfire_count'] > 0]
            if not misfire_df.empty:
                summary.append(f"\nMisfire Events: {len(misfire_df)}")
                summary.append(f"Total Misfires: {misfire_df['misfire_count'].sum()}")
        
        # Stats
        if 'rpm' in df.columns:
            summary.append(f"\nRPM Range: {df['rpm'].min():.0f} - {df['rpm'].max():.0f}")
            summary.append(f"Avg RPM: {df['rpm'].mean():.0f}")
        
        if 'speed' in df.columns:
            summary.append(f"Speed Range: {df['speed'].min():.0f} - {df['speed'].max():.0f} mph")
        
        if 'coolant_temp' in df.columns:
            summary.append(f"Coolant Temp Range: {df['coolant_temp'].min():.0f} - {df['coolant_temp'].max():.0f}°F")
        
        summary.append(f"{'='*60}\n")
        
        return "\n".join(summary)
    
    def write_diagnostic_report(
        self,
        df: pd.DataFrame,
        output_path: Path,
        issue_title: str = "Diagnostic Report"
    ):
        """Write a diagnostic markdown report"""
        with open(output_path, 'w') as f:
            f.write(f"# {issue_title}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- Total records analyzed: {len(df)}\n")
            
            if 'timestamp' in df.columns and not df.empty:
                f.write(f"- Date range: {df['timestamp'].min()} to {df['timestamp'].max()}\n")
            
            # DTC Analysis
            if 'dtc' in df.columns:
                dtc_counts = df['dtc'].value_counts()
                if not dtc_counts.empty:
                    f.write(f"\n## Diagnostic Trouble Codes\n\n")
                    for dtc, count in dtc_counts.items():
                        f.write(f"- **{dtc}**: {count} occurrences\n")
            
            # Misfire Analysis
            if 'misfire_count' in df.columns:
                misfire_analysis = self.analyze_misfires(df)
                if misfire_analysis['total_events'] > 0:
                    f.write(f"\n## Misfire Analysis\n\n")
                    f.write(f"- Total misfire events: {misfire_analysis['total_events']}\n")
                    f.write(f"- Total misfires: {misfire_analysis['total_misfires']}\n")
                    f.write(f"- Average per event: {misfire_analysis['avg_misfires_per_event']:.2f}\n")
                    
                    if 'misfires_by_rpm' in misfire_analysis:
                        f.write(f"\n### Misfires by RPM Range\n\n")
                        for rpm_range, count in misfire_analysis['misfires_by_rpm'].items():
                            f.write(f"- {rpm_range}: {count}\n")
            
            # Fuel Trim Analysis
            fuel_trim_analysis = self.analyze_fuel_trim(df)
            if fuel_trim_analysis:
                f.write(f"\n## Fuel Trim Analysis\n\n")
                f.write(f"- Short-term average: {fuel_trim_analysis.get('short_term_avg', 0):.2f}%\n")
                if 'classification_counts' in fuel_trim_analysis:
                    f.write(f"\n### Fuel Trim Classification\n\n")
                    for cls, count in fuel_trim_analysis['classification_counts'].items():
                        f.write(f"- {cls}: {count} readings\n")
            
            # Data table
            f.write(f"\n## Recent Events\n\n")
            f.write("| Timestamp | RPM | Speed | Coolant | DTC | Misfires |\n")
            f.write("|-----------|-----|-------|---------|-----|----------|\n")
            
            for _, row in df.head(20).iterrows():
                f.write(f"| {row.get('timestamp', 'N/A')} | ")
                f.write(f"{row.get('rpm', 'N/A')} | ")
                f.write(f"{row.get('speed', 'N/A')} | ")
                f.write(f"{row.get('coolant_temp', 'N/A')} | ")
                f.write(f"{row.get('dtc', 'N/A')} | ")
                f.write(f"{row.get('misfire_count', 'N/A')} |\n")
        
        logger.info(f"Diagnostic report written to {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Query and analyze OBD data"
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
        help='Directory with Parquet files (alternative to SQLite)'
    )
    parser.add_argument(
        '--dtc',
        type=str,
        help='Filter by specific DTC code'
    )
    parser.add_argument(
        '--range',
        nargs=2,
        metavar=('START', 'END'),
        help='Date range (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--misfire-only',
        action='store_true',
        help='Show only misfire events'
    )
    parser.add_argument(
        '--report',
        type=Path,
        help='Write diagnostic report to file'
    )
    parser.add_argument(
        '--output-format',
        choices=['table', 'csv', 'json'],
        default='table',
        help='Output format'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        use_parquet = args.parquet_dir is not None
        engine = OBDQueryEngine(args.db, args.parquet_dir)
        
        # Execute query based on parameters
        if args.dtc:
            df = engine.query_by_dtc(args.dtc, use_parquet)
            logger.info(f"Found {len(df)} records with DTC {args.dtc}")
        elif args.range:
            df = engine.query_by_date_range(args.range[0], args.range[1], use_parquet)
            logger.info(f"Found {len(df)} records in date range")
        elif args.misfire_only:
            df = engine.query_misfires(use_parquet)
            logger.info(f"Found {len(df)} misfire events")
        else:
            # Get all data
            if use_parquet:
                df = engine.query_parquet({})
            else:
                df = engine.query_sqlite("SELECT * FROM obd_logs ORDER BY timestamp")
            logger.info(f"Retrieved {len(df)} total records")
        
        # Output results
        if args.output_format == 'table':
            print(engine.generate_summary_table(df))
        elif args.output_format == 'csv':
            print(df.to_csv(index=False))
        elif args.output_format == 'json':
            print(df.to_json(orient='records', indent=2))
        
        # Generate report if requested
        if args.report:
            issue_title = f"Diagnostic Report"
            if args.dtc:
                issue_title = f"DTC {args.dtc} Analysis"
            elif args.misfire_only:
                issue_title = "Misfire Analysis"
            
            engine.write_diagnostic_report(df, args.report, issue_title)
        
        if df.empty:
            logger.warning("No data found matching criteria")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
