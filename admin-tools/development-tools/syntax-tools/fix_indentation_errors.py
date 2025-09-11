#!/usr/bin/env python3
"""
Fix Indentation and Syntax Errors
Specifically fixes issues introduced by the previous standards fixer
"""

import os
import re
from pathlib import Path


def fix_field_syntax_errors(content):
    """Fix common field definition syntax errors"""
    fixes_applied = 0

    # Fix misplaced help parameters and closing parentheses
    # Pattern: field = fields.Type(args,) help="...", )
    pattern1 = r'(\s+)([^,\s]+=[^,\n]*,)\s*help="([^"]*)",\s*\),\s*\n'
    replacement1 = r'\1\2\n\1    help="\3",\n\1)\n'
    new_content = re.sub(pattern1, replacement1, content)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    # Fix hanging help parameters
    # Pattern: args,) \n    help="...", \n    ),
    pattern2 = r'(\s+)([^,\n]+,)\s*\)\s*\n\s+help="([^"]*)",\s*\n\s+\),'
    replacement2 = r'\1\2\n\1    help="\3",\n\1)'
    new_content = re.sub(pattern2, replacement2, content)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    # Fix double closing parentheses
    pattern3 = r'(\s+help="[^"]*",\s*\n\s*)\),\s*\n'
    replacement3 = r"\1)\n"
    new_content = re.sub(pattern3, replacement3, content)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    return content, fixes_applied


def fix_action_method_indentation(content):
    """Fix indentation issues in action methods"""
    fixes_applied = 0

    # Fix methods where ensure_one is improperly indented
    pattern = r'(def action_\w+\([^)]*\):\s*\n\s*"""[^"]*"""\s*\n)(\s{4,})self\.ensure_one\(\)'
    replacement = r"\1        self.ensure_one()"
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    return content, fixes_applied


def process_file(file_path):
    """Process a single file to fix syntax errors"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        total_fixes = 0

        # Apply fixes
        content, fixes = fix_field_syntax_errors(content)
        total_fixes += fixes

        content, fixes = fix_action_method_indentation(content)
        total_fixes += fixes

        # Write back if changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return total_fixes

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0

    return 0


def main():
    """Main function"""
    models_dir = Path("records_management/models")

    # List of files with known syntax errors
    error_files = [
        "barcode_product.py",
        "service_item.py",
        "shredding_hard_drive.py",
        "portal_feedback_support_models.py",
        "processing_log.py",
        "paper_bale.py",
        "records_location.py",
        "shredding_team.py",
        "paper_bale_recycling.py",
        "shredding_inventory_item.py",
        "records_vehicle.py",
        "unlock_service_history.py",
        "records_access_log.py",
        "temp_inventory.py",
        "signed_document.py",
        "pickup_route.py",
        "records_document_type.py",
        "records_container_movement.py",
    ]

    print("🔧 FIXING INDENTATION & SYNTAX ERRORS")
    print("=" * 50)

    total_files_fixed = 0
    total_fixes = 0

    for file_name in error_files:
        file_path = models_dir / file_name
        if file_path.exists():
            fixes = process_file(file_path)
            if fixes > 0:
                print(f"✅ {file_name}: {fixes} fixes applied")
                total_files_fixed += 1
                total_fixes += fixes
            else:
                print(f"ℹ️  {file_name}: No fixes needed")
        else:
            print(f"⚠️  {file_name}: File not found")

    print("\n" + "=" * 50)
    print(f"📊 SUMMARY:")
    print(f"   • Files fixed: {total_files_fixed}")
    print(f"   • Total fixes applied: {total_fixes}")
    print("\n🧪 Next: Run syntax validation")


if __name__ == "__main__":
    main()
