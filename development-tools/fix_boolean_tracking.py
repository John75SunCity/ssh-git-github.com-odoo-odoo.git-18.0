#!/usr/bin/env python3
"""
Script to fix Boolean fields with tracking=True parameter
Boolean fields don't support tracking in Odoo
"""

import os
import re
import glob

def fix_boolean_tracking():
    """Fix Boolean fields with tracking=True parameter"""
    records_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    model_files = glob.glob(f"{records_path}/models/*.py")

    fixed_files = []

    for file_path in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Pattern to match Boolean fields with tracking=True
            # This pattern looks for fields.Boolean(..., tracking=True, ...)
            patterns_to_fix = [
                # Boolean field with tracking=True and other parameters
                r'(fields\.Boolean\([^)]*?)(,\s*tracking=True)([^)]*?\))',
                # Boolean field with only tracking=True
                r'(fields\.Boolean\()(tracking=True)(\))',
                # Boolean field with tracking=True at the end
                r'(fields\.Boolean\([^)]*?)(,\s*tracking=True)(\))',
            ]

            for pattern in patterns_to_fix:
                # Remove the tracking=True parameter
                content = re.sub(pattern, r'\1\3', content)

            # If content changed, write it back
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(os.path.basename(file_path))
                print(f"✅ Fixed Boolean tracking in: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")

    print(f"\n🎯 Summary: Fixed {len(fixed_files)} files")
    for file in fixed_files:
        print(f"  - {file}")

if __name__ == "__main__":
    fix_boolean_tracking()
