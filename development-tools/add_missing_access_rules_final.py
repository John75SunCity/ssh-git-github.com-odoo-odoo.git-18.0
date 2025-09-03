#!/usr/bin/env python3
"""
Script to add missing access rules for all models that don't have them.
This script reads the existing ir.model.access.csv file and adds missing rules
for models that exist in the codebase but don't have access rules.
"""

import os
import csv
import re
from pathlib import Path


def get_existing_access_rules(csv_path):
    """Get existing access rules from CSV file"""
    access_rules = set()

    if not csv_path.exists():
        return access_rules

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header

        for row in reader:
            if len(row) >= 3:
                model_ref = row[2].strip()
                if model_ref.startswith("model_"):
                    model_name = model_ref[6:]  # Remove 'model_' prefix
                    access_rules.add(model_name)

    return access_rules


def get_all_models(models_dir):
    """Get all model names from Python files"""
    models = set()

    for py_file in models_dir.glob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all _name attributes
            name_pattern = r'^\s*_name\s*=\s*["\']([^"\']+)["\']'
            matches = re.findall(name_pattern, content, re.MULTILINE)

            for model_name in matches:
                models.add(model_name)

        except Exception as e:
            print(f"Error reading {py_file}: {e}")

    return models


def add_missing_access_rules(csv_path, models_dir):
    """Add missing access rules to CSV file"""
    existing_rules = get_existing_access_rules(csv_path)
    all_models = get_all_models(models_dir)

    missing_models = all_models - existing_rules

    if not missing_models:
        print("✅ No missing access rules found!")
        return

    print(f"📝 Adding access rules for {len(missing_models)} missing models...")

    # Read existing CSV content
    existing_rows = []
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            existing_rows = list(reader)

    # Add missing rules
    new_rows = []
    for model_name in sorted(missing_models):
        # Add user access rule
        user_id = f"access_{model_name.replace('.', '_')}_user"
        user_row = [
            user_id,
            model_name,
            f"model_{model_name}",
            "records_management.group_records_user",
            "1",  # perm_read
            "1",  # perm_write
            "1",  # perm_create
            "0",  # perm_unlink
        ]
        new_rows.append(user_row)

        # Add manager access rule
        manager_id = f"access_{model_name.replace('.', '_')}_manager"
        manager_row = [
            manager_id,
            model_name,
            f"model_{model_name}",
            "records_management.group_records_manager",
            "1",  # perm_read
            "1",  # perm_write
            "1",  # perm_create
            "1",  # perm_unlink
        ]
        new_rows.append(manager_row)

    # Write updated CSV
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(existing_rows)
        writer.writerows(new_rows)

    print(f"✅ Added {len(new_rows)} access rules for {len(missing_models)} models")


def main():
    """Main function"""
    module_path = Path(__file__).parent.parent / "records_management"
    csv_path = module_path / "security" / "ir.model.access.csv"
    models_dir = module_path / "models"

    if not models_dir.exists():
        print(f"❌ Models directory not found: {models_dir}")
        return 1

    add_missing_access_rules(csv_path, models_dir)
    return 0


if __name__ == "__main__":
    exit(main())
