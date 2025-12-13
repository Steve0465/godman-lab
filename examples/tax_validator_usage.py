#!/usr/bin/env python3
"""
Example usage patterns for tax_archive_validator module.

Demonstrates various ways to use the validator in different scenarios.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.tax_archive_validator import (
    scan_archive,
    validate_archive,
    format_validation_summary,
    TaxArchiveStats,
    TaxArchiveValidationResult
)


def example_1_basic_scan():
    """Example 1: Basic filesystem scan without validation."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Filesystem Scan")
    print("=" * 70)
    
    archive_path = Path("~/Desktop/TAX_MASTER_ARCHIVE").expanduser()
    stats = scan_archive(archive_path)
    
    print(f"\n📊 Archive Statistics:")
    print(f"   Location: {stats.root}")
    print(f"   Total files: {stats.total_files}")
    print(f"   Data files (PDFs, CSVs, etc): {stats.data_files}")
    print(f"   Metadata files (MD, TXT, etc): {stats.metadata_files}")
    print(f"   Total size: {stats.total_bytes / (1024*1024):.2f} MB")
    print(f"   Zero-byte files: {len(stats.zero_byte_files)}")
    
    if stats.by_year:
        print(f"\n📅 Files by Year:")
        for year in sorted(stats.by_year.keys()):
            print(f"      {year}: {stats.by_year[year]} files")
    
    print()


def example_2_full_validation():
    """Example 2: Full validation with integrity checks."""
    print("=" * 70)
    print("EXAMPLE 2: Full Validation")
    print("=" * 70)
    
    archive_path = Path("~/Desktop/TAX_MASTER_ARCHIVE").expanduser()
    result = validate_archive(archive_path)
    
    print(f"\n✓ Validation complete!")
    print(f"   Integrity score: {result.integrity_score:.1f}/100")
    print(f"   Manifest OK: {'✓' if result.manifest_ok else '✗'}")
    print(f"   Hash index OK: {'✓' if result.hash_index_ok else '✗'}")
    print(f"   Problems found: {len(result.problems)}")
    
    if result.problems:
        print(f"\n⚠️  Issues detected:")
        for i, problem in enumerate(result.problems[:3], 1):
            print(f"      {i}. {problem}")
        if len(result.problems) > 3:
            print(f"      ... and {len(result.problems) - 3} more")
    
    print()


def example_3_formatted_summary():
    """Example 3: Generate and display formatted summary."""
    print("=" * 70)
    print("EXAMPLE 3: Formatted Summary Report")
    print("=" * 70)
    print()
    
    archive_path = Path("~/Desktop/TAX_MASTER_ARCHIVE").expanduser()
    result = validate_archive(archive_path)
    
    summary = format_validation_summary(result)
    print(summary)
    print()


def example_4_conditional_actions():
    """Example 4: Take action based on integrity score."""
    print("=" * 70)
    print("EXAMPLE 4: Conditional Actions Based on Score")
    print("=" * 70)
    print()
    
    archive_path = Path("~/Desktop/TAX_MASTER_ARCHIVE").expanduser()
    result = validate_archive(archive_path)
    
    score = result.integrity_score
    
    print(f"Current integrity score: {score:.1f}/100")
    print()
    
    if score == 100:
        print("🎉 ACTION: No action needed - archive is perfect!")
    elif score >= 95:
        print("✅ ACTION: Schedule routine maintenance")
    elif score >= 85:
        print("⚠️  ACTION: Review and fix issues within 1 week")
    elif score >= 70:
        print("⚠️  ACTION: Priority fix required within 48 hours")
    else:
        print("🚨 ACTION: URGENT - Fix immediately!")
        print("    Issues requiring attention:")
        for problem in result.problems[:5]:
            print(f"      • {problem}")
    
    print()


def example_5_filter_by_year():
    """Example 5: Analyze specific year's data."""
    print("=" * 70)
    print("EXAMPLE 5: Year-Specific Analysis")
    print("=" * 70)
    print()
    
    archive_path = Path("~/Desktop/TAX_MASTER_ARCHIVE").expanduser()
    stats = scan_archive(archive_path)
    
    print("📅 Documents per tax year:\n")
    
    for year in sorted(stats.by_year.keys(), reverse=True):
        count = stats.by_year[year]
        bar = "█" * (count // 2)  # Simple bar chart
        print(f"   {year}: {count:3d} files {bar}")
    
    # Find the year with most documents
    if stats.by_year:
        max_year = max(stats.by_year.items(), key=lambda x: x[1])
        print(f"\n   Most active year: {max_year[0]} ({max_year[1]} files)")
    
    print()


def example_6_save_to_file():
    """Example 6: Save validation report to file."""
    print("=" * 70)
    print("EXAMPLE 6: Save Report to File")
    print("=" * 70)
    print()
    
    archive_path = Path("~/Desktop/TAX_MASTER_ARCHIVE").expanduser()
    result = validate_archive(archive_path)
    
    # Generate report
    summary = format_validation_summary(result)
    
    # Save to file
    output_path = Path("./tax_validation_report.txt")
    output_path.write_text(summary)
    
    print(f"✓ Report saved to: {output_path.absolute()}")
    print(f"   File size: {output_path.stat().st_size} bytes")
    print()


def example_7_check_zero_bytes():
    """Example 7: Specifically check for zero-byte files."""
    print("=" * 70)
    print("EXAMPLE 7: Zero-Byte File Detection")
    print("=" * 70)
    print()
    
    archive_path = Path("~/Desktop/TAX_MASTER_ARCHIVE").expanduser()
    stats = scan_archive(archive_path)
    
    if stats.zero_byte_files:
        print(f"⚠️  Found {len(stats.zero_byte_files)} zero-byte files:")
        for zbf in stats.zero_byte_files:
            rel_path = zbf.relative_to(stats.root)
            print(f"      • {rel_path}")
    else:
        print("✅ No zero-byte files detected!")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" TAX ARCHIVE VALIDATOR - USAGE EXAMPLES")
    print("=" * 70)
    print()
    
    try:
        example_1_basic_scan()
        input("Press Enter to continue to Example 2...")
        
        example_2_full_validation()
        input("Press Enter to continue to Example 3...")
        
        example_3_formatted_summary()
        input("Press Enter to continue to Example 4...")
        
        example_4_conditional_actions()
        input("Press Enter to continue to Example 5...")
        
        example_5_filter_by_year()
        input("Press Enter to continue to Example 6...")
        
        example_6_save_to_file()
        input("Press Enter to continue to Example 7...")
        
        example_7_check_zero_bytes()
        
        print("=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
