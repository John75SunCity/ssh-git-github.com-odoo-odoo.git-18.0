#!/usr/bin/env python3
"""
Fix duplicate access rules in ir.model.access.csv
Keep only the first occurrence of each duplicate ID
"""

import csv
import os
from collections import OrderedDict

def fix_duplicate_access_rules():
    """Remove duplicate access rules from ir.model.access.csv"""
    
    access_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"
    
    print("🔍 Analyzing access rules for duplicates...")
    
    # Read the CSV file
    seen_ids = set()
    unique_rows = []
    header = None
    duplicates_removed = 0
    
    with open(access_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Read header
        header = next(reader)
        unique_rows.append(header)
        
        # Process data rows
        for row_num, row in enumerate(reader, start=2):
            if len(row) >= 1:
                access_id = row[0].strip()
                
                if access_id in seen_ids:
                    print(f"⚠️  Removing duplicate: {access_id} (line {row_num})")
                    duplicates_removed += 1
                else:
                    seen_ids.add(access_id)
                    unique_rows.append(row)
            else:
                # Keep empty rows as-is
                unique_rows.append(row)
    
    print(f"📊 Found {duplicates_removed} duplicate access rules")
    
    # Write the cleaned file
    with open(access_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for row in unique_rows:
            writer.writerow(row)
    
    print(f"✅ Fixed access rules file: {access_file}")
    print(f"   - Removed {duplicates_removed} duplicates")
    print(f"   - Kept {len(unique_rows) - 1} unique access rules")

if __name__ == "__main__":
    fix_duplicate_access_rules()
