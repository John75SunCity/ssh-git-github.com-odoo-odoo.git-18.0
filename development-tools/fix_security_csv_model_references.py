#!/usr/bin/env python3
"""
Fix Security Access CSV Model References

This script fixes the model references in the security access CSV file
by replacing incorrect model names with the correct technical names
from the actual model definitions.

Usage: python3 fix_security_csv_model_references.py
"""

import os
import re
import csv
from pathlib import Path

def get_actual_model_names(models_dir):
    """Extract actual model technical names from Python files"""
    model_names = {}

    for file_path in Path(models_dir).glob('*.py'):
        if file_path.name == '__init__.py':
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find _name attribute in model classes
            name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            for model_name in name_matches:
                # Convert model name to the incorrect format used in CSV
                # e.g., "display.name" -> "model_display_name"
                csv_model_name = f"model_{model_name.replace('.', '_')}"
                model_names[csv_model_name] = model_name

        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

    return model_names

def fix_security_csv(csv_path, model_mapping):
    """Fix the model references in the security CSV file"""
    fixed_lines = []
    changes_made = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        fixed_lines.append(','.join(header))

        for row in reader:
            if len(row) < 4:  # Skip malformed lines
                fixed_lines.append(','.join(row))
                continue

            original_model_ref = row[2]  # model_id column

            # Check if this model reference needs fixing
            if original_model_ref in model_mapping:
                corrected_model_ref = model_mapping[original_model_ref]
                row[2] = corrected_model_ref
                changes_made += 1
                print(f"Fixed: {original_model_ref} -> {corrected_model_ref}")

            fixed_lines.append(','.join(row))

    return fixed_lines, changes_made

def main():
    # Paths
    workspace_root = Path(__file__).parent.parent
    models_dir = workspace_root / "records_management" / "models"
    csv_path = workspace_root / "records_management" / "security" / "ir.model.access.csv"
    backup_path = csv_path.with_suffix('.csv.backup')

    print("🔍 Analyzing model definitions...")

    # Get actual model names
    model_mapping = get_actual_model_names(models_dir)
    print(f"Found {len(model_mapping)} model mappings")

    if not model_mapping:
        print("❌ No model mappings found. Check models directory.")
        return

    # Show sample mappings
    print("\n📋 Sample model mappings:")
    for incorrect, correct in list(model_mapping.items())[:10]:
        print(f"  {incorrect} -> {correct}")

    # Create backup
    if csv_path.exists():
        print(f"\nCreating backup: {backup_path}")
        csv_path.rename(backup_path)

    # Fix the CSV file
    print("\nFixing security CSV file...")
    fixed_lines, changes_made = fix_security_csv(backup_path, model_mapping)

    # Write the corrected file
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(fixed_lines))

    print("\nSecurity CSV file fixed!")
    print(f"   Changes made: {changes_made}")
    print(f"   Original file backed up to: {backup_path}")

    if changes_made == 0:
        print("Warning: No changes were made. The CSV file might already be correct.")

if __name__ == "__main__":
    main()
