#!/usr/bin/env python3
"""
Fix syntax errors in model files caused by unmatched closing parentheses.

This script fixes the pattern:
)    some_code
to:
    some_code

And also fixes:
)
^
SyntaxError: unmatched ')'
"""

import os
import re


def fix_unmatched_parentheses(content):
    """Fix unmatched closing parentheses at start of lines"""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Pattern: )    some_code -> just some_code
        if re.match(r"^\s*\)\s+\w", line):
            # Remove the `) ` at the start and keep the rest
            fixed_line = re.sub(r"^\s*\)\s+", "    ", line)
            print(f"  Fixed line {i+1}: '{line.strip()}' -> '{fixed_line.strip()}'")
            fixed_lines.append(fixed_line)
        # Pattern: )$ (just closing paren on its own line)
        elif re.match(r"^\s*\)\s*$", line):
            # Check if the next line looks like it should be part of a field definition
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if (
                    next_line.startswith("@api.")
                    or "= fields." in next_line
                    or next_line.startswith("def ")
                    or next_line.startswith("class ")
                    or next_line.startswith("#")
                ):
                    print(f"  Removed orphaned closing paren at line {i+1}: '{line}'")
                    continue  # Skip this line entirely
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_file(filepath):
    """Fix syntax errors in a single file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixed_content = fix_unmatched_parentheses(content)

        if fixed_content != original_content:
            print(f"Fixing {filepath}...")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Fix all Python files in the models directory"""
    models_dir = "records_management/models"

    if not os.path.exists(models_dir):
        print(f"Directory {models_dir} not found!")
        return

    fixed_count = 0

    # Get all Python files
    python_files = [f for f in os.listdir(models_dir) if f.endswith(".py")]

    print(f"Found {len(python_files)} Python files to check...")

    for filename in sorted(python_files):
        filepath = os.path.join(models_dir, filename)
        if fix_file(filepath):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files with syntax errors!")
    print("🔧 Run syntax check again to verify fixes...")


if __name__ == "__main__":
    main()
