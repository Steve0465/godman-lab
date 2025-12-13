"""
Banking module for godman_ai.

Provides functions for processing bank statements and managing transaction data.
"""

from datetime import date as date_type, datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import csv
import re
import shutil

import pandas as pd


def extract_dates_from_statement(statement_df: pd.DataFrame) -> List[date_type]:
    """
    Extract all dates from a bank statement DataFrame.
    
    Searches through all columns to find date values, attempting to parse
    common date formats.
    
    Args:
        statement_df: DataFrame containing bank statement data
        
    Returns:
        List of extracted dates, or empty list if none found
    """
    dates = []
    
    # Common column names that might contain dates
    date_columns = []
    for col in statement_df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['date', 'posted', 'transaction', 'time']):
            date_columns.append(col)
    
    # If no obvious date columns, check all columns
    if not date_columns:
        date_columns = statement_df.columns.tolist()
    
    # Try to extract dates from each candidate column
    for col in date_columns:
        for value in statement_df[col].dropna():
            if pd.isna(value):
                continue
                
            try:
                # Try parsing as date
                parsed_date = pd.to_datetime(value, errors='coerce')
                if pd.notna(parsed_date):
                    dates.append(parsed_date.date())
            except Exception:
                continue
    
    return dates


def determine_primary_tax_year(dates: List[date_type]) -> int:
    """
    Determine the primary tax year from a list of transaction dates.
    
    Uses the minimum year from all transactions, as bank statements
    typically cover a specific period and we want to categorize by
    the earliest transaction year.
    
    Args:
        dates: List of transaction dates
        
    Returns:
        Primary tax year (earliest year found, or current year if none)
    """
    if not dates:
        return datetime.now().year
    
    # Get the minimum year from all dates
    years = [d.year for d in dates]
    return min(years)


def ensure_bank_csv_exists(csv_path: Path) -> None:
    """
    Ensure bank transactions CSV exists with proper headers.
    
    Creates the file with headers if it doesn't exist, or validates
    headers if it does exist.
    
    Args:
        csv_path: Path to the bank transactions CSV file
    """
    headers = [
        'date',
        'description',
        'amount',
        'type',  # debit/credit
        'balance',
        'category',
        'source_file',
        'notes'
    ]
    
    if not csv_path.exists():
        # Create new file with headers
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
    else:
        # Validate existing file has headers
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_headers = reader.fieldnames
                if existing_headers != headers:
                    # Headers don't match - could log warning or update
                    pass
        except Exception:
            # If file is corrupted, recreate it
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()


