#!/usr/bin/env python3
"""
Orchestrator for receipts workflow.

- Reads a new batch JSON file from input path
- Adds ingest metadata (run id + timestamp)
- Validates using validate_receipts module
- Writes to data/receipts/receipts.json (merge)
- Creates backups
- Generates reports via build_receipts_report
"""

import argparse
import json
import os
import datetime
from scripts.validate.validate_receipts import validate_receipts
from scripts.receipts.build_receipts_report import build_receipts_report


def read_batch(path):
    with open(path, 'r') as f:
        return json.load(f)


def load_existing(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def write_data(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def backup_file(path, backup_dir):
    if os.path.exists(path):
        ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        os.makedirs(backup_dir, exist_ok=True)
        import shutil
        shutil.copy(path, os.path.join(backup_dir, f"receipts_backup_{ts}.json"))


def main():
    parser = argparse.ArgumentParser(description="Process receipts batch.")
    parser.add_argument('--input', required=True, help='Path to batch JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no write)')
    args = parser.parse_args()

    batch = read_batch(args.input)
    # add metadata
    run_id = datetime.datetime.now().isoformat()
    for rec in batch:
        rec['_ingest_run'] = run_id

    # validate
    ok, issues = validate_receipts(batch)
    if not ok:
        print("Validation failed:", issues)
        return

    data_path = 'data/receipts/receipts.json'
    backup_dir = 'backups/receipts'
    existing = load_existing(data_path)
    merged = existing + batch
    if args.dry_run:
        print(f"Would write {len(merged)} records")
    else:
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        backup_file(data_path, backup_dir)
        write_data(data_path, merged)
        build_receipts_report(merged)
        print(f"Wrote {len(merged)} records")


if __name__ == '__main__':
    main()
