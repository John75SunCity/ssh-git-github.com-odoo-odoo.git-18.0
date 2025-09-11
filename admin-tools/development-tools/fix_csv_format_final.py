#!/usr/bin/env python3
"""
Fix CSV Format Issues
This script fixes line wrapping and format issues in the security CSV file
"""

import csv
import os

def fix_csv_format():
    """Fix the CSV format by properly handling line breaks"""
    csv_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    # Read the entire file as text to handle line wrapping
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by actual newlines and clean up wrapped lines
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # If line doesn't start with 'access_' and doesn't contain the header, it's a wrapped line
        if not (line.startswith('access_') or line.startswith('id,')):
            # This is a continuation of the previous line
            if fixed_lines:
                fixed_lines[-1] += line
        else:
            fixed_lines.append(line)

    # Now parse the fixed lines as CSV
    fixed_rows = []
    for line in fixed_lines:
        # Split by comma and handle the fields
        parts = line.split(',')
        if parts:  # Valid CSV row should have fields
            fixed_rows.append(parts)

    # Write back the properly formatted CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for row in fixed_rows:
            writer.writerow(row)

    print(f"✅ Fixed CSV format. Processed {len(fixed_rows)} rows.")

def validate_csv():
    """Validate the CSV structure"""
    csv_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    print(f"📊 CSV contains {len(rows)} rows")

    # Check first few rows
    for i, row in enumerate(rows[:5]):
        print(f"Row {i}: {len(row)} fields - {row[0] if row else 'EMPTY'}")

    # Check for any malformed rows
    malformed = []
    for i, row in enumerate(rows):
        if not row or len(row) < 8:
            malformed.append((i, len(row), row[0] if row else 'EMPTY'))

    if malformed:
        print(f"⚠️  Found {len(malformed)} malformed rows:")
        for row_num, field_count, first_field in malformed[:5]:
            print(f"  Row {row_num}: {field_count} fields, starts with: {first_field}")
    else:
        print("✅ All rows appear properly formatted")

def main():
    print("🔧 Fixing CSV format issues...")
    fix_csv_format()

    print("\n🔍 Validating CSV structure...")
    validate_csv()

if __name__ == "__main__":
    main()
