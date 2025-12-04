#!/usr/bin/env python3
import re
import os
import shutil
from pathlib import Path
from datetime import datetime
from dateutil import parser as dateparser
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Optional environment overrides
POPPLER_PATH = os.getenv("POPPLER_PATH", None)  # e.g. /opt/homebrew/bin for mac homebrew
TESSERACT_CMD = os.getenv("TESSERACT_CMD", None)  # full path to tesseract binary if not in PATH

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

INPUT_DIR = Path(os.getenv("INPUT_DIR", "scans"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "receipts"))
METADATA_CSV = Path(os.getenv("METADATA_CSV", "receipts.csv"))
REVIEW_CSV = Path(os.getenv("REVIEW_CSV", "review_queue.csv"))

# helpers

def sanitize_name(s):
    return re.sub(r'[^A-Za-z0-9 _\-\.]', '_', s).strip()[:80]


def ocr_image(img):
    return pytesseract.image_to_string(img, lang='eng')


def extract_date(text):
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? \d{2,4}\b',
    ]
    for pat in date_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                dt = dateparser.parse(m.group(0), fuzzy=True, dayfirst=False)
                return dt.date().isoformat()
            except:
                pass
    try:
        dt = dateparser.parse(text, fuzzy=True, default=datetime(2000,1,1))
        if dt.year >= 2000 and dt.year <= datetime.now().year + 1:
            return dt.date().isoformat()
    except:
        return None
    return None


def extract_total(text):
    amounts = re.findall(r'[\$€£]?\s*\d{1,3}(?:[,
\d{3}])*(?:\.\d{2})', text)
    if 'total' in text.lower():
        lines = text.splitlines()
        for l in lines:
            if 'total' in l.lower():
                a = re.findall(r'[\$€£]?\s*\d{1,3}(?:[,
\d{3}])*(?:\.\d{2})', l)
                if a:
                    try:
                        return float(a[-1].replace('$','').replace(',','').strip())
                    except:
                        pass
    cleaned = []
    for a in amounts:
        try:
            cleaned.append(float(a.replace('$','').replace(',','').strip()))
        except:
            pass
    if cleaned:
        return max(cleaned)
    return None


def extract_vendor(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    blacklist = ['invoice','receipt','total','date','tax','amount','subtotal','qty']
    for l in lines[:8]:
        lower = l.lower()
        if not any(b in lower for b in blacklist) and len(l) > 2:
            return sanitize_name(l)
    return "UNKNOWN"


def needs_review(rec):
    if rec['vendor'] == 'UNKNOWN' or rec['total'] == 0.0:
        return True
    # additional heuristics could be added here
    return False


def process_file(path: Path):
    textual = ""
    imgs = []
    try:
        if path.suffix.lower() in ['.pdf']:
            pages = convert_from_path(str(path), dpi=300, poppler_path=POPPLER_PATH) if POPPLER_PATH else convert_from_path(str(path), dpi=300)
            imgs = pages
        else:
            imgs = [Image.open(path)]
    except Exception as e:
        print(f"Skipping {path} open/convert error: {e}")
        return None

    for img in imgs:
        try:
            textual += "\n" + ocr_image(img)
        except Exception as e:
            print(f"OCR error on {path}: {e}")

    vendor = extract_vendor(textual) or "UNKNOWN"
    date_iso = extract_date(textual) or datetime.now().date().isoformat()
    total = extract_total(textual) or 0.0

    year = date_iso.split("-")[0]
    month = date_iso.split("-")[1]
    dest_dir = OUTPUT_DIR / year / month / vendor
    dest_dir.mkdir(parents=True, exist_ok=True)
    new_name = f"{date_iso}_{vendor}_{total:.2f}{path.suffix}".replace(' ','_')
    dest = dest_dir / sanitize_name(new_name)
    try:
        shutil.move(str(path), str(dest))
    except Exception as e:
        print(f"Failed to move {path} -> {dest}: {e}")
        return None

    rec = {
        "original_name": path.name,
        "stored_path": str(dest),
        "vendor": vendor,
        "date": date_iso,
        "total": float(total),
        "parsed_text_snippet": textual[:1000].replace('\n',' ')
    }
    rec['needs_review'] = needs_review(rec)
    return rec


def main():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for p in sorted(INPUT_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in ['.pdf','.png','.jpg','.jpeg','.tiff']:
            print("Processing", p.name)
            rec = process_file(p)
            if rec:
                records.append(rec)

    if records:
        df = pd.DataFrame(records)
        if METADATA_CSV.exists():
            try:
                df_existing = pd.read_csv(METADATA_CSV)
                df = pd.concat([df_existing, df], ignore_index=True)
            except Exception as e:
                print("Warning: could not read existing metadata CSV:", e)
        df.to_csv(METADATA_CSV, index=False)
        print("Saved metadata to", METADATA_CSV)

        # save review queue
        review_df = df[df['needs_review'] == True]
        if not review_df.empty:
            review_df.to_csv(REVIEW_CSV, index=False)
            print("Saved review queue to", REVIEW_CSV)

        # monthly summary
        df['date'] = pd.to_datetime(df['date'])
        summary = df.groupby(df['date'].dt.to_period('M'))['total'].sum().sort_index()
        summary_df = summary.reset_index()
        summary_df.columns = ['month','total']
        summary_df.to_csv("monthly_summary.csv", index=False)
        print("Monthly summary saved to monthly_summary.csv")
    else:
        print("No files processed.")

if __name__ == "__main__":
    main()