#!/usr/bin/env python3
"""
XML Structure Validator and Fixer
Fixes XML files that have invalid nested <odoo><data> structure without noupdate attribute
"""

import os
import re

def check_and_fix_xml_structure():
    """Check and fix XML files with invalid nested structure."""
    print("🔍 Checking XML files for invalid nested <odoo><data> structure...")

    files_fixed = []
    files_checked = 0

    for root, dirs, files in os.walk("records_management"):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                files_checked += 1

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for problematic pattern: <odoo> followed by <data> without noupdate
                    # This pattern is invalid in modern Odoo
                    if ('<odoo>' in content and
                        '<data>' in content and
                        'noupdate=' not in content):

                        # Check if it's the nested structure we need to fix
                        if re.search(r'<odoo>\s*<data>', content):
                            print(f"🔧 Fixing: {file_path}")

                            # Remove the nested <data> tags
                            # Replace <odoo><data> with just <odoo>
                            fixed_content = re.sub(r'<odoo>\s*<data>', '<odoo>', content)
                            # Replace </data></odoo> with just </odoo>
                            fixed_content = re.sub(r'</data>\s*</odoo>', '</odoo>', fixed_content)

                            # Write the fixed content back
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(fixed_content)

                            files_fixed.append(file_path)

                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")

    print(f"\n📊 Results:")
    print(f"   - Files checked: {files_checked}")
    print(f"   - Files fixed: {len(files_fixed)}")

    if files_fixed:
        print(f"\n✅ Fixed files:")
        for file_path in files_fixed:
            print(f"   - {file_path}")
    else:
        print(f"\n✅ No additional files needed fixing!")

if __name__ == "__main__":
    check_and_fix_xml_structure()
