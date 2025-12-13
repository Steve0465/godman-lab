# Per-Year Manifest System

## Overview

Enhanced manifest update functions with per-year organization support. Each year maintains its own MANIFEST, HASH_INDEX, and AUDIT_DATA files, while also maintaining global versions.

## Features

✅ **Per-Year Manifests** - Each year has its own MANIFEST.md  
✅ **Per-Year Hash Indices** - Each year has its own HASH_INDEX.md  
✅ **Per-Year Audit Data** - Each year has its own AUDIT_DATA.md  
✅ **Global Tracking** - Global versions track entire archive  
✅ **File Isolation** - Updating one year never affects other years  
✅ **Automatic Organization** - Files automatically placed in correct year folder  

## Archive Structure

```
TAX_MASTER_ARCHIVE/
├── metadata/
│   ├── MANIFEST.md           # Global manifest (all files)
│   ├── HASH_INDEX.md         # Global hash index (all files)
│   └── AUDIT_DATA.md         # Global audit data (all files)
│
└── data/
    ├── 2022/
    │   ├── receipts_2022.csv
    │   ├── bank_transactions_2022.csv
    │   ├── MANIFEST.md       # 2022-specific manifest
    │   ├── HASH_INDEX.md     # 2022-specific hash index
    │   └── AUDIT_DATA.md     # 2022-specific audit data
    │
    ├── 2023/
    │   ├── receipts_2023.csv
    │   ├── bank_transactions_2023.csv
    │   ├── MANIFEST.md       # 2023-specific manifest
    │   ├── HASH_INDEX.md     # 2023-specific hash index
    │   └── AUDIT_DATA.md     # 2023-specific audit data
    │
    └── 2024/
        ├── receipts_2024.csv
        ├── bank_transactions_2024.csv
        ├── MANIFEST.md       # 2024-specific manifest
        ├── HASH_INDEX.md     # 2024-specific hash index
        └── AUDIT_DATA.md     # 2024-specific audit data
```

## Enhanced Functions

### BaseArchive Methods

```python
from libs.uaf.base_archive import BaseArchive

archive = BaseArchive(root=Path("/path/to/archive"), name="My Archive")

# Get paths for specific year
manifest_2024 = archive.get_manifest_path(year=2024)
# Returns: /path/to/archive/data/2024/MANIFEST.md

hash_2024 = archive.get_hash_index_path(year=2024)
# Returns: /path/to/archive/data/2024/HASH_INDEX.md

audit_2024 = archive.get_audit_data_path(year=2024)
# Returns: /path/to/archive/data/2024/AUDIT_DATA.md

# Get global paths
manifest_global = archive.get_manifest_path(year=None)
# Returns: /path/to/archive/metadata/MANIFEST.md
```

### Regenerate Manifest

```python
from libs.uaf.archive_sync import regenerate_manifest

# Generate manifest for specific year
manifest_2024 = regenerate_manifest(archive, year=2024)
# Creates: data/2024/MANIFEST.md
# Contains: Only files from 2024

# Generate global manifest
manifest_global = regenerate_manifest(archive, year=None)
# Creates: metadata/MANIFEST.md
# Contains: All files from all years
```

### Regenerate Hash Index

```python
from libs.uaf.archive_sync import regenerate_hash_index

# Generate hash index for specific year
hash_2024 = regenerate_hash_index(archive, year=2024, algorithm="sha256")
# Creates: data/2024/HASH_INDEX.md
# Contains: Hashes only for 2024 files

# Generate global hash index
hash_global = regenerate_hash_index(archive, year=None)
# Creates: metadata/HASH_INDEX.md
# Contains: Hashes for all files
```

### Regenerate Audit Data (NEW)

```python
from libs.uaf.archive_sync import regenerate_audit_data

# Generate audit data for specific year
audit_2024 = regenerate_audit_data(archive, year=2024)
# Creates: data/2024/AUDIT_DATA.md
# Contains: Audit trail for 2024 files (sizes, modified times)

# Generate global audit data
audit_global = regenerate_audit_data(archive, year=None)
# Creates: metadata/AUDIT_DATA.md
# Contains: Audit trail for all files
```

### Sync Archive

