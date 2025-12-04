Next steps:
- Verify Homebrew tesseract/poppler are available and TESSERACT_CMD/POPPLER_PATH set if needed.
- Create an OpenAI API key and put it in .env if you want LLM-assisted extraction.
- Run the processor on a small batch first and review the review_queue.csv with the Streamlit UI.
- Configure launchd or cron for scheduled runs and set up a secure place for EMAIL_PASS (Keychain recommended).
