#!/usr/bin/env python3
"""
Fix the model_id:id references in ir.model.access.csv
Replace 'records_management.model_<model>' with just '<model>'
"""

import csv
import os

def fix_model_references():
    csv_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    # Read the current CSV
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Fix the model_id:id column (index 2)
    fixed_rows = []
    for row in rows:
        if row and len(row) >= 3 and row[2].startswith('records_management.model_'):
            # Replace 'records_management.model_<model>' with just '<model>'
            row[2] = row[2].replace('records_management.model_', '')
        fixed_rows.append(row)

    # Write back the fixed CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(fixed_rows)

    print(f"✅ Fixed model references in {csv_path}")
    print(f"   Processed {len(fixed_rows)} rows")

if __name__ == "__main__":
    fix_model_references()
