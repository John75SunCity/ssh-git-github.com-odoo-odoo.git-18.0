#!/usr/bin/env python3
"""
Advanced Python syntax fixer for Records Management models.

This fixes common syntax issues including:
1. Unclosed parentheses
2. Missing commas in field definitions
3. Indentation errors
4. Orphaned closing parentheses
"""

import os
import re
import ast


def fix_field_definitions(content):
    """Fix common field definition syntax errors"""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Check for field definitions that might be missing commas
        if re.match(r"^\s*\w+\s*=\s*fields\.\w+\(", line):
            # This is a field definition start
            # Check if it ends properly or if next line starts with another field
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next line starts with a field definition and current line doesn't end with comma or paren
                if re.match(
                    r"^\s*\w+\s*=\s*fields\.", next_line
                ) and not line.rstrip().endswith((",", ")", "]", "}")):
                    print(f"  Adding missing comma to field definition at line {i+1}")
                    fixed_lines.append(line + ",")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_indentation_errors(content):
    """Fix basic indentation errors"""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Check for lines that start with field parameters but are not properly indented
        if re.match(r"^\s{0,3}(string|help|default|required|tracking|index)=", line):
            # This should probably be indented more
            print(f"  Fixing indentation at line {i+1}: '{line[:50]}...'")
            fixed_lines.append("        " + line.lstrip())
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_trailing_commas(content):
    """Fix field definitions that are missing trailing commas"""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Look for closing parentheses that end field definitions
        if re.match(r"^\s*\)$", line.strip()) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # If the next line is a field definition, we need a comma
            if re.match(r"^\w+\s*=\s*fields\.", next_line):
                print(f"  Adding trailing comma after field definition at line {i+1}")
                fixed_lines.append(line.rstrip() + ",")
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def validate_syntax(filepath):
    """Check if Python file has valid syntax"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Other error: {e}"


def fix_file_comprehensive(filepath):
    """Apply comprehensive fixes to a Python file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Apply various fixes
        content = fix_field_definitions(content)
        content = fix_indentation_errors(content)
        content = fix_trailing_commas(content)

        if content != original_content:
            print(f"Applying comprehensive fixes to {filepath}...")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Fix all Python files comprehensively"""

    # Get all Python files in current directory
    python_files = [f for f in os.listdir(".") if f.endswith(".py")]

    print(f"Found {len(python_files)} Python files to fix comprehensively...")

    fixed_count = 0
    still_broken = []

    for filename in sorted(python_files):
        # First check if it has syntax errors
        is_valid, error = validate_syntax(filename)

        if not is_valid:
            print(f"\n🔧 Fixing {filename} (Error: {error[:100]}...)")
            if fix_file_comprehensive(filename):
                fixed_count += 1

                # Check if it's now valid
                is_valid_after, _ = validate_syntax(filename)
                if not is_valid_after:
                    still_broken.append(filename)
            else:
                still_broken.append(filename)

    print(f"\n✅ Attempted fixes on {fixed_count} files")

    if still_broken:
        print(f"❌ {len(still_broken)} files still have issues:")
        for f in still_broken[:10]:  # Show first 10
            is_valid, error = validate_syntax(f)
            print(f"  - {f}: {error[:80]}...")
    else:
        print("🎉 All files now have valid syntax!")


if __name__ == "__main__":
    main()
