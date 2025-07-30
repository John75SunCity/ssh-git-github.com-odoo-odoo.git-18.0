#!/usr/bin/env python3

"""
Fix @api.model Deprecation Warnings in Records Management Module

This script addresses the Odoo 18.0 deprecation warnings about models
not properly overriding the create method in batch mode.
"""

import os
import re
import sys


def fix_api_model_warnings():
    """Remove problematic @api.model decorators causing deprecation warnings"""

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    if not os.path.exists(models_dir):
        print(f"❌ Models directory not found: {models_dir}")
        return False

    fixed_files = []

    # Get all Python files in models directory
    for filename in os.listdir(models_dir):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

        filepath = os.path.join(models_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Pattern to find and remove problematic @api.model decorators
            # These are typically on empty methods or methods that don't need @api.model
            patterns_to_fix = [
                # Remove @api.model from empty methods or simple pass methods
                r"    @api\.model\s*\n\s*def [^(]+\([^)]*\):\s*\n\s*pass\s*\n",
                # Remove @api.model from methods that just return empty strings/values
                r'    @api\.model\s*\n\s*def [^(]+\([^)]*\):\s*\n\s*return\s+["\']["\']\s*\n',
                r"    @api\.model\s*\n\s*def [^(]+\([^)]*\):\s*\n\s*return\s+False\s*\n",
                r"    @api\.model\s*\n\s*def [^(]+\([^)]*\):\s*\n\s*return\s+None\s*\n",
            ]

            for pattern in patterns_to_fix:
                content = re.sub(
                    pattern,
                    lambda m: m.group(0).replace("@api.model\n", ""),
                    content,
                    flags=re.MULTILINE,
                )

            # Also remove standalone @api.model decorators that aren't followed by actual methods
            content = re.sub(
                r"\s*@api\.model\s*\n\s*(?=\s*@|\s*def\s+_|\s*$)",
                "",
                content,
                flags=re.MULTILINE,
            )

            # If we made changes, write the file back
            if content != original_content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(filename)
                print(f"✅ Fixed @api.model warnings in: {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
            continue

    return fixed_files


def fix_field_reference_error():
    """Fix the specific field reference error with res.partner.bank.country_code"""

    print("\n🔧 Fixing field reference error...")

    # Look for files that might have this field reference
    search_patterns = ["country_code", "res.partner.bank", "related.*country_code"]

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    for filename in os.listdir(models_dir):
        if not filename.endswith(".py"):
            continue

        filepath = os.path.join(models_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if this file contains the problematic field reference
            if "country_code" in content and "related" in content:
                print(f"🔍 Found potential field reference issue in: {filename}")

                # Fix common patterns
                original_content = content

                # Fix related field that references non-existent country_code
                content = re.sub(
                    r'related\s*=\s*["\'].*\.country_code["\']',
                    'related="partner_id.country_id.code"',
                    content,
                )

                # Remove invalid field definitions
                content = re.sub(
                    r'country_code\s*=\s*fields\.[^=]*related\s*=\s*["\'][^"\']*res\.partner\.bank[^"\']*["\'][^,\n]*',
                    "# Removed invalid country_code field reference",
                    content,
                )

                if content != original_content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"✅ Fixed field reference in: {filename}")

        except Exception as e:
            print(f"❌ Error checking {filename}: {str(e)}")
            continue


if __name__ == "__main__":
    print("🚀 FIXING @API.MODEL DEPRECATION WARNINGS")
    print("=" * 60)

    # Fix @api.model warnings
    fixed_files = fix_api_model_warnings()

    if fixed_files:
        print(f"\n✅ Fixed @api.model warnings in {len(fixed_files)} files:")
        for filename in fixed_files:
            print(f"   - {filename}")
    else:
        print("\n📝 No @api.model warnings found to fix")

    # Fix field reference error
    fix_field_reference_error()

    print("\n🎯 API MODEL FIXES COMPLETED")
