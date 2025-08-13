#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Critical Inverse Fields Fix Script

This script systematically adds all 15 critical missing inverse fields
identified by the relationship validator to prevent KeyError exceptions
during Odoo.sh deployment.

Author: AI Assistant
Version: 1.0.0
"""

import os
import re
import sys

# Define all critical missing inverse fields based on validator output
CRITICAL_FIXES = [
    {
        "file": "records_management/models/naid_certificate.py",
        "field_name": "compliance_id",
        "field_type": "Many2one",
        "comodel": "naid.compliance",
        "description": "Related NAID Compliance",
    },
    {
        "file": "records_management/models/records_chain_of_custody.py",
        "field_name": "compliance_id",
        "field_type": "Many2one",
        "comodel": "naid.compliance",
        "description": "Related NAID Compliance",
    },
    {
        "file": "records_management/models/naid_custody_event.py",
        "field_name": "hard_drive_id",
        "field_type": "Many2one",
        "comodel": "hard.drive.scan.wizard",
        "description": "Related Hard Drive",
    },
    {
        "file": "records_management/models/barcode_product.py",
        "field_name": "storage_box_id",
        "field_type": "Many2one",
        "comodel": "barcode.storage.box",
        "description": "Storage Box",
    },
    {
        "file": "records_management/models/paper_bale.py",
        "field_name": "load_shipment_id",
        "field_type": "Many2one",
        "comodel": "paper.load.shipment",
        "description": "Load Shipment",
    },
    {
        "file": "records_management/models/paper_bale.py",
        "field_name": "load_id",
        "field_type": "Many2one",
        "comodel": "load",
        "description": "Load",
    },
    {
        "file": "records_management/models/shredding_service.py",
        "field_name": "shred_bin_id",
        "field_type": "Many2one",
        "comodel": "shred.bin",
        "description": "Shred Bin",
    },
    {
        "file": "records_management/models/pickup_request.py",
        "field_name": "shred_bin_id",
        "field_type": "Many2one",
        "comodel": "shred.bin",
        "description": "Shred Bin",
    },
    {
        "file": "records_management/models/fsm_reschedule_wizard.py",
        "field_name": "route_management_id",
        "field_type": "Many2one",
        "comodel": "fsm.route.management",
        "description": "Route Management",
    },
    {
        "file": "records_management/models/work_order_shredding.py",
        "field_name": "batch_id",
        "field_type": "Many2one",
        "comodel": "shredding.inventory.batch",
        "description": "Batch",
    },
    {
        "file": "records_management/models/container_retrieval_work_order.py",
        "field_name": "coordinator_id",
        "field_type": "Many2one",
        "comodel": "work.order.coordinator",
        "description": "Coordinator",
    },
    {
        "file": "records_management/models/file_retrieval_work_order.py",
        "field_name": "coordinator_id",
        "field_type": "Many2one",
        "comodel": "work.order.coordinator",
        "description": "Coordinator",
    },
    {
        "file": "records_management/models/scan_retrieval_work_order.py",
        "field_name": "coordinator_id",
        "field_type": "Many2one",
        "comodel": "work.order.coordinator",
        "description": "Coordinator",
    },
    {
        "file": "records_management/models/container_destruction_work_order.py",
        "field_name": "coordinator_id",
        "field_type": "Many2one",
        "comodel": "work.order.coordinator",
        "description": "Coordinator",
    },
    {
        "file": "records_management/models/container_access_work_order.py",
        "field_name": "coordinator_id",
        "field_type": "Many2one",
        "comodel": "work.order.coordinator",
        "description": "Coordinator",
    },
]


def find_field_insertion_point(content):
    """Find the best place to insert a field in the model class."""
    lines = content.split("\n")

    # Look for the last field definition or the end of class fields
    last_field_line = -1
    class_started = False
    indent_level = None

    for i, line in enumerate(lines):
        if "class " in line and "models.Model" in line:
            class_started = True
            continue

        if class_started:
            # Skip docstrings
            if '"""' in line:
                continue

            # Look for field definitions
            if "= fields." in line:
                last_field_line = i
                if indent_level is None:
                    indent_level = len(line) - len(line.lstrip())

            # Stop at method definitions
            elif line.strip().startswith("def ") and last_field_line > -1:
                break

            # Stop at decorators
            elif line.strip().startswith("@") and last_field_line > -1:
                break

    if last_field_line > -1:
        return last_field_line + 1, indent_level or 4

    # If no fields found, look for class definition and insert after
    for i, line in enumerate(lines):
        if "class " in line and "models.Model" in line:
            # Find first non-empty line after class definition
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('"""'):
                    return j, 4
            return i + 1, 4

    return len(lines), 4


def add_field_to_file(file_path, field_info):
    """Add a missing inverse field to a model file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if field already exists
        if f"{field_info['field_name']} =" in content:
            print(
                f"  ✅ Field {field_info['field_name']} already exists in {file_path}"
            )
            return True

        insert_line, indent = find_field_insertion_point(content)
        lines = content.split("\n")

        # Create the field definition
        indent_str = " " * indent
        field_def = f"{indent_str}{field_info['field_name']} = fields.{field_info['field_type']}('{field_info['comodel']}', string='{field_info['description']}')"

        # Insert the field
        lines.insert(insert_line, field_def)

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"  ✅ Added {field_info['field_name']} to {file_path}")
        return True

    except Exception as e:
        print(
            f"  ❌ Error adding {field_info['field_name']} to {file_path}: {e}"
        )
        return False


def main():
    """Main execution function."""
    print("🔧 CRITICAL INVERSE FIELDS FIX")
    print("=" * 50)

    workspace_root = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"
    success_count = 0

    for fix_info in CRITICAL_FIXES:
        file_path = os.path.join(workspace_root, fix_info["file"])

        print(f"\n📝 Processing {fix_info['file']}")
        print(
            f"   Adding field: {fix_info['field_name']} -> {fix_info['comodel']}"
        )

        if os.path.exists(file_path):
            if add_field_to_file(file_path, fix_info):
                success_count += 1
        else:
            print(f"  ❌ File not found: {file_path}")

    print(
        f"\n🎯 RESULTS: {success_count}/{len(CRITICAL_FIXES)} fields added successfully"
    )

    if success_count == len(CRITICAL_FIXES):
        print(
            "✅ All critical inverse fields added! Re-run validator to verify."
        )
    else:
        print(
            f"⚠️  {len(CRITICAL_FIXES) - success_count} fields failed to add."
        )


if __name__ == "__main__":
    main()
