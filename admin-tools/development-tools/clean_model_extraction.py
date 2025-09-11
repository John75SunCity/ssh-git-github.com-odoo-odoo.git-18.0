#!/usr/bin/env python3
"""
Clean model extraction - filter out invalid patterns and get accurate model list
"""

import os
import re
from pathlib import Path

def extract_clean_models(python_files):
    """Extract only valid model names from Python files"""
    valid_models = set()

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Find all _name = 'model.name' patterns
                name_patterns = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)

                for pattern in name_patterns:
                    # Filter out invalid patterns
                    pattern = pattern.strip()
                    if (pattern and
                        '.' in pattern and  # Must contain dots (valid model format)
                        not pattern.startswith('%') and  # Not a format string
                        not pattern.startswith(',') and  # Not a comma
                        not pattern.startswith(' ') and  # Not whitespace
                        not pattern.startswith('-') and  # Not a dash
                        len(pattern) > 3 and  # Must be reasonably long
                        not any(char in pattern for char in ['[', ']', '{', '}', '(', ')'])  # No brackets
                        ):
                        valid_models.add(pattern)

        except Exception as e:
            print(f"Error reading {py_file}: {e}")

    return valid_models

def main():
    # Paths
    workspace_root = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    models_dir = workspace_root / "records_management" / "models"

    # Find all Python files in models directory
    python_files = list(models_dir.glob("*.py"))

    print("🔍 Extracting clean model list...")
    print(f"Python files found: {len(python_files)}")
    print()

    # Extract clean models
    clean_models = extract_clean_models(python_files)

    print(f"📊 Clean models found: {len(clean_models)}")
    print()

    print("🎯 Valid models:")
    for model in sorted(clean_models):
        print(f"  - {model}")

    print("\n📋 Summary:")
    print(f"  Total clean models: {len(clean_models)}")

    # Save to file for reference
    output_file = workspace_root / "clean_models_list.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Clean Records Management Models\n")
        f.write(f"# Total: {len(clean_models)}\n")
        f.write("# Generated from Python files\n\n")
        for model in sorted(clean_models):
            f.write(f"{model}\n")

    print(f"💾 Saved clean model list to: {output_file}")

if __name__ == "__main__":
    main()
