# Receipt Processing - Setup & Usage

This folder contains tools to OCR, parse, categorize, review, and summarize scanned receipts.

Quick macOS setup:
1. Install Homebrew (if not installed):
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
2. Install system deps:
   brew install tesseract poppler
3. Create and activate a Python venv:
   python3 -m venv .venv && source .venv/bin/activate
4. Install Python deps:
   pip install -r requirements.txt
5. Copy .env.example to .env and fill values (especially OPENAI_API_KEY and EMAIL_PASS).
6. Place scanned files in ./scans/ and run:
   python process_receipts.py
7. Review flagged receipts:
   streamlit run review/streamlit_review.py
8. Send monthly email (once metadata exists):
   python expense_summary.py

Docker (optional):
- Build and run the image (Streamlit UI exposed on 8501):
  docker-compose up --build -d
- Mount your scans/ and receipts/ into the container via the compose file for persistence.

Scheduling on macOS:
- Use launchd or cron to run process_receipts.py on a schedule. See launchd/com.godmanlab.processreceipts.plist for an example.

Privacy note:
- If OPENAI_ENABLED=true, OCR text will be sent to OpenAI. Set this to false to keep processing local-only.
