#!/usr/bin/env python3
"""
Emergency Syntax Fixer - Fix the most critical deployment-blocking syntax errors

This script fixes common Python syntax errors in Odoo model files to make
them parseable and deployable. It focuses on the most critical issues that
prevent module loading.

Key Features:
- Fix missing colons in function/class definitions
- Repair broken field definitions
- Fix orphaned parameters
- Handle empty Selection fields
- Remove trailing commas in wrong places
- Basic error recovery for malformed code

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import os
import re
from pathlib import Path


def emergency_fix_file(file_path):
    """Apply emergency fixes to make file parseable by Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes_applied = []

        # Fix 1: Add missing colons to function/class definitions
        # Pattern: def function_name() <-- missing colon
        content = re.sub(
            r"(def\s+\w+\([^)]*\))\s*$", r"\1:", content, flags=re.MULTILINE
        )
        content = re.sub(
            r"(class\s+\w+\([^)]*\))\s*$", r"\1:", content, flags=re.MULTILINE
        )
        if content != original_content:
            fixes_applied.append("Added missing colons to function/class definitions")
            original_content = content

        # Fix 2: Fix missing colons in if/for/while/try statements
        content = re.sub(
            r"(^\s*(?:if|elif|else|for|while|try|except|finally|with)\b[^:]*?)\s*$",
            r"\1:",
            content,
            flags=re.MULTILINE,
        )
        if content != original_content:
            fixes_applied.append("Added missing colons to control statements")
            original_content = content

        # Fix 3: Remove orphaned 'pass' statements
        content = re.sub(r"\n\s*pass\s*\n(\s*)(\w+)", r"\n\1\2", content)
        if content != original_content:
            fixes_applied.append("Removed orphaned pass statements")
            original_content = content

        # Fix 4: Fix broken field definitions
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            # Check for incomplete field definitions
            if re.match(
                r"\s*\w+\s*=\s*fields\.\w+\(", line
            ) and not line.rstrip().endswith(")"):

                # Count opening and closing parentheses
                open_parens = line.count("(")
                close_parens = line.count(")")

                if open_parens > close_parens:
                    # Add missing closing parenthesis
                    if line.rstrip().endswith(","):
                        line = line.rstrip()[:-1] + ")"
                    else:
                        line = line.rstrip() + ")"
                    fixes_applied.append(
                        f"Fixed incomplete field definition on line {i+1}"
                    )

            # Fix orphaned field parameters
            elif (
                line.strip().startswith(
                    ("string=", "help=", "required=", "default=", "ondelete=")
                )
                and i > 0
                and not line.strip().endswith(")")
            ):

                prev_line = fixed_lines[-1] if fixed_lines else ""
                if (
                    "fields." in prev_line
                    and not prev_line.rstrip().endswith(")")
                    and not line.strip().endswith(")")
                ):
                    line = line.rstrip() + ")"
                    fixes_applied.append(f"Fixed orphaned parameter on line {i+1}")

            fixed_lines.append(line)

        if fixes_applied:
            content = "\n".join(fixed_lines)

        # Fix 5: Handle empty Selection fields
        pattern = r"fields\.Selection\(\[\)\s*,"
        if re.search(pattern, content):
            content = re.sub(
                pattern,
                "fields.Selection([('draft', 'Draft')], default='draft'),",
                content,
            )
            fixes_applied.append("Fixed empty Selection fields")

        # Fix 6: Remove trailing commas before closing parentheses
        content = re.sub(r",\s*\)", ")", content)
        if content != original_content:
            fixes_applied.append("Removed trailing commas")
            original_content = content

        # Fix 7: Fix unterminated string literals (basic fix)
        # Look for lines ending with unterminated quotes
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.count('"') % 2 == 1 and not line.strip().endswith("\\"):
                lines[i] = line + '"'
                fixes_applied.append(f"Fixed unterminated string on line {i+1}")
            elif line.count("'") % 2 == 1 and not line.strip().endswith("\\"):
                lines[i] = line + "'"
                fixes_applied.append(f"Fixed unterminated string on line {i+1}")

        content = "\n".join(lines)

        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
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
    """Apply emergency fixes to all Python files"""
    models_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")

    if not models_dir.exists():
        print(f"Error: Directory {models_dir} does not exist")
        return False

    print("=== Emergency Syntax Fixer ===")
    print("Applying critical fixes to make module loadable...")
    print()

    python_files = [f for f in models_dir.glob("*.py") if f.name != "__init__.py"]
    fixed_count = 0
    error_count = 0

    # Process all Python files
    for py_file in python_files:
        print(f"Processing: {py_file.name}")

        # First validate current syntax
        is_valid, msg = validate_python_syntax(py_file)
        if is_valid:
            print(f"  ✓ Already valid syntax")
            continue

        print(f"  ⚠ Syntax error: {msg}")

        # Apply emergency fixes
        success, fixes = emergency_fix_file(py_file)
        if success and fixes:
            print(f"  🔧 Applied fixes: {', '.join(fixes)}")

            # Re-validate after fixes
            is_valid_after, msg_after = validate_python_syntax(py_file)
            if is_valid_after:
                print(f"  ✅ Syntax now valid")
                fixed_count += 1
            else:
                print(f"  ❌ Still has errors: {msg_after}")
                error_count += 1

        elif success and not fixes:
            print(f"  ℹ No fixes needed")
        else:
            print(f"  ❌ Could not fix: {fixes[0] if fixes else 'Unknown error'}")
            error_count += 1

        print()

    print("=== Summary ===")
    print(f"Files processed: {len(python_files)}")
    print(f"Files successfully fixed: {fixed_count}")
    print(f"Files with remaining errors: {error_count}")
    print(f"Files already valid: {len(python_files) - fixed_count - error_count}")

    if error_count == 0:
        print("\n🎉 All files now have valid Python syntax!")
        return True
    else:
        print(f"\n⚠ {error_count} files still need manual attention")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
