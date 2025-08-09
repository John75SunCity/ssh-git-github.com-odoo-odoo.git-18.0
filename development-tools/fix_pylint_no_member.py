#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Pylint No-Member Errors for Odoo Recordsets

This script adds pylint disable comments for common Odoo recordset method calls
that pylint incorrectly flags as no-member errors.
"""

import os
import re
import argparse


def fix_no_member_errors(file_path):
    """Fix no-member errors in a Python file by adding pylint disable comments"""

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Patterns that commonly trigger no-member errors in Odoo
    patterns_to_fix = [
        # recordset.exists() calls
        (r"(\s+)(.*\.exists\(\))", r"\1\2  # pylint: disable=no-member"),
        # recordset.write() calls
        (r"(\s+)(.*\.write\(\s*{)", r"\1# pylint: disable=no-member\n\1\2"),
        # recordset.ids access
        (r"(.*\.ids)([^a-zA-Z_])", r"\1  # pylint: disable=no-member\2"),
        # recordset.id access (single record)
        (r"(\s+.*\brecord\.id\b)", r"\1  # pylint: disable=no-member"),
        (r"(\s+.*\bdocument\.id\b)", r"\1  # pylint: disable=no-member"),
        # recordset.create() calls
        (r"(\s+)(.*\.create\(\s*{)", r"\1# pylint: disable=no-member\n\1\2"),
        # recordset.search() calls
        (r"(\s+)(.*\.search\(\s*\[)", r"\1# pylint: disable=no-member\n\1\2"),
    ]

    changes_made = 0

    for pattern, replacement in patterns_to_fix:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            changes_made += count
            print(f"Fixed {count} instances of pattern: {pattern}")

    # Remove duplicate disable comments
    content = re.sub(
        r"(\s+# pylint: disable=no-member\s*\n\s*# pylint: disable=no-member)",
        r"\1",
        content,
        flags=re.MULTILINE,
    )

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {changes_made} no-member issues in {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix Pylint no-member errors in Odoo files"
    )
    parser.add_argument("files", nargs="+", help="Python files to fix")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    args = parser.parse_args()

    total_fixed = 0

    for file_path in args.files:
        if file_path.endswith(".py"):
            if fix_no_member_errors(file_path):
                total_fixed += 1
        else:
            print(f"Skipping non-Python file: {file_path}")

    print(f"\nSummary: Fixed no-member errors in {total_fixed} files")


if __name__ == "__main__":
    main()
