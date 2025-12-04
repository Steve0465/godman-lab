#!/usr/bin/env python3
"""
Google Sheets Sync Script
Sync maintenance log CSV to Google Sheets using service account authentication.

SECURITY NOTE: 
- Never commit service account JSON to the repository
- Store credentials in environment variable F250_GS_SERVICE_ACCOUNT or pass path via CLI
- Ensure service account JSON has appropriate permissions and is stored securely
"""
import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Error: gspread and google-auth libraries required. Install with:")
    print("  pip install gspread google-auth google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CSV_PATH = Path(__file__).parent.parent / "data" / "maintenance_log.csv"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def authorize_from_service_account(json_path):
    """
    Authorize Google Sheets API access using service account credentials.
    
    Args:
        json_path: Path to service account JSON file
        
    Returns:
        Authorized gspread client
        
    Raises:
        FileNotFoundError: If credentials file not found
        Exception: If authorization fails
    """
    json_path = Path(json_path)
    
    if not json_path.exists():
        raise FileNotFoundError(f"Service account JSON not found: {json_path}")
    
    try:
        credentials = Credentials.from_service_account_file(
            str(json_path),
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        logger.info("Successfully authorized with Google Sheets API")
        return client
    except Exception as e:
        logger.error(f"Failed to authorize with service account: {e}")
        raise


def push_maintenance_csv_to_sheet(service_account_json, sheet_name, csv_path=None):
    """
    Push maintenance log CSV to Google Sheets.
    
    Args:
        service_account_json: Path to service account JSON credentials
        sheet_name: Name or URL of the Google Sheet
        csv_path: Path to CSV file (defaults to maintenance_log.csv)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use default CSV path if not provided
        if csv_path is None:
            csv_path = DEFAULT_CSV_PATH
        else:
            csv_path = Path(csv_path)
        
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        # Read CSV data
        df = pd.read_csv(csv_path)
        logger.info(f"Read {len(df)} rows from {csv_path}")
        
        # Authorize client
        client = authorize_from_service_account(service_account_json)
        
        # Open or create spreadsheet
        try:
            # Try to open by name first
            spreadsheet = client.open(sheet_name)
            logger.info(f"Opened existing spreadsheet: {sheet_name}")
        except gspread.SpreadsheetNotFound:
            # If not found, try to open by URL
            try:
                spreadsheet = client.open_by_url(sheet_name)
                logger.info(f"Opened spreadsheet by URL")
            except:
                logger.error(f"Spreadsheet not found: {sheet_name}")
                logger.info("Ensure the spreadsheet exists and is shared with the service account email")
                return False
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.sheet1
        except:
            worksheet = spreadsheet.add_worksheet(title="Maintenance Log", rows=1000, cols=20)
        
        # Clear existing data
        worksheet.clear()
        
        # Prepare data for upload (include headers)
        data = [df.columns.tolist()] + df.values.tolist()
        
        # Upload data
        worksheet.update('A1', data)
        logger.info(f"Successfully uploaded {len(df)} rows to Google Sheets")
        
        # Format header row
        worksheet.format('A1:G1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        logger.info(f"Spreadsheet URL: {spreadsheet.url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to push data to Google Sheets: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Sync F250 maintenance log to Google Sheets"
    )
    parser.add_argument(
        '--service-account',
        type=Path,
        help='Path to service account JSON file (or use F250_GS_SERVICE_ACCOUNT env var)'
    )
    parser.add_argument(
        '--sheet-name',
        required=True,
        help='Name or URL of the Google Sheet'
    )
    parser.add_argument(
        '--csv-path',
        type=Path,
        default=DEFAULT_CSV_PATH,
        help='Path to maintenance log CSV'
    )
    
    args = parser.parse_args()
    
    # Determine service account path
    if args.service_account:
        service_account_path = args.service_account
    else:
        env_path = os.getenv('F250_GS_SERVICE_ACCOUNT')
        if env_path:
            service_account_path = Path(env_path)
        else:
            logger.error("Service account credentials not provided")
            logger.error("Use --service-account flag or set F250_GS_SERVICE_ACCOUNT environment variable")
            sys.exit(1)
    
    # Validate service account file exists
    if not service_account_path.exists():
        logger.error(f"Service account file not found: {service_account_path}")
        logger.error("\nTo create a service account:")
        logger.error("1. Go to Google Cloud Console: https://console.cloud.google.com")
        logger.error("2. Create a new project or select existing one")
        logger.error("3. Enable Google Sheets API and Google Drive API")
        logger.error("4. Create a service account in IAM & Admin")
        logger.error("5. Download JSON key file")
        logger.error("6. Share your Google Sheet with the service account email")
        sys.exit(1)
    
    # Push data to Google Sheets
    success = push_maintenance_csv_to_sheet(
        service_account_path,
        args.sheet_name,
        args.csv_path
    )
    
    if success:
        print("\n✓ Successfully synced maintenance log to Google Sheets")
        sys.exit(0)
    else:
        print("\n✗ Failed to sync maintenance log to Google Sheets")
        sys.exit(1)


if __name__ == "__main__":
    main()
