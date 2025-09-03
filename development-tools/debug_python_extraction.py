#!/usr/bin/env python3
"""
Debug Python model extraction to see what patterns are being found
"""

import os
import re
from pathlib import Path

def debug_python_extraction(python_files):
    """Debug what patterns are found in Python files"""
    all_patterns = []

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Find all _name = 'model.name' patterns
                name_patterns = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)

                if name_patterns:
                    print(f"\n📄 {py_file.name}:")
                    for pattern in name_patterns:
                        print(f"  Found: '{pattern}'")
                        all_patterns.append(pattern)

        except Exception as e:
            print(f"Error reading {py_file}: {e}")

    return all_patterns

def main():
    # Paths
    workspace_root = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    models_dir = workspace_root / "records_management" / "models"

    # Find all Python files in models directory
    python_files = list(models_dir.glob("*.py"))

    print("🔍 Debugging Python model extraction...")
    print(f"Python files found: {len(python_files)}")
    print()

    # Debug extraction
    all_patterns = debug_python_extraction(python_files)

    print(f"\n📊 Total patterns found: {len(all_patterns)}")

    # Filter out invalid patterns
    valid_models = [p for p in all_patterns if p and not p.startswith('%') and not p.startswith(',') and len(p.strip()) > 0]
    invalid_patterns = [p for p in all_patterns if not (p and not p.startswith('%') and not p.startswith(',') and len(p.strip()) > 0)]

    print(f"✅ Valid model names: {len(valid_models)}")
    print(f"❌ Invalid patterns: {len(invalid_patterns)}")

    if invalid_patterns:
        print("\n🚨 Invalid patterns found:")
        for pattern in invalid_patterns[:10]:  # Show first 10
            print(f"  - '{pattern}'")
        if invalid_patterns and len(invalid_patterns) > 10:
            print(f"  ... and {len(invalid_patterns) - 10} more")

    print("\n🎯 Valid models (first 20):")
    for model in valid_models[:20]:
        print(f"  - {model}")

if __name__ == "__main__":
    main()
