#!/usr/bin/env python3
"""
Enhanced Batch Fix Script for Data Wrapper Deployment Blockers
===============================================================

This script automatically fixes all XML files in the Records Management module
that have the deployment-blocking <data> wrapper issue.

Fixes the critical deployment error:
"Element odoo has extra content: data" - schema validation error in Odoo 18.0

Usage: python3 fix_all_data_wrappers.py
"""

import os
import re
import subprocess
from pathlib import Path


def fix_data_wrapper_in_file(file_path):
    """
    Remove <data> wrapper from an XML file and fix indentation.

    Args:
        file_path (str): Path to the XML file to fix

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file has <data> wrapper inside <odoo>
        if '<odoo>' not in content or '<data>' not in content:
            return False

        # Pattern to match and remove data wrapper
        # This handles various formatting styles
        pattern = r'<odoo>\s*\n\s*<data>\s*\n(.*?)\n\s*</data>\s*\n\s*</odoo>'

        def fix_content(match):
            inner_content = match.group(1)
            # Fix indentation - remove one level of indentation from all lines
            lines = inner_content.split('\n')
            fixed_lines = []
            for line in lines:
                # Remove 4 spaces or 1 tab of indentation if present
                if line.startswith('    '):
                    fixed_lines.append(line[4:])
                elif line.startswith('\t'):
                    fixed_lines.append(line[1:])
                else:
                    fixed_lines.append(line)

            return f'<odoo>\n\n{chr(10).join(fixed_lines)}\n\n</odoo>'

        # Apply the fix
        new_content = re.sub(pattern, fix_content, content, flags=re.DOTALL)

        # If no change was made with the above pattern, try simpler patterns
        if new_content == content:
            # Try pattern without leading/trailing whitespace preservation
            simple_pattern = r'<odoo>\s*<data>(.*?)</data>\s*</odoo>'
            if re.search(simple_pattern, content, re.DOTALL):
                new_content = re.sub(simple_pattern, r'<odoo>\1</odoo>', content, flags=re.DOTALL)

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def find_files_with_data_wrappers():
    """Find all XML files in views directory that have <data> wrappers."""
    views_dir = Path("records_management/views")
    if not views_dir.exists():
        print("❌ Views directory not found!")
        return []

    files_with_data = []
    for xml_file in views_dir.glob("*.xml"):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '<odoo>' in content and '<data>' in content:
                    files_with_data.append(str(xml_file))
        except Exception as e:
            print(f"⚠️ Could not read {xml_file}: {e}")

    return files_with_data


def validate_file(file_path):
    """Validate a single file using the comprehensive validator."""
    try:
        result = subprocess.run(
            ['python3', 'development-tools/comprehensive_validator.py', file_path],
            capture_output=True,
            text=True,
            cwd='.'
        )

        if result.returncode == 0 and "No validation errors found!" in result.stdout:
            return True, "No validation errors found!"
        else:
            return False, result.stdout
    except Exception as e:
        return False, f"Validation error: {e}"


def main():
    """Main function to fix all data wrapper deployment blockers."""
    print("🚀 Enhanced Batch Fix for ALL Data Wrapper Deployment Blockers")
    print("=" * 80)

    # Find all files with data wrappers
    print("🔍 Scanning for files with <data> wrapper deployment blockers...")
    files_to_fix = find_files_with_data_wrappers()

    if not files_to_fix:
        print("✅ No files found with <data> wrapper issues!")
        return

    print(f"📊 Found {len(files_to_fix)} files with <data> wrapper deployment blockers")
    print("\n🔧 Starting batch fix process...")

    fixed_count = 0
    validation_errors = []

    for i, file_path in enumerate(files_to_fix, 1):
        print(f"\n[{i}/{len(files_to_fix)}] 🔧 Fixing: {file_path}")

        # Apply the fix
        if fix_data_wrapper_in_file(file_path):
            print(f"  ✅ Fixed: {file_path}")
            fixed_count += 1

            # Validate the fixed file
            is_valid, validation_result = validate_file(file_path)
            if is_valid:
                print(f"  ✅ Validation: Passed")
            else:
                print(f"  ⚠️ Validation: Has issues")
                validation_errors.append((file_path, validation_result))
        else:
            print(f"  ℹ️ No changes needed: {file_path}")

    # Summary
    print("\n" + "=" * 80)
    print("📋 BATCH FIX SUMMARY")
    print("=" * 80)
    print(f"✅ Files processed: {len(files_to_fix)}")
    print(f"✅ Files fixed: {fixed_count}")
    print(f"⚠️ Files with validation issues: {len(validation_errors)}")

    if validation_errors:
        print("\n🔍 Files requiring manual review:")
        for file_path, error in validation_errors[:5]:  # Show first 5
            print(f"  - {file_path}")
            if len(validation_errors) > 5:
                print(f"  ... and {len(validation_errors) - 5} more")

    print(f"\n🎯 Deployment blocker resolution: {fixed_count} files should now deploy successfully!")

    if fixed_count > 0:
        print("\n💡 Next steps:")
        print("1. Test deployment with fixed files")
        print("2. Commit changes: git add . && git commit -m 'fix: Resolved data wrapper deployment blockers'")
        print("3. Continue systematic validation of remaining files")


if __name__ == "__main__":
    main()
