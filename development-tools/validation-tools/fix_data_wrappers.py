#!/usr/bin/env python3
"""
Quick fix script for remaining data wrapper deployment blockers
"""

import os
import re

# List of files that need data wrapper fixes based on our validation
files_to_fix = [
    "records_management/views/records_security_audit_views.xml",
    "records_management/views/records_series_views.xml",
    "records_management/views/records_service_type_views.xml",
    "records_management/views/records_storage_department_user_views.xml"
]

def fix_data_wrapper(file_path):
    """Remove <data> wrapper and fix indentation"""
    print(f"🔧 Fixing: {file_path}")

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove <data> wrapper and extra indentation
    # Pattern: remove <data> tags and reduce indentation by 4 spaces
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # Skip <data> and </data> lines
        if '<data>' in line or '</data>' in line:
            continue
        # Remove 4 spaces from the beginning if present (but preserve XML declaration and <odoo>)
        elif line.startswith('    ') and not line.strip().startswith('<?xml') and not line.strip().startswith('<odoo'):
            new_lines.append(line[4:])
        else:
            new_lines.append(line)

    # Join lines and clean up multiple empty lines
    new_content = '\n'.join(new_lines)
    new_content = re.sub(r'\n\n\n+', '\n\n', new_content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ Fixed: {file_path}")
    return True

def main():
    print("🚀 Starting batch fix for data wrapper deployment blockers...\n")

    fixed_count = 0
    for file_path in files_to_fix:
        if fix_data_wrapper(file_path):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count}/{len(files_to_fix)} files")
    print("🎯 All deployment blockers should now be resolved!")

if __name__ == "__main__":
    main()
