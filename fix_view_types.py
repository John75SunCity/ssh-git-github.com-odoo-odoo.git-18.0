#!/usr/bin/env python3
"""
Fix View Type Errors in Odoo XML View Files

This script fixes common Odoo 18 view type errors where 'type="tree"' should be
replaced with the correct view type (list, form, search, kanban, calendar).
"""

import os
import re
import glob


def fix_view_types_in_file(filepath):
    """Fix view type errors in a single XML file."""
    print(f"Processing: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Fix tree/list views: type="tree" -> type="list" (when arch contains <tree> or <list>)
    content = re.sub(
        r'(<record[^>]*model="ir\.ui\.view"[^>]*>.*?<field name="type">tree</field>.*?<field name="arch"[^>]*>.*?(?:<tree|<list))',
        lambda m: m.group(0).replace('<field name="type">tree</field>', '<field name="type">list</field>'),
        content,
        flags=re.DOTALL,
    )

    # Fix form views: type="tree" -> type="form" (when arch contains <form>)
    content = re.sub(
        r'(<record[^>]*model="ir\.ui\.view"[^>]*>.*?<field name="type">tree</field>.*?<field name="arch"[^>]*>.*?<form)',
        lambda m: m.group(0).replace('<field name="type">tree</field>', '<field name="type">form</field>'),
        content,
        flags=re.DOTALL,
    )

    # Fix search views: type="tree" -> type="search" (when arch contains <search>)
    content = re.sub(
        r'(<record[^>]*model="ir\.ui\.view"[^>]*>.*?<field name="type">tree</field>.*?<field name="arch"[^>]*>.*?<search)',
        lambda m: m.group(0).replace('<field name="type">tree</field>', '<field name="type">search</field>'),
        content,
        flags=re.DOTALL,
    )

    # Fix kanban views: type="tree" -> type="kanban" (when arch contains <kanban>)
    content = re.sub(
        r'(<record[^>]*model="ir\.ui\.view"[^>]*>.*?<field name="type">tree</field>.*?<field name="arch"[^>]*>.*?<kanban)',
        lambda m: m.group(0).replace('<field name="type">tree</field>', '<field name="type">kanban</field>'),
        content,
        flags=re.DOTALL,
    )

    # Fix calendar views: type="tree" -> type="calendar" (when arch contains <calendar>)
    content = re.sub(
        r'(<record[^>]*model="ir\.ui\.view"[^>]*>.*?<field name="type">tree</field>.*?<field name="arch"[^>]*>.*?<calendar)',
        lambda m: m.group(0).replace('<field name="type">tree</field>', '<field name="type">calendar</field>'),
        content,
        flags=re.DOTALL,
    )

    # Fix view_mode in actions: tree -> list
    content = re.sub(
        r'(<field name="view_mode">)([^<]*(?:tree|Tree)[^<]*)(</field>)',
        lambda m: m.group(1) + m.group(2).replace("tree", "list").replace("Tree", "list") + m.group(3),
        content,
    )

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Fixed view types in {filepath}")
        return True
    else:
        print(f"  ℹ️  No changes needed in {filepath}")
        return False


def main():
    """Main function to process all XML view files."""
    views_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views"

    if not os.path.exists(views_dir):
        print(f"Error: Views directory not found: {views_dir}")
        return

    # Get all XML files in views directory
    xml_files = glob.glob(os.path.join(views_dir, "*.xml"))

    print(f"Found {len(xml_files)} XML files in views directory")
    print("=" * 60)

    fixed_count = 0
    for xml_file in sorted(xml_files):
        if fix_view_types_in_file(xml_file):
            fixed_count += 1

    print("=" * 60)
    print(f"Summary: Fixed {fixed_count} out of {len(xml_files)} files")


if __name__ == "__main__":
    main()
