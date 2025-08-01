#!/usr/bin/env python3
"""
Simple fix for create methods to handle list inputs properly
"""

import os
import re


def fix_create_methods_simple():
    """Fix create methods with a simple pattern replacement"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    print("🔧 FIXING CREATE METHODS (SIMPLE APPROACH)")
    print("=" * 50)

    # Get all Python files in models directory
    models_dir = os.path.join(base_path, "models")
    python_files = []

    for file in os.listdir(models_dir):
        if file.endswith(".py") and file != "__init__.py":
            python_files.append(os.path.join(models_dir, file))

    fixed_count = 0

    for file_path in python_files:
        if fix_create_method_simple(file_path):
            fixed_count += 1
            print(f"✅ Fixed: {os.path.basename(file_path)}")

    print(f"\n✅ FIXED {fixed_count} CREATE METHODS")


def fix_create_method_simple(file_path):
    """Fix create method in a single file with simple replacement"""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for the problematic pattern
        old_pattern = r'(\s+)def create\(self, vals\):\s*\n(\s+"""Override create to set default values\."""\s*\n)(\s+if not vals\.get\(\'name\'\):\s*\n\s+vals\[\'name\'\] = _\(\'New Record\'\)\s*\n)(\s+return super\(\)\.create\(vals\))'

        if re.search(old_pattern, content):
            new_pattern = r"""\1@api.model_create_multi
\1def create(self, vals_list):
\2\1# Handle both single dict and list of dicts
\1if not isinstance(vals_list, list):
\1    vals_list = [vals_list]
\1
\1for vals in vals_list:
\1    if not vals.get('name'):
\1        vals['name'] = _('New Record')
\1
\1return super().create(vals_list)"""

            new_content = re.sub(old_pattern, new_pattern, content)

            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


if __name__ == "__main__":
    fix_create_methods_simple()
