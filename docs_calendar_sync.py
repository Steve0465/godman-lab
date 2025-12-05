#!/usr/bin/env python3
"""
Document Organizer - Calendar Integration

Automatically adds bill due dates to Google Calendar with reminders.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()


def create_calendar_event(service, title: str, due_date: str, amount: float = None, 
                          description: str = None, calendar_id: str = 'primary'):
    """
    Create a calendar event for a bill due date
    
    Args:
        service: Google Calendar API service
        title: Event title (e.g., "Utility Bill Payment Due")
        due_date: Due date in YYYY-MM-DD format
        amount: Bill amount (optional)
        description: Event description (optional)
        calendar_id: Calendar to add to (default: primary)
    """
    
    try:
        due_datetime = datetime.strptime(due_date, '%Y-%m-%d')
        
        # Create event details
        event_title = f"💰 {title}"
        if amount:
            event_title += f" - ${amount:.2f}"
        
        event_description = description or ""
        if amount:
            event_description = f"Amount: ${amount:.2f}\n\n{event_description}"
        
        # Create all-day event on due date
        event = {
            'summary': event_title,
            'description': event_description,
            'start': {
                'date': due_date,
                'timeZone': 'America/Chicago',
            },
            'end': {
                'date': due_date,
                'timeZone': 'America/Chicago',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 3 * 24 * 60},  # 3 days before
                    {'method': 'popup', 'minutes': 1 * 24 * 60},  # 1 day before
                ],
            },
            'colorId': '11',  # Red color for bills
        }
        
        created_event = service.events().insert(
            calendarId=calendar_id, 
            body=event
        ).execute()
        
        return created_event
        
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return None


def get_calendar_service(credentials_path: str = None):
    """
    Get Google Calendar API service
    
    Args:
        credentials_path: Path to service account JSON or OAuth credentials
    """
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    try:
        # Try service account first
        creds_path = credentials_path or os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if creds_path and Path(creds_path).exists():
            credentials = service_account.Credentials.from_service_account_file(
                creds_path, scopes=SCOPES
            )
        else:
            print("No credentials found. Please set up Google Calendar API access.")
            print("Visit: https://console.cloud.google.com")
            return None
        
        service = build('calendar', 'v3', credentials=credentials)
        return service
        
    except Exception as e:
        print(f"Error connecting to Google Calendar: {e}")
        return None


def sync_bills_to_calendar(csv_path: Path, credentials_path: str = None, dry_run: bool = False):
    """
    Sync bills from analysis CSV to Google Calendar
    
    Args:
        csv_path: Path to document_analysis.csv
        credentials_path: Path to Google credentials
        dry_run: If True, only show what would be added
    """
    
    if not csv_path.exists():
        print(f"Error: CSV not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    # Filter for bills with due dates
    bills = df[
        (df['category'] == 'BILLS') & 
        (df['due_date'].notna()) &
        (df['action'].isin(['URGENT', 'ACTION']))
    ]
    
    if len(bills) == 0:
        print("No bills with due dates found")
        return
    
    print("=" * 70)
    print("SYNCING BILLS TO GOOGLE CALENDAR")
    print("=" * 70)
    print()
    print(f"Found {len(bills)} bills to add\n")
    
    if dry_run:
        print("[DRY RUN MODE - No changes will be made]\n")
    
    # Get calendar service
    service = None
    if not dry_run:
        service = get_calendar_service(credentials_path)
        if not service:
            print("Could not connect to Google Calendar")
            return
    
    added = 0
    
    for _, bill in bills.iterrows():
        title = f"{bill['category']} - {bill['filename']}"
        due_date = bill['due_date']
        amount = bill.get('amount')
        description = f"{bill['summary']}\n\nFile: {bill['filename']}"
        
        if bill.get('action_required'):
            description += f"\n\nAction: {bill['action_required']}"
        
        print(f"📅 {bill['filename']}")
        print(f"   Due: {due_date}")
        if amount:
            print(f"   Amount: ${amount}")
        
        if dry_run:
            print(f"   [Would add to calendar]")
        else:
            event = create_calendar_event(
                service, title, due_date, amount, description
            )
            if event:
                print(f"   ✓ Added to calendar")
                print(f"   Link: {event.get('htmlLink')}")
                added += 1
            else:
                print(f"   ✗ Failed to add")
        
        print()
    
    print("=" * 70)
    if dry_run:
        print(f"[DRY RUN] Would add {len(bills)} events to calendar")
    else:
        print(f"✓ Added {added}/{len(bills)} events to Google Calendar")
    print("=" * 70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sync document due dates to Google Calendar'
    )
    parser.add_argument(
        'csv_file',
        type=Path,
        help='Path to document_analysis.csv'
    )
    parser.add_argument(
        '--credentials',
        type=str,
        help='Path to Google service account JSON'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be added without making changes'
    )
    
    args = parser.parse_args()
    
    sync_bills_to_calendar(args.csv_file, args.credentials, args.dry_run)
