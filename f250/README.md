# F250 Workspace - OBD Diagnostics and Maintenance Tracking

Robust tooling for managing F250 OBD diagnostic data and maintenance history.

## Overview

This workspace provides a comprehensive set of tools for:
- Importing and managing OBD-II diagnostic data
- Querying and analyzing vehicle sensor readings
- Tracking maintenance history
- Generating diagnostic reports
- Syncing maintenance logs with Google Sheets

## Directory Structure

```
f250/
├── scripts/              # Executable scripts
│   ├── obd_import.py    # Import OBD CSV data to SQLite/Parquet
│   ├── obd_query.py     # Query and analyze OBD data
│   ├── maintenance.py   # Manage maintenance log
│   ├── diag_report.py   # Generate diagnostic reports
│   └── gsheets_sync.py  # Sync maintenance log with Google Sheets
├── data/                # Data storage (gitignored)
│   ├── f250.db         # SQLite database
│   ├── csv/            # Raw CSV imports
│   ├── parquet/        # Parquet format data
│   ├── photos/         # Diagnostic photos
│   ├── maintenance_log.csv  # Maintenance history
│   └── notes/          # Diagnostic reports and notes
```

## Scripts

### 1. obd_import.py - OBD Data Import

Import OBD-II CSV data into SQLite database and convert to Parquet format.

**Features:**
- Automatic CSV discovery and validation
- Streaming import for large files
- DTC column normalization
- Robust error handling and logging

**Usage:**
```bash
# Dry run to validate files
./f250/scripts/obd_import.py --csv-dir f250/data/csv --dry-run

# Import data
./f250/scripts/obd_import.py --csv-dir f250/data/csv --run

# Custom paths
./f250/scripts/obd_import.py --csv-dir /path/to/csv --db-path custom.db --run
```

**Required CSV Columns:**
- At least one of: `timestamp`, `device_time`
- Optional: `dtc_code`, `engine_rpm`, `vehicle_speed`, fuel trim columns, etc.

### 2. obd_query.py - OBD Data Query and Analysis

Query and analyze OBD data with advanced filtering and reporting.

**Features:**
- Query SQLite or Parquet data sources
- Filter by DTC, date range, misfire events
- Misfire analysis
- Fuel trim classification
- Generate diagnostic reports

**Usage:**
```bash
# Query all data
./f250/scripts/obd_query.py --source sqlite

# Filter by DTC
./f250/scripts/obd_query.py --dtc P0300 --source sqlite

# Filter by date range
./f250/scripts/obd_query.py --range 2024-01-01 2024-12-31

# Misfire events only
./f250/scripts/obd_query.py --misfire-only

# Generate diagnostic report
./f250/scripts/obd_query.py --dtc P0300 --report f250/data/notes/p0300_analysis.md
```

### 3. maintenance.py - Maintenance Log Management

Track and manage vehicle maintenance history.

**Features:**
- CSV-based maintenance log
- Add, list, and filter maintenance entries
- Sync to SQLite database
- Multiple maintenance types supported

**Usage:**
```bash
# Add maintenance entry
./f250/scripts/maintenance.py add \
  --date 2024-12-01 \
  --mileage 50000 \
  --type oil_change \
  --description "5W-20 full synthetic oil change" \
  --cost 75.00 \
  --shop "Local Garage"

# List all maintenance
./f250/scripts/maintenance.py list

# Filter by type
./f250/scripts/maintenance.py list --type oil_change

# Filter by date range
./f250/scripts/maintenance.py list --start-date 2024-01-01 --end-date 2024-12-31

# Sync to database
./f250/scripts/maintenance.py sync
```

**Maintenance Types:**
- `oil_change` - Oil and filter change
- `tire_rotation` - Tire rotation/balance
- `brake_service` - Brake inspection/service
- `inspection` - Vehicle inspection
- `repair` - Repairs
- `fluid_change` - Fluid changes (coolant, transmission, etc.)
- `other` - Other maintenance

### 4. diag_report.py - Diagnostic Report Generator

Generate comprehensive diagnostic reports combining OBD data, maintenance history, and photos.

**Features:**
- Pull relevant OBD events by DTC or date range
- Link related maintenance entries
- Reference related photos
- Markdown format with structured sections

