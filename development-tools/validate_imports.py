#!/usr/bin/env python3
"""
Import Validation Script
Checks all imports in models/__init__.py against actual files
"""

import os
import re


def get_actual_files():
    """Get list of actual Python files in models directory"""
    # Get script directory and navigate to workspace root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    models_dir = os.path.join(workspace_root, "records_management", "models")
    files = []

    for filename in os.listdir(models_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            files.append(filename[:-3])  # Remove .py extension

    return sorted(files)


def get_imported_files():
    """Get list of files imported in __init__.py"""
    # Get script directory and navigate to workspace root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    init_file = os.path.join(workspace_root, "records_management", "models", "__init__.py")
    imports = []

    try:
        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: {init_file} not found")
        return []

    # Find all "from . import" statements
    import_lines = re.findall(r"from \. import (.+)", content)

    for line in import_lines:
        # Handle multiple imports on one line
        modules = [m.strip() for m in line.split(",")]
        imports.extend(modules)

    return sorted(imports)


def main():
    print("🔍 Validating model imports...\n")

    actual_files = get_actual_files()
    imported_files = get_imported_files()

    print(f"📁 Actual files found: {len(actual_files)}")
    print(f"📋 Imported files: {len(imported_files)}\n")

    # Find missing files (imported but don't exist)
    missing = [f for f in imported_files if f not in actual_files]
    if missing:
        print("❌ Missing files (imported but don't exist):")
        for f in missing:
            print(f"  - {f}")
        print()

    # Find unused files (exist but not imported)
    unused = [f for f in actual_files if f not in imported_files]
    if unused:
        print("⚠️  Files not imported:")
        for f in unused:
            print(f"  - {f}")
        print()

    if not missing and not unused:
        print("✅ All imports are valid!")
    else:
        print(f"📊 Summary: {len(missing)} missing, {len(unused)} unused")

        if missing:
            print("\n🔧 Suggested fixes for missing imports:")
            for f in missing:
                print(f"  Remove: from . import {f}")


if __name__ == "__main__":
    main()
