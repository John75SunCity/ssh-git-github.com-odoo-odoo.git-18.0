#!/usr/bin/env python3
import os
import re
import xml.etree.ElementTree as ET

def fix_missing_model_references():
    """Fix missing model references in report files"""

    # Mapping of missing models to correct existing models
    model_mapping = {
        'records.container.type.converter.wizard': 'records.container.type.converter',
        'records.config.setting': 'rm.module.configurator',  # Use configurator instead
        'work.order.bin.assignment': 'work.order.shredding',
        'survey.user.input': 'records.survey.user.input',
        'product.template': 'product.product',  # Standard Odoo model
        'advanced.billing': 'records.billing',  # Fix the advanced billing reference
        'records_management.bale': 'paper.bale',  # Fix bale model reference
    }

    reports_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/report"
    fixed_files = []

    for filename in os.listdir(reports_dir):
        if filename.endswith('.xml'):
            file_path = os.path.join(reports_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                modified = False

                # Fix model references in binding_model_id
                for old_model, new_model in model_mapping.items():
                    old_pattern = f'binding_model_id="records_management.model_{old_model}"'
                    new_pattern = f'binding_model_id="records_management.model_{new_model}"'
                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern)
                        modified = True
                        print(f"Fixed {old_model} -> {new_model} in {filename}")

                # Also fix direct model references in XML
                for old_model, new_model in model_mapping.items():
                    if f'model="{old_model}"' in content:
                        content = content.replace(f'model="{old_model}"', f'model="{new_model}"')
                        modified = True
                        print(f"Fixed model reference {old_model} -> {new_model} in {filename}")

                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_files.append(filename)

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\nFixed {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")

    return fixed_files

if __name__ == "__main__":
    fix_missing_model_references()