def bank_statement_ingest(
    statement_path: Path,
    base_archive: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Ingest a bank statement CSV into the TAX_MASTER_ARCHIVE structure.
    
    Workflow:
    1. Load and parse the bank statement CSV
    2. Extract all transaction dates from the statement
    3. Determine primary tax year (minimum year from all transactions)
    4. Build dynamic output paths based on that year
    5. Ensure bank_transactions_{year}.csv exists with headers
    6. Append transactions to year-specific CSV
    7. Archive statement into year's Bank_Statements/ folder
    8. Return workflow result with year routing info
    
    Args:
        statement_path: Path to the bank statement CSV file
        base_archive: Base path for TAX_MASTER_ARCHIVE (defaults to ~/Desktop/TAX_MASTER_ARCHIVE)
        
    Returns:
        Dictionary with workflow results:
            - success: bool
            - year: int (primary tax year based on min transaction date)
            - paths: dict (all generated paths)
            - transaction_count: int
            - date_range: dict (min and max dates)
            - message: str
    """
    # Step 1: Load statement
    try:
        statement_df = pd.read_csv(statement_path)
    except Exception as e:
        return {
            "success": False,
            "year": datetime.now().year,
            "paths": {},
            "transaction_count": 0,
            "date_range": None,
            "message": f"Failed to load statement: {str(e)}"
        }
    
    if statement_df.empty:
        return {
            "success": False,
            "year": datetime.now().year,
            "paths": {},
            "transaction_count": 0,
            "date_range": None,
            "message": "Statement is empty"
        }
    
    # Step 2: Extract all dates
    dates = extract_dates_from_statement(statement_df)
    
    if not dates:
        return {
            "success": False,
            "year": datetime.now().year,
            "paths": {},
            "transaction_count": len(statement_df),
            "date_range": None,
            "message": "No valid dates found in statement"
        }
    
    # Step 3: Determine primary tax year
    year = determine_primary_tax_year(dates)
    
    # Calculate date range for logging
    date_range = {
        "min": min(dates).isoformat(),
        "max": max(dates).isoformat()
    }
    
    # Step 4: Build dynamic output paths
    if base_archive is None:
        base_archive = Path.home() / "Desktop" / "TAX_MASTER_ARCHIVE"
    
    year_base = base_archive / str(year)
    bank_csv = year_base / f"bank_transactions_{year}.csv"
    bank_statements_dir = year_base / "Bank_Statements"
    
    paths = {
        "year_base": year_base,
        "bank_csv": bank_csv,
        "bank_statements_dir": bank_statements_dir
    }
    
    # Step 5: Ensure directories exist
    try:
        bank_statements_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {
            "success": False,
            "year": year,
            "paths": {k: str(v) for k, v in paths.items()},
            "transaction_count": len(statement_df),
            "date_range": date_range,
            "message": f"Failed to create directories: {str(e)}"
        }
    
    # Step 6: Ensure CSV exists with headers
    try:
        ensure_bank_csv_exists(bank_csv)
    except Exception as e:
        return {
            "success": False,
            "year": year,
            "paths": {k: str(v) for k, v in paths.items()},
            "transaction_count": len(statement_df),
            "date_range": date_range,
            "message": f"Failed to create/validate CSV: {str(e)}"
        }
    
    # Step 7: Parse and append transactions to CSV
    try:
        # Read existing transactions
        existing_df = pd.read_csv(bank_csv)
        
        # Parse transactions from statement into standard schema
        parsed_transactions = []
        
        for _, row in statement_df.iterrows():
            # Try to find date column
            date_value = None
            for col in statement_df.columns:
                if 'date' in str(col).lower():
                    date_value = row[col]
                    break
            
            # Try to find description column
            description = None
            for col in statement_df.columns:
                if 'description' in str(col).lower() or 'memo' in str(col).lower():
                    description = row[col]
                    break
            
            # Try to find amount column
            amount = None
            for col in statement_df.columns:
                if 'amount' in str(col).lower() or 'debit' in str(col).lower() or 'credit' in str(col).lower():
                    amount = row[col]
                    break
            
            # Try to find balance column
            balance = None
            for col in statement_df.columns:
                if 'balance' in str(col).lower():
                    balance = row[col]
                    break
            
            # Determine transaction type
            trans_type = 'debit' if amount and float(amount) < 0 else 'credit'
            
            parsed_transactions.append({
                'date': date_value,
                'description': description or 'Unknown',
                'amount': amount,
                'type': trans_type,
                'balance': balance,
                'category': '',  # To be filled in later
                'source_file': statement_path.name,
                'notes': ''
            })
        
        # Create DataFrame from parsed transactions
        new_transactions_df = pd.DataFrame(parsed_transactions)
        
        # Append to existing
        combined_df = pd.concat([existing_df, new_transactions_df], ignore_index=True)
        
        # Remove duplicates based on date, description, and amount
        combined_df = combined_df.drop_duplicates(subset=['date', 'description', 'amount'], keep='first')
        
        # Save to CSV
        combined_df.to_csv(bank_csv, index=False)
        
    except Exception as e:
        return {
            "success": False,
            "year": year,
            "paths": {k: str(v) for k, v in paths.items()},
            "transaction_count": len(statement_df),
            "date_range": date_range,
            "message": f"Failed to append transactions: {str(e)}"
        }
    
    # Step 8: Archive statement file
    statement_destination = bank_statements_dir / statement_path.name
    try:
        if statement_path.exists():
            # Check if destination already exists
            if statement_destination.exists():
                # Add timestamp to avoid overwriting
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = statement_path.stem
                extension = statement_path.suffix
                statement_destination = bank_statements_dir / f"{base_name}_{timestamp}{extension}"
            
            shutil.copy2(str(statement_path), str(statement_destination))
        else:
            return {
                "success": False,
                "year": year,
                "paths": {k: str(v) for k, v in paths.items()},
                "transaction_count": len(statement_df),
                "date_range": date_range,
                "message": f"Statement file not found: {statement_path}"
            }
    except Exception as e:
        return {
            "success": False,
            "year": year,
            "paths": {k: str(v) for k, v in paths.items()},
            "transaction_count": len(statement_df),
            "date_range": date_range,
            "message": f"Failed to archive statement: {str(e)}"
        }
    
    # Step 9: Return success result
    return {
        "success": True,
        "year": year,
        "paths": {k: str(v) for k, v in paths.items()},
        "transaction_count": len(statement_df),
        "date_range": date_range,
        "message": f"Bank statement ingested successfully to {year} archive ({len(statement_df)} transactions)"
    }
