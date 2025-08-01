#!/usr/bin/env python3
"""
Validate that all label fields from demo data exist in the model
"""

import os
import re
import xml.etree.ElementTree as ET


def validate_label_fields():
    """Validate that all label fields are properly defined"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    print("🔍 COMPREHENSIVE LABEL FIELD VALIDATION")
    print("=" * 50)

    # 1. Extract fields from demo data
    demo_fields = extract_demo_fields(base_path)

    # 2. Extract fields from model
    model_fields = extract_model_fields(base_path)

    # 3. Compare and validate
    validate_field_completeness(demo_fields, model_fields)


def extract_demo_fields(base_path):
    """Extract all label fields from demo data"""

    demo_file = os.path.join(base_path, "data/field_label_demo_data.xml")
    demo_fields = set()

    try:
        tree = ET.parse(demo_file)
        root = tree.getroot()

        for field_elem in root.findall(".//field[@name]"):
            field_name = field_elem.get("name")
            if field_name and field_name.startswith("label_"):
                demo_fields.add(field_name)

        print(f"📋 Demo Data Fields: {len(demo_fields)} found")
        for field in sorted(demo_fields):
            print(f"   - {field}")

        return demo_fields

    except Exception as e:
        print(f"❌ Error reading demo data: {e}")
        return set()


def extract_model_fields(base_path):
    """Extract all label fields from model definition"""

    model_file = os.path.join(base_path, "models/field_label_customization.py")
    model_fields = set()

    try:
        with open(model_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all field definitions starting with label_
        field_pattern = r"(label_[a-z_]+)\s*=\s*fields\."
        matches = re.findall(field_pattern, content)

        model_fields = set(matches)

        print(f"\n🐍 Model Fields: {len(model_fields)} found")
        for field in sorted(model_fields):
            print(f"   - {field}")

        return model_fields

    except Exception as e:
        print(f"❌ Error reading model file: {e}")
        return set()


def validate_field_completeness(demo_fields, model_fields):
    """Validate that all demo fields exist in model"""

    print(f"\n✅ VALIDATION RESULTS")
    print("=" * 30)

    missing_fields = demo_fields - model_fields
    extra_fields = model_fields - demo_fields

    if not missing_fields:
        print("✅ All demo data fields are defined in model")
    else:
        print(f"❌ Missing fields in model: {len(missing_fields)}")
        for field in sorted(missing_fields):
            print(f"   - {field}")

    if extra_fields:
        print(f"\nℹ️  Extra fields in model (not used in demo): {len(extra_fields)}")
        for field in sorted(extra_fields):
            print(f"   - {field}")

    # Overall status
    if not missing_fields:
        print(f"\n🎉 SUCCESS: Model is complete for demo data loading")
        return True
    else:
        print(f"\n⚠️  WARNING: {len(missing_fields)} fields need to be added to model")
        return False


if __name__ == "__main__":
    validate_label_fields()
