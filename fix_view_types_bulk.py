#!/usr/bin/env python3
"""
Bulk fix for view type errors in Records Management module.
Fixes type="tree" to type="list" and <tree> to <list> for list views.
"""

import os
import re
import glob


def fix_view_types():
    """Fix all view type errors in XML files."""

    # Find all XML view files
    view_files = glob.glob("records_management/views/*.xml")

    fixed_count = 0

    for file_path in view_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Pattern 1: Fix type="tree" to type="list" for list views
            # Look for records that have <tree> in arch but type="tree"
            tree_pattern = r'(<record[^>]*model="ir\.ui\.view"[^>]*>.*?<field name="type">tree</field>.*?<field name="arch"[^>]*>.*?<tree>)'
            tree_matches = re.findall(tree_pattern, content, re.DOTALL)

            if tree_matches:
                # Replace type="tree" with type="list"
                content = re.sub(r'(<field name="type">)tree(</field>)', r"\1list\2", content)
                # Replace <tree> with <list>
                content = re.sub(r"(<tree>)", r"<list>", content)
                content = re.sub(r"(</tree>)", r"</list>", content)

                fixed_count += 1
                print(f"Fixed: {file_path}")

            # Save the file if changes were made
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"\n✅ Fixed {fixed_count} view files")
    return fixed_count


if __name__ == "__main__":
    fix_view_types()
