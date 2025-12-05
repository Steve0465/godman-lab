"""
AI-powered file organizer using OpenAI to intelligently categorize files.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import json
import mimetypes


def get_file_info(file_path: Path) -> Dict:
    """Extract metadata from a file."""
    stat = file_path.stat()
    mime_type, _ = mimetypes.guess_type(str(file_path))
    
    return {
        "name": file_path.name,
        "extension": file_path.suffix,
        "size": stat.st_size,
        "mime_type": mime_type,
        "path": str(file_path)
    }


def analyze_file_with_ai(file_info: Dict, openai_api_key: str) -> Dict:
    """Use OpenAI to categorize a file based on its metadata."""
    try:
        import openai
        openai.api_key = openai_api_key
        
        prompt = f"""Analyze this file and suggest the best category and subcategory for organization:

File name: {file_info['name']}
Extension: {file_info['extension']}
MIME type: {file_info['mime_type']}
Size: {file_info['size']} bytes

Categories to choose from:
- Documents (Receipts, Invoices, Contracts, Letters, Reports, Manuals)
- Media (Photos, Videos, Music, Screenshots)
- Work (Projects, Presentations, Spreadsheets, Code)
- Personal (Health, Finance, Legal, Taxes)
- Archive (Old, Backup, Temp)
- Other

