#!/usr/bin/env python3
"""
Script to generate missing security access rules for Records Management module.
"""

import csv
import re
from pathlib import Path


def extract_models_from_init():
    """Extract all model names from models/__init__.py"""
    init_file = Path("records_management/models/__init__.py")

    if not init_file.exists():
        print("models/__init__.py not found")
        return []

    models = []
    with open(init_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all from . import statements
    import_pattern = r"from \. import (\w+)"
    matches = re.findall(import_pattern, content)

    for module_name in matches:
        # Read the module file to find model classes
        module_file = Path(f"records_management/models/{module_name}.py")
        if module_file.exists():
            with open(module_file, "r", encoding="utf-8") as f:
                module_content = f.read()

            # Find all class definitions with _name attribute
            class_pattern = r'class (\w+)\([^)]*\):.*?(?=_name = [\'"]([^\'"]+)[\'"])'
            class_matches = re.findall(class_pattern, module_content, re.DOTALL)

            for class_name, model_name in class_matches:
                if model_name:  # Only add if _name is found
                    models.append(model_name)

    return sorted(list(set(models)))


def read_existing_access_rules():
    """Read existing access rules from CSV"""
    csv_file = Path("records_management/security/ir.model.access.csv")

    if not csv_file.exists():
        print("security/ir.model.access.csv not found")
        return set()

    existing_models = set()
    with open(csv_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "model_id:id" in row:
                # Extract model name from model_id:id (format: model_modelname)
                model_ref = row["model_id:id"]
                if model_ref.startswith("model_"):
                    model_name = model_ref[6:]  # Remove 'model_' prefix
                    existing_models.add(model_name)

    return existing_models


def generate_access_rules(missing_models):
    """Generate access rules for missing models"""
    rules = []

    for model_name in missing_models:
        # Generate user access rule
        user_rule = {
            "id": f'access_{model_name.replace(".", "_")}_user',
            "name": f"{model_name}.user",
            "model_id:id": f"model_{model_name}",
            "group_id:id": "records_management.group_records_user",
            "perm_read": "1",
            "perm_write": "1",
            "perm_create": "1",
            "perm_unlink": "0",
        }

        # Generate manager access rule
        manager_rule = {
            "id": f'access_{model_name.replace(".", "_")}_manager',
            "name": f"{model_name}.manager",
            "model_id:id": f"model_{model_name}",
            "group_id:id": "records_management.group_records_manager",
            "perm_read": "1",
            "perm_write": "1",
            "perm_create": "1",
            "perm_unlink": "1",
        }

        rules.extend([user_rule, manager_rule])

    return rules


def append_rules_to_csv(rules):
    """Append new rules to the CSV file"""
    csv_file = Path("records_management/security/ir.model.access.csv")

    # Read existing content
    existing_rows = []
    fieldnames = ["id", "name", "model_id:id", "group_id:id", "perm_read", "perm_write", "perm_create", "perm_unlink"]

    if csv_file.exists():
        with open(csv_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
            if reader.fieldnames:
                fieldnames = reader.fieldnames

    # Add new rules
    existing_rows.extend(rules)

    # Write back to file
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)

    print(f"Added {len(rules)} access rules to {csv_file}")


def main():
    print("Analyzing Records Management module security...")

    # Get all models from __init__.py
    all_models = extract_models_from_init()
    print(f"Found {len(all_models)} models in models/__init__.py")

    # Get existing access rules
    existing_models = read_existing_access_rules()
    print(f"Found {len(existing_models)} models with existing access rules")

    # Find missing models
    missing_models = [model for model in all_models if model not in existing_models]
    print(f"Found {len(missing_models)} models missing access rules:")

    if missing_models:
        for model in missing_models[:10]:  # Show first 10
            print(f"   - {model}")
        if len(missing_models) > 10:
            print(f"   ... and {len(missing_models) - 10} more")

    if not missing_models:
        print("All models have access rules!")
        return

    # Generate and append rules
    print("Generating access rules...")
    rules = generate_access_rules(missing_models)
    append_rules_to_csv(rules)

    print("Security access rules generation complete!")
    print("Summary:")
    print(f"   - Total models: {len(all_models)}")
    print(f"   - Models with rules: {len(existing_models)}")
    print(f"   - Missing rules: {len(missing_models)}")
    print(f"   - Rules added: {len(rules)}")


if __name__ == "__main__":
    main()
