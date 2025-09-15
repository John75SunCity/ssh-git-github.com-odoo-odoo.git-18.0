#!/usr/bin/env python3
"""
Fix Unwrapped XML Records
========================

Fixes XML files where record, menuitem, or act_window elements
are directly under <odoo> without a <data> wrapper.
"""

import os
import glob

def fix_unwrapped_records(file_path):
    """Fix XML files with unwrapped records under odoo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if '<odoo>' not in content:
            return False

        # Check if file has records/menuitem/act_window directly under odoo without data wrapper
        lines = content.split('\n')
        in_odoo = False
        has_direct_elements = False
        has_data_wrapper = False

        for line in lines:
            stripped = line.strip()
            if '<odoo>' in stripped:
                in_odoo = True
            elif '</odoo>' in stripped:
                in_odoo = False
            elif in_odoo and not stripped.startswith('<!--'):
                if (stripped.startswith('<record') or
                    stripped.startswith('<menuitem') or
                    stripped.startswith('<act_window')):
                    has_direct_elements = True
                elif stripped.startswith('<data'):
                    has_data_wrapper = True

        if has_direct_elements and not has_data_wrapper:
            # Need to wrap everything in data tags
            # Find content between <odoo> and </odoo>
            start_idx = content.find('<odoo>') + len('<odoo>')
            end_idx = content.rfind('</odoo>')

            if start_idx > 0 and end_idx > start_idx:
                inner_content = content[start_idx:end_idx].strip()
                new_content = (content[:start_idx] +
                             '\n    <data>\n' +
                             inner_content +
                             '\n    </data>\n' +
                             content[end_idx:])

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f'🔧 Fixed: {file_path}')
                return True

    except Exception as e:
        print(f'❌ Error processing {file_path}: {e}')

    return False

def main():
    """Main function."""
    print("🔧 FIXING UNWRAPPED XML RECORDS")
    print("=" * 40)

    # Process all XML files
    xml_files = glob.glob('records_management/**/*.xml', recursive=True)
    fixed_count = 0

    for xml_file in xml_files:
        if fix_unwrapped_records(xml_file):
            fixed_count += 1

    print(f'\n✅ Fixed {fixed_count} files with unwrapped records')

if __name__ == "__main__":
    main()
