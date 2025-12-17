"""
Memphis Pool bills PDF processing.

Downloads bill attachments from Trello, extracts text (no OCR),
and indexes dollar amounts found in the text.

Does NOT make pricing assumptions. Only records amounts actually in PDFs.
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import List, Tuple

from pypdf import PdfReader

from trello_client import TrelloClient, TrelloError


def safe_filename(name: str) -> str:
    """Convert filename to safe version with only alphanumeric, dots, dashes, underscores.
    
    Args:
        name: Original filename
        
    Returns:
        Safe filename with spaces replaced by underscores, special chars removed
        
    Example:
        >>> safe_filename("Invoice #123 (Final).pdf")
        "Invoice_123_Final.pdf"
    """
    # Replace spaces with underscores
    safe = name.replace(" ", "_")
    
    # Keep only alphanumeric, dots, dashes, underscores
    safe = re.sub(r'[^\w\.\-]', '', safe)
    
    # Remove multiple consecutive underscores
    safe = re.sub(r'_+', '_', safe)
    
    return safe


def sha256_file(path: Path) -> str:
    """Calculate SHA256 hash of file.
    
    Args:
        path: Path to file
        
    Returns:
        Hex string of SHA256 hash
    """
    sha256 = hashlib.sha256()
    
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def download_bills_from_index(
    index_csv: Path,
    out_dir: Path,
    client: TrelloClient,
    overwrite: bool = False
) -> List[Path]:
    """Download all bill PDFs from bills_attachments_index.csv.
    
    Args:
        index_csv: Path to bills_attachments_index.csv
        out_dir: Directory to save PDFs (creates if needed)
        client: Authenticated TrelloClient
        overwrite: If True, re-download existing files
        
    Returns:
        List of successfully downloaded PDF paths
        
    Download filename format:
        <date_for_filename>__<attachment_id>__<safe_filename>.pdf
        
    Date priority for filename:
        1. bill_date (best available from index)
        2. bill_date_action (action timestamp if present)
        3. bill_date_filename (parsed from name or URL)
        4. "UNKNOWN" as fallback
        
    Download strategy:
        1. Try direct attachment_url
        2. If 401/403, retry with Trello API download endpoint
        
    Resilient: Logs failures but continues processing remaining bills.
    """
    index_csv = Path(index_csv)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Downloading bills from index: {index_csv}")
    print(f"Output directory: {out_dir}")
    print(f"{'='*70}\n")
    
    if not index_csv.exists():
        print(f"❌ Index file not found: {index_csv}")
        return []
    
    # Read index
    with open(index_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("⚠️  No bills found in index")
        return []
    
    print(f"Found {len(rows)} bills to download\n")
    
    downloaded: List[Path] = []
    skipped = 0
    failed: List[Tuple[str, str]] = []
    
    for idx, row in enumerate(rows, 1):
        # Determine date for filename with fallback priority
        # 1. bill_date (best available from index)
        # 2. bill_date_action (action timestamp if present)
        # 3. bill_date_filename (parsed from name or URL)
        # 4. "UNKNOWN" as last resort
        date_for_filename = (
            row.get('bill_date') or 
            row.get('bill_date_action') or 
            row.get('bill_date_filename') or 
            'UNKNOWN'
        )
        
        attachment_id = row.get('attachment_id', '')
        attachment_name = row.get('attachment_name', 'unknown.pdf')
        attachment_url = row.get('attachment_url', '')
        source_card_id = row.get('source_card_id', '')
        
        # Build filename
        safe_name = safe_filename(attachment_name)
        if not safe_name.lower().endswith('.pdf'):
            safe_name += '.pdf'
        
        filename = f"{date_for_filename}__{attachment_id}__{safe_name}"
        pdf_path = out_dir / filename
        
        print(f"[{idx}/{len(rows)}] {attachment_name[:50]}...", end=" ")
        
        # Skip if exists and not overwrite
        if pdf_path.exists() and not overwrite:
            print("⏭️  (exists, skipping)")
            skipped += 1
            downloaded.append(pdf_path)
            continue
        
        # Try download
        try:
            # Strategy 1: Direct URL
            try:
                client.download_url(attachment_url, pdf_path)
                print("✓")
                downloaded.append(pdf_path)
                continue
            except TrelloError as e:
                # If auth error, try strategy 2
                if '401' in str(e) or '403' in str(e):
                    print("🔄 (auth failed, retrying with API endpoint)...", end=" ")
                    
                    # Strategy 2: Trello API download endpoint
                    api_url = f"https://api.trello.com/1/cards/{source_card_id}/attachments/{attachment_id}/download/{attachment_name}"
                    
                    # Use client's session with auth params
                    params = {
                        'key': client.api_key,
                        'token': client.token
                    }
                    
                    resp = client.session.get(api_url, params=params, stream=True, timeout=60)
                    resp.raise_for_status()
                    
                    # Save file
                    with open(pdf_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    print("✓")
                    downloaded.append(pdf_path)
                    continue
                else:
                    raise  # Re-raise if not auth error
        
        except Exception as e:
            print(f"❌ {e}")
            failed.append((attachment_name, str(e)))
            continue
    
    # Summary
    print(f"\n{'='*70}")
    print(f"DOWNLOAD SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successfully downloaded: {len(downloaded) - skipped}")
    print(f"⏭️  Skipped (already exist): {skipped}")
    
    if failed:
        print(f"❌ Failed: {len(failed)}")
        print("\nFailed downloads:")
        for name, error in failed[:10]:
            print(f"  - {name}: {error}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    print(f"{'='*70}\n")
    
    return downloaded


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, int]:
    """Extract text from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Tuple of (text, page_count)
        
    Uses pypdf (PdfReader) for text extraction.
    Does NOT perform OCR.
    """
    try:
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())
        
        text = "\n".join(text_parts)
        return text, page_count
    
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")


def write_text_for_pdf(pdf_path: Path, text_dir: Path, text: str) -> Path:
    """Write extracted text to corresponding .txt file.
    
    Args:
        pdf_path: Original PDF path
        text_dir: Directory to save text files
        text: Extracted text content
        
    Returns:
        Path to created text file
        
    Text filename matches PDF filename with .txt extension.
    """
    text_dir = Path(text_dir)
    text_dir.mkdir(parents=True, exist_ok=True)
    
    text_filename = pdf_path.stem + ".txt"
    text_path = text_dir / text_filename
    
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return text_path


def build_bills_text_index(
    pdf_dir: Path,
    text_dir: Path,
    out_csv: Path
) -> None:
    """Build index CSV of extracted bill texts with metadata.
    
    Args:
        pdf_dir: Directory containing downloaded PDFs
        text_dir: Directory to save extracted text files
        out_csv: Output CSV path
        
    CSV columns:
        pdf_file, sha256, file_bytes, page_count, text_chars, likely_scanned, error
        
    likely_scanned is True if text length < 50 chars (indicates OCR needed).
    Resilient: Records errors in error column, continues processing.
    """
    pdf_dir = Path(pdf_dir)
    text_dir = Path(text_dir)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Building bills text index from: {pdf_dir}")
    print(f"Text output: {text_dir}")
    print(f"Index output: {out_csv}")
    print(f"{'='*70}\n")
    
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  No PDF files found")
        return
    
    print(f"Processing {len(pdf_files)} PDF files...\n")
    
    rows = []
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"[{idx}/{len(pdf_files)}] {pdf_path.name[:50]}...", end=" ")
        
        row = {
            'pdf_file': pdf_path.name,
            'sha256': '',
            'file_bytes': 0,
            'page_count': 0,
            'text_chars': 0,
            'likely_scanned': False,
            'error': ''
        }
        
        try:
            # Get file metadata
            row['file_bytes'] = pdf_path.stat().st_size
            row['sha256'] = sha256_file(pdf_path)
            
            # Extract text
            text, page_count = extract_text_from_pdf(pdf_path)
            row['page_count'] = page_count
            row['text_chars'] = len(text)
            
            # Check if likely scanned (minimal text extracted)
            if len(text) < 50:
                row['likely_scanned'] = True
                print("⚠️  (likely scanned, < 50 chars)")
            else:
                print(f"✓ ({page_count} pages, {len(text)} chars)")
            
            # Write text file
            write_text_for_pdf(pdf_path, text_dir, text)
        
        except Exception as e:
            row['error'] = str(e)
            print(f"❌ {e}")
        
        rows.append(row)
    
    # Write CSV
    fieldnames = ['pdf_file', 'sha256', 'file_bytes', 'page_count', 'text_chars', 'likely_scanned', 'error']
    
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Summary
    success_count = sum(1 for r in rows if not r['error'])
    scanned_count = sum(1 for r in rows if r['likely_scanned'])
    error_count = sum(1 for r in rows if r['error'])
    
    print(f"\n{'='*70}")
    print(f"TEXT INDEX SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successfully processed: {success_count}")
    print(f"⚠️  Likely scanned (OCR needed): {scanned_count}")
    print(f"❌ Errors: {error_count}")
    print(f"{'='*70}\n")


def build_bills_line_candidates(
    text_dir: Path,
    out_csv: Path
) -> None:
    """Build index CSV of dollar amounts found in bill texts.
    
    Scans each text file for lines containing dollar amounts.
    Does NOT make assumptions about which amounts are job prices.
    Records all dollar amounts found with their context.
    
    Args:
        text_dir: Directory containing extracted text files
        out_csv: Output CSV path
        
    CSV columns:
        pdf_file, line_no, amount, line_text
        
    Dollar amount regex pattern: r'\\$\\s*\\d{1,3}(?:,\\d{3})*(?:\\.\\d{2})?'
    
    Examples matched:
        $100, $1,234.56, $ 5000, $12,345.00
    """
    text_dir = Path(text_dir)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Building bills line candidates from: {text_dir}")
    print(f"Output: {out_csv}")
    print(f"{'='*70}\n")
    
    text_files = sorted(text_dir.glob("*.txt"))
    
    if not text_files:
        print("⚠️  No text files found")
        return
    
    print(f"Scanning {len(text_files)} text files for dollar amounts...\n")
    
    # Regex for dollar amounts
    # Matches: $100, $1,234.56, $ 5000, $12,345.00
    dollar_pattern = re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?')
    
    rows = []
    
    for idx, text_path in enumerate(text_files, 1):
        print(f"[{idx}/{len(text_files)}] {text_path.name[:50]}...", end=" ")
        
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            matches_in_file = 0
            
            for line_no, line in enumerate(lines, 1):
                # Find all dollar amounts in line
                matches = dollar_pattern.findall(line)
                
                if matches:
                    # Clean and store each match
                    for amount_str in matches:
                        # Clean amount string (remove spaces, keep $)
                        amount_clean = amount_str.replace(' ', '')
                        
                        # Store with context
                        rows.append({
                            'pdf_file': text_path.stem + '.pdf',  # Original PDF name
                            'line_no': line_no,
                            'amount': amount_clean,
                            'line_text': line.strip()
                        })
                        
                        matches_in_file += 1
            
            print(f"✓ ({matches_in_file} amounts found)")
        
        except Exception as e:
            print(f"❌ {e}")
            continue
    
    # Write CSV
    fieldnames = ['pdf_file', 'line_no', 'amount', 'line_text']
    
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Summary
    files_with_amounts = len(set(r['pdf_file'] for r in rows))
    total_amounts = len(rows)
    
    print(f"\n{'='*70}")
    print(f"LINE CANDIDATES SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Files with dollar amounts: {files_with_amounts}/{len(text_files)}")
    print(f"✓ Total dollar amounts found: {total_amounts}")
    
    if total_amounts > 0:
        # Show sample
        print(f"\nSample amounts found:")
        for row in rows[:5]:
            print(f"  {row['amount']} in {row['pdf_file']} (line {row['line_no']})")
            print(f"    Context: {row['line_text'][:60]}...")
    
    print(f"{'='*70}\n")


def main():
    """Run complete bills processing pipeline."""
    import os
    
    print("=" * 70)
    print("MEMPHIS POOL BILLS PROCESSING")
    print("=" * 70)
    print()
    
    # Setup paths
    data_root = Path("data/memphis_pool")
    index_csv = data_root / "indexes" / "bills_attachments_index.csv"
    pdf_dir = data_root / "raw_bills"
    text_dir = data_root / "bills_text"
    indexes_dir = data_root / "indexes"
    
    text_index_csv = indexes_dir / "bills_text_index.csv"
    line_candidates_csv = indexes_dir / "bills_line_candidates.csv"
    
    print(f"Input index: {index_csv}")
    print(f"PDF output: {pdf_dir}")
    print(f"Text output: {text_dir}")
    print(f"Text index: {text_index_csv}")
    print(f"Line candidates: {line_candidates_csv}")
    print("=" * 70)
    print()
    
    # Check prerequisites
    if not index_csv.exists():
        print(f"❌ Index file not found: {index_csv}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_ingest.py")
        return
    
    try:
        # Initialize Trello client
        print("Step 1: Initializing TrelloClient...")
        client = TrelloClient()
        print()
        
        # Download PDFs
        print("Step 2: Downloading bill PDFs...")
        downloaded = download_bills_from_index(index_csv, pdf_dir, client)
        
        if not downloaded:
            print("❌ No PDFs downloaded. Exiting.")
            return
        
        # Extract text and build text index
        print("Step 3: Extracting text from PDFs...")
        build_bills_text_index(pdf_dir, text_dir, text_index_csv)
        
        # Build line candidates
        print("Step 4: Scanning for dollar amounts...")
        build_bills_line_candidates(text_dir, line_candidates_csv)
        
        # Final summary
        print("\n" + "=" * 70)
        print("✅ BILLS PROCESSING COMPLETE")
        print("=" * 70)
        print(f"PDFs: {pdf_dir}")
        print(f"Text files: {text_dir}")
        print(f"Text index: {text_index_csv}")
        print(f"Line candidates: {line_candidates_csv}")
        print("=" * 70)
        print()
        
        # Counts
        pdf_count = len(list(pdf_dir.glob("*.pdf")))
        txt_count = len(list(text_dir.glob("*.txt")))
        
        print(f"📊 Total PDFs: {pdf_count}")
        print(f"📊 Total text files: {txt_count}")
        
        if text_index_csv.exists():
            with open(text_index_csv) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                scanned = sum(1 for r in rows if r['likely_scanned'] == 'True')
                errors = sum(1 for r in rows if r['error'])
                print(f"📊 Likely scanned (need OCR): {scanned}")
                print(f"📊 Processing errors: {errors}")
        
        if line_candidates_csv.exists():
            with open(line_candidates_csv) as f:
                reader = csv.DictReader(f)
                amount_count = len(list(reader))
                print(f"📊 Dollar amounts found: {amount_count}")
        
        print("=" * 70)
        print()
        
    except TrelloError as e:
        print(f"\n❌ Trello error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
