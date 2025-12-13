# Trello API Client - libs/trello.py

A minimal, production-ready Trello REST API client using simple authentication via query parameters.

---

## Features

✅ **Simple authentication** - API key + token via environment variables  
✅ **Clean API** - Pythonic method names and return types  
✅ **Error handling** - Descriptive exceptions for all error cases  
✅ **Type hints** - Full type annotations for IDE support  
✅ **Session reuse** - Efficient connection pooling  
✅ **Context manager** - Proper resource cleanup  
✅ **No dependencies** - Only uses `requests` (already installed)  

---

## Quick Start

### 1. Get Credentials

Visit: https://trello.com/power-ups/admin

1. Click **"New"** or select existing Power-Up
2. Copy your **API Key**
3. Click **"Token"** → **"Allow"** → Copy **Token**

### 2. Set Environment Variables

```bash
export TRELLO_API_KEY="your_api_key_here"
export TRELLO_TOKEN="your_token_here"
```

Or add to `.env` file:
```bash
# .env
export TRELLO_API_KEY="abc123..."
export TRELLO_TOKEN="xyz789..."
```

Then: `source .env`

### 3. Use the Client

```python
from libs.trello import TrelloClient

# Initialize client (reads from environment variables)
client = TrelloClient()

# Get your boards
boards = client.get_boards()
for board in boards:
    print(f"{board['name']} - {board['url']}")

# Get cards from a board
cards = client.get_board_cards(board_id="abc123")
```

---

## API Reference

### Initialization

```python
from libs.trello import TrelloClient, TrelloAuthError

# Option 1: From environment variables (recommended)
client = TrelloClient()

# Option 2: Pass credentials directly
client = TrelloClient(
    api_key="your_key",
    token="your_token"
)

# Option 3: Context manager (auto-closes session)
with TrelloClient() as client:
    boards = client.get_boards()
```

### User Methods

#### `get_me()`
Get information about the authenticated user.

```python
user = client.get_me()
print(user['fullName'])  # "John Doe"
print(user['username'])  # "johndoe"
print(user['id'])        # "abc123..."
```

**Returns:** `Dict[str, Any]` - User information

---

### Board Methods

#### `get_boards(fields="id,name,url")`
Get all boards for the authenticated user.

```python
boards = client.get_boards()
# [{'id': '...', 'name': 'My Board', 'url': 'https://...'}, ...]

# Custom fields
boards = client.get_boards(fields="id,name,desc,closed")
```

**Args:**
- `fields` (str): Comma-separated list of fields to return
  - Default: `"id,name,url"`
  - Available: `id, name, desc, url, closed, idOrganization, prefs, ...`

**Returns:** `List[Dict[str, Any]]` - List of boards

---

#### `get_board(board_id, **params)`
Get a specific board by ID.

```python
board = client.get_board("abc123")
print(board['name'])
print(board['url'])

# With additional data
board = client.get_board(
    "abc123",
    lists="all",
    cards="visible",
    members="all"
)
```

**Args:**
- `board_id` (str): The board ID
- `**params`: Additional query parameters
  - `lists`: `"all"` to include lists
  - `cards`: `"visible"`, `"all"`, or `"none"`
  - `members`: `"all"` to include members

**Returns:** `Dict[str, Any]` - Board information

---

#### `get_board_lists(board_id, fields=None, **params)`
Get all lists from a board.

```python
lists = client.get_board_lists("abc123")
for lst in lists:
    print(lst['name'])

# With custom fields
lists = client.get_board_lists(
    "abc123",
    fields="id,name,closed,pos"
)
```

**Args:**
- `board_id` (str): The board ID
- `fields` (str, optional): Fields to return
- `**params`: Additional query parameters

**Returns:** `List[Dict[str, Any]]` - List of lists

---

#### `get_board_cards(board_id, fields=None, **params)`
Get all cards from a board.

```python
cards = client.get_board_cards("abc123")
for card in cards:
    print(card['name'])

# With attachments and checklists
cards = client.get_board_cards(
    "abc123",
    attachments="true",
    checklists="all"
)
```

**Args:**
- `board_id` (str): The board ID
- `fields` (str, optional): Fields to return
- `**params`: Additional query parameters
  - `attachments`: `"true"` or `"cover"`
  - `checklists`: `"all"`
  - `members`: `"true"`

