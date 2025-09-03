#!/usr/bin/env python3
"""
Remove duplicate access rules from ir.model.access.csv
"""

import csv
from collections import defaultdict

def remove_duplicates():
    csv_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    # Read the current CSV
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Remove duplicates based on the model_id:id column (index 2)
    seen_models = set()
    unique_rows = []

    for row in rows:
        if row and len(row) >= 3:
            model_id = row[2]
            if model_id not in seen_models:
                seen_models.add(model_id)
                unique_rows.append(row)

    # Write back the unique rows
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(unique_rows)

    print(f"✅ Removed duplicates from {csv_path}")
    print(f"   Original rows: {len(rows)}")
    print(f"   Unique rows: {len(unique_rows)}")
    print(f"   Duplicates removed: {len(rows) - len(unique_rows)}")

if __name__ == "__main__":
    remove_duplicates()
