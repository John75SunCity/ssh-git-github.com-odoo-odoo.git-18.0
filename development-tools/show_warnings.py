#!/usr/bin/env python3
"""
Show detailed warnings from the XML validator
"""

import sys
import os
from pathlib import Path
from collections import defaultdict

# Import the validator
sys.path.insert(0, os.path.dirname(__file__))
from advanced_xml_model_validator import OdooFieldExtractor, XMLDataValidator


def main():
    print("🔍 Getting detailed warnings from XML validator...")

    records_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    # Extract fields from models
    print("📊 Phase 1: Extracting field definitions from Python models...")
    field_extractor = OdooFieldExtractor()

    model_files_processed = 0
    for model_dir in ["models", "wizards"]:
        model_path = records_path / model_dir
        if model_path.exists():
            for py_file in model_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    field_extractor.parse_model_file(py_file)
                    model_files_processed += 1

    print(f"✅ Found {len(field_extractor.models)} models")

    # Create validator
    validator = XMLDataValidator(field_extractor)

    # Find all XML files
    all_warnings = []

    for data_dir in ["data", "demo"]:
        data_path = records_path / data_dir
        if data_path.exists():
            for xml_file in data_path.glob("*.xml"):
                _, warnings = validator.validate_xml_file(xml_file)
                all_warnings.extend(warnings)

    print(f"\n⚠️  DETAILED WARNINGS FOUND: {len(all_warnings)}")
    print("=" * 60)

    if all_warnings:
        # Group warnings by file
        warnings_by_file = defaultdict(list)
        for warning in all_warnings:
            warnings_by_file[warning["file"]].append(warning)

        for file_name, file_warnings in warnings_by_file.items():
            print(f"\n📁 File: {file_name} ({len(file_warnings)} warnings)")

            for warning in file_warnings:
                print(f"   ⚠️  Record: {warning['record_id']}")
                print(f"      Model: {warning['model']}")
                print(f"      Issue: {warning.get('issue', 'Unknown')}")
                if warning.get("line"):
                    print(f"      Line: {warning['line']}")
                if warning.get("details"):
                    print(f"      Details: {warning['details']}")
                print()
    else:
        print("✅ No warnings found!")


if __name__ == "__main__":
    main()
