#!/usr/bin/env python3
"""
Smart File Organizer - Scan and organize all files on your Mac

Automatically groups files by type, cleans up duplicates, and organizes your computer.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
from collections import defaultdict

# Organization rules
ORGANIZATION_MAP = {
    # Documents
    'Documents': {
        'extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
        'subfolders': {
            'Invoices': ['invoice', 'bill', 'receipt'],
            'Contracts': ['contract', 'agreement', 'lease'],
            'Tax': ['tax', '1099', 'w2', 'w-2'],
            'Personal': []  # catch-all
        }
    },
    
    # Images
    'Images': {
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.heic', '.webp'],
        'subfolders': {
            'Screenshots': ['screen shot', 'screenshot'],
            'Photos': ['img_', 'dsc_', 'photo'],
            'Downloads': []
        }
    },
    
    # Scanned Documents (for your printer)
    'Scanned': {
        'extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
        'subfolders': {
            'Receipts': ['receipt'],
            'Bills': ['bill', 'utility', 'statement'],
            'Other': []
        }
    },
    
    # Spreadsheets
    'Spreadsheets': {
        'extensions': ['.xls', '.xlsx', '.csv', '.numbers'],
        'subfolders': {}
    },
    
    # Archives
    'Archives': {
        'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'subfolders': {}
    },
    
    # Videos
    'Videos': {
        'extensions': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'],
        'subfolders': {}
    },
    
    # Audio
    'Audio': {
        'extensions': ['.mp3', '.wav', '.aac', '.flac', '.m4a'],
        'subfolders': {}
    },
    
    # Applications (don't move)
    'Applications': {
        'extensions': ['.app', '.dmg', '.pkg'],
        'subfolders': {}
    }
}


def get_file_hash(file_path):
    """Get MD5 hash of file for duplicate detection"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None


def scan_directory(directory):
    """Scan directory and categorize files"""
    files_by_category = defaultdict(list)
    duplicates = {}
    file_hashes = {}
    
    print(f"Scanning: {directory}")
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden folders and system folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
        
        for file in files:
            if file.startswith('.'):
                continue
            
            file_path = Path(root) / file
            
            # Skip very large files (>500MB)
            try:
                if file_path.stat().st_size > 500 * 1024 * 1024:
                    continue
            except:
                continue
            
            ext = file_path.suffix.lower()
            
            # Categorize
            category = 'Other'
            for cat, rules in ORGANIZATION_MAP.items():
                if ext in rules['extensions']:
                    category = cat
                    break
            
            files_by_category[category].append(file_path)
            
            # Check for duplicates
            if category not in ['Applications']:
                file_hash = get_file_hash(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        if file_hash not in duplicates:
                            duplicates[file_hash] = [file_hashes[file_hash]]
                        duplicates[file_hash].append(file_path)
                    else:
                        file_hashes[file_hash] = file_path
    
    return files_by_category, duplicates


def create_organization_plan(files_by_category, base_output_dir):
    """Create a plan for organizing files"""
    plan = []
    
    for category, files in files_by_category.items():
        if category == 'Applications':
            continue  # Don't move applications
        
        for file_path in files:
            # Determine subfolder
            subfolder = None
            filename_lower = file_path.name.lower()
            
            if category in ORGANIZATION_MAP and 'subfolders' in ORGANIZATION_MAP[category]:
                for sub, keywords in ORGANIZATION_MAP[category]['subfolders'].items():
                    if keywords:
                        if any(kw in filename_lower for kw in keywords):
                            subfolder = sub
                            break
                
                # Default subfolder if none matched
                if not subfolder and ORGANIZATION_MAP[category]['subfolders']:
                    subfolder = list(ORGANIZATION_MAP[category]['subfolders'].keys())[-1]
            
            # Build destination path
            if subfolder:
                dest_dir = base_output_dir / category / subfolder
            else:
                dest_dir = base_output_dir / category
            
            dest_path = dest_dir / file_path.name
            
            # Handle duplicates
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1
            
            plan.append({
                'source': file_path,
                'destination': dest_path,
                'category': category,
                'subfolder': subfolder
            })
    
    return plan


def execute_organization(plan, dry_run=True):
    """Execute the organization plan"""
    print("\n" + "=" * 70)
    if dry_run:
        print("DRY RUN - No files will be moved")
    else:
        print("ORGANIZING FILES")
    print("=" * 70 + "\n")
    
    stats = defaultdict(int)
    
    for item in plan:
        source = item['source']
        dest = item['destination']
        category = item['category']
        
        stats[category] += 1
        
        if dry_run:
            print(f"Would move: {source.name}")
            print(f"  → {dest.relative_to(dest.parents[2])}")
        else:
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                print(f"✓ Moved: {source.name} → {category}")
            except Exception as e:
                print(f"✗ Error moving {source.name}: {e}")
        
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for category, count in sorted(stats.items()):
        print(f"{category}: {count} files")
    print(f"\nTotal: {sum(stats.values())} files")


def organize_computer(scan_dirs, output_dir, dry_run=True):
    """Main organization function"""
    print("=" * 70)
    print("SMART FILE ORGANIZER")
    print("=" * 70)
    print()
    
    all_files = defaultdict(list)
    all_duplicates = {}
    
    # Scan all directories
    for directory in scan_dirs:
        if Path(directory).exists():
            files, dupes = scan_directory(directory)
            for cat, file_list in files.items():
                all_files[cat].extend(file_list)
            all_duplicates.update(dupes)
    
    print(f"\nFound {sum(len(f) for f in all_files.values())} files")
    print(f"Found {len(all_duplicates)} sets of duplicates\n")
    
    # Show duplicates
    if all_duplicates:
        print("\n" + "=" * 70)
        print("DUPLICATE FILES (keeping newest, can delete others)")
        print("=" * 70)
        for hash_val, file_list in list(all_duplicates.items())[:10]:  # Show first 10
            print(f"\nDuplicate set ({len(file_list)} copies):")
            for f in file_list:
                print(f"  - {f}")
        print()
    
    # Create organization plan
    plan = create_organization_plan(all_files, Path(output_dir))
    
    # Execute
    execute_organization(plan, dry_run)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart File Organizer')
    parser.add_argument(
        '--scan',
        nargs='+',
        default=[
            str(Path.home() / 'Downloads'),
            str(Path.home() / 'Desktop'),
            str(Path.home() / 'Documents')
        ],
        help='Directories to scan'
    )
    parser.add_argument(
        '--output',
        default=str(Path.home() / 'Organized'),
        help='Output directory'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually move files (default is dry-run)'
    )
    
    args = parser.parse_args()
    
    organize_computer(
        args.scan,
        args.output,
        dry_run=not args.execute
    )
