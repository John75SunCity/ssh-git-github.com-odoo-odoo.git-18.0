#!/usr/bin/env python3
"""
Script to fix PostgreSQL constraint violations by removing duplicate access rules
"""

import csv
from collections import defaultdict
import os
import shutil
from datetime import datetime

def fix_duplicate_access_rules():
    file_path = "records_management/security/ir.model.access.csv"
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("🔧 Fixing PostgreSQL constraint violations in ir.model.access.csv...")
    
    # Create backup
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    # Read all rows
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    print(f"📊 Original file: {len(rows)} access rules")
    
    # Remove duplicates by ID (keep first occurrence)
    seen_ids = set()
    unique_rows = []
    duplicates_removed = []
    
    for row in rows:
        rule_id = row['id']
        if rule_id not in seen_ids:
            seen_ids.add(rule_id)
            unique_rows.append(row)
        else:
            duplicates_removed.append(rule_id)
    
    print(f"🗑️  Removed {len(duplicates_removed)} duplicate entries:")
    for dup_id in sorted(set(duplicates_removed)):
        print(f"   - {dup_id}")
    
    print(f"✅ Cleaned file: {len(unique_rows)} access rules")
    
    # Write cleaned file
    with open(file_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_rows)
    
    print(f"💾 File saved: {file_path}")
    
    # Verify the fix
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        verification_rows = list(reader)
    
    ids_after = [row['id'] for row in verification_rows]
    duplicate_check = len(ids_after) - len(set(ids_after))
    
    if duplicate_check == 0:
        print("✅ VERIFICATION PASSED: No duplicates remain")
        print(f"🎯 PostgreSQL constraint violation should be resolved")
        return True
    else:
        print(f"❌ VERIFICATION FAILED: {duplicate_check} duplicates still exist")
        return False

if __name__ == "__main__":
    success = fix_duplicate_access_rules()
    if success:
        print("\n🚀 Ready for deployment!")
        print("   The PostgreSQL 'ON CONFLICT DO UPDATE cannot affect row a second time' error should be resolved.")
    else:
        print("\n⚠️  Manual review required - some duplicates may remain")
