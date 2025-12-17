# Memphis Pool: Local Board Export Ingest

**Branch:** `feat/memphis-pool-trello-rebuild`  
**Commit:** 9924b92

## Overview

Enhanced `libs/memphis_pool_ingest.py` to support ingesting from a local Trello board export JSON file, eliminating the need for API access when working with exported data.

## New Features

### 1. Local Export Loading

```python
def load_board_export(export_json_path: Path) -> dict
```

- Loads and validates Trello board export JSON from disk
- Validates presence of required keys: `cards` and `lists`
- Returns parsed board data dictionary

### 2. Card Writing from Export

```python
def write_raw_cards_from_export(export_data: dict, raw_cards_dir: Path) -> int
```

- Writes individual card JSON files from board export
- One file per card: `<card_id>.json`
- Returns count of cards written

### 3. List Mapping from Export

```python
def get_lists_by_id_from_export(export_data: dict) -> Dict[str, str]
```

- Builds `{list_id: list_name}` mapping from export data
- No API calls required

### 4. Complete Export Ingest Pipeline

```python
def ingest_from_board_export(
    export_json_path: Path,
    raw_cards_dir: Path,
    indexes_dir: Path,
    bills_list_id: str = "67d1e94e3597c3ef2fdc8300"
) -> None
```

- Complete ingest workflow from local export
- Steps:
  1. Load export JSON
  2. Write individual card files
  3. Build lists mapping
  4. Generate `cards_index.csv`
  5. Generate `bills_attachments_index.csv`

### 5. Card ID Date Extraction

```python
def trello_id_created_at(card_id: str) -> str
```

- Extracts creation date from Trello card ID
- Trello IDs encode Unix timestamp in first 8 hex chars
- Fallback when `createCard` action is missing

## Improvements to Existing Functions

### Enhanced `build_cards_index()`

- **Before:** Required `createCard` action for `created_at`
- **After:** Falls back to deriving date from card ID if action missing
- More robust for board exports with limited action history

### Enhanced `build_bills_index()`

- **Before:** Only extracted from `addAttachmentToCard` actions
- **After:** Falls back to `card["attachments"]` array if no actions
- Strategy:
  1. Prefer `addAttachmentToCard` actions (includes timestamps)
  2. Fallback to `attachments` array (no timestamps, but still captures attachments)
- Handles exports with different action detail levels

### Argparse Support in `main()`

New command-line arguments:

```bash
--export-json PATH          # Path to board export JSON (triggers local ingest)
--raw-cards-dir PATH        # Override raw cards directory
--indexes-dir PATH          # Override indexes directory
--bills-list-id ID          # Override BILLS list ID
```

## Usage

### From Local Export (No API Required)

```bash
# Basic usage
python3 libs/memphis_pool_ingest.py \
  --export-json memphis_data/raw_exports/board_export.json

# With custom output directories
python3 libs/memphis_pool_ingest.py \
  --export-json board_export.json \
  --raw-cards-dir output/cards \
  --indexes-dir output/indexes
```

### From API (Original Behavior)

```bash
# Requires TRELLO_KEY and TRELLO_TOKEN environment variables
export TRELLO_KEY="your_key"
export TRELLO_TOKEN="your_token"

python3 libs/memphis_pool_ingest.py
```

## Test Results

Tested with real Memphis Pool board export:

```
Source: memphis_data/raw_exports/board_export.json (7.5MB)
Cards: 479 cards ingested
Lists: 25 lists mapped
Bills: 17 bill attachments indexed (1 BILLS card)

Output:
- memphis_data/raw_cards/          (479 JSON files)
- memphis_data/indexes/cards_index.csv         (480 rows: header + 479 cards)
- memphis_data/indexes/bills_attachments_index.csv  (18 rows: header + 17 bills)
```

## Output Files

### cards_index.csv

All cards with metadata:

| Column | Description |
|--------|-------------|
| card_id | Trello card ID |
| shortLink | Short URL identifier |
| name | Card name/title |
| idList | List ID |
| list_name | List name (from mapping) |
| created_at | Creation date (from action or card ID) |
| last_activity | Last activity timestamp |
| attachments_count | Number of attachments |

### bills_attachments_index.csv

Bill attachments from BILLS list:

| Column | Description |
|--------|-------------|
| bill_date_action | Date from action (empty if no action) |
| bill_date_filename | Date parsed from filename pattern |
| attachment_name | Filename |
| attachment_id | Trello attachment ID |
| attachment_url | Download URL |
| source_card_id | Card containing attachment |
| source_card_name | Card name |
| action_id | Action ID (empty if from fallback) |
| action_datetime_utc | Action timestamp (empty if from fallback) |

## Benefits

### 1. No API Required

- Works with exported board data
- No Trello credentials needed
- No rate limits
- Repeatable/deterministic results

### 2. Offline Processing

- Process board data anywhere
- No internet connection required
- Version control friendly (can track exports over time)

### 3. Historical Data

- Process old board exports
- Compare board states at different points in time
- Audit trail of changes

### 4. Faster Development

- No API delays
- Immediate results
- Easy to test with different data

### 5. Privacy

- Keep sensitive board data local
- No credentials in environment
- Full control over data access

## Technical Details

### Trello ID Date Extraction

Trello card IDs are 24-character hex strings where:
- First 8 chars = Unix timestamp (seconds) in hex
- Remaining 16 chars = random/sequence data

Example:
```
Card ID: 6836232640f2ffc8c8edb6a2
         ^^^^^^^^ (first 8 chars)
Hex: 68362326
Decimal: 1748075302
Date: 2024-05-24
```

### Fallback Logic

**created_at determination:**
1. Try `createCard` action date
2. Fall back to card ID extraction
3. Empty string if all fail

**Bills attachment extraction:**
1. Try `addAttachmentToCard` actions (preferred - has timestamps)
2. Fall back to `card["attachments"]` array (no timestamps)
3. Empty list if card not in BILLS list

## Backward Compatibility

✅ **100% backward compatible** - original API-based ingest unchanged:

- If `--export-json` not provided → uses API (original behavior)
- All existing environment variables respected
- All existing functions work as before
- No breaking changes

## Future Enhancements

Potential additions:

1. **Diff mode:** Compare two exports and show changes
2. **Merge mode:** Combine multiple exports
3. **Filter mode:** Export subset of cards (by list, date range, etc.)
4. **Validation mode:** Check export integrity and completeness
5. **Action history:** Reconstruct timeline from action logs

## Related Files

- `libs/memphis_pool_ingest.py` - Main ingest module (enhanced)
- `libs/memphis_pool_bills.py` - Bills PDF processing (unchanged)
- `libs/trello_client.py` - API client (unchanged, not used for export mode)

## No Pricing Logic

As required, zero pricing assumptions or calculations added:
- ✅ Read-only operations
- ✅ Index generation only
- ✅ No job price inference
- ✅ No cost calculations
- ✅ Only records what exists in data

---

**Status:** ✅ Complete and tested  
**Commit:** 9924b92  
**Files Changed:** 1 (`libs/memphis_pool_ingest.py`)  
**Lines Added:** +265  
**Lines Removed:** -17