**Returns:** `List[Dict[str, Any]]` - List of cards

---

### List Methods

#### `get_list(list_id, fields=None, **params)`
Get a specific list by ID.

```python
lst = client.get_list("list123")
print(lst['name'])
```

**Returns:** `Dict[str, Any]` - List information

---

#### `get_list_cards(list_id, fields=None, **params)`
Get all cards from a list.

```python
cards = client.get_list_cards("list123")
```

**Returns:** `List[Dict[str, Any]]` - List of cards

---

### Card Methods

#### `get_card(card_id, fields=None, **params)`
Get a specific card by ID.

```python
card = client.get_card("card123")
print(card['name'])
print(card['desc'])

# With full details
card = client.get_card(
    "card123",
    attachments="true",
    checklists="all",
    members="true"
)
```

**Returns:** `Dict[str, Any]` - Card information

---

### Search Methods

#### `search(query, modelTypes="cards,boards", **params)`
Search Trello for cards, boards, etc.

```python
results = client.search("pool installation")
cards = results.get('cards', [])
boards = results.get('boards', [])

# Search only cards
results = client.search(
    "customer name",
    modelTypes="cards"
)
```

**Args:**
- `query` (str): Search query
- `modelTypes` (str): Types to search
  - Options: `"cards"`, `"boards"`, `"members"`, `"organizations"`
  - Comma-separated for multiple

**Returns:** `Dict[str, Any]` - Search results by type

---

## Usage Examples

### Example 1: List All Boards

```python
from libs.trello import TrelloClient

client = TrelloClient()
boards = client.get_boards()

print(f"You have {len(boards)} boards:\n")
for board in boards:
    print(f"• {board['name']}")
    print(f"  {board['url']}\n")
```

### Example 2: Export Board Data

```python
from libs.trello import TrelloClient
import json

client = TrelloClient()

# Find board by name
boards = client.get_boards()
board = next(b for b in boards if b['name'] == "Memphis Pool")

# Get complete board data
lists = client.get_board_lists(board['id'])
cards = client.get_board_cards(
    board['id'],
    attachments="true",
    checklists="all"
)

# Export to JSON
export_data = {
    'board': board,
    'lists': lists,
    'cards': cards
}

with open('board_export.json', 'w') as f:
    json.dump(export_data, f, indent=2)
```

### Example 3: Find Cards by Customer

```python
from libs.trello import TrelloClient

client = TrelloClient()

# Search for customer
results = client.search("John Smith", modelTypes="cards")
cards = results.get('cards', [])

print(f"Found {len(cards)} cards for John Smith:\n")
for card in cards:
    print(f"• {card['name']}")
    print(f"  {card['url']}\n")
```

### Example 4: Get Unbilled Jobs

```python
from libs.trello import TrelloClient

client = TrelloClient()

# Get board
boards = client.get_boards()
board_id = boards[0]['id']

# Get all lists
lists = client.get_board_lists(board_id)

# Find "Jobs that I need to bill for" list
unbilled_list = next(
    lst for lst in lists 
    if "bill" in lst['name'].lower()
)

# Get cards from that list
cards = client.get_list_cards(unbilled_list['id'])

print(f"You have {len(cards)} unbilled jobs:\n")
for card in cards:
    print(f"• {card['name']}")
```

### Example 5: Context Manager (Auto-Cleanup)

```python
from libs.trello import TrelloClient

with TrelloClient() as client:
    boards = client.get_boards()
    print(f"Found {len(boards)} boards")
    
    for board in boards:
        cards = client.get_board_cards(board['id'])
        print(f"{board['name']}: {len(cards)} cards")

# Session automatically closed here
```

---

## Error Handling

### Authentication Errors

```python
from libs.trello import TrelloClient, TrelloAuthError

try:
    client = TrelloClient()
except TrelloAuthError as e:
    print(f"Authentication failed: {e}")
    # Output: TRELLO_API_KEY not found. Set environment variable...
```

### API Errors

```python
from libs.trello import TrelloClient, TrelloAPIError

client = TrelloClient()

try:
    board = client.get_board("invalid_id")
except TrelloAPIError as e:
    print(f"API error: {e}")
    # Output: Trello API error 404: invalid id
```

### Complete Error Handling

