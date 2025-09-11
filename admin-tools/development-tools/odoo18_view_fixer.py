#!/usr/bin/env python3
"""
Comprehensive Odoo 18.0 View Type Fixer
Fixes all view files to use 'list' instead of 'tree' for Odoo 18.0 compatibility
"""

import os
import re
import glob
from pathlib import Path


def fix_view_file(file_path):
    """Fix a single view file for Odoo 18.0 compatibility"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix view type attribute
        content = re.sub(r'type\s*=\s*["\']tree["\']', 'type="list"', content)

        # Fix XML element from <tree> to <list>
        content = re.sub(r"<tree([^>]*)>", r"<list\1>", content)
        content = re.sub(r"</tree>", "</list>", content)

        # Fix any tree references in field names or other attributes
        content = re.sub(r"tree_", "list_", content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix all view files"""
    views_dir = Path("records_management/views")

    if not views_dir.exists():
        print("Views directory not found!")
        return

    # Find all XML files
    xml_files = list(views_dir.glob("*.xml"))

    print(f"Found {len(xml_files)} XML files to process")

    fixed_count = 0
    processed_count = 0

    for xml_file in xml_files:
        processed_count += 1
        if fix_view_file(xml_file):
            fixed_count += 1
            print(f"Fixed: {xml_file.name}")
        else:
            print(f"No changes needed: {xml_file.name}")

    print("\nSUMMARY:")
    print(f"  Total files processed: {processed_count}")
    print(f"  Files fixed: {fixed_count}")
    print(f"  Files unchanged: {processed_count - fixed_count}")

    if fixed_count > 0:
        print("\nAll view files have been updated for Odoo 18.0 compatibility!")
        print("   - Changed type='tree' to type='list'")
        print("   - Changed <tree> elements to <list>")
        print("   - Updated tree_ references to list_")
    else:
        print("\nNo files needed fixing - all views are already Odoo 18.0 compatible!")


if __name__ == "__main__":
    main()
