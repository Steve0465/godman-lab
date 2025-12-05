#!/usr/bin/env python3
"""
Intelligent Document Organizer with AI Analysis

Scans documents, uses AI to:
- Classify document type
- Extract key information (due dates, amounts, etc.)
- Identify action items
- Auto-organize into folders
- Flag urgent items
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
from pdf2image import convert_from_path
import pytesseract
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration
POPPLER_PATH = os.getenv("POPPLER_PATH")
TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Document categories
CATEGORIES = {
    'BILLS': 'Bills & Invoices',
    'TAXES': 'Tax Documents',
    'RECEIPTS': 'Receipts',
    'CONTRACTS': 'Contracts & Agreements',
    'INSURANCE': 'Insurance Documents',
    'MEDICAL': 'Medical Records',
    'BANK': 'Bank Statements',
    'LEGAL': 'Legal Documents',
    'PERSONAL': 'Personal Documents',
    'OTHER': 'Uncategorized'
}

# Action priorities
ACTIONS = {
    'URGENT': 'Needs immediate action (due soon)',
    'ACTION': 'Needs action (payment, signature, etc.)',
    'REVIEW': 'Review and file',
    'ARCHIVE': 'Archive only (no action needed)'
}


def ocr_document(pdf_path: Path, max_pages: int = 3) -> str:
    """Extract text from PDF using OCR"""
    print(f"  OCR: {pdf_path.name}...")
    
    try:
        # Convert PDF to images (first few pages)
        images = convert_from_path(
            str(pdf_path),
            first_page=1,
            last_page=max_pages,
            poppler_path=POPPLER_PATH
        )
        
        # OCR each page
        text_parts = []
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image)
            text_parts.append(f"--- Page {i+1} ---\n{page_text}")
        
        full_text = "\n\n".join(text_parts)
        return full_text[:4000]  # Limit to first 4000 chars
        
    except Exception as e:
        print(f"  Error OCR: {e}")
        return ""


def analyze_document_with_ai(text: str, filename: str) -> dict:
    """Use OpenAI to analyze document and extract structured info"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {
            'category': 'OTHER',
            'action': 'REVIEW',
            'summary': 'AI analysis not available',
            'due_date': None,
            'amount': None
        }
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Analyze this document and provide structured information.

Document filename: {filename}
Document text:
{text}

Provide a JSON response with:
{{
  "category": "BILLS|TAXES|RECEIPTS|CONTRACTS|INSURANCE|MEDICAL|BANK|LEGAL|PERSONAL|OTHER",
  "action": "URGENT|ACTION|REVIEW|ARCHIVE",
  "summary": "Brief description of what this document is",
  "due_date": "YYYY-MM-DD if there's a payment/action due date, null otherwise",
  "amount": "Dollar amount if this is a bill/payment (number only)",
  "key_info": "Any important details (account numbers, reference numbers, etc.)",
  "action_required": "Specific action needed, if any"
}}