```python
from libs.uaf.archive_sync import sync_archive

# Sync specific year (creates both year-specific AND global files)
result = sync_archive(archive, year=2024)
# Creates:
#   - data/2024/MANIFEST.md
#   - data/2024/HASH_INDEX.md
#   - data/2024/AUDIT_DATA.md
#   - metadata/MANIFEST.md
#   - metadata/HASH_INDEX.md
#   - metadata/AUDIT_DATA.md

# Sync global only
result = sync_archive(archive, year=None)
# Creates:
#   - metadata/MANIFEST.md
#   - metadata/HASH_INDEX.md
#   - metadata/AUDIT_DATA.md

# Sync ALL years
result = sync_archive(archive, sync_all_years=True)
# Creates files for every year directory found, plus global files
```

## Usage Examples

### Example 1: Sync After Adding 2024 Files

```python
from pathlib import Path
from libs.uaf.base_archive import BaseArchive
from libs.uaf.archive_sync import sync_archive

# Initialize archive
archive = BaseArchive(
    root=Path.home() / "Desktop" / "TAX_MASTER_ARCHIVE",
    name="Tax Master Archive"
)

# After adding new 2024 files via receipt_ingest() or bank_statement_ingest()
result = sync_archive(archive, year=2024)

print(f"✓ Synced year 2024")
print(f"  Manifests created: {len(result['manifest_paths'])}")
print(f"  Files tracked: {result['stats']['data_files']}")
```

### Example 2: Sync All Years at End of Tax Season

```python
# After processing entire tax year
result = sync_archive(archive, sync_all_years=True)

print(f"✓ Synced all years")
print(f"  Years processed: {result['stats']['years_synced']}")
print(f"  Total files: {result['stats']['total_files']}")

# List all created files
for path in result['manifest_paths']:
    print(f"  Created: {path}")
```

### Example 3: Selective Sync

```python
# Sync only specific components for a year
from libs.uaf.archive_sync import (
    regenerate_manifest,
    regenerate_hash_index,
    regenerate_audit_data
)

# Just update manifest for 2023
regenerate_manifest(archive, year=2023)

# Just update hash index for 2024
regenerate_hash_index(archive, year=2024)

# Just update audit data for 2025
regenerate_audit_data(archive, year=2025)
```

### Example 4: Verify Integrity of Specific Year

```python
from libs.uaf.archive_validator import ArchiveValidator

# Create validator
validator = ArchiveValidator(archive)

# Validate specific year
validation_result = validator.validate()

# Check hash index for 2024
hash_2024_path = archive.get_hash_index_path(year=2024)
if hash_2024_path.exists():
    print(f"✓ 2024 hash index exists")
    # Could add hash verification logic here
```

## Integration with Receipt and Bank Statement Ingest

### Receipt Workflow

```python
from godman_ai.tools import receipt_ingest
from libs.uaf.base_archive import BaseArchive
from libs.uaf.archive_sync import sync_archive

# Process receipt
result = receipt_ingest(
    pdf_path=Path("receipt.pdf"),
    ocr_text="HOME DEPOT\nDate: 05/15/2024\nTotal: $169.28"
)

if result['success']:
    year = result['year']  # 2024
    
    # Sync that year's manifest
    archive = BaseArchive(
        root=Path.home() / "Desktop" / "TAX_MASTER_ARCHIVE",
        name="Tax Archive"
    )
    sync_archive(archive, year=year)
    
    print(f"✓ Receipt ingested and {year} manifest updated")
```

### Bank Statement Workflow

```python
from godman_ai.tools import bank_statement_ingest
from libs.uaf.archive_sync import sync_archive

# Process statement
result = bank_statement_ingest(
    statement_path=Path("statement_202403.csv")
)

if result['success']:
    year = result['year']  # 2024
    
    # Sync manifest
    archive = BaseArchive(
        root=Path.home() / "Desktop" / "TAX_MASTER_ARCHIVE",
        name="Tax Archive"
    )
    sync_archive(archive, year=year)
    
    print(f"✓ Statement ingested and {year} manifest updated")
```

## File Isolation Guarantees

### What's Guaranteed

✅ **Updating 2024 never touches 2023 files**
- Each year's MANIFEST, HASH_INDEX, and AUDIT_DATA are independent
- Changes to one year don't affect other years

✅ **Global files track everything**
- Global MANIFEST includes all years
- Global HASH_INDEX includes all files
- Global AUDIT_DATA includes all files

✅ **No overwrites between years**
- Each year's metadata lives in its own directory
- Syncing year X only updates year X files (plus global)

### What Gets Updated

When you call `sync_archive(archive, year=2024)`:

**Updated:**
- `data/2024/MANIFEST.md` ✓
- `data/2024/HASH_INDEX.md` ✓
- `data/2024/AUDIT_DATA.md` ✓
- `metadata/MANIFEST.md` ✓ (global)
- `metadata/HASH_INDEX.md` ✓ (global)
- `metadata/AUDIT_DATA.md` ✓ (global)

