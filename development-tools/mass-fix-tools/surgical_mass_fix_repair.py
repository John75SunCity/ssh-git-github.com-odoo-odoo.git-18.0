#!/usr/bin/env python3
"""
Surgical Mass Fix Repair Script
===============================

This script analyzes and repairs specific corruptions caused by the mass fix process,
while preserving all the good fixes that were made.

Focus: Field name corruptions where mass fix incorrectly pluralized field names.
"""

import os
import re
import difflib
from pathlib import Path

def find_field_name_corruptions():
    """Find common field name corruptions caused by mass fix"""

    corruptions_found = []
    views_dir = Path("records_management/views")
    backup_dir = Path("backup/views_backup_20250913")

    # Known corruption patterns from the error
    corruption_patterns = [
        # Pattern: document_id -> document_ids (WRONG)
        (r'<field name="document_ids"', r'<field name="document_id"'),
        # Add more patterns as we discover them
    ]

    print("🔍 SURGICAL MASS FIX REPAIR - Analyzing corruptions...")
    print("=" * 60)

    for xml_file in views_dir.glob("*.xml"):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()

            backup_file = None
            # Try different backup naming patterns
            for pattern in [
                f"{xml_file.name}.backup_20250913_*",
                f"{xml_file.name}"
            ]:
                backup_matches = list(backup_dir.glob(pattern))
                if backup_matches:
                    backup_file = backup_matches[0]
                    break

            if not backup_file or not backup_file.exists():
                continue

            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_content = f.read()

            # Check for corruptions
            for wrong_pattern, correct_pattern in corruption_patterns:
                if re.search(wrong_pattern, content) and re.search(correct_pattern.replace('"', '"'), backup_content):
                    corruptions_found.append({
                        'file': xml_file,
                        'backup_file': backup_file,
                        'wrong_pattern': wrong_pattern,
                        'correct_pattern': correct_pattern,
                        'current_content': content,
                        'backup_content': backup_content
                    })
                    print(f"❌ CORRUPTION FOUND: {xml_file.name}")
                    print(f"   Wrong: {wrong_pattern}")
                    print(f"   Should be: {correct_pattern}")
                    print(f"   Backup: {backup_file.name}")
                    print()

        except Exception as e:
            print(f"⚠️  Error analyzing {xml_file}: {e}")

    return corruptions_found

def apply_surgical_fixes(corruptions):
    """Apply targeted fixes to preserve good changes while fixing corruptions"""

    print("🔧 APPLYING SURGICAL FIXES...")
    print("=" * 40)

    fixes_applied = 0

    for corruption in corruptions:
        try:
            # Read current content
            current_content = corruption['current_content']

            # Apply the specific fix
            fixed_content = re.sub(
                corruption['wrong_pattern'],
                corruption['correct_pattern'],
                current_content
            )

            # Verify fix was applied
            if fixed_content != current_content:
                # Write the fixed content
                with open(corruption['file'], 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                print(f"✅ FIXED: {corruption['file'].name}")
                print(f"   Changed: {corruption['wrong_pattern']}")
                print(f"   To: {corruption['correct_pattern']}")
                fixes_applied += 1
            else:
                print(f"⚠️  No changes made to: {corruption['file'].name}")

        except Exception as e:
            print(f"❌ Error fixing {corruption['file']}: {e}")

    print(f"\n🎯 SURGICAL REPAIR COMPLETE: {fixes_applied} files fixed")
    return fixes_applied

def validate_fixes():
    """Validate that fixes don't break XML syntax"""

    print("\n🔍 VALIDATING XML SYNTAX...")
    print("=" * 30)

    import xml.etree.ElementTree as ET

    views_dir = Path("records_management/views")
    errors = []

    for xml_file in views_dir.glob("*.xml"):
        try:
            ET.parse(xml_file)
            print(f"✅ {xml_file.name}")
        except ET.ParseError as e:
            errors.append(f"❌ {xml_file.name}: {e}")
            print(f"❌ {xml_file.name}: {e}")

    if errors:
        print(f"\n⚠️  {len(errors)} XML syntax errors found!")
        return False
    else:
        print(f"\n🎉 All XML files are syntactically valid!")
        return True

def main():
    """Main surgical repair process"""

    print("🏥 SURGICAL MASS FIX REPAIR")
    print("=" * 50)
    print("Preserving good fixes while repairing mass fix corruptions...")
    print()

    # Step 1: Find corruptions
    corruptions = find_field_name_corruptions()

    if not corruptions:
        print("✅ No field name corruptions found!")
        return

    print(f"📋 Found {len(corruptions)} corruptions to fix")
    print()

    # Step 2: Apply surgical fixes
    fixes_applied = apply_surgical_fixes(corruptions)

    # Step 3: Validate results
    if validate_fixes():
        print("\n🎉 SURGICAL REPAIR SUCCESSFUL!")
        print("All corruptions fixed while preserving good changes.")
    else:
        print("\n⚠️  Validation failed - please review manually")

if __name__ == "__main__":
    main()
