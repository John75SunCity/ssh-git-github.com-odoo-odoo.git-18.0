#!/usr/bin/env python3
"""
Simple Regex-based Ensure One Fixer (Fallback Version)

This script uses careful regex matching to add self.ensure_one() calls
to action methods while preserving indentation and syntax.

SAFER APPROACH: More conservative regex patterns to avoid syntax corruption.
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

def detect_indentation(content: str, line_number: int) -> str:
    """Detect the indentation level of the first statement in a method."""
    lines = content.split('\n')

    # Look for the next non-empty, non-comment line after the method definition
    for i in range(line_number, len(lines)):
        line = lines[i].strip()
        if line and not line.startswith('#') and not line.startswith('"""') and not line.startswith("'''"):
            # Get the indentation of this line
            original_line = lines[i]
            indent = len(original_line) - len(original_line.lstrip())
            return ' ' * indent

    # Default to 8 spaces (2 levels of indentation)
    return '        '

def has_ensure_one_call(method_content: str) -> bool:
    """Check if method already contains self.ensure_one() call."""
    # Look for self.ensure_one() pattern
    ensure_one_pattern = r'self\.ensure_one\(\)'
    return bool(re.search(ensure_one_pattern, method_content))

def fix_action_methods_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """
    Fix action methods in a single file.

    Returns:
        Tuple of (methods_fixed_count, list_of_fixed_methods)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find action method definitions
        action_method_pattern = r'^(\s*)def\s+(action_\w+)\s*\([^)]*self[^)]*\):[^\n]*\n'
        matches = list(re.finditer(action_method_pattern, content, re.MULTILINE))

        if not matches:
            return 0, []

        # Process matches in reverse order to maintain line numbers
        fixed_methods = []
        methods_fixed = 0

        for match in reversed(matches):
            method_indent = match.group(1)
            method_name = match.group(2)
            method_start = match.end()

            # Find the end of this method
            method_end = find_method_end(content, method_start)
            method_content = content[method_start:method_end]

            # Skip if already has ensure_one
            if has_ensure_one_call(method_content):
                continue

            # Find the indentation for the method body
            body_indent = detect_indentation(content, content[:method_start].count('\n'))

            # Create the ensure_one line
            ensure_one_line = f"{body_indent}self.ensure_one()\n"

            # Insert ensure_one at the beginning of method body
            # Find the first non-empty line that's not a docstring
            lines = method_content.split('\n')
            insert_position = 0

            # Skip docstrings and empty lines
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    insert_position = i
                    break
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    # Skip entire docstring
                    quote = '"""' if stripped.startswith('"""') else "'''"
                    if stripped.count(quote) >= 2:
                        # Single line docstring
                        insert_position = i + 1
                    else:
                        # Multi-line docstring - find the end
                        for j in range(i + 1, len(lines)):
                            if quote in lines[j]:
                                insert_position = j + 1
                                break
                    break

            # Insert the ensure_one line
            new_method_lines = lines[:]
            new_method_lines.insert(insert_position, ensure_one_line.rstrip())
            new_method_content = '\n'.join(new_method_lines)

            # Replace in the original content
            content = content[:method_start] + new_method_content + content[method_end:]

            fixed_methods.append(method_name)
            methods_fixed += 1

        # Write back if we made changes
        if methods_fixed > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return methods_fixed, fixed_methods

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0, []

def find_method_end(content: str, method_start: int) -> int:
    """Find the end of a method definition."""
    lines = content[method_start:].split('\n')

    # Find the indentation level of the method definition
    # Look for the next method or class definition at the same or higher level
    method_indent_level = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue

        # Get indentation level
        indent = len(line) - len(line.lstrip())

        # Set the method indentation level on first non-empty line
        if method_indent_level is None:
            method_indent_level = indent
            continue

        # If we find a line with same or less indentation that starts with 'def' or 'class'
        if (indent <= method_indent_level and
            (stripped.startswith('def ') or stripped.startswith('class '))):
            # This is the start of the next method/class
            return method_start + sum(len(lines[j]) + 1 for j in range(i))

    # If no next method found, return end of content
    return len(content)

def scan_for_action_methods(root_path: Path) -> List[dict]:
    """Scan for action methods that need ensure_one() calls."""
    methods_needing_fix = []

    for file_path in root_path.rglob("*.py"):
        # Skip __pycache__ and other non-source directories
        if "__pycache__" in file_path.parts:
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find action methods
            action_method_pattern = r'^(\s*)def\s+(action_\w+)\s*\([^)]*self[^)]*\):'
            matches = re.finditer(action_method_pattern, content, re.MULTILINE)

            for match in matches:
                method_name = match.group(2)
                line_num = content[:match.start()].count('\n') + 1

                # Check if this method already has ensure_one
                method_start = match.end()
                method_end = find_method_end(content, method_start)
                method_content = content[method_start:method_end]

                if not has_ensure_one_call(method_content):
                    methods_needing_fix.append({
                        'file': str(file_path.relative_to(Path.cwd())),
                        'method': method_name,
                        'line': line_num
                    })

        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")
            continue

    return methods_needing_fix

def main():
    """Main execution function."""
    print("🔧 Simple Regex-based Ensure One Fixer")
    print("=" * 50)

    # Define the root path for the Records Management module
    root_path = Path("records_management")

    if not root_path.exists():
        print(f"❌ Records Management module not found at {root_path}")
        return 1

    # Scan for methods needing fix
    print("🔍 Scanning for action methods needing ensure_one()...")
    methods_needing_fix = scan_for_action_methods(root_path)

    if not methods_needing_fix:
        print("✅ All action methods already have ensure_one() calls!")
        return 0

    print(f"📋 Found {len(methods_needing_fix)} action methods needing ensure_one():")
    for method_info in methods_needing_fix[:10]:  # Show first 10
        print(f"   📄 {method_info['file']}:{method_info['line']} - {method_info['method']}()")

    if len(methods_needing_fix) > 10:
        print(f"   ... and {len(methods_needing_fix) - 10} more")

    # Ask for confirmation
    response = input(f"\n🤔 Proceed to fix {len(methods_needing_fix)} methods? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled by user.")
        return 0

    # Process files
    print("\n🔧 Processing files...")
    total_files_processed = 0
    total_methods_fixed = 0

    # Group by file
    files_to_process = {}
    for method_info in methods_needing_fix:
        file_path = method_info['file']
        if file_path not in files_to_process:
            files_to_process[file_path] = []
        files_to_process[file_path].append(method_info)

    for file_path, methods in files_to_process.items():
        methods_fixed, fixed_method_names = fix_action_methods_in_file(Path(file_path))

        if methods_fixed > 0:
            print(f"✅ {file_path}: Fixed {methods_fixed} methods ({', '.join(fixed_method_names)})")
            total_methods_fixed += methods_fixed
        else:
            print(f"⚠️  {file_path}: No methods were fixed")

        total_files_processed += 1

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"Files processed: {total_files_processed}")
    print(f"Methods fixed: {total_methods_fixed}")

    if total_methods_fixed > 0:
        print("\n🎉 Successfully added ensure_one() calls!")
        print("💡 Run syntax validation to verify changes.")
    else:
        print("\n⚠️  No methods were modified.")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
