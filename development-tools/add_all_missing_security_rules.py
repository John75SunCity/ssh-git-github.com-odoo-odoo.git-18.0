#!/usr/bin/env python3
"""
Add All Missing Security Rules for Records Management Module
This script adds security access rules for all 256 missing models
"""

import os
import re
import csv

def extract_models_from_python():
    """Extract all model names from Python files"""
    models = set()
    records_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    # Walk through all Python files
    for root, dirs, files in os.walk(records_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Find all _name = 'model.name' patterns
                    name_patterns = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                    for model_name in name_patterns:
                        models.add(model_name)

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return sorted(list(models))

def get_existing_models_from_csv():
    """Get existing model names from CSV (clean extraction)"""
    existing_models = set()
    csv_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if row:
                    # Extract model name from format: access_model_name_user,model.name.user,model_model_name,...
                    model_part = row[2]  # Third column contains model_model_name
                    if model_part.startswith('model_') and len(model_part) > 6:
                        model_name = model_part[6:]  # Remove 'model_' prefix
                        existing_models.add(model_name)
    except Exception as e:
        print(f"Error reading CSV: {e}")

    return existing_models

def add_security_rules(missing_models):
    """Add security rules for missing models"""
    csv_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    # Read existing content
    existing_lines = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            existing_lines = f.readlines()
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Remove empty lines and prepare for appending
    existing_lines = [line.strip() for line in existing_lines if line.strip()]

    # Add new security rules
    new_rules = []
    for model_name in missing_models:
        # Create user access rule
        user_rule = f"access_{model_name.replace('.', '_')}_user,{model_name}.user,model_{model_name},records_management.group_records_user,1,1,1,0"
        new_rules.append(user_rule)

        # Create manager access rule
        manager_rule = f"access_{model_name.replace('.', '_')}_manager,{model_name}.manager,model_{model_name},records_management.group_records_manager,1,1,1,1"
        new_rules.append(manager_rule)

    # Write back to CSV
    try:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            # Write existing content
            for line in existing_lines:
                f.write(line + '\n')

            # Add new rules
            for rule in new_rules:
                f.write(rule + '\n')

        print(f"✅ Successfully added {len(new_rules)} security rules for {len(missing_models)} models")

    except Exception as e:
        print(f"Error writing CSV: {e}")

def main():
    print("🔍 Extracting models from Python files...")
    python_models = extract_models_from_python()
    print(f"Found {len(python_models)} models in Python files")

    print("\n🔍 Extracting existing models from CSV...")
    csv_models = get_existing_models_from_csv()
    print(f"Found {len(csv_models)} models in CSV")

    # Find missing models
    missing_models = [model for model in python_models if model not in csv_models]
    print(f"\n❌ Missing models: {len(missing_models)}")

    if missing_models:
        print("\n📝 Adding security rules for missing models...")
        add_security_rules(missing_models)

        print("\n✅ Security rules added successfully!")
        print(f"Total rules added: {len(missing_models) * 2} (user + manager for each model)")

        # Verify the update
        print("\n🔍 Verifying update...")
        updated_csv_models = get_existing_models_from_csv()
        still_missing = [model for model in python_models if model not in updated_csv_models]

        if still_missing:
            print(f"⚠️  Still missing: {len(still_missing)} models")
            for model in still_missing[:5]:  # Show first 5
                print(f"  - {model}")
        else:
            print("✅ All models now have security rules!")

    else:
        print("✅ No missing models found!")

if __name__ == "__main__":
    main()
