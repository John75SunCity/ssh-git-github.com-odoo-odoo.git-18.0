#!/usr/bin/env python3
"""
Fix ir.model.access.csv file by:
1. Only including models that actually exist in models/__init__.py
2. Using correct external ID format (model_{model_name} not model_records_management_{model_name})
3. Using correct group external IDs
"""

import csv
import re
from pathlib import Path

def extract_models_from_init(init_file_path):
    """Extract model names from models/__init__.py"""
    models = set()

    with open(init_file_path, 'r') as f:
        content = f.read()

    # Find all import statements in parentheses
    import_match = re.search(r'from \. import \((.*?)\)', content, re.DOTALL)
    if import_match:
        imports_block = import_match.group(1)
        # Split by commas and clean up
        for line in imports_block.split(','):
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove comments and clean
                line = line.split('#')[0].strip()
                if line:
                    models.add(line)

    return models

def fix_csv_file(csv_path, models_set):
    """Fix the CSV file with correct external IDs"""
    fixed_rows = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_id = row['model_id:id']

            # Skip if model_id is empty or DEFAULT
            if not model_id or model_id == 'DEFAULT':
                continue

            # Extract model name from external ID
            # Format: model_records_management_{model_name} -> {model_name}
            if model_id.startswith('model_records_management_'):
                model_name = model_id[len('model_records_management_'):]
            elif model_id.startswith('model_'):
                model_name = model_id[len('model_'):]
            else:
                # Skip invalid format
                continue

            # Check if model exists
            if model_name not in models_set:
                continue

            # Fix model external ID
            row['model_id:id'] = f'model_{model_name}'

            # Fix group external IDs if needed
            group_id = row['group_id:id']
            if group_id == 'records_management.group_records_user':
                row['group_id:id'] = 'records_management.group_records_user'
            elif group_id == 'records_management.group_records_manager':
                row['group_id:id'] = 'records_management.group_records_manager'

            fixed_rows.append(row)

    return fixed_rows

def main():
    base_path = Path('/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management')
    csv_path = base_path / 'security' / 'ir.model.access.csv'
    init_path = base_path / 'models' / '__init__.py'

    # Extract existing models
    models_set = extract_models_from_init(init_path)
    print(f"Found {len(models_set)} models in __init__.py")

    # Fix CSV
    fixed_rows = fix_csv_file(csv_path, models_set)
    print(f"Fixed CSV has {len(fixed_rows)} valid access rules")

    # Write back to CSV
    with open(csv_path, 'w', newline='') as f:
        if fixed_rows:
            writer = csv.DictWriter(f, fieldnames=fixed_rows[0].keys())
            writer.writeheader()
            writer.writerows(fixed_rows)

    print(f"Successfully fixed {csv_path}")

if __name__ == '__main__':
    main()
