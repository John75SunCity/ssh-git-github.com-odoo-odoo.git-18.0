#!/usr/bin/env python3
"""
COMPREHENSIVE DATA FILE VALIDATION
Analyzes all data files against model definitions to find field mismatches
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_data_files():
    """Validate all data files against expected model fields"""

    base_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    data_dir = base_path / "data"
    models_dir = base_path / "models"

    issues = []
    warnings = []

    print("🔍 COMPREHENSIVE DATA FILE VALIDATION")
    print("=" * 70)

    # Get all model field definitions
    model_fields = get_model_fields(models_dir)

    # Validate each data file
    data_files = [
        "naid_compliance_data.xml",
        "paper_products.xml",
        "portal_mail_templates.xml",
        "products.xml",
        "scheduled_actions.xml",
        "sequence.xml",
        "storage_fee.xml",
        "tag_data.xml",
        "user_setup.xml",
        "model_records.xml",  # This is where the current error is
        "feedback_survey_data.xml",
        "advanced_billing_demo.xml",
        "field_label_demo_data.xml",
    ]

    for data_file in data_files:
        file_path = data_dir / data_file
        if file_path.exists():
            print(f"\n📄 Validating: {data_file}")
            file_issues = validate_single_data_file(file_path, model_fields)
            if file_issues:
                issues.extend(file_issues)
            else:
                print(f"   ✅ All field references valid")
        else:
            warnings.append(f"⚠️ Data file not found: {data_file}")

    # Summary
    print(f"\n📊 DATA FILE VALIDATION SUMMARY")
    print("=" * 70)
    print(f"🚨 Critical Issues: {len(issues)}")
    print(f"⚠️  Warnings: {len(warnings)}")

    if issues:
        print(f"\n🚨 CRITICAL FIELD ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")

    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")

    if not issues:
        print(f"\n🎉 NO CRITICAL DATA FILE ISSUES FOUND!")

    return issues, warnings


def get_model_fields(models_dir):
    """Extract field definitions from all model files"""
    model_fields = {}

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find model name
        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            model_name = name_match.group(1)

            # Find all field definitions
            field_pattern = r"(\w+)\s*=\s*fields\."
            fields = re.findall(field_pattern, content)

            model_fields[model_name] = set(fields)

    # Add common Odoo fields that always exist
    common_fields = {
        "id",
        "create_date",
        "write_date",
        "create_uid",
        "write_uid",
        "__last_update",
    }
    for model_name in model_fields:
        model_fields[model_name].update(common_fields)

    return model_fields


def validate_single_data_file(file_path, model_fields):
    """Validate a single XML data file"""
    issues = []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Find all record elements
        for record in root.findall(".//record"):
            model = record.get("model")
            record_id = record.get("id", "unknown")

            if model and model in model_fields:
                # Check each field in this record
                for field_elem in record.findall("field"):
                    field_name = field_elem.get("name")
                    if field_name and field_name not in model_fields[model]:
                        issues.append(
                            f"❌ {file_path.name}: Model '{model}' missing field '{field_name}' (record: {record_id})"
                        )
            elif model and model not in model_fields:
                # Skip core Odoo models that we don't have definitions for
                core_models = [
                    "ir.cron",
                    "ir.sequence",
                    "product.product",
                    "mail.template",
                    "sms.template",
                    "res.users",
                ]
                if model not in core_models:
                    issues.append(
                        f"❌ {file_path.name}: Unknown model '{model}' (record: {record_id})"
                    )

    except ET.ParseError as e:
        issues.append(f"❌ {file_path.name}: XML parsing error - {e}")
    except Exception as e:
        issues.append(f"❌ {file_path.name}: Validation error - {e}")

    return issues


def analyze_current_error():
    """Analyze the specific current error with location_type field"""
    print("\n🎯 ANALYZING CURRENT ERROR: location_type field")
    print("=" * 50)

    # Check if records.location model has location_type field
    location_model_file = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/records_location.py"
    )

    if location_model_file.exists():
        with open(location_model_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "location_type" in content:
            print("✅ location_type field IS defined in records.location model")

            # Check the field definition
            location_type_match = re.search(
                r"location_type\s*=\s*fields\..*?\n.*?\n.*?\]", content, re.DOTALL
            )
            if location_type_match:
                print("📋 Field definition found:")
                print(location_type_match.group(0))

                # Check if 'warehouse' is a valid option
                if "warehouse" in location_type_match.group(0):
                    print("✅ 'warehouse' is a valid selection option")
                else:
                    print("❌ 'warehouse' is NOT in selection options")
            else:
                print("⚠️ Could not parse location_type field definition")
        else:
            print("❌ location_type field NOT found in records.location model")
    else:
        print("❌ records_location.py model file not found")


if __name__ == "__main__":
    analyze_current_error()
    print("\n" + "=" * 70)
    issues, warnings = validate_data_files()
    exit(1 if issues else 0)
