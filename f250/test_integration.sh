#!/bin/bash
# Integration test for F250 tooling
# Tests all scripts in sequence to demonstrate functionality

set -e  # Exit on error

echo "=========================================="
echo "F250 Tooling Integration Test"
echo "=========================================="

# Setup
TEST_DIR=$(mktemp -d /tmp/f250_test_XXXXXX)
mkdir -p "${TEST_DIR}/obd_csv"
DB_PATH="${TEST_DIR}/test.db"
CSV_DIR="${TEST_DIR}/obd_csv"
MAINT_CSV="${TEST_DIR}/maintenance.csv"

echo -e "\n1. Creating test CSV data..."
cat > "${TEST_DIR}/obd_csv/test_scan.csv" << 'EOF'
timestamp,rpm,speed,engine_load,coolant_temp,fuel_trim_short,fuel_trim_long,dtc_code,dtc_description
2024-12-04 10:00:00,800,0,12.5,190,2.0,1.5,,
2024-12-04 10:01:00,1500,30,38.2,192,2.3,1.6,,
2024-12-04 10:02:00,850,0,15.2,194,15.5,10.2,P0300,Random Misfire Detected
2024-12-04 10:03:00,850,0,14.8,194,14.8,9.8,P0301,Cylinder 1 Misfire Detected
2024-12-04 10:04:00,900,5,18.3,195,13.2,8.5,P0301,Cylinder 1 Misfire Detected
EOF

echo "✓ Test CSV created"

echo -e "\n2. Testing obd_import.py (dry-run)..."
python3 f250/scripts/obd_import.py \
    --csv-dir "$CSV_DIR" \
    --db-path "$DB_PATH" \
    --parquet-path "${TEST_DIR}/obd.parquet" \
    --dry-run
echo "✓ Dry-run successful"

echo -e "\n3. Testing obd_import.py (actual import)..."
python3 f250/scripts/obd_import.py \
    --csv-dir "$CSV_DIR" \
    --db-path "$DB_PATH" \
    --parquet-path "${TEST_DIR}/obd.parquet" \
    --run
echo "✓ Import successful"

echo -e "\n4. Testing maintenance.py (init)..."
python3 f250/scripts/maintenance.py \
    --csv-path "$MAINT_CSV" \
    --db-path "$DB_PATH" \
    init
echo "✓ Maintenance log initialized"

echo -e "\n5. Testing maintenance.py (add entry)..."
python3 f250/scripts/maintenance.py \
    --csv-path "$MAINT_CSV" \
    --db-path "$DB_PATH" \
    add \
    --date 2024-12-04 \
    --mileage 50000 \
    --type spark_plugs \
    --description "Replaced all 8 spark plugs" \
    --cost 120.00 \
    --vendor "AutoZone"
echo "✓ Maintenance entry added"

echo -e "\n6. Testing maintenance.py (sync to DB)..."
python3 f250/scripts/maintenance.py \
    --csv-path "$MAINT_CSV" \
    --db-path "$DB_PATH" \
    sync
echo "✓ Maintenance synced to database"

echo -e "\n7. Testing obd_query.py (DTC query)..."
python3 f250/scripts/obd_query.py \
    --db-path "$DB_PATH" \
    --dtc P0301 \
    --limit 10
echo "✓ DTC query successful"

echo -e "\n8. Testing obd_query.py (misfire-only)..."
python3 f250/scripts/obd_query.py \
    --db-path "$DB_PATH" \
    --misfire-only \
    --limit 5
echo "✓ Misfire query successful"

echo -e "\n9. Testing diag_report.py (generate report)..."
python3 f250/scripts/diag_report.py \
    --db-path "$DB_PATH" \
    --dtc P0301 \
    --output "${TEST_DIR}/diagnostic_report.md"
echo "✓ Diagnostic report generated"

echo -e "\n10. Verifying generated files..."
if [ -f "$DB_PATH" ]; then
    echo "✓ SQLite database created"
fi
if [ -f "${TEST_DIR}/obd.parquet" ]; then
    echo "✓ Parquet file created"
fi
if [ -f "$MAINT_CSV" ]; then
    echo "✓ Maintenance CSV created"
fi
if [ -f "${TEST_DIR}/diagnostic_report.md" ]; then
    echo "✓ Diagnostic report created"
fi

echo -e "\n=========================================="
echo "All tests passed successfully! ✓"
echo "=========================================="
echo -e "\nTest artifacts located in: ${TEST_DIR}"
echo "You can review:"
echo "  - Database: $DB_PATH"
echo "  - Parquet: ${TEST_DIR}/obd.parquet"
echo "  - Maintenance CSV: $MAINT_CSV"
echo "  - Diagnostic Report: ${TEST_DIR}/diagnostic_report.md"

# Cleanup prompt
echo -e "\nTo clean up test data, run:"
echo "  rm -rf ${TEST_DIR}"
