#!/usr/bin/env python3
"""
EXTENSION-BASED DATA FILE VALIDATOR
Testing workspace - validates data files against model definitions
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_data_files_with_extensions():
    """Use extension validation approach to check data files"""

    print("🔍 EXTENSION-BASED DATA FILE VALIDATION")
    print("=" * 60)

    # Get all data files that need to be processed
    data_files = [
        "naid_compliance_data.xml",
        "feedback_survey_data.xml",
        "advanced_billing_demo.xml",
        "field_label_demo_data.xml",
        "model_records.xml",
        "fsm_automated_actions.xml",
        "document_retrieval_rates.xml",
        "user_setup.xml",
    ]

    base_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/data"
    )
    issues_found = []

    for data_file in data_files:
        file_path = base_path / data_file
        if not file_path.exists():
            print(f"⚠️  {data_file} - File not found")
            continue

        print(f"\n📄 Analyzing {data_file}...")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract model references and field usage
            for record in root.findall(".//record"):
                model_name = record.get("model")
                record_id = record.get("id")

                if model_name:
                    # Get all field references in this record
                    fields_used = []
                    for field_elem in record.findall("field"):
                        field_name = field_elem.get("name")
                        if field_name:
                            fields_used.append(field_name)

                    # Check for potentially problematic patterns
                    if model_name.startswith("records."):
                        # This is our custom model - needs validation
                        print(
                            f"   🔍 {model_name} record '{record_id}' uses fields: {fields_used}"
                        )

                        # Flag potential issues
                        for field_name in fields_used:
                            if field_name in [
                                "location_type",
                                "access_level",
                                "climate_controlled",
                            ]:
                                print(f"      ❓ Field '{field_name}' needs validation")

        except ET.ParseError as e:
            issues_found.append(f"❌ {data_file}: XML Parse Error - {e}")
        except Exception as e:
            issues_found.append(f"❌ {data_file}: Analysis Error - {e}")

    # Report findings
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 60)

    if issues_found:
        print("🚨 Issues Found:")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print("✅ All data files parsed successfully")

    print(f"\n💡 NEXT STEPS:")
    print("1. Create extension-validated model copies")
    print("2. Let extensions suggest missing fields")
    print("3. Compare with current implementations")
    print("4. Apply fixes to main development files")


def extract_field_references_from_data():
    """Extract all field references from data files for validation"""

    print("\n🔍 EXTRACTING FIELD REFERENCES FROM DATA FILES")
    print("=" * 60)

    base_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/data"
    )
    model_fields = {}

    # Focus on the problematic file first
    problem_file = base_path / "model_records.xml"

    if problem_file.exists():
        try:
            tree = ET.parse(problem_file)
            root = tree.getroot()

            for record in root.findall(".//record"):
                model_name = record.get("model")
                if model_name == "records.location":
                    print(f"\n📋 Fields used in records.location data:")
                    for field_elem in record.findall("field"):
                        field_name = field_elem.get("name")
                        field_value = field_elem.text or field_elem.get("eval", "")
                        print(f"   - {field_name}: {field_value}")

        except Exception as e:
            print(f"❌ Error analyzing model_records.xml: {e}")


if __name__ == "__main__":
    validate_data_files_with_extensions()
    extract_field_references_from_data()