**NOT Updated:**
- `data/2023/MANIFEST.md` ✗
- `data/2023/HASH_INDEX.md` ✗
- `data/2023/AUDIT_DATA.md` ✗
- `data/2025/...` ✗

## AUDIT_DATA Contents

The AUDIT_DATA.md file contains:

- Total file count
- Total size (MB)
- Per-file information:
  - File path
  - Size (KB)
  - Last modified timestamp
- Integrity check timestamp
- Status summary

Example:

```markdown
# Audit Data: Tax Archive - 2024

**Generated:** 2024-12-13T01:55:00
**Total Files:** 15
**Total Size:** 2.45 MB
**Year:** 2024

## File Audit Trail

| File | Size (KB) | Last Modified |
| ---- | --------- | ------------- |
| `data/2024/receipts_2024.csv` | 12.45 | 2024-12-01T10:30:00 |
| `data/2024/bank_transactions_2024.csv` | 45.67 | 2024-12-05T14:22:00 |
...

## Integrity Checks

Last integrity check: 2024-12-13T01:55:00
Status: ✓ All files accounted for
```

## Best Practices

### 1. Sync After Each Ingest

```python
# After processing any file for a specific year
result = ingest_function(...)
if result['success']:
    sync_archive(archive, year=result['year'])
```

### 2. Full Sync Periodically

```python
# Weekly or monthly
sync_archive(archive, sync_all_years=True)
```

### 3. Backup Before Sync

```python
import shutil

# Backup metadata before regenerating
metadata_dir = archive.root / "metadata"
backup_dir = archive.root / "metadata_backup"
shutil.copytree(metadata_dir, backup_dir, dirs_exist_ok=True)

# Then sync
sync_archive(archive, year=2024)
```

## API Reference

### regenerate_manifest(archive, year=None, template_path=None)

Regenerate MANIFEST.md file.

**Parameters:**
- `archive` (BaseArchive): Archive instance
- `year` (Optional[int]): Year for year-specific manifest, None for global
- `template_path` (Optional[Path]): Custom template

**Returns:** Path to generated MANIFEST.md

### regenerate_hash_index(archive, year=None, template_path=None, algorithm="sha256")

Regenerate HASH_INDEX.md file.

**Parameters:**
- `archive` (BaseArchive): Archive instance
- `year` (Optional[int]): Year for year-specific index, None for global
- `template_path` (Optional[Path]): Custom template
- `algorithm` (str): Hash algorithm

**Returns:** Path to generated HASH_INDEX.md

### regenerate_audit_data(archive, year=None, template_path=None)

Regenerate AUDIT_DATA.md file.

**Parameters:**
- `archive` (BaseArchive): Archive instance
- `year` (Optional[int]): Year for year-specific audit, None for global
- `template_path` (Optional[Path]): Custom template

**Returns:** Path to generated AUDIT_DATA.md

### sync_archive(archive, year=None, regenerate_manifest_file=True, regenerate_hash_file=True, regenerate_audit_file=True, hash_algorithm="sha256", sync_all_years=False)

Synchronize archive metadata files.

**Parameters:**
- `archive` (BaseArchive): Archive instance
- `year` (Optional[int]): Specific year to sync
- `regenerate_manifest_file` (bool): Whether to regenerate manifest
- `regenerate_hash_file` (bool): Whether to regenerate hash index
- `regenerate_audit_file` (bool): Whether to regenerate audit data
- `hash_algorithm` (str): Hash algorithm
- `sync_all_years` (bool): Sync all years instead of just one

**Returns:** Dict with sync results

## Files Modified

- `libs/uaf/base_archive.py`
  - Enhanced `get_manifest_path(year=None)`
  - Enhanced `get_hash_index_path(year=None)`
  - Added `get_audit_data_path(year=None)`

- `libs/uaf/archive_sync.py`
  - Enhanced `regenerate_manifest(archive, year=None, ...)`
  - Enhanced `regenerate_hash_index(archive, year=None, ...)`
  - Added `regenerate_audit_data(archive, year=None, ...)`
  - Enhanced `sync_archive(archive, year=None, ..., sync_all_years=False)`

## Testing

Run the test suite:

```bash
cd /Users/stephengodman/Desktop/godman-lab
source .venv_release/bin/activate
python3 -c "from libs.uaf.archive_sync import sync_archive; print('✓ Import successful')"
```
