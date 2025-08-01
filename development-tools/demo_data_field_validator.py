#!/usr/bin/env python3
"""
Comprehensive Demo Data Field Validation Script

This script validates that all field values in demo data files match
the valid selection values defined in the corresponding models.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_selection_values_from_model(model_file):
    """Extract selection field values from a Python model file."""
    selections = {}

    if not os.path.exists(model_file):
        return selections

    with open(model_file, "r") as f:
        content = f.read()

    # Find selection fields with regex
    pattern = r"(\w+)\s*=\s*fields\.Selection\(\s*\[\s*((?:\([^)]+\),?\s*)*)\s*\]"
    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        field_name = match.group(1)
        selection_content = match.group(2)

        # Extract individual selection tuples
        tuple_pattern = r'\(\s*["\']([^"\']+)["\']\s*,\s*["\'][^"\']*["\']\s*\)'
        values = re.findall(tuple_pattern, selection_content)

        if values:
            selections[field_name] = values

    return selections


def validate_demo_data_file(xml_file, models_dir):
    """Validate field values in a demo data XML file."""
    issues = []

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for record in root.findall(".//record"):
            model_name = record.get("model")
            record_id = record.get("id")

            if not model_name:
                continue

            # Convert model name to file path
            model_file = os.path.join(models_dir, f"{model_name.replace('.', '_')}.py")

            # Get valid selection values for this model
            valid_selections = extract_selection_values_from_model(model_file)

            # Check each field in the record
            for field in record.findall(".//field"):
                field_name = field.get("name")
                field_value = field.text

                if field_name in valid_selections and field_value:
                    field_value = field_value.strip()
                    valid_values = valid_selections[field_name]

                    if field_value not in valid_values:
                        issues.append(
                            {
                                "file": xml_file,
                                "record_id": record_id,
                                "model": model_name,
                                "field": field_name,
                                "invalid_value": field_value,
                                "valid_values": valid_values,
                            }
                        )

    except ET.ParseError as e:
        issues.append({"file": xml_file, "error": f"XML Parse Error: {e}"})

    return issues


def main():
    """Main validation function."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "records_management" / "data"
    models_dir = base_dir / "records_management" / "models"

    print("🔍 Comprehensive Demo Data Field Validation")
    print("=" * 50)

    all_issues = []

    # Find all XML files in data directory
    xml_files = list(data_dir.glob("*.xml"))

    for xml_file in xml_files:
        print(f"Checking: {xml_file.name}")
        issues = validate_demo_data_file(xml_file, models_dir)
        all_issues.extend(issues)

    # Report results
    print("\n📊 Validation Results:")
    print("-" * 30)

    if not all_issues:
        print("✅ All demo data field values are valid!")
        return 0

    print(f"❌ Found {len(all_issues)} validation issues:")
    print()

    for issue in all_issues:
        if "error" in issue:
            print(f"🚨 {issue['file']}: {issue['error']}")
        else:
            print(f"❌ {issue['file']}:")
            print(f"   Record: {issue['record_id']} (model: {issue['model']})")
            print(f"   Field: {issue['field']}")
            print(f"   Invalid Value: '{issue['invalid_value']}'")
            print(f"   Valid Values: {issue['valid_values']}")
            print()

    return len(all_issues)


if __name__ == "__main__":
    exit(main())
