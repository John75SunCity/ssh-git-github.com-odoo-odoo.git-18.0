#!/usr/bin/env python3
"""
Fix model external IDs in ir.model.access.csv

This script corrects the model external IDs from the incorrect format (module.model)
to the correct Odoo format (module.model_modelname).

Example:
- hr.employee -> hr.model_hr_employee
- maintenance.equipment -> maintenance.model_maintenance_equipment
"""

import csv
import re
import sys
from pathlib import Path

def fix_model_external_id(model_id):
    """Convert model ID to correct external ID format"""
    if '.' not in model_id:
        return model_id

    # Split module and model name
    parts = model_id.split('.')
    if not parts or len(parts) != 2:
        return model_id

    module, model_name = parts

    # Convert model name to proper format
    # Replace dots with underscores and add 'model_' prefix
    model_name_formatted = model_name.replace('.', '_')
    corrected_id = f"{module}.model_{model_name_formatted}"

    return corrected_id

def fix_csv_file(csv_path):
    """Fix all model external IDs in the CSV file"""
    print(f"Processing {csv_path}...")

    # Read the CSV file
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("CSV file is empty")
        return

    # Check header
    header = rows[0]
    if not header or len(header) < 3 or header[2] != 'model_id':
        print("Invalid CSV format - expected 'model_id' in column 3")
        return

    # Fix model IDs in data rows
    fixed_count = 0
    for i, row in enumerate(rows[1:], 1):  # Skip header
        if row and len(row) >= 3:
            original_model_id = row[2]
            corrected_model_id = fix_model_external_id(original_model_id)

            if corrected_model_id != original_model_id:
                row[2] = corrected_model_id
                fixed_count += 1
                print(f"Line {i+1}: {original_model_id} -> {corrected_model_id}")

    # Write back the fixed CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Fixed {fixed_count} model external IDs in {csv_path}")

def main():
    """Main function"""
    if not sys.argv or len(sys.argv) != 2:
        print("Usage: python fix_model_ids.py <csv_file>")
        sys.exit(1)

    csv_file = Path(sys.argv[1])
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        sys.exit(1)

    fix_csv_file(csv_file)

if __name__ == '__main__':
    main()
