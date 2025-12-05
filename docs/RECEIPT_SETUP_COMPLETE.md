# Receipt Processing System - Setup Complete! 🎉

## ✅ Installation Status

### System Dependencies
- ✅ **Tesseract** v5.5.1 (OCR engine)
- ✅ **Poppler** v25.12.0 (PDF utilities)
- ✅ **Python** dependencies in requirements.txt

### Directories
- ✅ `scans/` - Drop receipt images/PDFs here
- ✅ `receipts/` - Processed receipts stored here
- ✅ `.env` - Configuration file created

## 🔑 Next Steps: API Keys

### 1. OpenAI API Key (Recommended for better extraction)

Get your API key:
1. Visit https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)
4. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

**Cost**: ~$0.01-0.05 per receipt with gpt-4o-mini (very affordable)

**Without OpenAI**: The system will still work using regex patterns, but extraction quality will be lower.

### 2. Email Setup (Optional - for monthly summaries)

For Gmail:
1. Go to https://myaccount.google.com/apppasswords
2. Generate an app password
3. Update `.env`:
   ```bash
   EMAIL_USER=your.email@gmail.com
   EMAIL_PASS=your-16-char-app-password
   RECIPIENT=your.email@gmail.com
   ```

## 🚀 Quick Start

### Test with a sample receipt:

```bash
# Activate your virtual environment (if not already)
source .venv/bin/activate

# Put a receipt image or PDF in scans/
# Then run:
python process_receipts.py
```

### Review flagged receipts:

```bash
streamlit run review/streamlit_review.py
```

This opens a web UI at http://localhost:8501 where you can:
- Review extracted data
- Edit amounts, dates, categories
- Approve or reject receipts

### Send monthly summary:

```bash
python expense_summary.py
```

## 📁 Workflow

1. **Scan** → Drop files into `scans/`
2. **Process** → Run `python process_receipts.py`
3. **Review** → Check `review_queue.csv` or use Streamlit UI
4. **Summarize** → Run `python expense_summary.py` monthly

## 🤖 Automation (Optional)

### macOS Launchd (recommended)

Edit `launchd/com.godmanlab.processreceipts.plist`:
1. Update paths to match your system
2. Set desired schedule (default: daily at 9 AM)
3. Load:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.godmanlab.processreceipts.plist
   ```

### Or use cron:

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/godman-lab && source .venv/bin/activate && python process_receipts.py
```

## 🧪 Test Commands

```bash
# Run receipt tests
cd receipts
python -m pytest test_process_receipts.py -v

# Test OCR on a specific file
python process_receipts.py --file scans/sample.jpg

# Dry run (no files moved)
python process_receipts.py --dry-run
```

## 📊 Output Files

- `receipts.csv` - All processed receipts metadata
- `review_queue.csv` - Receipts needing human review
- `receipts/*.{jpg,pdf}` - Organized receipt files

## ⚙️ Configuration

Edit `.env` to customize:
- `CATEGORIES` - Expense categories
- `OPENAI_MODEL` - AI model (gpt-4o-mini is fastest/cheapest)
- Input/output directories
- Email settings

## 🐛 Troubleshooting

**Issue**: "Tesseract not found"
- Check: `which tesseract` returns `/opt/homebrew/bin/tesseract`
- Set `TESSERACT_CMD` in `.env`

**Issue**: "No module named pytesseract"
- Run: `pip install -r requirements.txt`

**Issue**: "OpenAI API error"
- Verify your API key is correct
- Check you have credits: https://platform.openai.com/usage
- Or set `OPENAI_ENABLED=false` to use regex-only mode

## 📈 What's Next?

Once you have receipts processing:
1. Build up historical data
2. Set up monthly email automation
3. Analyze spending patterns
4. Export to accounting software

**Ready to test?** Drop a receipt in `scans/` and run:
```bash
python process_receipts.py
```
