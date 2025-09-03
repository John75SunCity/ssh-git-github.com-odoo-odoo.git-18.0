#!/usr/bin/env python3
"""
Add Missing Access Rules to CSV

This script identifies models missing access rules in ir.model.access.csv
and adds the required access rules for each missing model across all security groups.
"""

import os
import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def get_existing_models_from_csv(csv_path):
    """Get all models that already have access rules in the CSV"""
    existing_models = set()

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_id = row.get('model_id:id', '')
            if model_id:
                # Extract model name from external ID reference
                model_name = model_id.replace('records_management.model_', '')
                existing_models.add(model_name)

    return existing_models

def get_all_models_from_files(models_dir):
    """Get all models defined in Python files"""
    all_models = set()

    for py_file in Path(models_dir).glob('*.py'):
        if py_file.name == '__init__.py':
            continue

        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # Find _name attributes
            name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            for model_name in name_matches:
                all_models.add(model_name)

    return all_models

def get_missing_models(existing_models, all_models):
    """Find models that exist but don't have access rules"""
    return all_models - existing_models

def get_all_security_groups(base_dir):
    """Get all security groups defined in XML files"""
    groups = set()

    # Search for groups.xml or similar files in security/ and data/ directories
    for xml_file in Path(base_dir).glob('records_management/security/*.xml'):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Find all group records
            for record in root.findall(".//record[@model='res.groups']"):
                group_id = record.find("field[@name='id']")
                if group_id is not None and group_id.text:
                    groups.add(group_id.text)
        except ET.ParseError:
            continue

    # Also search data/ directory for group definitions
    for xml_file in Path(base_dir).glob('records_management/data/*.xml'):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for record in root.findall(".//record[@model='res.groups']"):
                group_id = record.find("field[@name='id']")
                if group_id is not None and group_id.text:
                    groups.add(group_id.text)
        except ET.ParseError:
            continue

    return groups

def add_access_rules_to_csv(csv_path, missing_models, all_groups):
    """Add access rules for missing models to the CSV file for all groups"""
    print(f"Adding access rules for {len(missing_models)} missing models across {len(all_groups)} groups...")

    # Read existing CSV
    rows = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

        # Fix: Handle case where fieldnames is None
        if fieldnames is None:
            fieldnames = ['id', 'name', 'model_id:id', 'group_id:id', 'perm_read', 'perm_write', 'perm_create', 'perm_unlink']

    # Add new access rules for each group
    new_rows = []
    for model_name in sorted(missing_models):
        # Skip if it's not a records_management model
        if not model_name.startswith(('records.', 'advanced.', 'barcode.', 'bin.',
                                   'chain.', 'container.', 'custody.', 'customer.',
                                   'destruction.', 'document.', 'feedback.', 'field.',
                                   'file.', 'hard.', 'inventory.', 'location.',
                                   'mobile.', 'naid.', 'paper.', 'partner.', 'payment.',
                                   'pickup.', 'portal.', 'product.', 'project.',
                                   'records.', 'retrieval.', 'revenue.', 'route.',
                                   'scan.', 'service.', 'shred.', 'signed.', 'stock.',
                                   'survey.', 'system.', 'temp.', 'transitory.',
                                   'unlock.', 'visitor.', 'work.', 'workflow.')):
            continue

        for group_id in sorted(all_groups):
            # Determine permissions based on group (e.g., managers get full access)
            if 'manager' in group_id.lower():
                perm_unlink = '1'
            else:
                perm_unlink = '0'

            rule = {
                'id': f'access_{model_name.replace(".", "_")}_{group_id.split(".")[-1]}',
                'name': f'{model_name.replace(".", " ").title()} ({group_id.split(".")[-1]})',
                'model_id:id': f'records_management.model_{model_name.replace(".", "_")}',
                'group_id:id': group_id,
                'perm_read': '1',
                'perm_write': '1',
                'perm_create': '1',
                'perm_unlink': perm_unlink
            }

            new_rows.append(rule)

    # Write updated CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} new access rules to {csv_path}")

def main():
    """Main function"""
    base_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0"
    csv_path = os.path.join(base_dir, "records_management", "security", "ir.model.access.csv")
    models_dir = os.path.join(base_dir, "records_management", "models")

    print("Analyzing existing access rules...")
    existing_models = get_existing_models_from_csv(csv_path)
    print(f"Found {len(existing_models)} models with existing access rules")

    print("Analyzing all defined models...")
    all_models = get_all_models_from_files(models_dir)
    print(f"Found {len(all_models)} total models in the module")

    print("Analyzing all security groups...")
    all_groups = get_all_security_groups(base_dir)
    print(f"Found {len(all_groups)} security groups:")
    for group in sorted(all_groups):
        print(f"  - {group}")

    missing_models = get_missing_models(existing_models, all_models)
    print(f"Found {len(missing_models)} models missing access rules:")

    for model in sorted(missing_models):
        print(f"  - {model}")

    if missing_models:
        add_access_rules_to_csv(csv_path, missing_models, all_groups)
        print("\n✅ Successfully added missing access rules for all groups!")
    else:
        print("\n✅ All models already have access rules!")

if __name__ == "__main__":
    main()
