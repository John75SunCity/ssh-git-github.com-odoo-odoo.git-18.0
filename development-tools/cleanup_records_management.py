#!/usr/bin/env python3
"""
Records Management Module Cleanup Script
Removes unnecessary files and identifies empty files that need attention
"""

import os
import shutil
from pathlib import Path

def remove_cache_files():
    """Remove all Python cache files and directories"""
    print("🧹 Removing Python cache files...")
    
    cache_dirs_removed = 0
    cache_files_removed = 0
    
    # Remove __pycache__ directories
    for pycache_dir in Path("records_management").rglob("__pycache__"):
        if pycache_dir.is_dir():
            shutil.rmtree(pycache_dir)
            cache_dirs_removed += 1
            print(f"   Removed: {pycache_dir}")
    
    # Remove .pyc files
    for pyc_file in Path("records_management").rglob("*.pyc"):
        pyc_file.unlink()
        cache_files_removed += 1
        print(f"   Removed: {pyc_file}")
    
    print(f"   ✅ Removed {cache_dirs_removed} cache directories and {cache_files_removed} .pyc files")

def check_versioned_files():
    """Check for files with version suffixes that might be duplicates"""
    print("\n🔍 Checking for versioned/duplicate files...")
    
    versioned_patterns = ["*2.py", "*_new.py", "*_backup.py", "*_old.py", "*_bak.py"]
    found_files = []
    
    for pattern in versioned_patterns:
        for file_path in Path("records_management").rglob(pattern):
            found_files.append(file_path)
            print(f"   ⚠️  Found: {file_path}")
    
    if found_files:
        print(f"   📋 Found {len(found_files)} potentially duplicate files")
        return found_files
    else:
        print("   ✅ No versioned files found")
        return []

def analyze_empty_files():
    """Analyze empty files and determine if they should be kept or removed"""
    print("\n📄 Analyzing empty files...")
    
    empty_files = []
    
    # Find empty files
    for file_path in Path("records_management").rglob("*"):
        if file_path.is_file() and file_path.stat().st_size == 0:
            # Skip cache files
            if "__pycache__" not in str(file_path) and not str(file_path).endswith('.pyc'):
                empty_files.append(file_path)
    
    if not empty_files:
        print("   ✅ No empty files found")
        return []
    
    print(f"   Found {len(empty_files)} empty files:")
    
    for file_path in empty_files:
        file_ext = file_path.suffix
        file_type = "Unknown"
        action = "Review needed"
        
        if file_ext == ".xml":
            if "report" in str(file_path):
                file_type = "Report template"
                action = "Should be populated or removed"
            else:
                file_type = "XML file"
                action = "Likely should be removed"
        elif file_ext == ".py":
            file_type = "Python module"
            action = "Should have minimal content or be removed"
        elif file_ext == ".csv":
            file_type = "Data file"
            action = "Should be populated or removed"
        elif file_ext == ".js":
            file_type = "JavaScript"
            action = "Should be populated or removed"
        elif file_ext == ".css":
            file_type = "Stylesheet"
            action = "Should be populated or removed"
        
        print(f"   📄 {file_path}")
        print(f"      Type: {file_type}")
        print(f"      Action: {action}")
        print()
    
    return empty_files

def check_report_structure():
    """Check the report directory structure"""
    print("\n📊 Analyzing report structure...")
    
    report_dir = Path("records_management/report")
    reports_dir = Path("records_management/reports")
    
    if report_dir.exists():
        report_files = list(report_dir.glob("*.xml"))
        python_files = list(report_dir.glob("*.py"))
        print(f"   📁 /report directory: {len(report_files)} XML files, {len(python_files)} Python files")
    
    if reports_dir.exists():
        reports_files = list(reports_dir.glob("*.xml"))
        print(f"   📁 /reports directory: {len(reports_files)} XML files")
        if len(reports_files) > 0:
            print("   ⚠️  Having both /report and /reports directories might be confusing")
    
    # Check if there are conflicts or duplicates
    if report_dir.exists() and reports_dir.exists():
        print("   💡 Consider consolidating into single /report directory")

def main():
    """Main cleanup function"""
    print("🎯 Records Management Module Cleanup")
    print("=" * 50)
    
    # Step 1: Remove cache files
    remove_cache_files()
    
    # Step 2: Check versioned files
    versioned_files = check_versioned_files()
    
    # Step 3: Analyze empty files
    empty_files = analyze_empty_files()
    
    # Step 4: Check report structure
    check_report_structure()
    
    # Summary
    print("\n📋 CLEANUP SUMMARY")
    print("=" * 30)
    print("✅ Python cache files removed")
    
    if versioned_files:
        print(f"⚠️  {len(versioned_files)} versioned files found - manual review needed")
        print("   Suggested action: Compare with main versions and remove if duplicate")
    
    if empty_files:
        print(f"📄 {len(empty_files)} empty files found - decisions needed:")
        for f in empty_files:
            print(f"   - {f}")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Review versioned files and remove duplicates")
    print("2. Populate or remove empty report templates")
    print("3. Consider consolidating report directories")
    print("4. Add .gitignore rules for cache files")

if __name__ == "__main__":
    main()