Guidelines:
- URGENT: Due within 7 days or overdue
- ACTION: Needs payment, signature, or response
- REVIEW: Should be reviewed but no immediate action
- ARCHIVE: Just for records, no action needed
"""
    
    try:
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "You are a document analysis expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content
        
        # Try to extract JSON
        try:
            result = json.loads(result_text)
        except:
            # Try to find JSON in response
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result = json.loads(result_text[start:end+1])
            else:
                raise
        
        return result
        
    except Exception as e:
        print(f"  AI analysis error: {e}")
        return {
            'category': 'OTHER',
            'action': 'REVIEW',
            'summary': f'Error analyzing: {str(e)[:100]}',
            'due_date': None,
            'amount': None
        }


def organize_documents(source_dir: Path, output_dir: Path, dry_run: bool = False):
    """Main function to organize documents"""
    
    print("=" * 70)
    print("INTELLIGENT DOCUMENT ORGANIZER")
    print("=" * 70)
    print()
    
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        return
    
    # Find all PDFs
    pdf_files = list(source_dir.glob("*.pdf")) + list(source_dir.glob("*.PDF"))
    
    if not pdf_files:
        print(f"No PDF files found in {source_dir}")
        return
    
    print(f"Found {len(pdf_files)} documents to analyze\n")
    
    results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}")
        
        # OCR the document
        text = ocr_document(pdf_path)
        
        if not text.strip():
            print("  ⚠ No text extracted, skipping")
            continue
        
        # AI analysis
        print("  AI: Analyzing...")
        analysis = analyze_document_with_ai(text, pdf_path.name)
        
        # Print results
        print(f"  📁 Category: {analysis.get('category', 'OTHER')}")
        print(f"  🎯 Action: {analysis.get('action', 'REVIEW')}")
        print(f"  📝 {analysis.get('summary', 'N/A')}")
        
        if analysis.get('due_date'):
            print(f"  📅 Due: {analysis['due_date']}")
        if analysis.get('amount'):
            print(f"  💰 Amount: ${analysis['amount']}")
        if analysis.get('action_required'):
            print(f"  ✅ Action: {analysis['action_required']}")
        
        # Determine destination folder
        category = analysis.get('category', 'OTHER')
        action = analysis.get('action', 'REVIEW')
        
        dest_folder = output_dir / category
        if action in ['URGENT', 'ACTION']:
            dest_folder = dest_folder / 'NEEDS_ACTION'
        
        # Save result
        results.append({
            'filename': pdf_path.name,
            'category': category,
            'action': action,
            'summary': analysis.get('summary', ''),
            'due_date': analysis.get('due_date'),
            'amount': analysis.get('amount'),
            'key_info': analysis.get('key_info', ''),
            'action_required': analysis.get('action_required', ''),
            'dest_folder': str(dest_folder)
        })
        
        # Move/organize file
        if not dry_run:
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_path = dest_folder / pdf_path.name
            
            # Avoid overwriting
            if dest_path.exists():
                dest_path = dest_folder / f"{pdf_path.stem}_{i}{pdf_path.suffix}"
            
            pdf_path.rename(dest_path)
            print(f"  ✓ Moved to: {dest_folder.name}/")
        else:
            print(f"  [DRY RUN] Would move to: {dest_folder.name}/")
        
        print()
    
    # Save report
    if results:
        df = pd.DataFrame(results)
        output_dir.mkdir(parents=True, exist_ok=True)  # Ensure output dir exists
        report_path = output_dir / 'document_analysis.csv'
        df.to_csv(report_path, index=False)
        print(f"✓ Analysis report saved: {report_path}")
        
        # Summary
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        print(f"\nTotal documents: {len(results)}")
        print(f"\nBy category:")
        print(df['category'].value_counts().to_string())
        
        print(f"\nBy action:")
        print(df['action'].value_counts().to_string())
        
        # Urgent items
        urgent = df[df['action'] == 'URGENT']
        if len(urgent) > 0:
            print(f"\n⚠️  URGENT ITEMS ({len(urgent)}):")
            for _, row in urgent.iterrows():
                print(f"  • {row['filename']}")
                print(f"    {row['summary']}")
                if row['due_date']:
                    print(f"    Due: {row['due_date']}")
                print()
        
        # Action items
        action = df[df['action'] == 'ACTION']
        if len(action) > 0:
            print(f"\n✅ NEEDS ACTION ({len(action)}):")
            for _, row in action.iterrows():
                print(f"  • {row['filename']}: {row['action_required']}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Intelligent Document Organizer')
    parser.add_argument('source', type=Path, help='Source directory with PDFs')
    parser.add_argument('--output', '-o', type=Path, default=Path('organized_documents'),
                       help='Output directory (default: organized_documents)')
    parser.add_argument('--dry-run', action='store_true',
                       help="Don't move files, just analyze")
    
    args = parser.parse_args()
    
    organize_documents(args.source, args.output, args.dry_run)
