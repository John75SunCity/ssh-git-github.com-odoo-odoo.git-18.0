#!/usr/bin/env python3
"""
Script to restore corrupted XML files from backup
"""

import xml.etree.ElementTree as ET
import os
import glob
import shutil

def restore_corrupted_files():
    views_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views'
    backup_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/backup/views_backup_20250913'

    xml_files = glob.glob(os.path.join(views_dir, '*.xml'))

    invalid_files = []
    restored_files = []

    print("🔍 Checking all XML files for syntax errors...")

    for file_path in xml_files:
        try:
            ET.parse(file_path)
        except ET.ParseError as e:
            filename = os.path.basename(file_path)
            invalid_files.append(filename)
            print(f"❌ {filename}: {e}")

            # Try to find and restore backup
            backup_patterns = [
                f"{filename}.backup_20250913_231913",
                f"{filename}.backup_20250913_231851"
            ]

            for pattern in backup_patterns:
                backup_path = os.path.join(backup_dir, pattern)
                if os.path.exists(backup_path):
                    print(f"  🔄 Restoring from {pattern}")
                    try:
                        shutil.copy2(backup_path, file_path)
                        # Verify the restored file
                        ET.parse(file_path)
                        print(f"  ✅ Successfully restored {filename}")
                        restored_files.append(filename)
                        break
                    except Exception as restore_error:
                        print(f"  ❌ Failed to restore {filename}: {restore_error}")
                        continue
            else:
                print(f"  ⚠️  No backup found for {filename}")

    print(f"\n📊 Summary:")
    print(f"   Total files checked: {len(xml_files)}")
    print(f"   Invalid files found: {len(invalid_files)}")
    print(f"   Files restored: {len(restored_files)}")

    if restored_files:
        print(f"\n✅ Restored files:")
        for filename in restored_files:
            print(f"   - {filename}")

if __name__ == "__main__":
    restore_corrupted_files()
