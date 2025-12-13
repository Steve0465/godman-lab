# Trello Export - Quick Start

## 🚀 3-Step Setup

### 1. Get Credentials (2 minutes)

Visit: https://trello.com/power-ups/admin

- Copy your **API Key**
- Click "Token" → Allow → Copy **Token**

### 2. Set Environment Variables

```bash
export TRELLO_API_KEY="your_api_key_here"
export TRELLO_TOKEN="your_token_here"
```

### 3. Run Export

```bash
python tools/trello_export.py --board "Memphis Pool" --verbose
```

---

## 📝 Common Commands

```bash
# Basic export
python tools/trello_export.py --board "Memphis Pool"

# With progress
python tools/trello_export.py --board "Memphis Pool" --verbose

# By board ID
python tools/trello_export.py --board-id "ABC123"

# Custom output
python tools/trello_export.py --board "Memphis Pool" --output backup.json

# Debug mode
python tools/trello_export.py --board "Memphis Pool" --raw
```

---

## 📂 Output

**Default location:** `exports/memphis_pool_board.json`

Use for:
- AI/Codex analysis
- Backup/archival
- Project reporting
- Data migration

---

## 🤖 Codex Prompts

After exporting, try:

```
"Analyze exports/memphis_pool_board.json:
 - Show overdue tasks
 - List incomplete checklists
 - Identify blockers"
```

```
"Generate a progress report from the Trello board export"
```

```
"What are the next 5 action items based on the board?"
```

---

## ❓ Troubleshooting

**Credentials not found?**
```bash
echo $TRELLO_API_KEY  # Should show your key
echo $TRELLO_TOKEN    # Should show your token
```

**Board not found?**
- Check exact board name
- Run without `--board` to list all boards
- Use `--board-id` if multiple matches

**Need help?**
- See `tools/TRELLO_EXPORT_README.md` for full docs
- Check API status: https://trello.status.atlassian.com/

---

## 🔒 Security

✅ Use environment variables (not hardcoded)  
✅ Never commit credentials to Git  
✅ Add `.env` to `.gitignore`  
✅ Rotate tokens every 3-6 months  

---

For complete documentation, see: **tools/TRELLO_EXPORT_README.md**
