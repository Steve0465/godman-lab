#!/usr/bin/env python3
"""
Google Sheets Sync - Sync F250 data with Google Sheets
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Sheets API scope
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


class GoogleSheetsSync:
    """Sync F250 data with Google Sheets"""
    
    def __init__(self, db_path: Path, credentials_path: Optional[Path] = None):
        self.db_path = Path(db_path).resolve()
        self.credentials_path = Path(credentials_path).resolve() if credentials_path else None
        
        # Validate database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        # Validate gspread is installed
        if gspread is None:
            raise ImportError(
                "gspread and google-auth are required. Install with: "
                "pip install gspread google-auth"
            )
        
        self.client = None
        
    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API"""
        try:
            if not self.credentials_path or not self.credentials_path.exists():
                logger.error(
                    f"Credentials file not found: {self.credentials_path}. "
                    "Please provide a valid service account JSON file."
                )
                return False
            
            creds = Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
            logger.info("Successfully authenticated with Google Sheets API")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_maintenance_data(self) -> pd.DataFrame:
        """Get maintenance data from SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT date, mileage, type, description, cost, shop, notes FROM maintenance ORDER BY date DESC"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            logger.error(f"Failed to query maintenance data: {e}")
            return pd.DataFrame()
    
    def get_obd_summary(self) -> pd.DataFrame:
        """Get OBD summary data from SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT dtc) as unique_dtcs,
                    SUM(CASE WHEN misfire_count > 0 THEN 1 ELSE 0 END) as misfire_events,
                    SUM(misfire_count) as total_misfires,
                    AVG(rpm) as avg_rpm,
                    AVG(speed) as avg_speed,
                    AVG(coolant_temp) as avg_coolant_temp
                FROM obd_logs
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            logger.error(f"Failed to query OBD data: {e}")
            return pd.DataFrame()
    
    def get_dtc_summary(self) -> pd.DataFrame:
        """Get DTC summary from SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    dtc,
                    COUNT(*) as occurrences,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM obd_logs
                WHERE dtc IS NOT NULL AND dtc != ''
                GROUP BY dtc
                ORDER BY occurrences DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            logger.error(f"Failed to query DTC data: {e}")
            return pd.DataFrame()
    
    def sync_to_sheet(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        data: pd.DataFrame,
        clear_existing: bool = True
    ) -> bool:
        """Sync DataFrame to Google Sheet"""
        try:
            if self.client is None:
                logger.error("Not authenticated. Call authenticate() first.")
                return False
            
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=len(data) + 1,
                    cols=len(data.columns)
                )
                logger.info(f"Created new worksheet: {worksheet_name}")
            
            # Clear existing data if requested
            if clear_existing:
                worksheet.clear()
            
            # Prepare data with headers
            values = [data.columns.tolist()] + data.fillna('').values.tolist()
            
            # Update sheet
            worksheet.update('A1', values)
            
            logger.info(
                f"Successfully synced {len(data)} rows to "
                f"'{worksheet_name}' in spreadsheet {spreadsheet_id}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync to sheet: {e}")
            return False
    
    def sync_all_data(
        self,
        spreadsheet_id: str,
        sync_maintenance: bool = True,
        sync_obd: bool = True,
        sync_dtc: bool = True
    ) -> Dict[str, bool]:
        """Sync all data to Google Sheets"""
        results = {}
        
        if sync_maintenance:
            logger.info("Syncing maintenance data...")
            maintenance_df = self.get_maintenance_data()
            if not maintenance_df.empty:
                results['maintenance'] = self.sync_to_sheet(
                    spreadsheet_id,
                    'Maintenance Log',
                    maintenance_df
                )
            else:
                logger.warning("No maintenance data to sync")
                results['maintenance'] = False
        
        if sync_obd:
            logger.info("Syncing OBD summary...")
            obd_df = self.get_obd_summary()
            if not obd_df.empty:
                results['obd_summary'] = self.sync_to_sheet(
                    spreadsheet_id,
                    'OBD Summary',
                    obd_df
                )
            else:
                logger.warning("No OBD data to sync")
                results['obd_summary'] = False
        
        if sync_dtc:
            logger.info("Syncing DTC summary...")
            dtc_df = self.get_dtc_summary()
            if not dtc_df.empty:
                results['dtc_summary'] = self.sync_to_sheet(
                    spreadsheet_id,
                    'DTC Summary',
                    dtc_df
                )
            else:
                logger.warning("No DTC data to sync")
                results['dtc_summary'] = False
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sync F250 data to Google Sheets"
    )
    parser.add_argument(
        '--db',
        type=Path,
        default=Path('f250/data/f250.db'),
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--credentials',
        type=Path,
        required=True,
        help='Path to Google service account credentials JSON file'
    )
    parser.add_argument(
        '--spreadsheet-id',
        required=True,
        help='Google Spreadsheet ID'
    )
    parser.add_argument(
        '--maintenance-only',
        action='store_true',
        help='Sync only maintenance data'
    )
    parser.add_argument(
        '--obd-only',
        action='store_true',
        help='Sync only OBD data'
    )
    parser.add_argument(
        '--dtc-only',
        action='store_true',
        help='Sync only DTC data'
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
        # Convert paths to absolute
        db_path = Path(args.db).resolve()
        credentials_path = Path(args.credentials).resolve()
        
        # Create sync instance
        sync = GoogleSheetsSync(db_path, credentials_path)
        
        # Authenticate
        if not sync.authenticate():
            logger.error("Authentication failed. Exiting.")
            sys.exit(1)
        
        # Determine what to sync
        if args.maintenance_only:
            sync_maintenance = True
            sync_obd = False
            sync_dtc = False
        elif args.obd_only:
            sync_maintenance = False
            sync_obd = True
            sync_dtc = False
        elif args.dtc_only:
            sync_maintenance = False
            sync_obd = False
            sync_dtc = True
        else:
            # Sync all by default
            sync_maintenance = True
            sync_obd = True
            sync_dtc = True
        
        # Sync data
        results = sync.sync_all_data(
            args.spreadsheet_id,
            sync_maintenance=sync_maintenance,
            sync_obd=sync_obd,
            sync_dtc=sync_dtc
        )
        
        # Report results
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        logger.info(f"Sync complete: {success_count}/{total_count} successful")
        
        if success_count < total_count:
            logger.warning("Some syncs failed. Check logs for details.")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
