#!/usr/bin/env python3
"""
Field Syntax Cleanup Script
Fixes syntax errors in auto-generated fields
"""

import os
import re
from pathlib import Path


def fix_field_syntax(file_path):
    """Fix common syntax errors in field definitions"""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Fix 1: Remove invalid characters in field names (like =True, ==, in [], etc.)
    # Find field definitions with invalid names
    invalid_field_pattern = r"^\s*([^=\s]+[=<>!]+[^=\s]*)\s*=\s*fields\."

    def fix_invalid_field_name(match):
        field_name = match.group(1)
        # Clean field name by removing invalid characters
        clean_name = re.sub(r"[=<>!]+.*$", "", field_name).strip()
        # Replace with underscores for safety
        clean_name = re.sub(r"[^\w]", "_", clean_name)
        # Remove duplicate underscores
        clean_name = re.sub(r"_+", "_", clean_name)
        # Remove trailing underscore
        clean_name = clean_name.strip("_")

        if not clean_name or not clean_name[0].isalpha():
            clean_name = "field_" + clean_name

        return f"    {clean_name} = fields."

    content = re.sub(
        invalid_field_pattern, fix_invalid_field_name, content, flags=re.MULTILINE
    )

    # Fix 2: Remove invalid string values that contain unescaped quotes
    def fix_string_values(match):
        field_def = match.group(0)
        # Fix string values with problematic content
        field_def = re.sub(
            r'string="[^"]*=True[^"]*"', 'string="Auto Generated Field"', field_def
        )
        field_def = re.sub(
            r'string="[^"]*==\'[^"]*"', 'string="Auto Generated Field"', field_def
        )
        field_def = re.sub(
            r'string="[^"]*in \[[^"]*"', 'string="Auto Generated Field"', field_def
        )
        return field_def

    content = re.sub(
        r'^\s*\w+\s*=\s*fields\.[^(]+\([^)]*string="[^"]*"[^)]*\)',
        fix_string_values,
        content,
        flags=re.MULTILINE,
    )

    # Fix 3: Clean up field names that are Python keywords or invalid
    python_keywords = {
        "def",
        "class",
        "if",
        "else",
        "elif",
        "while",
        "for",
        "try",
        "except",
        "import",
        "from",
        "in",
        "is",
        "not",
        "and",
        "or",
    }

    def fix_keyword_field(match):
        field_name = match.group(1)
        if field_name in python_keywords:
            return f"    {field_name}_field = fields."
        return match.group(0)

    content = re.sub(
        r"^\s*(\w+)\s*=\s*fields\.", fix_keyword_field, content, flags=re.MULTILINE
    )

    # Write back if changed
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    return False


def main():
    """Main function"""
    print("🔧 Field Syntax Cleanup Script")
    print("==============================")

    records_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    # Models that were modified
    modified_models = [
        "models/visitor_pos_wizard.py",
        "models/records_billing_config.py",
        "models/naid_compliance.py",
        "models/records_document_type.py",
        "models/records_location.py",
    ]

    for model_path in modified_models:
        full_path = records_path / model_path
        if full_path.exists():
            print(f"\n🎯 Processing {model_path}")
            if fix_field_syntax(full_path):
                print(f"   ✅ Fixed syntax errors")
            else:
                print(f"   ℹ️  No syntax errors found")
        else:
            print(f"   ❌ File not found: {full_path}")

    print(f"\n🎉 Cleanup complete!")


if __name__ == "__main__":
    main()
