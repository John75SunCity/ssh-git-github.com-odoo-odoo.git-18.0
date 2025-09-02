#!/usr/bin/env python3
"""
Comprehensive script to add missing security access rules to ir.model.access.csv
"""

import os
import re
from pathlib import Path


def get_existing_access_rules():
    """Get all existing model access rules from ir.model.access.csv"""
    access_file = Path("records_management/security/ir.model.access.csv")
    existing_models = set()

    if access_file.exists():
        with open(access_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Skip header
        for line in lines[1:]:
            if line.strip():
                parts = line.split(",")
                if parts:  # Check if parts list is not empty
                    model_name = parts[2].strip()
                    if model_name.startswith("model_"):
                        model_name = model_name[6:]  # Remove 'model_' prefix
                    existing_models.add(model_name)

    return existing_models


def find_all_models():
    """Find all models defined in the codebase"""
    models_dir = Path("records_management/models")
    all_models = set()

    if models_dir.exists():
        for py_file in models_dir.glob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find _name patterns
                name_matches = re.findall(r'_name\s*=\s*["\']([^"\']+)["\']', content)
                for model_name in name_matches:
                    all_models.add(model_name)

            except Exception as e:
                print(f"Error reading {py_file}: {e}")

    return all_models


def generate_missing_access_rules():
    """Generate access rules for missing models"""
    existing_models = get_existing_access_rules()
    all_models = find_all_models()

    missing_models = all_models - existing_models

    print(f"Found {len(existing_models)} existing access rules")
    print(f"Found {len(all_models)} total models")
    print(f"Found {len(missing_models)} missing access rules")

    if missing_models:
        print("\nMissing models:")
        for model in sorted(missing_models):
            print(f"  - {model}")

        # Generate access rules
        access_rules = []
        for model in sorted(missing_models):
            # User access rule
            user_rule = f"access_{model.replace('.', '_')}_user,{model.replace('.', '_')} user,model_{model},records_management.group_records_user,1,1,0,0"
            access_rules.append(user_rule)

            # Manager access rule
            manager_rule = f"access_{model.replace('.', '_')}_manager,{model.replace('.', '_')} manager,model_{model},records_management.group_records_manager,1,1,1,0"
            access_rules.append(manager_rule)

        # Write to file
        access_file = Path("records_management/security/ir.model.access.csv")
        with open(access_file, "a", encoding="utf-8") as f:
            f.write("\n")
            for rule in access_rules:
                f.write(rule + "\n")

        print(f"\nAdded {len(access_rules)} access rules to ir.model.access.csv")
        return True
    else:
        print("No missing access rules found!")
        return False


if __name__ == "__main__":
    generate_missing_access_rules()
