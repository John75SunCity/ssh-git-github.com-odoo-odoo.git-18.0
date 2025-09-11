#!/usr/bin/env python3
"""
Script to add missing access rules for all models in Records Management module.
This script will:
1. Extract all model files from models/__init__.py
2. Read the actual _name attribute from each model file
3. Check existing access rules in ir.model.access.csv
4. Add missing user and manager access rules for all models
"""

import csv
import re
from pathlib import Path


def extract_models_from_init(init_file_path):
    """Extract all model import names from models/__init__.py"""
    models = []

    with open(init_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the multi-line import block
    import_pattern = r"from \. import \(\s*([^)]+)\s*\)"
    match = re.search(import_pattern, content, re.DOTALL)

    if match:
        imports_block = match.group(1)
        # Split by comma and clean up
        import_lines = imports_block.split(",")
        for line in import_lines:
            # Remove comments and whitespace
            line = line.split("#")[0].strip()
            if line and not line.startswith("#"):
                models.append(line)

    return sorted(list(set(models)))


def get_model_name_from_file(model_file_path):
    """Extract the _name attribute from a model file"""
    try:
        with open(model_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for _name = 'model.name' pattern
        name_pattern = r"_name\s*=\s*['\"]([^'\"]+)['\"]"
        match = re.search(name_pattern, content)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error reading {model_file_path}: {e}")

    return None


def get_actual_model_names(models_dir, import_names):
    """Get actual model names from _name attributes in model files"""
    actual_names = {}

    for import_name in import_names:
        model_file = models_dir / f"{import_name}.py"
        actual_name = get_model_name_from_file(model_file)
        if actual_name:
            actual_names[import_name] = actual_name
        else:
            print(f"Warning: Could not find _name in {model_file}")

    return actual_names


def read_existing_access_rules(csv_path):
    """Read existing access rules from CSV"""
    existing_rules = set()

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("id"):
                    existing_rules.add(row["id"])
    except FileNotFoundError:
        pass

    return existing_rules


def generate_access_rules(model_mapping, existing_rules):
    """Generate missing access rules for all models using actual _name values"""
    new_rules = []

    for import_name, actual_name in model_mapping.items():
        # Generate user access rule
        user_rule_id = f"access_{actual_name.replace('.', '_')}_user"
        if user_rule_id not in existing_rules:
            new_rules.append(
                {
                    "id": user_rule_id,
                    "name": f"{actual_name}.user",
                    "model_id:id": f"model_{actual_name.replace('.', '_')}",
                    "group_id:id": "records_management.group_records_user",
                    "perm_read": "1",
                    "perm_write": "1",
                    "perm_create": "1",
                    "perm_unlink": "0",
                }
            )

        # Generate manager access rule
        manager_rule_id = f"access_{actual_name.replace('.', '_')}_manager"
        if manager_rule_id not in existing_rules:
            new_rules.append(
                {
                    "id": manager_rule_id,
                    "name": f"{actual_name}.manager",
                    "model_id:id": f"model_{actual_name.replace('.', '_')}",
                    "group_id:id": "records_management.group_records_manager",
                    "perm_read": "1",
                    "perm_write": "1",
                    "perm_create": "1",
                    "perm_unlink": "1",
                }
            )

    return new_rules


def main():
    # File paths
    models_dir = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    init_file = models_dir / "__init__.py"
    csv_file = Path(
        "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"
    )

    # Extract import names
    print("Extracting model imports from __init__.py...")
    import_names = extract_models_from_init(init_file)
    print(f"Found {len(import_names)} model imports")

    # Get actual model names from _name attributes
    print("Reading actual model names from files...")
    model_mapping = get_actual_model_names(models_dir, import_names)
    print(f"Successfully mapped {len(model_mapping)} models")

    # Read existing rules
    print("Reading existing access rules...")
    existing_rules = read_existing_access_rules(csv_file)
    print(f"Found {len(existing_rules)} existing access rules")

    # Generate new rules
    print("Generating missing access rules...")
    new_rules = generate_access_rules(model_mapping, existing_rules)
    print(f"Generated {len(new_rules)} new access rules")

    # Read existing CSV content
    existing_content = []
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_content = list(reader)
    except FileNotFoundError:
        existing_content = []

    # Add new rules
    existing_content.extend(new_rules)

    # Write updated CSV
    print("Writing updated CSV file...")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        if existing_content:
            fieldnames = existing_content[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_content)

    print(f"✅ Successfully added {len(new_rules)} access rules")
    print(f"Total access rules: {len(existing_content)}")


if __name__ == "__main__":
    main()
