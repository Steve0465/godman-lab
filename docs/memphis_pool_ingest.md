# Memphis Pool Trello Ingest

Card-by-card ingestion and indexing system for the Memphis Pool Trello board.

## Overview

This module provides tools to:
1. Fetch all cards from the Memphis Pool board with full details
2. Build a searchable index of all cards
3. Track bill attachments with date extraction
4. Index attachment metadata without downloading files

**Key principle**: No pricing assumptions. No job cost calculations. Index-only approach.

## Setup

### Prerequisites

```bash
pip install requests
```

### Environment Variables

**Required:**
```bash
export TRELLO_KEY="your_api_key_here"
export TRELLO_TOKEN="your_api_token_here"
```

**Optional (with defaults):**
```bash
export MEMPHIS_POOL_BOARD_ID="60df29145c9a576f23056516"
export MEMPHIS_POOL_BILLS_LIST_ID="67d1e94e3597c3ef2fdc8300"
```

## Usage

### Full Ingest Pipeline

```bash
# Run complete ingest
python3 libs/memphis_pool_ingest.py
```

Output:
```
data/memphis_pool/
├── raw_cards/
│   ├── 673abc123def4567.json    # Full card details
│   └── ...
└── indexes/
    ├── cards_index.csv          # All cards metadata
    └── bills_attachments_index.csv  # Bills attachments
```

### Python API

```python
from pathlib import Path
from libs.trello_client import TrelloClient
from libs.memphis_pool_ingest import (
    pull_cards_one_by_one,
    build_cards_index,
    build_bills_index,
    get_lists_by_id
)

# Initialize client (reads from env vars)
client = TrelloClient()

# Get board structure
lists_by_id = get_lists_by_id("60df29145c9a576f23056516", client=client)

# Pull all cards with full details
output_dir = Path("data/memphis_pool/raw_cards")
saved_files = pull_cards_one_by_one(
    output_dir, 
    "60df29145c9a576f23056516", 
    client=client
)

# Build indexes
build_cards_index(
    output_dir, 
    lists_by_id, 
    Path("data/memphis_pool/indexes/cards_index.csv")
)

build_bills_index(
    output_dir,
    "67d1e94e3597c3ef2fdc8300",  # BILLS list ID
    Path("data/memphis_pool/indexes/bills_attachments_index.csv")
)
```

## Output Files

### cards_index.csv

All cards from the board with metadata:

| Column | Description |
|--------|-------------|
| card_id | Trello card ID |
| shortLink | Short URL identifier (e.g., "Z6JwfLEl") |
| name | Card name/title |
| idList | List ID where card resides |
| list_name | Human-readable list name |
| created_at | Date card was created (YYYY-MM-DD) |
| last_activity | Last activity timestamp |
| attachments_count | Number of attachments |

**Example:**
```csv
card_id,shortLink,name,idList,list_name,created_at,last_activity,attachments_count
673abc123,Z6JwfLEl,NOLEN CANON: TUNICA MS,67d1e94e,Need to Bill For,2024-11-15,2024-12-11T14:30:00.000Z,1
```

### bills_attachments_index.csv

Attachment metadata from cards in BILLS list:

| Column | Description |
|--------|-------------|
| bill_date_action | Date attachment was added (YYYY-MM-DD) |
| bill_date_filename | Date parsed from filename pattern |
| attachment_name | Filename of attachment |
| attachment_id | Trello attachment ID |
| attachment_url | Download URL for attachment |
| source_card_id | Card containing the attachment |
| source_card_name | Card name |
| action_id | Trello action ID |
| action_datetime_utc | Full timestamp (UTC) |

**Filename Date Parsing:**

Pattern: `_MMDDYYYYHHMMSS`

Examples:
- `Xerox Scan_11192025103635.pdf` → `2025-11-19`
- `invoice_12012024120000.pdf` → `2024-12-01`
- `receipt.pdf` → (empty - no pattern match)

### raw_cards/*.json

Full card details including:
- All fields (id, name, desc, idList, etc.)
- Attachments array with metadata
- Filtered actions:
  - `createCard` - card creation
  - `updateCard` - card updates
  - `addAttachmentToCard` - attachment additions
  - `deleteAttachmentFromCard` - attachment deletions

## Functions

### pull_cards_one_by_one()

```python
def pull_cards_one_by_one(
    out_dir: Path, 
    board_id: str, 
    *, 
    client: TrelloClient
) -> List[Path]
```

Fetches all cards from board with full details, one at a time.

