#!/usr/bin/env python3
"""
Debug script to check what models are found by validation vs CSV
"""

import os
import re
from pathlib import Path

def debug_model_extraction():
    """Debug model extraction from both CSV and Python files"""

    module_path = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management")

    # 1. Extract models from CSV
    csv_models = set()
    access_file = module_path / "security" / "ir.model.access.csv"
    if access_file.exists():
        with open(access_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Skip header
        data_lines = [line.strip() for line in lines[1:] if line.strip()]

        for line in data_lines:
            parts = line.split(",")
            if parts and len(parts) >= 3:
                model_ref = parts[2].strip()  # model_id:id column
                if model_ref.startswith("model_"):
                    model_name = model_ref[6:]  # Remove 'model_' prefix
                    csv_models.add(model_name)

    print(f"📊 Models found in CSV: {len(csv_models)}")
    print("Sample CSV models:", sorted(list(csv_models))[:10])

    # 2. Extract models from Python files
    python_models = set()
    python_files = list(module_path.glob("models/*.py"))
    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find model names - same pattern as validation script
            name_pattern = r'^\s*_name\s*=\s*["\']([^"\']+)["\']'
            matches = re.findall(name_pattern, content, re.MULTILINE)

            for model_name in matches:
                python_models.add(model_name)

        except Exception as e:
            print(f"Error parsing {py_file.name}: {e}")

    print(f"\n📊 Models found in Python files: {len(python_models)}")
    print("Sample Python models:", sorted(list(python_models))[:10])

    # 3. Find differences
    missing_in_csv = python_models - csv_models
    extra_in_csv = csv_models - python_models

    print(f"\n❌ Models in Python but missing from CSV ({len(missing_in_csv)}):")
    for model in sorted(missing_in_csv):
        print(f"  {model}")

    print(f"\n⚠️ Models in CSV but not found in Python ({len(extra_in_csv)}):")
    for model in sorted(extra_in_csv):
        print(f"  {model}")

    # 4. Check for regex issues
    print("\n🔍 Checking regex pattern matches:")
    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '_name' in line and ('=' in line):
                    print(f"  {py_file.name}:{i+1}: {line.strip()}")

        except Exception as e:
            print(f"Error checking {py_file.name}: {e}")

if __name__ == "__main__":
    debug_model_extraction()
