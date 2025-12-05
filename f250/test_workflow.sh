#!/bin/bash
# F250 Workflow Test Script
# Demonstrates the complete workflow for OBD and maintenance tracking
# Can be run from anywhere - paths are automatically detected

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== F250 OBD & Maintenance Tracking Workflow Test ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Import OBD data
echo "Step 1: Importing OBD data..."
python "$PROJECT_ROOT/f250/scripts/obd_import.py" --run
echo ""

# Step 2: Query OBD data
echo "Step 2: Querying OBD data..."
python "$PROJECT_ROOT/f250/scripts/obd_query.py"
echo ""

# Step 3: Query misfire events
echo "Step 3: Querying misfire events..."
python "$PROJECT_ROOT/f250/scripts/obd_query.py" --misfire-only
echo ""

# Step 4: Add maintenance entry
echo "Step 4: Adding maintenance entry..."
python "$PROJECT_ROOT/f250/scripts/maintenance.py" add \
  --date 2024-12-04 \
  --mileage 85000 \
  --type spark_plugs \
  --description "Replaced all spark plugs" \
  --cost 120.00 \
  --shop "Auto Shop"
echo ""

# Step 5: List maintenance entries
echo "Step 5: Listing maintenance entries..."
python "$PROJECT_ROOT/f250/scripts/maintenance.py" list
echo ""

# Step 6: Sync to SQLite
echo "Step 6: Syncing maintenance to SQLite..."
python "$PROJECT_ROOT/f250/scripts/maintenance.py" sync
echo ""

# Step 7: Generate diagnostic report
echo "Step 7: Generating diagnostic report for P0300..."
python "$PROJECT_ROOT/f250/scripts/diag_report.py" --dtc P0300
echo ""

echo "=== Workflow Test Complete ==="