**Usage:**
```bash
# Generate report for specific DTC
./f250/scripts/diag_report.py --dtc P0300 --title "Random Misfire Investigation"

# Generate report with job ID
./f250/scripts/diag_report.py --job-id JOB-001 --title "Rough Idle Diagnosis"

# Specify date range
./f250/scripts/diag_report.py --dtc P0171 --date-range 2024-11-01 2024-12-01

# Custom output path
./f250/scripts/diag_report.py --dtc P0300 --output f250/data/notes/misfire_report.md
```

**Report Sections:**
- Issue summary
- OBD diagnostic data (DTCs, sensor readings, fuel trim)
- Related maintenance history
- Related photos
- Analysis and findings
- Recommendations
- Parts needed
- Additional notes

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create data directories:
```bash
mkdir -p f250/data/{csv,parquet,photos,notes}
```

3. Place OBD CSV files in `f250/data/csv/`

4. Import data:
```bash
./f250/scripts/obd_import.py --csv-dir f250/data/csv --run
```

## Database Schema

### obd_logs Table
- `id` - Auto-increment primary key
- `timestamp` - Event timestamp
- `device_time` - Device time
- `session_id` - Session identifier
- `dtc_code` - Diagnostic Trouble Code
- `dtc_description` - DTC description
- `engine_rpm` - Engine RPM
- `vehicle_speed` - Vehicle speed
- `coolant_temp` - Coolant temperature
- `intake_temp` - Intake air temperature
- `maf` - Mass air flow
- `throttle_pos` - Throttle position
- `fuel_pressure` - Fuel pressure
- `fuel_level` - Fuel level
- `o2_sensor_1` - O2 sensor 1
- `o2_sensor_2` - O2 sensor 2
- `stft_bank1` - Short term fuel trim bank 1
- `ltft_bank1` - Long term fuel trim bank 1
- `stft_bank2` - Short term fuel trim bank 2
- `ltft_bank2` - Long term fuel trim bank 2
- `misfire_count` - Misfire count
- `raw_data` - Raw data JSON
- `imported_at` - Import timestamp

### maintenance Table
- `id` - Auto-increment primary key
- `date` - Maintenance date
- `mileage` - Vehicle mileage
- `type` - Maintenance type
- `description` - Work description
- `cost` - Cost
- `shop` - Shop/location
- `notes` - Additional notes
- `created_at` - Creation timestamp

## Workflow Example

1. **Import OBD data:**
```bash
./f250/scripts/obd_import.py --csv-dir f250/data/csv --run
```

2. **Query for issues:**
```bash
./f250/scripts/obd_query.py --misfire-only
```

3. **Add maintenance entry:**
```bash
./f250/scripts/maintenance.py add --date 2024-12-04 --type repair \
  --description "Replaced spark plugs" --cost 150.00
```

4. **Generate diagnostic report:**
```bash
./f250/scripts/diag_report.py --dtc P0300 --title "Misfire Repair"
```

5. **Sync maintenance to database:**
```bash
./f250/scripts/maintenance.py sync
```

6. **Sync to Google Sheets (optional):**
```bash
# Setup: Create service account at https://console.cloud.google.com
# Enable Google Sheets API and download credentials JSON
export GOOGLE_SERVICE_ACCOUNT_JSON=~/f250-credentials.json
./f250/scripts/gsheets_sync.py push --sheet "F250 Maintenance"
```

## Google Sheets Integration

The `gsheets_sync.py` script allows bidirectional sync with Google Sheets:

**Setup:**
1. Create Google Cloud project: https://console.cloud.google.com
2. Enable Google Sheets API
3. Create service account and download JSON credentials
4. Share your Google Sheet with the service account email (found in JSON)
5. Install dependencies: `pip install gspread google-auth`

**Usage:**
```bash
# Push local CSV to Google Sheets
./f250/scripts/gsheets_sync.py push --sheet "F250 Maintenance" \
  --service-account ~/credentials.json

# Pull from Google Sheets to local CSV
./f250/scripts/gsheets_sync.py pull --sheet "F250 Maintenance" \
  --service-account ~/credentials.json
```

**Security:** Never commit service account credentials to git. Use environment variable or secure storage.

## Notes

- All dates should be in `YYYY-MM-DD` format
- DTC codes are case-insensitive
- Database and data files are excluded from git (see .gitignore)
- Photos should be named with DTC codes or job IDs for automatic linking
- All scripts support `--verbose` flag for detailed logging
