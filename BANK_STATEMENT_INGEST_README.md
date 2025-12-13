# Bank Statement Ingest with Dynamic Year Routing

## Overview

The `bank_statement_ingest()` function provides automated bank statement processing with intelligent year-based routing to the TAX_MASTER_ARCHIVE structure.

## Features

✅ **Automatic Date Extraction** - Extracts all transaction dates from statement  
✅ **Primary Year Determination** - Uses minimum transaction year for routing  
✅ **Dynamic Path Building** - Creates year-specific folder structure  
✅ **Auto-Folder Creation** - Creates all necessary directories automatically  
✅ **CSV Management** - Ensures bank_transactions_{year}.csv exists with headers  
✅ **Transaction Parsing** - Maps statement columns to standard schema  
✅ **Deduplication** - Prevents duplicate transactions  
✅ **Statement Archival** - Archives original statement file  
✅ **Workflow Logging** - Returns comprehensive result with routing info  

## Function Signature

```python
from godman_ai.tools import bank_statement_ingest

result = bank_statement_ingest(
    statement_path: Path,           # Path to bank statement CSV
    base_archive: Path = None       # Optional: defaults to ~/Desktop/TAX_MASTER_ARCHIVE
) -> Dict[str, Any]
```

## Usage Example

```python
from pathlib import Path
from godman_ai.tools import bank_statement_ingest

# Process a bank statement
result = bank_statement_ingest(
    statement_path=Path("/path/to/statement_202403.csv")
)

# Check result
if result['success']:
    print(f"✓ Statement routed to year: {result['year']}")
    print(f"  Transactions: {result['transaction_count']}")
    print(f"  Date Range: {result['date_range']['min']} to {result['date_range']['max']}")
    print(f"  CSV: {result['paths']['bank_csv']}")
else:
    print(f"✗ Error: {result['message']}")
```

## Return Value Structure

```python
{
    'success': bool,              # True if ingestion succeeded
    'year': int,                  # Primary tax year (min transaction year)
    'paths': {                    # All dynamically built paths
        'year_base': str,                              # e.g., ~/Desktop/TAX_MASTER_ARCHIVE/2024
        'bank_csv': str,                               # e.g., .../2024/bank_transactions_2024.csv
        'bank_statements_dir': str                     # e.g., .../2024/Bank_Statements/
    },
    'transaction_count': int,     # Number of transactions in statement
    'date_range': {               # Transaction date range
        'min': str,               # Earliest date (ISO format)
        'max': str                # Latest date (ISO format)
    },
    'message': str                # Status message for logging
}
```

## Archive Structure

The function creates this structure automatically:

```
~/Desktop/TAX_MASTER_ARCHIVE/
├── 2024/
│   ├── bank_transactions_2024.csv     # Year-specific transactions
│   └── Bank_Statements/               # Original statements
│       ├── statement_202401.csv
│       └── statement_202402.csv
├── 2023/
│   ├── bank_transactions_2023.csv
│   └── Bank_Statements/
│       └── statement_202312.csv
└── 2022/
    └── ...
```

## Year Determination Logic

The function uses **minimum transaction year** for routing:

```python
# Example: Statement spanning Dec 2022 - Jan 2023
transactions = [
    {'Date': '12/15/2022', ...},  # Min year
    {'Date': '12/20/2022', ...},
    {'Date': '01/05/2023', ...},
]

# Result: Routes to 2022 archive (earliest transaction year)
```

This ensures statements are categorized by when the transactions **began**, making it easier to organize statements that span year boundaries.

## Transaction Schema

Parsed transactions follow this standard schema:

```python
{
    'date': str,           # Transaction date
    'description': str,    # Transaction description/memo
    'amount': float,       # Transaction amount
    'type': str,           # 'debit' or 'credit'
    'balance': float,      # Account balance after transaction
    'category': str,       # Category (empty by default)
    'source_file': str,    # Source statement filename
    'notes': str          # Additional notes (empty by default)
}
```

