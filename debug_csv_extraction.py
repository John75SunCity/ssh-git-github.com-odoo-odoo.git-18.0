#!/usr/bin/env python3
"""
Debug CSV extraction to see what model names are being read
"""

import csv
from pathlib import Path

def debug_csv_extraction(csv_path):
    """Debug what model names are extracted from CSV"""
    extracted_models = set()

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header

            count = 0
            for row in reader:
                if row and len(row) >= 3:
                    model_entry = row[2].strip()
                    print(f"Row {count}: '{model_entry}'")

                    if model_entry.startswith('model_records_management_'):
                        model_name = model_entry[26:]  # Remove 'model_records_management_' prefix
                        model_name = model_name.replace('_', '.')
                        extracted_models.add(model_name)
                        print(f"  -> Extracted: '{model_name}'")

                    count += 1
                    if count >= 10:  # Only show first 10
                        break

    except Exception as e:
        print(f"Error reading CSV: {e}")

    print(f"\nTotal extracted models: {len(extracted_models)}")
    print("Sample extracted models:")
    for model in list(extracted_models)[:5]:
        print(f"  - {model}")

if __name__ == "__main__":
    workspace_root = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    csv_path = workspace_root / "records_management" / "security" / "ir.model.access.csv"
    debug_csv_extraction(csv_path)
