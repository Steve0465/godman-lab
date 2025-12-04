# OBD-II Data Directory

This directory contains OBD-II scan data from diagnostic tools.

## Supported File Formats

- **CSV**: Comma-separated values with timestamp and sensor readings
- **Parquet**: Compressed columnar format (generated from CSV imports)

## Required CSV Columns

At minimum, CSV files must contain:
- `timestamp` - Date/time of reading (ISO format or parseable)
- `rpm` - Engine RPM
- `speed` - Vehicle speed (MPH or KPH)
- `engine_load` - Engine load percentage

## Optional CSV Columns

Additional useful columns:
- `coolant_temp` - Coolant temperature
- `intake_temp` - Intake air temperature
- `maf` - Mass air flow
- `throttle_position` - Throttle position percentage
- `fuel_trim_short` - Short-term fuel trim
- `fuel_trim_long` - Long-term fuel trim
- `dtc_code` - Diagnostic Trouble Code
- `dtc_description` - DTC description

## Data Collection

### Using OBD-II Scanner/Logger

1. Connect OBD-II scanner to vehicle diagnostic port (usually under dashboard)
2. Configure scanner to log desired PIDs (Parameter IDs)
3. Start data logging before driving/testing
4. Save logged data as CSV file
5. Copy CSV file to `f250/data/obd_csv/` directory

### Recommended Scanners

- BlueDriver Bluetooth Pro
- OBDLink MX+
- Innova CarScan Pro
- Torque Pro (Android app with Bluetooth adapter)

## Data Import

Import CSV files to database using:

```bash
# Validate files first
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --dry-run

# Import to database and parquet
python f250/scripts/obd_import.py --csv-dir f250/data/obd_csv --run
```

## File Naming Convention

Use descriptive names for CSV files:
- `scan_YYYYMMDD_description.csv`
- Example: `scan_20241204_rough_idle_test.csv`

This helps identify scan purpose and date when reviewing data later.

## Data Retention

- Keep raw CSV files as backup
- Database and parquet files are generated/updated by import script
- Archive old scans periodically to save space
- Export important diagnostic sessions to notes/

## Privacy & Security

- OBD-II data may contain VIN and other vehicle identifiers
- Do not share raw scan files publicly
- Sanitize data before sharing for diagnostics help
- Use .gitignore to prevent accidental commits of sensitive data

## Query Examples

```bash
# Query for specific DTC
python f250/scripts/obd_query.py --dtc P0301

# Query misfires only
python f250/scripts/obd_query.py --misfire-only

# Query date range
python f250/scripts/obd_query.py --range 2024-01-01 2024-12-31

# Generate diagnostic report
python f250/scripts/obd_query.py --dtc P0301 --report analysis.md
```

## Troubleshooting

**Import fails with "Missing required columns"**
- Ensure CSV has timestamp, rpm, speed, engine_load columns
- Check for typos in column names
- Some scanners may use different names (e.g., "RPM" vs "rpm")

**Import shows "already imported"**
- Files are tracked in database to prevent duplicates
- Use `--force` flag to re-import: `--run --force`

**Large CSV files slow import**
- Import streams data in chunks
- Consider splitting very large files (>100MB)
- Parquet format is more efficient for large datasets

## Resources

- [OBD-II PIDs Reference](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [DTC Code Lookup](https://www.obd-codes.com/)
- [F250 Service Manual](https://www.motorcraftservice.com/)
