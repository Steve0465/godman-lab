# Trello Board Export Tool

Export complete Trello board structure (lists, cards, checklists, attachments, labels) to structured JSON for Codex analysis and archival.

---

## Setup Instructions

### 1. Get Trello API Credentials

#### Step 1: Get Your API Key

1. Go to https://trello.com/power-ups/admin
2. Log in with your Trello account
3. Click **"New"** to create a new Power-Up or API Key
4. Your **API Key** will be displayed at the top of the page
5. Copy and save it securely

#### Step 2: Generate an API Token

1. On the same page, look for the **"Token"** link next to your API key
2. Click the **"Token"** link (or manually visit: `https://trello.com/1/authorize?key=YOUR_API_KEY&name=BoardExporter&expiration=never&response_type=token&scope=read`)
3. Click **"Allow"** to authorize the application
4. Copy the **Token** that appears on the next page
5. Save it securely

---

### 2. Set Environment Variables

#### On macOS/Linux:

Add to your `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`:

```bash
export TRELLO_API_KEY="your_api_key_here"
export TRELLO_TOKEN="your_token_here"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### On Windows:

**PowerShell:**
```powershell
$env:TRELLO_API_KEY="your_api_key_here"
$env:TRELLO_TOKEN="your_token_here"
```

**Command Prompt:**
```cmd
set TRELLO_API_KEY=your_api_key_here
set TRELLO_TOKEN=your_token_here
```

#### Temporary (Current Session Only):

```bash
export TRELLO_API_KEY="your_api_key_here"
export TRELLO_TOKEN="your_token_here"
```

---

### 3. Install Dependencies

```bash
pip install requests
```

Or from the project root:

```bash
pip install -r requirements.txt
```

---

## Usage

### Basic Export

Export a board by name:

```bash
python tools/trello_export.py --board "Memphis Pool"
```

### Export with Verbose Logging

See detailed progress:

```bash
python tools/trello_export.py --board "Memphis Pool" --verbose
```

### Export by Board ID

If you have multiple boards with the same name:

```bash
python tools/trello_export.py --board-id "5a1b2c3d4e5f6g7h"
```

### Custom Output Path

Specify a different output file:

```bash
python tools/trello_export.py --board "Memphis Pool" --output exports/my_board.json
```

### Save Raw API Response

For debugging purposes:

```bash
python tools/trello_export.py --board "Memphis Pool" --raw
```

This creates both:
- `exports/memphis_pool_board.json` (structured)
- `exports/memphis_pool_board.raw.json` (raw API data)

---

## Output Format

The exported JSON follows this structure:

```json
{
  "board": {
    "id": "board_id",
    "name": "Memphis Pool",
    "url": "https://trello.com/b/...",
    "desc": "Board description",
    "closed": false,
    "exported_at": "2024-12-11T21:00:00"
  },
  "lists": [
    {
      "id": "list_id",
      "name": "To Do",
      "pos": 0,
      "closed": false,
      "cards": [
        {
          "id": "card_id",
          "name": "Card Title",
          "desc": "Card description...",
          "due": "2024-12-15T12:00:00.000Z",
          "dueComplete": false,
          "url": "https://trello.com/c/...",
          "labels": [
            {
              "id": "label_id",
              "name": "Urgent",
              "color": "red"
            }
          ],
          "attachments": [
            {
              "id": "att_id",
              "name": "diagram.pdf",
              "url": "https://...",
              "mimeType": "application/pdf",
              "bytes": 12345
            }
          ],
          "checklists": [
            {
              "id": "checklist_id",
              "name": "Tasks",
              "pos": 0,
              "items": [
                {
                  "id": "item_id",
                  "name": "Complete task",
                  "state": "complete",
                  "pos": 0
                }
              ]
            }
          ],
          "pos": 0,
          "closed": false
        }
      ]
    }
  ]
}
```

---

## Output Location

By default, the export is saved to:

```
exports/memphis_pool_board.json
```

This file can be used for:
- **Codex analysis** - Ask AI to analyze your project board
- **Backup/archival** - Keep historical snapshots
- **Data migration** - Move to other tools
- **Reporting** - Generate custom reports from board data

---

## Using with Codex

Once exported, you can use the JSON with GitHub Copilot or other AI tools:

### Example Prompts:

**1. Analyze Project Status:**
```
Analyze the Trello board export in exports/memphis_pool_board.json. 
Give me a summary of:
- How many tasks are in each list
- Which tasks are overdue
- Which tasks have incomplete checklists
```

**2. Generate Progress Report:**
```
Based on the Trello export, create a weekly progress report showing:
- Completed tasks (cards in "Done" list)
- In-progress tasks
- Blocked tasks (cards with "Blocked" label)
- Upcoming due dates
```

**3. Extract Action Items:**
```
Review the board export and list all incomplete checklist items 
from cards that are due within the next 7 days.
```

**4. Dependency Analysis:**
```
Analyze the board structure and identify potential dependencies 
between cards based on descriptions and checklists.
```

---

## Troubleshooting

### "Trello credentials not found"

Make sure environment variables are set:
```bash
echo $TRELLO_API_KEY
echo $TRELLO_TOKEN
```

If empty, set them as shown in Setup section.

### "Board 'Memphis Pool' not found"

The script will list all your available boards. Check the exact board name or use `--board-id`.

### "Multiple boards found matching..."

If you have multiple boards with the same name, use the `--board-id` flag with the specific board ID shown in the error message.

### Rate Limiting

The script automatically retries with exponential backoff if Trello rate limits are hit. Just wait for the retry.

### API Errors

If you see authentication errors:
1. Verify your API key and token are correct
2. Make sure the token has read access to your boards
3. Try generating a new token

---

## Advanced Usage

### Automated Exports

Set up a cron job to export regularly:

```bash
# Add to crontab (crontab -e)
0 0 * * * cd /path/to/godman-lab && python tools/trello_export.py --board "Memphis Pool" --output exports/backup_$(date +\%Y\%m\%d).json
```

### Export Multiple Boards

Create a shell script:

```bash
#!/bin/bash
boards=("Memphis Pool" "Project X" "Team Tasks")

for board in "${boards[@]}"; do
    python tools/trello_export.py --board "$board" --output "exports/${board// /_}.json"
done
```

### Diff Between Exports

Compare two exports to see changes:

```bash
diff exports/backup_20241201.json exports/backup_20241211.json
```

Or use a JSON diff tool:

```bash
jq -S . exports/backup_20241201.json > /tmp/old.json
jq -S . exports/backup_20241211.json > /tmp/new.json
diff /tmp/old.json /tmp/new.json
```

---

## Security Best Practices

1. **Never commit credentials** - Add `.env` to `.gitignore`
2. **Use environment variables** - Don't hardcode keys in scripts
3. **Rotate tokens periodically** - Generate new tokens every few months
4. **Limit token scope** - Only request read access if that's all you need
5. **Store securely** - Use a password manager for credentials

---

## API Rate Limits

Trello API limits:
- **300 requests per 10 seconds** per token
- **100 requests per 10 seconds** per API key

The script automatically handles rate limiting with retry logic.

---

## Support

For issues with:
- **Trello API** - Visit https://developer.atlassian.com/cloud/trello/
- **Script bugs** - Open an issue in the godman-lab repository
- **Feature requests** - Submit a pull request or issue

---

## License

Part of the godman-lab project.
