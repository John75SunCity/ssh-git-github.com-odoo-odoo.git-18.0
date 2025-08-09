#!/usr/bin/env python3
"""
Emergency Syntax Fixer - Fix syntax errors in 11 identified files

This script fixes common Python syntax errors in the specific files that
were identified as having syntax errors by the find_syntax_errors.py script.

Target Files: 11 files with syntax errors
- Focused fixes for orphaned parentheses
- Indentation normalization
- Trailing comma removal

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import os
import re
from pathlib import Path


# Target files that need fixing (based on syntax error detection)
TARGET_FILES = [
    "product_template.py",
    "records_chain_of_custody.py",
    "records_management_base_menus.py",
    "processing_log.py",
    "records_container_type_converter.py",
    "payment_split.py",
    "records_access_log.py",
    "records_billing_contact.py",
    "pickup_request.py",
    "pickup_route.py",
    "records_container_movement.py",
]


def emergency_fix_file(file_path):
    """Apply emergency fixes to make file parseable by Python"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixes_applied = []

        # Fix 1: Remove orphaned closing parentheses on their own lines
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # Check for lines that are just closing parentheses
            if line.strip() == ")":
                # Look at the previous lines to see if this is orphaned
                if i > 0:
                    prev_line = lines[i - 1].strip()
                    # If previous line already ends properly, this ) is orphaned
                    if (
                        prev_line.endswith(",")
                        or prev_line.endswith(")")
                        or prev_line.endswith('"')
                        or prev_line.endswith("'")
                        or prev_line == ""
                        or "fields." in prev_line
                    ):
                        fixes_applied.append(f"Removed orphaned ')' on line {i+1}")
                        continue  # Skip this orphaned )

            fixed_lines.append(line)

        if len(fixed_lines) != len(lines):
            content = "\n".join(fixed_lines)

        # Fix 2: Remove trailing commas before closing parentheses
        content = re.sub(r",\s*\)", ")", content)
        if content != original_content:
            fixes_applied.append("Removed trailing commas")
            original_content = content

        # Fix 3: Fix unexpected indentation by normalizing whitespace
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            if line.strip():  # Non-empty line
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())

                # Convert to proper 4-space indentation
                if leading_spaces > 0:
                    # Calculate proper indentation level (multiples of 4)
                    indent_level = leading_spaces // 4
                    if leading_spaces % 4 != 0:
                        # Normalize to proper 4-space indentation
                        proper_indent = " " * (indent_level * 4)
                        line = proper_indent + line.lstrip()
                        if original_content != content:
                            fixes_applied.append(f"Fixed indentation on line {i+1}")

            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        # Fix 4: Add missing colons to function/class definitions
        content = re.sub(
            r"(def\s+\w+\([^)]*\))\s*$", r"\1:", content, flags=re.MULTILINE
        )
        content = re.sub(
            r"(class\s+\w+\([^)]*\))\s*$", r"\1:", content, flags=re.MULTILINE
        )

        # Fix 5: Fix missing colons in control statements
        content = re.sub(
            r"(^\s*(?:if|elif|else|for|while|try|except|finally|with)\b[^:]*?)\s*$",
            r"\1:",
            content,
            flags=re.MULTILINE,
        )

        # Write back if changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, fixes_applied

        return False, []

    except Exception as e:
        return False, [f"Error: {str(e)}"]


def validate_python_syntax(file_path):
    """Validate if Python file has valid syntax"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to compile the content
        compile(content, str(file_path), "exec")
        return True, "Valid syntax"

    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Apply emergency fixes to specific problematic files"""
    models_dir = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    if not models_dir.exists():
        print(f"Error: Directory {models_dir} does not exist")
        return False

    print("=== Emergency Syntax Fixer ===")
    print("Fixing syntax errors in 11 identified files...")
    print()

    fixed_count = 0
    error_count = 0
    already_valid = 0

    # Process only the target files with syntax errors
    for filename in TARGET_FILES:
        py_file = models_dir / filename

        if not py_file.exists():
            print(f"⚠ File not found: {filename}")
            continue

        print(f"Processing: {filename}")

        # First validate current syntax
        is_valid, msg = validate_python_syntax(py_file)
        if is_valid:
            print(f"  ✓ Already valid syntax")
            already_valid += 1
            continue

        print(f"  ⚠ Syntax error: {msg}")

        # Apply emergency fixes
        success, fixes = emergency_fix_file(py_file)
        if success and fixes:
            print(f"  🔧 Applied fixes:")
            for fix in fixes:
                print(f"    - {fix}")

            # Re-validate after fixes
            is_valid_after, msg_after = validate_python_syntax(py_file)
            if is_valid_after:
                print(f"  ✅ Syntax now valid")
                fixed_count += 1
            else:
                print(f"  ❌ Still has errors: {msg_after}")
                error_count += 1

        elif success and not fixes:
            print(f"  ℹ No fixes applied but file unchanged")
            error_count += 1
        else:
            print(f"  ❌ Could not fix: {fixes[0] if fixes else 'Unknown error'}")
            error_count += 1

        print()

    print("=== Summary ===")
    print(f"Target files processed: {len(TARGET_FILES)}")
    print(f"Files successfully fixed: {fixed_count}")
    print(f"Files already valid: {already_valid}")
    print(f"Files with remaining errors: {error_count}")

    if error_count == 0:
        print("\n🎉 All target files now have valid Python syntax!")
        return True
    else:
        print(f"\n⚠ {error_count} files still need manual attention")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
