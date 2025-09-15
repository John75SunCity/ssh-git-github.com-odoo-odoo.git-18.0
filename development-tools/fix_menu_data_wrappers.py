#!/usr/bin/env python3
"""
Menu and Action Data Wrapper Fix Tool
=====================================

Automatically fixes XML files where menuitem and act_window elements
are not properly wrapped in <data> tags, causing Odoo schema validation errors.

This fixes the specific error: "Element odoo has extra content: record"
"""

import os
import re
import glob
from pathlib import Path

def fix_menu_data_wrapper(file_path):
    """
    Fix a single XML file by wrapping menu items and actions in <data> tags.

    Args:
        file_path (str): Path to the XML file to fix

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        lines = content.split('\n')

        # Find lines with menu items or actions that are not inside records
        menu_action_lines = []
        in_record = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Track if we're inside a record
            if '<record' in stripped and not stripped.startswith('<!--'):
                in_record = True
            elif '</record>' in stripped and not stripped.startswith('<!--'):
                in_record = False

            # Find menu items or actions outside of records
            if ('<menuitem' in stripped or '<act_window' in stripped) and not stripped.startswith('<!--'):
                if not in_record:
                    menu_action_lines.append(i)

        if not menu_action_lines:
            return False

        # Group consecutive menu/action lines together
        groups = []
        current_group = [menu_action_lines[0]]

        for i in range(1, len(menu_action_lines)):
            if menu_action_lines[i] - menu_action_lines[i-1] <= 2:  # Allow for empty lines
                current_group.append(menu_action_lines[i])
            else:
                groups.append(current_group)
                current_group = [menu_action_lines[i]]
        groups.append(current_group)

        # Process groups in reverse order to maintain line numbers
        for group in reversed(groups):
            start_line = group[0]
            end_line = group[-1]

            # Find the actual start and end of the group (including multi-line tags)
            actual_start = start_line
            actual_end = end_line

            # Extend to include closing tags
            while actual_end < len(lines) - 1:
                if '/>' in lines[actual_end] or '</' in lines[actual_end + 1]:
                    if '/>' not in lines[actual_end]:
                        actual_end += 1
                    break
                actual_end += 1

            # Get the indentation of the first menu/action line
            base_indent = len(lines[actual_start]) - len(lines[actual_start].lstrip())
            data_indent = ' ' * (base_indent - 4) if base_indent >= 4 else ''

            # Insert <data> tag before the group
            lines.insert(actual_start, f'{data_indent}<data>')

            # Insert </data> tag after the group (adjust for the inserted line)
            lines.insert(actual_end + 2, f'{data_indent}</data>')

        # Join the lines back together
        new_content = '\n'.join(lines)

        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all XML files in the module."""
    print("🔧 MENU AND ACTION DATA WRAPPER FIX TOOL")
    print("=" * 50)

    # Find all XML files in the records_management module
    xml_files = glob.glob("records_management/**/*.xml", recursive=True)

    if not xml_files:
        print("❌ No XML files found in records_management/")
        return

    print(f"📊 Processing {len(xml_files)} XML files...")

    fixed_count = 0

    for xml_file in xml_files:
        if fix_menu_data_wrapper(xml_file):
            fixed_count += 1
            print(f"🔧 Fixed: {xml_file}")

    print(f"\n✅ Processing complete!")
    print(f"   - Files processed: {len(xml_files)}")
    print(f"   - Files fixed: {fixed_count}")

    if fixed_count > 0:
        print(f"\n💡 {fixed_count} files were modified with proper <data> wrappers.")
        print("   Run the validator again to confirm all issues are resolved.")
    else:
        print("\n✅ No files needed fixing - all menu items properly wrapped!")

if __name__ == "__main__":
    main()