**Features:**
- Minimal initial fetch (id, shortLink, name, idList, dateLastActivity)
- Individual card fetch with full details
- Action filtering for efficiency
- Resilient: continues on failures
- Progress logging

**Returns:** List of successfully saved card file paths

### build_cards_index()

```python
def build_cards_index(
    raw_cards_dir: Path,
    lists_by_id: Dict[str, str],
    out_csv: Path
) -> None
```

Creates CSV index of all cards with metadata.

**Extracts:**
- Card creation date from `createCard` action
- Attachment count from badges or attachments array
- List name from lists_by_id mapping

### build_bills_index()

```python
def build_bills_index(
    raw_cards_dir: Path,
    bills_list_id: str,
    out_csv: Path
) -> None
```

Creates CSV index of attachments from BILLS list cards.

**Process:**
1. Filter cards in BILLS list
2. Find all `addAttachmentToCard` actions
3. Extract attachment metadata
4. Parse dates from filenames
5. Write to CSV

**Note:** Does NOT download files. Use `TrelloClient.download_url()` separately.

### get_lists_by_id()

```python
def get_lists_by_id(
    board_id: str, 
    *, 
    client: TrelloClient
) -> Dict[str, str]
```

Fetches board lists and returns `{list_id: list_name}` mapping.

**Example:**
```python
lists = get_lists_by_id("60df29145c9a576f23056516", client=client)
# {'67d1e94e3597c3ef2fdc8300': 'BILLS', ...}
```

### parse_bill_date_from_filename()

```python
def parse_bill_date_from_filename(name: str) -> str
```

Extracts date from filename with pattern `_MMDDYYYYHHMMSS`.

**Returns:** `YYYY-MM-DD` or empty string if parse fails.

**Examples:**
```python
parse_bill_date_from_filename("Xerox Scan_11192025103635.pdf")
# "2025-11-19"

parse_bill_date_from_filename("invoice.pdf")
# ""
```

## Testing

### Test Date Parsing

```bash
python3 -c "
from libs.memphis_pool_ingest import parse_bill_date_from_filename
print(parse_bill_date_from_filename('Xerox Scan_11192025103635.pdf'))
# 2025-11-19
"
```

### Test Full Pipeline (Limited)

```bash
python3 test_memphis_ingest.py
```

This runs a limited test with the first 10 cards to validate the pipeline.

## Error Handling

The module is designed to be resilient:

- **Card fetch failures**: Logged and skipped, doesn't stop pipeline
- **Invalid JSON**: Skipped with warning
- **Missing fields**: Defaults to empty strings
- **Invalid dates**: Returns empty string
- **Rate limits**: Handled by TrelloClient (5 retries with backoff)

## Architecture Decisions

### Why Card-by-Card?

- **Controlled**: Individual card failures don't break entire ingest
- **Filtered actions**: Only fetch relevant action types
- **Debuggable**: Easy to identify which cards failed
- **Rate-limit friendly**: Exponential backoff between requests

### Why Index-Only?

- **Fast**: No large file downloads during indexing
- **Flexible**: Download specific files as needed
- **Storage efficient**: Don't duplicate Trello's storage
- **Auditable**: CSV indexes are human-readable

### Why No Pricing?

- **Accuracy**: Actual prices vary by job complexity
- **Business logic**: Pricing belongs in separate module
- **Separation of concerns**: Ingest focuses on data collection
- **No assumptions**: Let humans verify job costs

## Next Steps

After running ingest:

1. **Review indexes**: Open CSV files in Excel/Numbers
2. **Identify patterns**: Look for missing data or anomalies
3. **Download attachments**: Use `TrelloClient.download_url()` for specific files
4. **Build reports**: Use CSV indexes for analysis
5. **Track payments**: Cross-reference bills index with bank records

## Troubleshooting

### "Missing TRELLO_KEY" error

Set environment variables:
```bash
export TRELLO_KEY="your_key"
export TRELLO_TOKEN="your_token"
```

### Rate limit errors (HTTP 429)

The client automatically retries with backoff. If persistent:
- Wait 60 seconds between runs
- Reduce batch size
- Check Trello API rate limits

### Empty cards_index.csv

Check:
- Board ID is correct
- Trello credentials have access to board
- Board actually has cards

### Missing bill attachments

Check:
- BILLS list ID is correct
- Cards are actually in BILLS list (not another list)
- Cards have attachments

## Related Files

- `libs/trello_client.py` - Enhanced Trello API client
- `libs/memphis_pool_ingest.py` - This module
- `test_memphis_ingest.py` - Integration tests
- `scripts/test_trello_client.py` - Client tests

## License

Part of godman-lab internal tools.
