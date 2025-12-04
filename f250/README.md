# F250 OBD and Maintenance Tracking

Robust tooling for managing OBD diagnostics and maintenance logs for the Ford F250.

## Features

- **OBD Data Import**: CSV discovery, validation, and import to SQLite and Parquet
- **Query Engine**: Query OBD data with DTC filtering, date ranges, and misfire analysis
- **Maintenance Tracking**: CSV-based maintenance log with SQLite sync
- **Diagnostic Reports**: Generate comprehensive diagnostic sheets with linked data

## Directory Structure

```
f250/
├── data/
│   ├── f250.db                  # SQLite database
│   ├── maintenance_log.csv      # Maintenance entries
│   ├── obd_csv/                 # Raw OBD CSV files
│   ├── parquet/                 # Converted Parquet files
│   ├── notes/                   # Diagnostic reports
│   └── photos/                  # Related photos
└── scripts/
    ├── obd_import.py            # Import OBD data
    ├── obd_query.py             # Query and analyze OBD data
    ├── maintenance.py           # Manage maintenance log
    └── diag_report.py           # Generate diagnostic reports
```

## Setup

Install required dependencies:

```bash
pip install pandas pyarrow sqlite3
```

## Usage

### Import OBD Data

Import CSV files containing OBD data:

```bash
# Dry run to validate files
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --dry-run

# Import files
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --run
```

Required CSV columns: `timestamp`, `rpm`, `speed`, `coolant_temp`

Optional columns: `dtc`, `fuel_trim_st`, `fuel_trim_lt`, `misfire_count`

### Query OBD Data

Query imported data:

```bash
# Get summary of all data
python f250/scripts/obd_query.py

# Filter by DTC
python f250/scripts/obd_query.py --dtc P0300

# Filter by date range
python f250/scripts/obd_query.py --range 2024-01-01 2024-12-31

# Show only misfire events
python f250/scripts/obd_query.py --misfire-only

# Generate diagnostic report
python f250/scripts/obd_query.py --dtc P0300 --report f250/data/notes/p0300_analysis.md
```

### Manage Maintenance Log

Track maintenance entries:

```bash
# Add a maintenance entry
python f250/scripts/maintenance.py add \
  --date 2024-01-15 \
  --mileage 75000 \
  --type oil_change \
  --description "5W-30 synthetic oil change" \
  --cost 65.00 \
  --shop "Local Auto"

# List all entries
python f250/scripts/maintenance.py list

# List specific type
python f250/scripts/maintenance.py list --type oil_change

# Get history
python f250/scripts/maintenance.py history --start-date 2024-01-01

# Sync to SQLite
python f250/scripts/maintenance.py sync
```

### Generate Diagnostic Reports

Create comprehensive diagnostic sheets:

```bash
# Generate report for a DTC
python f250/scripts/diag_report.py --dtc P0300

# Generate report for a maintenance job
python f250/scripts/diag_report.py \
  --job-name "Ignition Coil Replacement" \
  --job-type repair
```

## Data Schema

### OBD Logs Table

```sql
CREATE TABLE obd_logs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    rpm REAL,
    speed REAL,
    coolant_temp REAL,
    dtc TEXT,
    fuel_trim_st REAL,
    fuel_trim_lt REAL,
    misfire_count INTEGER,
    source_file TEXT,
    import_date TEXT NOT NULL
);
```

### Maintenance Table

```sql
CREATE TABLE maintenance (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    mileage INTEGER,
    type TEXT NOT NULL,
    description TEXT,
    cost REAL,
    shop TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

## Features

### OBD Import (`obd_import.py`)

- Automatic CSV discovery and validation
- Required column checking
- DTC column normalization
- Idempotent imports (skip already-imported files)
- Streaming import to both Parquet and SQLite
- Comprehensive logging
- Dry-run mode for validation

### OBD Query (`obd_query.py`)

- Query by DTC code
- Date range filtering
- Misfire-only filtering
- Misfire pattern analysis by RPM range
- Fuel trim classification (lean/rich/normal)
- Summary statistics
- Multiple output formats (table, CSV, JSON)
- Diagnostic report generation

### Maintenance Log (`maintenance.py`)

- CSV-based storage
- Add/list/history operations
- Type filtering
- Date range queries
- SQLite sync for integration with OBD data
- Multiple output formats

### Diagnostic Reports (`diag_report.py`)

- DTC-specific reports
- Job-based reports
- Linked OBD events
- Maintenance history integration
- Photo discovery and linking
- Markdown format for easy viewing

## Error Handling

All scripts include:
- Comprehensive logging
- Input validation
- Database transaction safety
- Non-zero exit codes on errors
- Graceful error messages

## Examples

### Complete Workflow

```bash
# 1. Import OBD data
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --run

# 2. Query for misfires
python f250/scripts/obd_query.py --misfire-only

# 3. Add maintenance entry
python f250/scripts/maintenance.py add \
  --date 2024-12-01 \
  --mileage 80000 \
  --type spark_plugs \
  --description "Replaced all 8 spark plugs" \
  --cost 120.00

# 4. Sync maintenance to database
python f250/scripts/maintenance.py sync

# 5. Generate diagnostic report
python f250/scripts/diag_report.py --dtc P0300
```

## Notes

- All scripts support `--verbose` for detailed logging
- Database is automatically initialized on first use
- Import operations are idempotent and safe to re-run
- Reports are generated in Markdown format
- Photo discovery uses fuzzy filename matching
