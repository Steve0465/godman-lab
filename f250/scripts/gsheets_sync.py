#!/usr/bin/env python3
"""
Google Sheets Sync for F250 Maintenance Log

Syncs maintenance_log.csv to Google Sheets using service account authentication.
Requires gspread and google-auth libraries.

Setup:
1. Create a Google Cloud project: https://console.cloud.google.com
2. Enable Google Sheets API
3. Create a service account and download JSON key
4. Share your Google Sheet with the service account email
5. Set GOOGLE_SERVICE_ACCOUNT_JSON environment variable or pass path to --service-account

Security: Keep service account JSON secure. Never commit to git.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials
    import pandas as pd
except ImportError as e:
    print(f"Error: Missing required library. Install with: pip install gspread google-auth pandas")
    print(f"Details: {e}")
    sys.exit(1)

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
DEFAULT_CSV_PATH = Path(__file__).parent.parent / 'data' / 'maintenance_log.csv'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def authorize_from_service_account(json_path: Path) -> gspread.Client:
    """
    Authorize gspread client using service account credentials.
    
    Args:
        json_path: Path to service account JSON file
        
    Returns:
        Authorized gspread client
        
    Raises:
        FileNotFoundError: If JSON file doesn't exist
        Exception: If authorization fails
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Service account JSON not found: {json_path}")
    
    try:
        credentials = Credentials.from_service_account_file(
            str(json_path),
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        logger.info(f"✓ Authorized with service account: {json_path.name}")
        return client
    except Exception as e:
        logger.error(f"Authorization failed: {e}")
        raise


def push_maintenance_csv_to_sheet(
    service_account_json: Path,
    sheet_name: str,
    csv_path: Path = DEFAULT_CSV_PATH,
    worksheet_name: str = "Maintenance Log"
) -> bool:
    """
    Push maintenance log CSV to Google Sheets.
    
    Args:
        service_account_json: Path to service account JSON
        sheet_name: Name of the Google Sheet
        csv_path: Path to maintenance_log.csv
        worksheet_name: Name of worksheet within the sheet
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read CSV
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return False
            
        df = pd.read_csv(csv_path)
        logger.info(f"✓ Loaded {len(df)} entries from {csv_path.name}")
        
        # Authorize
        client = authorize_from_service_account(service_account_json)
        
        # Open/create sheet
        try:
            spreadsheet = client.open(sheet_name)
            logger.info(f"✓ Opened existing sheet: {sheet_name}")
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(sheet_name)
            logger.info(f"✓ Created new sheet: {sheet_name}")
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logger.info(f"✓ Using worksheet: {worksheet_name}")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=len(df) + 1,
                cols=len(df.columns)
            )
            logger.info(f"✓ Created worksheet: {worksheet_name}")
        
        # Clear existing data
        worksheet.clear()
        
        # Prepare data (headers + rows)
        data = [df.columns.tolist()] + df.fillna('').values.tolist()
        
        # Update sheet
        worksheet.update(data, 'A1')
        logger.info(f"✓ Synced {len(df)} entries to Google Sheets")
        logger.info(f"Sheet URL: {spreadsheet.url}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync to Google Sheets: {e}")
        return False


def pull_sheet_to_csv(
    service_account_json: Path,
    sheet_name: str,
    csv_path: Path = DEFAULT_CSV_PATH,
    worksheet_name: str = "Maintenance Log"
) -> bool:
    """
    Pull data from Google Sheets to CSV.
    
    Args:
        service_account_json: Path to service account JSON
        sheet_name: Name of the Google Sheet
        csv_path: Path to save CSV
        worksheet_name: Name of worksheet to pull from
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Authorize
        client = authorize_from_service_account(service_account_json)
        
        # Open sheet
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Get all values
        data = worksheet.get_all_values()
        
        if not data:
            logger.warning("No data found in sheet")
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Save to CSV
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        
        logger.info(f"✓ Pulled {len(df)} entries from Google Sheets to {csv_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to pull from Google Sheets: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Sync F250 maintenance log with Google Sheets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Push CSV to Google Sheets
  %(prog)s push --sheet "F250 Maintenance" --service-account ~/credentials.json
  
  # Pull from Google Sheets to CSV
  %(prog)s pull --sheet "F250 Maintenance" --service-account ~/credentials.json
  
  # Use environment variable for credentials
  export GOOGLE_SERVICE_ACCOUNT_JSON=~/credentials.json
  %(prog)s push --sheet "F250 Maintenance"

Setup Instructions:
  1. Go to https://console.cloud.google.com
  2. Create a project and enable Google Sheets API
  3. Create service account and download JSON key
  4. Share your Google Sheet with service account email (found in JSON)
  5. Set GOOGLE_SERVICE_ACCOUNT_JSON or use --service-account flag
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Push command
    push_parser = subparsers.add_parser('push', help='Push CSV to Google Sheets')
    push_parser.add_argument('--sheet', required=True, help='Google Sheet name')
    push_parser.add_argument('--csv', type=Path, default=DEFAULT_CSV_PATH,
                           help=f'CSV file path (default: {DEFAULT_CSV_PATH})')
    push_parser.add_argument('--service-account', type=Path,
                           help='Service account JSON file path')
    push_parser.add_argument('--worksheet', default='Maintenance Log',
                           help='Worksheet name (default: Maintenance Log)')
    
    # Pull command
    pull_parser = subparsers.add_parser('pull', help='Pull from Google Sheets to CSV')
    pull_parser.add_argument('--sheet', required=True, help='Google Sheet name')
    pull_parser.add_argument('--csv', type=Path, default=DEFAULT_CSV_PATH,
                           help=f'CSV file path (default: {DEFAULT_CSV_PATH})')
    pull_parser.add_argument('--service-account', type=Path,
                           help='Service account JSON file path')
    pull_parser.add_argument('--worksheet', default='Maintenance Log',
                           help='Worksheet name (default: Maintenance Log)')
    
    args = parser.parse_args()
    
    # Get service account JSON path
    if args.service_account:
        json_path = args.service_account
    else:
        import os
        json_env = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not json_env:
            logger.error("Service account JSON not specified. Use --service-account or set GOOGLE_SERVICE_ACCOUNT_JSON")
            return 1
        json_path = Path(json_env)
    
    # Execute command
    if args.command == 'push':
        success = push_maintenance_csv_to_sheet(
            json_path,
            args.sheet,
            args.csv,
            args.worksheet
        )
    elif args.command == 'pull':
        success = pull_sheet_to_csv(
            json_path,
            args.sheet,
            args.csv,
            args.worksheet
        )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
