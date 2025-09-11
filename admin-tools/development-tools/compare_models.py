#!/usr/bin/env python3
"""
Compare models found in CSV vs Python files to identify discrepancies
"""

import os
import csv
import re
from pathlib import Path

def extract_models_from_csv(csv_path):
    """Extract model names from CSV file"""
    models_in_csv = set()

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header

            for row in reader:
                if row and len(row) >= 3:
                    # Extract model name from column 3 (format: model_records_management_model_name)
                    model_entry = row[2].strip()
                    if model_entry.startswith('model_records_management_'):
                        model_name = model_entry[25:]  # Remove 'model_records_management_' prefix (25 chars)
                        # Convert underscores back to dots
                        model_name = model_name.replace('_', '.')
                        models_in_csv.add(model_name)

    except Exception as e:
        print(f"Error reading CSV: {e}")

    return models_in_csv

def extract_models_from_python(python_files):
    """Extract clean model names from Python files"""
    models_in_python = set()

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
                        models_in_python.add(pattern)

        except Exception as e:
            print(f"Error reading {py_file}: {e}")

    return models_in_python

def main():
    # Paths
    workspace_root = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    csv_path = workspace_root / "records_management" / "security" / "ir.model.access.csv"
    models_dir = workspace_root / "records_management" / "models"

    # Find all Python files in models directory
    python_files = list(models_dir.glob("*.py"))

    print("🔍 Analyzing model coverage...")
    print(f"CSV file: {csv_path}")
    print(f"Python files found: {len(python_files)}")
    print()

    # Extract models
    models_in_csv = extract_models_from_csv(csv_path)
    models_in_python = extract_models_from_python(python_files)

    print(f"📊 Models in CSV: {len(models_in_csv)}")
    print(f"📊 Models in Python: {len(models_in_python)}")
    print()

    # Find missing models
    missing_in_csv = models_in_python - models_in_csv
    extra_in_csv = models_in_csv - models_in_python

    print("❌ Models MISSING from CSV (need security rules):")
    if missing_in_csv:
        for model in sorted(missing_in_csv):
            print(f"  - {model}")
        print(f"\nTotal missing: {len(missing_in_csv)}")
    else:
        print("  ✅ None missing!")

    print("\n⚠️  Models in CSV but NOT in Python (orphaned rules):")
    if extra_in_csv:
        for model in sorted(extra_in_csv):
            print(f"  - {model}")
        print(f"\nTotal orphaned: {len(extra_in_csv)}")
    else:
        print("  ✅ None orphaned!")

    print("\n📋 Summary:")
    print(f"  Total models in Python: {len(models_in_python)}")
    print(f"  Total models in CSV: {len(models_in_csv)}")
    print(f"  Missing from CSV: {len(missing_in_csv)}")
    print(f"  Orphaned in CSV: {len(extra_in_csv)}")

    if missing_in_csv:
        print("\n🔧 Next steps:")
        print("  1. Add security rules for missing models")
        print("  2. Run validation again")
        print("  3. Test module loading")

if __name__ == "__main__":
    main()
