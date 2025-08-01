#!/usr/bin/env python3
"""
Critical Field Fixes for Data File Validation
==============================================

This script identifies and generates fixes for missing fields in data files.
Using the validation results, we'll add the missing fields to their respective models.
"""

import os
import re

# Critical missing fields identified by validation
CRITICAL_FIXES = {
    "records_tag": {
        "file": "records_management/models/records_tag.py",
        "missing_fields": ["color"],
        "field_definitions": {
            "color": "color = fields.Integer(string='Color Index', default=0, help='Tag color for visual identification')"
        },
    },
    "records_retention_policy": {
        "file": "records_management/models/records_retention_policy.py",
        "missing_fields": ["code", "retention_period"],
        "field_definitions": {
            "code": "code = fields.Char(string='Policy Code', required=True, help='Unique identifier for the retention policy')",
            "retention_period": "retention_period = fields.Integer(string='Retention Period (Years)', required=True, help='Number of years to retain documents')",
        },
    },
    "records_container": {
        "file": "records_management/models/records_container.py",
        "missing_fields": ["max_boxes", "length", "width", "height", "active"],
        "field_definitions": {
            "max_boxes": "max_boxes = fields.Integer(string='Maximum Boxes', default=50, help='Maximum number of boxes this container can hold')",
            "length": "length = fields.Float(string='Length (cm)', help='Container length in centimeters')",
            "width": "width = fields.Float(string='Width (cm)', help='Container width in centimeters')",
            "height": "height = fields.Float(string='Height (cm)', help='Container height in centimeters')",
            "active": "active = fields.Boolean(string='Active', default=True, help='Set to false to hide this container')",
        },
    },
    "shredding_service": {
        "file": "records_management/models/shredding_service.py",
        "missing_fields": ["customer_id"],
        "field_definitions": {
            "customer_id": "customer_id = fields.Many2one('res.partner', string='Customer', required=True, help='Customer requesting shredding service')"
        },
    },
    "paper_bale_recycling": {
        "file": "records_management/models/paper_bale_recycling.py",
        "missing_fields": ["gross_weight", "bale_date"],
        "field_definitions": {
            "gross_weight": "gross_weight = fields.Float(string='Gross Weight (kg)', help='Total weight of bale including packaging')",
            "bale_date": "bale_date = fields.Date(string='Bale Date', default=fields.Date.today, help='Date when bale was created')",
        },
    },
    "records_chain_of_custody": {
        "file": "records_management/models/records_chain_of_custody.py",
        "missing_fields": ["custody_event"],
        "field_definitions": {
            "custody_event": "custody_event = fields.Selection([('pickup', 'Pickup'), ('transport', 'Transport'), ('storage', 'Storage'), ('destruction', 'Destruction')], string='Custody Event', required=True)"
        },
    },
    "portal_request": {
        "file": "records_management/models/portal_request.py",
        "missing_fields": ["customer_id", "request_type", "priority"],
        "field_definitions": {
            "customer_id": "customer_id = fields.Many2one('res.partner', string='Customer', required=True)",
            "request_type": "request_type = fields.Selection([('destruction', 'Destruction'), ('retrieval', 'Retrieval'), ('service', 'Service')], string='Request Type', required=True)",
            "priority": "priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], string='Priority', default='medium')",
        },
    },
}


def check_model_exists(file_path):
    """Check if model file exists"""
    return os.path.exists(file_path)


def read_model_file(file_path):
    """Read model file content"""
    with open(file_path, "r") as f:
        return f.read()


def field_exists_in_model(content, field_name):
    """Check if field already exists in model"""
    pattern = rf"{field_name}\s*="
    return bool(re.search(pattern, content))


def find_field_insertion_point(content):
    """Find where to insert new fields (after existing field definitions)"""
    # Look for the last field definition
    field_pattern = r"(\w+)\s*=\s*fields\."
    matches = list(re.finditer(field_pattern, content))
    if matches:
        last_match = matches[-1]
        # Find end of that field definition (look for next line that doesn't continue the field)
        lines = content.split("\n")
        start_line = content[: last_match.start()].count("\n")

        for i in range(start_line, len(lines)):
            line = lines[i].strip()
            if line and not line.startswith((")", ",", '"', "'")):
                # Found next non-field line
                insertion_point = sum(len(lines[j]) + 1 for j in range(i))
                return insertion_point

    # Fallback: insert before class methods
    method_pattern = r"\n\s*def\s+"
    method_match = re.search(method_pattern, content)
    if method_match:
        return method_match.start()

    # Fallback: insert before end of class
    return len(content) - 100  # Rough estimate


def generate_field_additions(model_info):
    """Generate field addition code"""
    additions = []
    for field_name, field_def in model_info["field_definitions"].items():
        additions.append(f"    {field_def}")

    return "\n\n" + "\n".join(additions) + "\n"


def main():
    print("🔧 CRITICAL FIELD FIXES GENERATOR")
    print("=" * 50)

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"
    fixes_needed = []

    for model_name, model_info in CRITICAL_FIXES.items():
        file_path = os.path.join(base_path, model_info["file"])
        print(f"\n📄 Checking {model_name}...")

        if not check_model_exists(file_path):
            print(f"   ❌ Model file not found: {file_path}")
            continue

        content = read_model_file(file_path)
        missing_fields = []

        for field_name in model_info["missing_fields"]:
            if not field_exists_in_model(content, field_name):
                missing_fields.append(field_name)
            else:
                print(f"   ✅ Field '{field_name}' already exists")

        if missing_fields:
            fixes_needed.append(
                {
                    "model": model_name,
                    "file": file_path,
                    "missing_fields": missing_fields,
                    "definitions": {
                        field: model_info["field_definitions"][field]
                        for field in missing_fields
                    },
                }
            )
            print(f"   🚨 Missing fields: {', '.join(missing_fields)}")
        else:
            print(f"   ✅ All fields present")

    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"Models needing fixes: {len(fixes_needed)}")

    for fix in fixes_needed:
        print(f"\n🔧 {fix['model']}")
        print(f"   File: {fix['file']}")
        print(f"   Missing: {', '.join(fix['missing_fields'])}")
        print("   Definitions:")
        for field_name, field_def in fix["definitions"].items():
            print(f"     {field_def}")


if __name__ == "__main__":
    main()
