#!/usr/bin/env python3
"""
Comprehensive duplicate field finder for Records Management module
Finds all files with duplicate field definitions that could cause KeyError issues
"""

import os
import re
from pathlib import Path

def find_duplicate_fields_in_file(file_path):
    """Find duplicate field definitions in a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all field definitions with line numbers
        field_pattern = r'(\w+)\s*=\s*fields\.\w+'
        lines = content.split('\n')
        
        field_locations = {}
        duplicates = {}
        
        for line_num, line in enumerate(lines, 1):
            matches = re.findall(field_pattern, line)
            for field_name in matches:
                if field_name in field_locations:
                    # This is a duplicate
                    if field_name not in duplicates:
                        duplicates[field_name] = [field_locations[field_name]]
                    duplicates[field_name].append(line_num)
                else:
                    field_locations[field_name] = line_num
        
        return duplicates
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

def main():
    """Main function to find all duplicate fields"""
    models_dir = Path('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models')
    
    print("🔍 Scanning for duplicate field definitions...")
    print("=" * 60)
    
    files_with_duplicates = []
    total_files_checked = 0
    
    for py_file in models_dir.glob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        total_files_checked += 1
        duplicates = find_duplicate_fields_in_file(py_file)
        
        if duplicates:
            files_with_duplicates.append((py_file.name, duplicates))
            print(f"\n❌ {py_file.name}:")
            for field_name, line_numbers in duplicates.items():
                print(f"   Duplicate field '{field_name}' on lines: {line_numbers}")
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   Files checked: {total_files_checked}")
    print(f"   Files with duplicates: {len(files_with_duplicates)}")
    
    if not files_with_duplicates:
        print("✅ No duplicate fields found in any model files!")
    else:
        print(f"\n🚨 Files requiring duplicate field removal:")
        for filename, duplicates in files_with_duplicates:
            print(f"   - {filename}: {list(duplicates.keys())}")

if __name__ == "__main__":
    main()
