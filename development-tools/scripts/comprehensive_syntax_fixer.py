#!/usr/bin/env python3
"""
🔧 COMPREHENSIVE SYNTAX FIXER
============================
Fixes all syntax errors introduced by the batch field/action generation process.
Handles unterminated strings, invalid f-strings, and line continuation issues.
"""

import os
import re
import ast
from pathlib import Path


def fix_file_syntax(file_path):
    """Fix common syntax errors in a Python file"""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Cannot read {file_path}: {e}")
        return False

    original_content = content

    # 1. Fix backslash-n patterns
    content = content.replace("\\n    #", "\n    #")
    content = content.replace("\\n    def", "\n    def")
    content = content.replace('\\n    """', '\n    """')
    content = content.replace('\\n        """', '\n        """')
    content = content.replace("\\n        self", "\n        self")
    content = content.replace("\\n        return", "\n        return")
    content = content.replace("\\n        }", "\n        }")

    # 2. Fix unterminated strings and f-strings
    lines = content.split("\n")
    fixed_lines = []
    in_multiline_string = False
    string_delimiter = None

    for i, line in enumerate(lines):
        original_line = line

        # Skip if we're in a multiline string
        if in_multiline_string:
            if string_delimiter in line:
                in_multiline_string = False
                string_delimiter = None
            fixed_lines.append(line)
            continue

        # Check for multiline string start
        if '"""' in line and line.count('"""') == 1:
            in_multiline_string = True
            string_delimiter = '"""'
            fixed_lines.append(line)
            continue
        elif "'''" in line and line.count("'''") == 1:
            in_multiline_string = True
            string_delimiter = "'''"
            fixed_lines.append(line)
            continue

        # Fix unterminated single/double quotes
        if '"' in line:
            quote_count = line.count('"')
            # If odd number of quotes, there's an unterminated string
            if quote_count % 2 == 1:
                # Find the last quote and check if line should end with quote
                last_quote_pos = line.rfind('"')
                after_quote = line[last_quote_pos + 1 :].strip()

                # If there's meaningful content after the quote, add closing quote
                if (
                    after_quote
                    and not after_quote.startswith(",")
                    and not after_quote.startswith(")")
                ):
                    line = line[: last_quote_pos + 1] + '", ' + after_quote
                elif not after_quote:
                    # Line probably should end with a quote
                    line = line + '"'

        # Fix f-string issues
        if line.strip().startswith('f"') or line.strip().startswith("f'"):
            # Check for unterminated f-string
            if line.strip().startswith('f"') and line.count('"') % 2 == 1:
                if not line.endswith('"'):
                    line = line + '"'
            elif line.strip().startswith("f'") and line.count("'") % 2 == 1:
                if not line.endswith("'"):
                    line = line + "'"

        # Fix lines that end with unexpected characters
        if line.endswith("\\"):
            # Remove trailing backslash if it's not needed
            line = line.rstrip("\\").rstrip()

        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # 3. Fix common syntax patterns
    # Fix method definitions that got mangled
    content = re.sub(
        r'def\s+(\w+)\s*\(\s*self\s*\)\s*:\s*"""(.+?)"""\s*self\.ensure_one\(\)',
        r'def \1(self):\n        """\2"""\n        self.ensure_one()',
        content,
        flags=re.DOTALL,
    )

    # Fix return statements that got mangled
    content = re.sub(
        r'return\s*\{\s*"type":', r'return {\n            "type":', content
    )
    content = re.sub(
        r'"context":\s*self\.env\.context,?\s*\}',
        r'"context": self.env.context,\n        }',
        content,
    )

    # 4. Remove duplicate field definitions (common issue)
    lines = content.split("\n")
    seen_fields = set()
    cleaned_lines = []

    for line in lines:
        # Check if this is a field definition
        field_match = re.match(r"\s*(\w+)\s*=\s*fields\.", line)
        if field_match:
            field_name = field_match.group(1)
            if field_name in seen_fields:
                # Skip duplicate field
                continue
            seen_fields.add(field_name)
        cleaned_lines.append(line)

    content = "\n".join(cleaned_lines)

    # 5. Try to validate syntax
    try:
        ast.parse(content)
        syntax_valid = True
    except SyntaxError as e:
        print(f"⚠️  Still has syntax error in {file_path}: {e}")
        syntax_valid = False

    # Write the fixed content if it changed
    if content != original_content:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            status = "✅ FIXED" if syntax_valid else "⚠️  PARTIAL"
            print(f"{status}: {file_path}")
            return syntax_valid
        except Exception as e:
            print(f"❌ Cannot write {file_path}: {e}")
            return False
    else:
        print(f"✓ OK: {file_path}")
        return syntax_valid


def main():
    """Fix syntax errors in all Python model files"""

    print("🔧 COMPREHENSIVE SYNTAX FIXER")
    print("=" * 50)

    # Change to correct directory
    if os.path.exists("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"):
        os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")

    models_dir = Path("records_management/models")

    if not models_dir.exists():
        print("❌ Models directory not found!")
        return False

    # Get all Python files with syntax errors
    error_files = []
    all_files = list(models_dir.glob("*.py"))

    print(f"\n📊 Checking {len(all_files)} Python files for syntax errors...")

    for py_file in all_files:
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file, "r") as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError:
            error_files.append(py_file)

    print(f"🔍 Found {len(error_files)} files with syntax errors")

    if not error_files:
        print("🎉 No syntax errors found!")
        return True

    print(f"\n🛠️  Fixing {len(error_files)} files...")

    fixed_count = 0
    partial_count = 0
    failed_count = 0

    for error_file in error_files:
        result = fix_file_syntax(error_file)
        if result:
            fixed_count += 1
        elif result is None:
            failed_count += 1
        else:
            partial_count += 1

    print(f"\n📊 SYNTAX FIXING RESULTS:")
    print(f"   ✅ Fully Fixed: {fixed_count}")
    print(f"   ⚠️  Partially Fixed: {partial_count}")
    print(f"   ❌ Failed: {failed_count}")

    # Verify final state
    print(f"\n🔍 Final verification...")
    remaining_errors = 0

    for py_file in all_files:
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file, "r") as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            remaining_errors += 1
            print(f"   ❌ {py_file.name}: {e}")

    if remaining_errors == 0:
        print("🎉 ALL SYNTAX ERRORS FIXED!")
        return True
    else:
        print(f"⚠️  {remaining_errors} files still have syntax errors")
        return False


if __name__ == "__main__":
    main()