Return ONLY a JSON object with this structure:
{{"category": "category_name", "subcategory": "subcategory_name", "confidence": 0.0-1.0, "reason": "brief explanation"}}
"""
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a file organization expert. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        # Fallback to rule-based categorization
        return fallback_categorization(file_info)


def fallback_categorization(file_info: Dict) -> Dict:
    """Simple rule-based categorization fallback."""
    ext = file_info['extension'].lower()
    name = file_info['name'].lower()
    
    # Document types
    if ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
        if any(word in name for word in ['receipt', 'invoice', 'bill']):
            return {"category": "Documents", "subcategory": "Receipts", "confidence": 0.8, "reason": "Filename suggests receipt"}
        if any(word in name for word in ['contract', 'agreement']):
            return {"category": "Documents", "subcategory": "Contracts", "confidence": 0.8, "reason": "Filename suggests contract"}
        return {"category": "Documents", "subcategory": "General", "confidence": 0.6, "reason": "Document file type"}
    
    # Media types
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic']:
        if 'screenshot' in name or 'screen shot' in name:
            return {"category": "Media", "subcategory": "Screenshots", "confidence": 0.9, "reason": "Screenshot detected"}
        return {"category": "Media", "subcategory": "Photos", "confidence": 0.8, "reason": "Image file"}
    
    if ext in ['.mp4', '.mov', '.avi', '.mkv']:
        return {"category": "Media", "subcategory": "Videos", "confidence": 0.9, "reason": "Video file"}
    
    if ext in ['.mp3', '.wav', '.m4a', '.flac']:
        return {"category": "Media", "subcategory": "Music", "confidence": 0.9, "reason": "Audio file"}
    
    # Work types
    if ext in ['.xls', '.xlsx', '.csv']:
        return {"category": "Work", "subcategory": "Spreadsheets", "confidence": 0.8, "reason": "Spreadsheet file"}
    
    if ext in ['.ppt', '.pptx']:
        return {"category": "Work", "subcategory": "Presentations", "confidence": 0.9, "reason": "Presentation file"}
    
    if ext in ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.json']:
        return {"category": "Work", "subcategory": "Code", "confidence": 0.9, "reason": "Code file"}
    
    # Archive
    if ext in ['.zip', '.tar', '.gz', '.rar', '.7z']:
        return {"category": "Archive", "subcategory": "Compressed", "confidence": 0.9, "reason": "Archive file"}
    
    return {"category": "Other", "subcategory": "Uncategorized", "confidence": 0.3, "reason": "Unknown type"}


def organize_files(
    source_dir: str,
    dest_dir: str,
    use_ai: bool = True,
    openai_api_key: Optional[str] = None,
    dry_run: bool = False,
    min_confidence: float = 0.5
) -> Dict:
    """
    Scan and organize files using AI categorization.
    
    Args:
        source_dir: Directory to scan
        dest_dir: Base directory for organized files
        use_ai: Whether to use AI (requires API key)
        openai_api_key: OpenAI API key
        dry_run: If True, only preview without moving files
        min_confidence: Minimum confidence to auto-organize (0.0-1.0)
    
    Returns:
        Dict with statistics and results
    """
    source_path = Path(source_dir).expanduser()
    dest_path = Path(dest_dir).expanduser()
    
    if not source_path.exists():
        raise ValueError(f"Source directory does not exist: {source_dir}")
    
    if not dry_run:
        dest_path.mkdir(parents=True, exist_ok=True)
    
    results = {
        "total_files": 0,
        "organized": 0,
        "skipped": 0,
        "errors": 0,
        "categories": {},
        "files": []
    }
    
    # Scan all files
    for root, dirs, files in os.walk(source_path):
        # Skip hidden directories and the destination directory
        dirs[:] = [d for d in dirs if not d.startswith('.') and Path(root, d) != dest_path]
        
        for filename in files:
            if filename.startswith('.'):
                continue
            
            file_path = Path(root, filename)
            results["total_files"] += 1
            
            try:
                # Get file info
                file_info = get_file_info(file_path)
                
                # Categorize
                if use_ai and openai_api_key:
                    categorization = analyze_file_with_ai(file_info, openai_api_key)
                else:
                    categorization = fallback_categorization(file_info)
                
                category = categorization["category"]
                subcategory = categorization["subcategory"]
                confidence = categorization["confidence"]
                
                # Track categories
                cat_key = f"{category}/{subcategory}"
                results["categories"][cat_key] = results["categories"].get(cat_key, 0) + 1
                
                file_result = {
                    "original_path": str(file_path),
                    "category": category,
                    "subcategory": subcategory,
                    "confidence": confidence,
                    "reason": categorization["reason"],
                    "moved": False
                }
                
                # Move file if confidence is high enough
                if confidence >= min_confidence:
                    target_dir = dest_path / category / subcategory
                    target_path = target_dir / filename
                    
                    # Handle duplicates
                    counter = 1
                    while target_path.exists():
                        stem = file_path.stem
                        suffix = file_path.suffix
                        target_path = target_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    file_result["target_path"] = str(target_path)
                    
                    if not dry_run:
                        target_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(target_path))
                        file_result["moved"] = True
                        results["organized"] += 1
                    else:
                        results["organized"] += 1
                else:
                    results["skipped"] += 1
                
                results["files"].append(file_result)
                
            except Exception as e:
                results["errors"] += 1
                results["files"].append({
                    "original_path": str(file_path),
                    "error": str(e)
                })
    
    return results


def print_organization_report(results: Dict, dry_run: bool = False):
    """Print a formatted report of the organization results."""
    mode = "DRY RUN" if dry_run else "EXECUTION"
    print(f"\n{'='*60}")
    print(f"FILE ORGANIZATION REPORT ({mode})")
    print(f"{'='*60}\n")
    
    print(f"Total files scanned: {results['total_files']}")
    print(f"Files organized: {results['organized']}")
    print(f"Files skipped (low confidence): {results['skipped']}")
    print(f"Errors: {results['errors']}")
    
    print(f"\n{'='*60}")
    print("CATEGORIES:")
    print(f"{'='*60}\n")
    
    for category, count in sorted(results['categories'].items()):
        print(f"  {category}: {count} files")
    
    if results['files']:
        print(f"\n{'='*60}")
        print("SAMPLE FILES:")
        print(f"{'='*60}\n")
        
        for file_info in results['files'][:10]:  # Show first 10
            if 'error' not in file_info:
                print(f"📄 {Path(file_info['original_path']).name}")
                print(f"   → {file_info['category']}/{file_info['subcategory']}")
                print(f"   Confidence: {file_info['confidence']:.1%} | {file_info['reason']}")
                if 'target_path' in file_info:
                    print(f"   Target: {file_info['target_path']}")
                print()
        
        if len(results['files']) > 10:
            print(f"... and {len(results['files']) - 10} more files\n")
