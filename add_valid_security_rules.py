#!/usr/bin/env python3
"""
Add Valid Security Access Rules

This script adds proper security access rules for all valid models
in the records_management module.
"""

import csv
import os


def get_valid_models():
    """Get list of valid model names from models/__init__.py"""
    init_file = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/__init__.py"

    model_names = []

    with open(init_file, "r") as f:
        content = f.read()

    # Find all import statements
    import_pattern = r"from \. import ([a-zA-Z_][a-zA-Z0-9_]*)"
    import_match = content.find("from . import (")

    if import_match != -1:
        # Extract the import block
        start = import_match + len("from . import (")
        end = content.find(")", start)
        if end != -1:
            imports_block = content[start:end]

            # Split by commas and clean up
            imports = [line.strip().rstrip(",") for line in imports_block.split("\n") if line.strip()]

            for import_line in imports:
                # Remove comments
                if "#" in import_line:
                    import_line = import_line.split("#")[0].strip()

                if import_line and not import_line.startswith("#"):
                    # Convert filename to model name
                    model_name = import_line.replace(".py", "")
                    if model_name:
                        model_names.append(f"records_management.{model_name}")

    return model_names


def create_security_rules():
    """Create security access rules for all valid models"""
    csv_file = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    # Get valid models
    valid_models = get_valid_models()
    print(f"Found {len(valid_models)} valid models to add security rules for")

    # Create security rules
    rules = []
    rules.append(["id", "name", "model_id:id", "group_id:id", "perm_read", "perm_write", "perm_create", "perm_unlink"])

    for model_name in valid_models:
        # User access rule
        user_rule_id = f"access_{model_name.replace('.', '_')}_user"
        rules.append(
            [
                user_rule_id,
                f"{model_name}.user",
                f"model_{model_name.replace('.', '_')}",
                "records_management.group_records_user",
                "1",
                "1",
                "1",
                "0",
            ]
        )

        # Manager access rule
        manager_rule_id = f"access_{model_name.replace('.', '_')}_manager"
        rules.append(
            [
                manager_rule_id,
                f"{model_name}.manager",
                f"model_{model_name.replace('.', '_')}",
                "records_management.group_records_manager",
                "1",
                "1",
                "1",
                "1",
            ]
        )

    # Write to CSV
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rules)

    print(f"Created {len(rules) - 1} security access rules")  # -1 for header
    print(f"Security rules written to: {csv_file}")


if __name__ == "__main__":
    create_security_rules()
