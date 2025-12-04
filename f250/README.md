# F250 Diagnostic & Maintenance Toolkit

Production-ready tools for managing Ford F-250 OBD-II diagnostics and maintenance logs.

## Overview

This workspace provides robust, production-ready scripts for:
- Importing and validating OBD-II scan data
- Querying diagnostic data with advanced filtering
- Managing maintenance logs
- Generating comprehensive diagnostic reports

## Directory Structure

```
f250/
├── data/
│   ├── f250.db              # SQLite database (auto-generated)
│   ├── obd_logs.parquet     # Parquet format OBD data (auto-generated)
│   ├── maintenance_log.csv  # Maintenance history CSV
│   ├── obd_csv/            # Input directory for OBD CSV files
│   ├── photos/             # Photos related to repairs/diagnostics
│   └── notes/              # Generated diagnostic reports
└── scripts/
    ├── obd_import.py       # CSV import tool
    ├── obd_query.py        # Query and analysis tool
    ├── maintenance.py      # Maintenance log manager
    └── diag_report.py      # Diagnostic report generator
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create data directories:
```bash
mkdir -p f250/data/{obd_csv,photos,notes}
```

3. Initialize maintenance log:
```bash
python f250/scripts/maintenance.py init
```

## Usage

### 1. Import OBD Data

Import CSV files from OBD-II scan tools:

```bash
# Dry run to validate files
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --dry-run

# Actually import the data
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --run

# Force re-import of already imported files
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --run --force
```

**Required CSV columns:** timestamp, rpm, speed, engine_load

**Optional columns:** coolant_temp, intake_temp, maf, throttle_position, fuel_trim_short, fuel_trim_long, dtc_code, dtc_description

### 2. Query OBD Data

Query and analyze OBD data:

```bash
# Query for specific DTC
python f250/scripts/obd_query.py --dtc P0300

# Query misfire events only
python f250/scripts/obd_query.py --misfire-only

# Query with date range
python f250/scripts/obd_query.py --range 2024-01-01 2024-12-31

# Generate diagnostic report
python f250/scripts/obd_query.py --dtc P0301 --report f250/data/notes/p0301_analysis.md

# Query from parquet instead of SQLite
python f250/scripts/obd_query.py --source parquet --dtc P0300
```

### 3. Manage Maintenance Log

Track maintenance and repairs:

```bash
# Add maintenance entry
python f250/scripts/maintenance.py add \
  --date 2024-12-04 \
  --mileage 45000 \
  --type oil_change \
  --description "Full synthetic oil change, new filter" \
  --cost 75.00 \
  --vendor "Local Shop"

# List all maintenance
python f250/scripts/maintenance.py list

# List specific type of maintenance
python f250/scripts/maintenance.py list --type oil_change

# List recent entries
python f250/scripts/maintenance.py list --limit 10

# Sync CSV to SQLite database
python f250/scripts/maintenance.py sync
```

### 4. Generate Diagnostic Reports

Create comprehensive diagnostic sheets:

```bash
# Generate report for specific DTC
python f250/scripts/diag_report.py --dtc P0301

# Generate report for a job/issue
python f250/scripts/diag_report.py --job "rough_idle_investigation"

# Generate with date range filter
python f250/scripts/diag_report.py --dtc P0300 --range 2024-11-01 2024-12-04

# Specify output location
python f250/scripts/diag_report.py --dtc P0301 --output f250/data/notes/cylinder1_misfire.md
```

## Data Format

### OBD CSV Format

CSV files should contain at minimum:
- `timestamp` - ISO format or parseable date/time
- `rpm` - Engine RPM
- `speed` - Vehicle speed
- `engine_load` - Engine load percentage

Optional but recommended:
- `coolant_temp` - Coolant temperature
- `fuel_trim_short` - Short-term fuel trim
- `fuel_trim_long` - Long-term fuel trim
- `dtc_code` - Diagnostic Trouble Code
- `dtc_description` - Code description

### Maintenance Log Format

CSV with columns:
- `date` - Service date (YYYY-MM-DD)
- `mileage` - Odometer reading
- `type` - Service type (oil_change, tire_rotation, etc.)
- `description` - Detailed description
- `cost` - Service cost (optional)
- `vendor` - Shop/vendor name (optional)
- `notes` - Additional notes (optional)

## Features

### OBD Import (`obd_import.py`)
- ✅ Robust CSV validation
- ✅ Streaming import to both Parquet and SQLite
- ✅ Idempotency (skip already-imported files)
- ✅ DTC normalization
- ✅ Misfire detection
- ✅ Comprehensive logging
- ✅ Dry-run mode

### OBD Query (`obd_query.py`)
- ✅ Query by DTC code
- ✅ Date range filtering
- ✅ Misfire-only filtering
- ✅ Fuel trim analysis and classification
- ✅ Summary statistics
- ✅ Diagnostic report generation
- ✅ Support for both SQLite and Parquet sources

### Maintenance Manager (`maintenance.py`)
- ✅ CSV-based maintenance log
- ✅ Easy entry management (add/list)
- ✅ SQLite sync for integration
- ✅ Type-based filtering
- ✅ Formatted display

### Diagnostic Reports (`diag_report.py`)
- ✅ Comprehensive markdown reports
- ✅ DTC analysis and interpretation
- ✅ Related OBD event correlation
- ✅ Maintenance history integration
- ✅ Photo reference linking
- ✅ Auto-generated recommendations section

## Error Handling

All scripts include:
- Comprehensive logging
- Proper exit codes (0 = success, 1 = error)
- Input validation
- Graceful failure handling
- Informative error messages

## Integration Notes

### Google Sheets Sync (Future Enhancement)
To enable Google Sheets synchronization:
1. Set up a service account in Google Cloud Console
2. Download credentials JSON
3. Store as `f250/data/service_account.json`
4. Share target spreadsheet with service account email

Note: Trello integration is explicitly excluded per requirements.

## Tips

1. **Regular Imports**: Set up a cron job or scheduled task to run `obd_import.py --run` regularly
2. **Backup Data**: Regularly backup `f250.db` and `maintenance_log.csv`
3. **Photo Organization**: Name photos with DTC codes or job names for automatic linking
4. **Maintenance Tracking**: Always sync after adding maintenance entries for full database integration

## Troubleshooting

### Import Issues
- Ensure CSV files have required columns
- Check for UTF-8 encoding
- Verify timestamp format is parseable

### Query Performance
- Use Parquet for large datasets (faster than SQLite for analytical queries)
- Use date range filters to limit result sets
- Consider indexing SQLite tables for frequent queries

### Missing Data
- Check that maintenance log has been synced
- Verify OBD imports completed successfully
- Review import logs in database

## License

Part of the godman-lab personal automation toolkit.