## Deduplication

The function automatically prevents duplicate transactions:

- Duplicates detected by: `date`, `description`, `amount`
- First occurrence is kept
- Useful when processing overlapping statements

```python
# Statement 1: Jan 1-15
# Statement 2: Jan 10-25
# Overlap (Jan 10-15) is automatically deduplicated
```

## CSV Management

### Headers Created Automatically

When `bank_transactions_{year}.csv` doesn't exist, it's created with headers:

```csv
date,description,amount,type,balance,category,source_file,notes
```

### Appending Transactions

New transactions are appended to the existing CSV, with deduplication applied.

## Workflow Integration

The return value provides complete logging information:

```python
# Log workflow execution
print(f"Year routing: {result['year']} (based on min transaction date)")
print(f"Transactions processed: {result['transaction_count']}")
print(f"Date range: {result['date_range']['min']} to {result['date_range']['max']}")

for key, path in result['paths'].items():
    print(f"  {key}: {path}")
```

## Error Handling

The function handles errors gracefully:

```python
result = bank_statement_ingest(statement_path)

if not result['success']:
    print(f"Error: {result['message']}")
    # Possible errors:
    # - Failed to load statement
    # - Statement is empty
    # - No valid dates found
    # - Failed to create directories
    # - Failed to create/validate CSV
    # - Failed to append transactions
    # - Failed to archive statement
```

## Helper Functions

### extract_dates_from_statement

```python
from godman_ai.tools import extract_dates_from_statement

dates = extract_dates_from_statement(statement_df)
# Returns: [date(2024, 1, 1), date(2024, 1, 2), ...]
```

### determine_primary_tax_year

```python
from godman_ai.tools import determine_primary_tax_year

year = determine_primary_tax_year(dates)
# Returns: 2024 (minimum year from dates)
```

### ensure_bank_csv_exists

```python
from godman_ai.tools import ensure_bank_csv_exists

ensure_bank_csv_exists(Path("bank_transactions_2024.csv"))
# Creates CSV with headers if it doesn't exist
```

## Advanced Usage

### Processing Multiple Statements

```python
from pathlib import Path
from godman_ai.tools import bank_statement_ingest

statements = Path("downloads").glob("statement_*.csv")

for statement in statements:
    result = bank_statement_ingest(statement)
    print(f"{statement.name}: Year {result['year']}, {result['transaction_count']} trans")
```

### Custom Archive Location

```python
result = bank_statement_ingest(
    statement_path=Path("statement.csv"),
    base_archive=Path("/custom/archive/location")
)
```

## Files Modified

- `godman_ai/tools/banking.py` - Complete implementation (350+ lines)
- `godman_ai/tools/__init__.py` - Added exports

## Testing

Run the test suite:

```bash
cd /Users/stephengodman/Desktop/godman-lab
source .venv_release/bin/activate
python3 -c "from godman_ai.tools import bank_statement_ingest; print('✓ Import successful')"
```

## Notes

- **Statements are copied** (not moved) to archive for safety
- If destination file exists, timestamp is added to filename
- Column names are detected automatically (case-insensitive matching)
- Date parsing handles multiple formats via pandas
- Transaction type is determined by amount sign (negative = debit)
- CSV is created with standard headers on first use
- Deduplication prevents duplicate entries from overlapping statements

## Column Detection

The function automatically detects columns:

| Standard Field | Detected From                           |
|----------------|----------------------------------------|
| date           | Columns containing 'date', 'posted', 'transaction' |
| description    | Columns containing 'description', 'memo' |
| amount         | Columns containing 'amount', 'debit', 'credit' |
| balance        | Columns containing 'balance'            |

## Future Enhancements

Potential improvements:

- Category auto-assignment based on description patterns
- Support for multiple statement formats (PDF, OFX, QFX)
- Transaction reconciliation with bank API
- Duplicate detection across years
- Transaction categorization ML model
