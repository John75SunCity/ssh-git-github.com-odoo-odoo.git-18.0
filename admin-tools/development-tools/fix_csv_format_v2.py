#!/usr/bin/env python3
"""
Fix CSV format for newly added security access rules.
The validation script expects model_id:id format like 'model_model_name'
but the newly added rules have incorrect format.
"""

import csv
import os
from pathlib import Path

def fix_csv_format():
    """Fix the CSV format for security access rules"""

    csv_path = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv")

    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return

    # Read all lines
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        print("❌ Empty CSV file")
        return

    header = lines[0].strip()
    data_lines = lines[1:]

    print(f"📊 Processing {len(data_lines)} data lines...")

    fixed_lines = [header]

    for i, line in enumerate(data_lines, 1):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',')
        if not parts or len(parts) < 4:
            print(f"⚠️ Line {i}: Insufficient columns ({len(parts)}), skipping")
            continue

        # Check if this is a newly added rule (incorrect format)
        # Newly added rules have format: id,name,group,perm_read,perm_write,perm_create,perm_unlink
        # Should be: id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink

        if len(parts) == 6 and parts[2].startswith('records_management.group_'):
            # This is a newly added rule with wrong format
            rule_id = parts[0]
            model_name = parts[1]  # e.g., "paper.load.shipment"
            group_id = parts[2]
            perm_read = parts[3]
            perm_write = parts[4]
            perm_create = parts[5]
            perm_unlink = parts[6] if parts and len(parts) > 6 else '0'

            # Convert model name to proper format
            model_id = f"model_{model_name.replace('.', '_')}"

            # Fix the line
            fixed_line = f"{rule_id},{model_name},{model_id},{group_id},{perm_read},{perm_write},{perm_create},{perm_unlink}"
            fixed_lines.append(fixed_line)
            print(f"🔧 Fixed line {i}: {model_name}")

        elif len(parts) == 7 and parts[2].startswith('records_management.group_'):
            # Another variant of newly added rule
            rule_id = parts[0]
            model_name = parts[1]
            group_id = parts[2]
            perm_read = parts[3]
            perm_write = parts[4]
            perm_create = parts[5]
            perm_unlink = parts[6]

            # Convert model name to proper format
            model_id = f"model_{model_name.replace('.', '_')}"

            # Fix the line
            fixed_line = f"{rule_id},{model_name},{model_id},{group_id},{perm_read},{perm_write},{perm_create},{perm_unlink}"
            fixed_lines.append(fixed_line)
            print(f"🔧 Fixed line {i}: {model_name}")

        else:
            # This is an existing rule with correct format or already fixed
            fixed_lines.append(line)

    # Write back the fixed CSV
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines) + '\n')

    print(f"✅ Fixed CSV format. Total lines: {len(fixed_lines)}")

    # Verify the fix by checking a few lines
    print("\n🔍 Verification - First few lines:")
    with open(csv_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 5:
                print(f"Line {i+1}: {line.strip()}")
            elif i >= 625:  # Check the newly added lines
                print(f"Line {i+1}: {line.strip()}")
                if i >= 630:
                    break

if __name__ == "__main__":
    fix_csv_format()
