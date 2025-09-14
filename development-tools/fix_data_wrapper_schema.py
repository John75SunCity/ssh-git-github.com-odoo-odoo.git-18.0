#!/usr/bin/env python3
"""
Fix Odoo 18.0 Data Wrapper Schema Issues
Removes unnecessary <data> wrappers that cause "Element odoo has extra content: data" errors
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def fix_data_wrapper_file(file_path):
    """Fix a single XML file by removing unnecessary <data> wrapper"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse XML to check structure
        tree = ET.parse(file_path)
        root = tree.getroot()

        if root.tag != 'odoo':
            return False, "Not an Odoo XML file"

        # Check if there's a single <data> wrapper containing all records
        data_elements = [child for child in root if child.tag == 'data']
        if not data_elements:
            return False, "No <data> wrapper found"

        if len(data_elements) > 1:
            return False, "Multiple <data> elements found - manual review needed"

        # Check if ALL content is inside the single <data> wrapper
        records_outside_data = [child for child in root if child.tag != 'data']
        if records_outside_data:
            return False, "Content exists outside <data> wrapper - manual review needed"

        # Get the content inside <data>
        data_element = data_elements[0]
        data_content = []

        for child in data_element:
            # Convert element back to string
            elem_str = ET.tostring(child, encoding='unicode')
            data_content.append(elem_str)

        # Rebuild the file content
        lines = content.split('\n')
        new_lines = []
        inside_data = False
        data_indent = ""

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip the <data> opening tag
            if '<data>' in line and not inside_data:
                inside_data = True
                data_indent = line[:line.find('<data>')]
                continue

            # Skip the </data> closing tag
            if '</data>' in line and inside_data:
                inside_data = False
                continue

            # If we're inside <data>, remove one level of indentation
            if inside_data and line.startswith(data_indent + '    '):
                new_lines.append(line[4:])  # Remove 4 spaces of indentation
            elif inside_data and line.startswith(data_indent + '\t'):
                new_lines.append(line[1:])  # Remove 1 tab of indentation
            else:
                new_lines.append(line)

        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        return True, "Fixed successfully"

    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Fix all XML files with data wrapper issues"""
    records_mgmt_path = Path("records_management")

    if not records_mgmt_path.exists():
        print("❌ records_management directory not found")
        return

    # Find all XML files
    xml_files = []
    for xml_file in records_mgmt_path.rglob("*.xml"):
        xml_files.append(xml_file)

    print(f"🔍 Found {len(xml_files)} XML files to check")

    fixed_files = []
    skipped_files = []
    error_files = []

    for xml_file in xml_files:
        success, message = fix_data_wrapper_file(xml_file)

        if success:
            fixed_files.append(xml_file)
            print(f"✅ Fixed: {xml_file}")
        elif "No <data> wrapper found" in message:
            # This is normal - many files don't have data wrappers
            continue
        else:
            if "manual review needed" in message:
                skipped_files.append((xml_file, message))
                print(f"⚠️  Skipped: {xml_file} - {message}")
            else:
                error_files.append((xml_file, message))
                print(f"❌ Error: {xml_file} - {message}")

    print(f"\n📊 SUMMARY:")
    print(f"✅ Fixed: {len(fixed_files)} files")
    print(f"⚠️  Skipped: {len(skipped_files)} files (need manual review)")
    print(f"❌ Errors: {len(error_files)} files")

    if fixed_files:
        print(f"\n🎯 FIXED FILES:")
        for file in fixed_files:
            print(f"  - {file}")

    if skipped_files:
        print(f"\n⚠️  FILES NEEDING MANUAL REVIEW:")
        for file, reason in skipped_files:
            print(f"  - {file}: {reason}")

    if error_files:
        print(f"\n❌ FILES WITH ERRORS:")
        for file, error in error_files:
            print(f"  - {file}: {error}")

if __name__ == "__main__":
    main()
