# Tax Inbox Watcher Implementation Summary

## Overview
Automatic file processing system for tax archive inbox using watchdog, classification, and intelligent routing.

## Architecture

### Components
1. **TaxInboxWatcher** - Main orchestrator
2. **InboxEventHandler** - File system event handler
3. **TaxClassifier** - Document classification engine
4. **TaxSync** - File organization and deduplication

### Flow
```
New File → Debounce (30s) → Stability Check → Classify → Route → Move
```

## Features

### 1. Debounced Event Processing
- Configurable debounce window (default: 30 seconds)
- Batches multiple file events together
- Waits for file write completion before processing

### 2. File Stability Detection
- Checks file age (minimum 5 seconds old)
- Verifies size hasn't changed
- Prevents processing incomplete downloads

### 3. Automatic Classification
- Extracts text from PDFs using pdfplumber
- Falls back to OCR for scanned documents
- Infers year and category with confidence scoring
- Logs detailed evidence for each decision

### 4. Intelligent Routing

#### High Confidence (≥0.7) → Auto-Apply
- Moves to canonical `YYYY/category/` structure
- No user confirmation required
- Logged with full evidence trail

#### Low Confidence (<0.7) → Review Queue
- Moves to `_metadata/review/`
- Logs classification uncertainty
- Manual review required

#### Always Auto-Applied
- Moves to `_metadata/misc/` (uncategorizable files)
- Duplicate resolution to `_metadata/duplicates/`

### 5. Duplicate Resolution
- Integrated with TaxSync duplicate detection
- Automatic resolution without user prompts
- Canonical winner stays in place
- Duplicates archived to `_metadata/duplicates/<md5>/`

### 6. Safety Guarantees
- ✅ Never deletes files
- ✅ Never processes files being written
- ✅ Never moves files outside inbox (except deduplication)
- ✅ All operations wrapped in try/except
- ✅ Comprehensive error logging

## Directory Structure

```
TAX_MASTER_ARCHIVE/
├── _inbox/                    # Drop zone for new files
├── _metadata/
│   ├── logs/                  # inbox_YYYYMMDD.log
│   ├── review/                # Low-confidence files
│   ├── misc/                  # Uncategorizable files
│   └── duplicates/            # Resolved duplicates
├── 2023/
│   ├── taxes/
│   ├── receipts/
│   └── ...
└── 2024/
    ├── taxes/
    ├── receipts/
    └── ...
```

## Usage

### Start Watcher
```bash
godman tax watch ~/Desktop/TAX_MASTER_ARCHIVE
```

### With Custom Debounce
```bash
godman tax watch ~/Desktop/TAX_MASTER_ARCHIVE --debounce 60
```

### Typical Workflow
1. Drop files into `_inbox/`
2. Watcher detects and waits for stability
3. Classification runs automatically
4. Files move to appropriate locations
5. Check `_metadata/review/` for uncertain items
6. Review logs in `_metadata/logs/`

## Logging

### Log Location
`_metadata/logs/inbox_YYYYMMDD.log`

### Log Content
- File detection events
- Classification results with confidence
- Evidence for each decision
- Move operations (source → destination)
- Errors and warnings
- Review-needed notifications

### Example Log Entry
```
2025-12-13 05:30:15 - TaxInboxWatcher.TAX_MASTER_ARCHIVE - INFO - Classified invoice_2024.pdf: year=2024, category=receipts, confidence=0.85
2025-12-13 05:30:15 - TaxInboxWatcher.TAX_MASTER_ARCHIVE - DEBUG -   Evidence: Found explicit year mention: 'Tax Year 2024'
2025-12-13 05:30:15 - TaxInboxWatcher.TAX_MASTER_ARCHIVE - DEBUG -   Evidence: Detected document type: receipt/invoice
2025-12-13 05:30:15 - TaxInboxWatcher.TAX_MASTER_ARCHIVE - INFO - Moved: invoice_2024.pdf -> 2024/receipts/invoice_2024.pdf
```

## Configuration

### Debounce Window
Time to wait after last file event before processing batch.
- **Default**: 30 seconds
- **Recommended**: 30-60 seconds for downloads
- **Minimum**: 10 seconds

### File Stability Age
Minimum file age before processing.
- **Default**: 5 seconds
- **Purpose**: Ensure write operations complete

### Ignored Files
- Extensions: `.part`, `.tmp`, `.crdownload`, `.download`
- System files: `.DS_Store`, `Thumbs.db`, `desktop.ini`, `.localized`

## Error Handling

### Unreadable Files
- Logged as error
- Skipped without blocking other files
- Can be manually reviewed in inbox

### Classification Failures
- Logged with stack trace
- File remains in inbox
- Will retry on next watcher restart

### Move Failures
- Logged with error details
- File remains in source location
- Other operations continue

## Integration Points

### TaxClassifier
- Called for each new file
- Returns classification result with evidence
- Confidence score determines routing

### TaxSync
- Generates sync plan for inbox files
- Handles duplicate detection
- Executes all move operations

### TaxValidator
- Excludes `_inbox` from validation
- Excludes `_metadata` from structural checks
- Ignores resolved duplicates

## Testing

### Manual Test
```bash
# Terminal 1: Start watcher
godman tax watch ~/Desktop/TAX_MASTER_ARCHIVE --debounce 10

# Terminal 2: Add test file
cp some_document.pdf ~/Desktop/TAX_MASTER_ARCHIVE/_inbox/

# Observe logs and file movement
```

### Check Results
```bash
# Validate archive structure
godman tax validate ~/Desktop/TAX_MASTER_ARCHIVE

# Review low-confidence items
ls ~/Desktop/TAX_MASTER_ARCHIVE/_metadata/review/

# Check logs
tail -f ~/Desktop/TAX_MASTER_ARCHIVE/_metadata/logs/inbox_*.log
```

## Dependencies

```python
watchdog          # File system event monitoring
pdfplumber        # PDF text extraction
pytesseract       # OCR fallback
Pillow           # Image processing for OCR
```

## Implementation Files

- `libs/tax/tax_inbox_watcher.py` - Main implementation (13.8KB)
- `cli/godman/tax.py` - CLI command integration
- `libs/tax/__init__.py` - Module exports

## Future Enhancements

### Potential Additions
1. Email integration (forward documents to inbox)
2. Cloud sync (Dropbox, Google Drive auto-import)
3. Bulk import mode (process existing files)
4. Machine learning confidence tuning
5. Custom routing rules configuration
6. Webhook notifications for review-needed items

### Not Planned
- Automatic deletion (safety policy)
- Processing files outside inbox
- Modification of canonical files

## Commit Reference

```
feat(tax): Add automatic inbox watcher with classification and routing
- Implement TaxInboxWatcher with debounced file processing
- Auto-classify new files using TaxClassifier
- Route high-confidence files to canonical structure
- Move low-confidence files to _metadata/review
- Integrate duplicate resolution with sync
- Add structured logging to _metadata/logs/
- Add 'godman tax watch' CLI command
- Safety: never delete files, stable file detection, comprehensive error handling
```

Branch: `feature/tax-tools-bootstrap`
Commit: `1dbac45`