```python
from libs.trello import TrelloClient, TrelloAuthError, TrelloAPIError

try:
    client = TrelloClient()
    boards = client.get_boards()
    
except TrelloAuthError as e:
    print(f"❌ Authentication failed: {e}")
    print("Get credentials from: https://trello.com/power-ups/admin")
    
except TrelloAPIError as e:
    print(f"❌ API error: {e}")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

---

## Testing

Run the test suite:

```bash
# Ensure credentials are set
source .env

# Run tests
python libs/test_trello.py
```

Expected output:
```
================================================================================
TRELLO API CLIENT TEST
================================================================================

Test 1: Authentication
--------------------------------------------------------------------------------
✅ Successfully authenticated with Trello
   API Key: cb4db562...
   Token: ATTA88db...

Test 2: Get User Info
--------------------------------------------------------------------------------
✅ User: Your Name
   Username: @yourname
   ID: abc123...

Test 3: Get Boards
--------------------------------------------------------------------------------
✅ Found 5 boards:
   1. Memphis Pool (ID: 60df2914...)
   2. Personal Tasks (ID: 5f8a9b...)
   ...

ALL TESTS COMPLETED
```

---

## Advanced Usage

### Custom Request Parameters

The `_request()` method automatically injects authentication, but you can pass any Trello API parameter:

```python
# Get cards with custom filters
cards = client.get_board_cards(
    board_id="abc123",
    filter="visible",           # visible, all, closed, open
    fields="id,name,desc,due",  # Specific fields
    limit=100,                  # Max cards to return
    since="2024-01-01"          # Date filter
)
```

### Rate Limiting

Trello's API has rate limits (300 requests per 10 seconds per API key). The client doesn't automatically handle this, but you can:

```python
import time
from libs.trello import TrelloClient, TrelloAPIError

client = TrelloClient()

boards = client.get_boards()

for board in boards:
    try:
        cards = client.get_board_cards(board['id'])
        print(f"{board['name']}: {len(cards)} cards")
    except TrelloAPIError as e:
        if "429" in str(e):  # Rate limit
            print("Rate limited, waiting 10 seconds...")
            time.sleep(10)
            cards = client.get_board_cards(board['id'])  # Retry
```

### Session Configuration

The client uses `requests.Session()` for connection pooling. You can customize it:

```python
from libs.trello import TrelloClient

client = TrelloClient()

# Configure session
client.session.headers.update({'User-Agent': 'MyApp/1.0'})
client.session.verify = True  # SSL verification

# Now make requests
boards = client.get_boards()
```

---

## Integration with Existing Tools

### Use with tools/trello_export.py

The new client can replace the custom implementation in `tools/trello_export.py`:

```python
from libs.trello import TrelloClient

client = TrelloClient()

# Get board
boards = client.get_boards()
board = next(b for b in boards if b['name'] == "Memphis Pool")

# Get full data
lists = client.get_board_lists(board['id'])
cards = client.get_board_cards(
    board['id'],
    attachments="true",
    checklists="all"
)

# Process and export...
```

---

## Troubleshooting

### "TRELLO_API_KEY not found"

**Solution:** Set environment variables

```bash
export TRELLO_API_KEY="your_key"
export TRELLO_TOKEN="your_token"
```

### "Trello API error 401: unauthorized"

**Cause:** Invalid or expired credentials

**Solution:** Generate new token from https://trello.com/power-ups/admin

### "Trello API error 404: board not found"

**Cause:** Invalid board ID or no access

**Solution:** 
1. Verify board ID is correct
2. Check you have access to the board
3. Use `get_boards()` to see available boards

### "Network error communicating with Trello"

**Cause:** No internet connection or firewall blocking

**Solution:** Check internet connection and proxy settings

---

## Security Best Practices

✅ **Never commit credentials** to Git  
✅ **Use environment variables** for API keys  
✅ **Add `.env` to `.gitignore`**  
✅ **Rotate tokens** every 3-6 months  
✅ **Use read-only tokens** when possible  
✅ **Monitor API usage** for suspicious activity  

---

## API Documentation

For complete Trello REST API documentation:
https://developer.atlassian.com/cloud/trello/rest/

---

## Support

**Get API Credentials:**  
https://trello.com/power-ups/admin

**Trello API Docs:**  
https://developer.atlassian.com/cloud/trello/

**Status Page:**  
https://trello.status.atlassian.com/

---

## License

This module is part of the godman-lab project.
