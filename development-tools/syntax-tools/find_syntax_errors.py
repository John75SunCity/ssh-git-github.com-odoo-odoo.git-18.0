#!/usr/bin/env python3
"""
Find files with syntax errors - Conservative approach

This script identifies Python files with syntax errors WITHOUT making any changes.
Safe to run - only reports issues, doesn't modify anything.
"""

import os
from pathlib import Path


def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to compile the content
        compile(content, str(file_path), "exec")
        return True, "OK"

    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Find all Python files with syntax errors"""

    # Use the correct local path for the models directory
    models_dir = Path(__file__).parent.parent.parent / "records_management" / "models"

    if not models_dir.exists():
        print(f"Error: Directory {models_dir} does not exist")
        return

    print("=== Syntax Error Detection ===")
    print("Scanning all Python files for syntax errors...")
    print()

    python_files = [f for f in models_dir.glob("*.py") if f.name != "__init__.py"]
    error_files = []

    # Check all Python files
    for py_file in python_files:
        is_valid, msg = check_syntax(py_file)
        if not is_valid:
            error_files.append((py_file.name, msg))
            print(f"❌ {py_file.name}: {msg}")

    print()
    print("=== Summary ===")
    print(f"Total Python files checked: {len(python_files)}")
    print(f"Files with syntax errors: {len(error_files)}")
    print(f"Files with valid syntax: {len(python_files) - len(error_files)}")

    if error_files:
        print(f"\n📋 Files needing fixes:")
        for filename, _ in error_files:
            print(f"  - {filename}")
    else:
        print(f"\n🎉 All files have valid syntax!")

    return error_files


if __name__ == "__main__":
    error_files = main()
