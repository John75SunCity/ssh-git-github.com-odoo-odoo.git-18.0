#!/usr/bin/env python3
"""
Comprehensive syntax error fixer for Odoo Records Management module
Fixes the 62 identified Python files with syntax errors
"""

import os
import re
import ast


def fix_missing_commas_and_parentheses(file_path):
    """Fix common syntax errors: missing commas and unclosed parentheses"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Pattern 1: Fix missing closing parenthesis after field definition
        # Look for patterns like: field_name = fields.Type(\n    param\n    next_field =
        pattern1 = re.compile(
            r"(\w+\s*=\s*fields\.\w+\(\s*\n(?:.*\n)*?)(\s+)(\w+\s*=\s*fields\.)",
            re.MULTILINE,
        )
        content = pattern1.sub(r"\1\2)\n\2\3", content)

        # Pattern 2: Fix missing closing parenthesis in selection fields
        # Look for: fields.Selection([\n    options\n]    # Missing closing paren
        pattern2 = re.compile(
            r"(fields\.Selection\(\s*\[\s*\n(?:.*\n)*?\s*\]\s*)([\s,]*\n\s*)(\w+\s*=)",
            re.MULTILINE,
        )
        content = pattern2.sub(r"\1)\2\3", content)

        # Pattern 3: Fix missing commas after field definitions
        # Look for: field = fields.Type(params)\n    field2 =
        pattern3 = re.compile(
            r"(\w+\s*=\s*fields\.\w+\([^)]*\))\s*\n(\s+)(\w+\s*=\s*fields\.)",
            re.MULTILINE,
        )
        content = pattern3.sub(r"\1,\n\2\3", content)

        # Pattern 4: Fix unmatched parentheses in method calls
        pattern4 = re.compile(r"(\w+\([^)]*\))\)\s*$", re.MULTILINE)
        content = pattern4.sub(r"\1", content)

        # Pattern 5: Fix missing closing parentheses in multi-line field definitions
        lines = content.split("\n")
        fixed_lines = []
        in_field_def = False
        paren_count = 0

        for i, line in enumerate(lines):
            # Check if line starts a field definition
            if re.match(r"\s*\w+\s*=\s*fields\.\w+\(", line):
                in_field_def = True
                paren_count = line.count("(") - line.count(")")
            elif in_field_def:
                paren_count += line.count("(") - line.count(")")

                # Check if next line starts a new field or method
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if (
                        re.match(r"\s*\w+\s*=\s*fields\.", next_line)
                        or re.match(r"\s*def\s+", next_line)
                        or re.match(r"\s*@", next_line)
                    ) and paren_count > 0:
                        # Need to close the parentheses
                        line += ")" * paren_count
                        paren_count = 0
                        in_field_def = False

            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        # Only write if content changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def check_syntax(file_path):
    """Check if file has valid Python syntax"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True
    except:
        return False


# List of files with syntax errors to fix
error_files = [
    "records_management/models/bin_key_management.py",
    "records_management/models/customer_billing_profile.py",
    "records_management/models/customer_feedback.py",
    "records_management/models/customer_inventory.py",
    "records_management/models/customer_inventory_report.py",
    "records_management/models/document_retrieval_support_models.py",
    "records_management/models/document_retrieval_work_order.py",
    "records_management/models/fsm_notification.py",
    "records_management/models/fsm_route_management.py",
    "records_management/models/fsm_task.py",
    "records_management/models/integration_error.py",
    "records_management/models/key_restriction_checker.py",
    "records_management/models/load.py",
    "records_management/models/location_report_wizard.py",
    "records_management/models/maintenance_extensions.py",
    "records_management/models/mobile_bin_key_wizard.py",
    "records_management/models/naid_certificate.py",
    "records_management/models/naid_compliance.py",
    "records_management/models/naid_compliance_support_models.py",
    "records_management/models/paper_bale_recycling.py",
    "records_management/models/partner_bin_key.py",
    "records_management/models/payment_split.py",
    "records_management/models/photo.py",
    "records_management/models/pickup_request.py",
    "records_management/models/pickup_route.py",
    "records_management/models/portal_feedback.py",
    "records_management/models/portal_feedback_support_models.py",
    "records_management/models/portal_request.py",
    "records_management/models/pos_config.py",
    "records_management/models/processing_log.py",
    "records_management/models/product_template.py",
    "records_management/models/records_access_log.py",
    "records_management/models/records_billing_config.py",
    "records_management/models/records_billing_contact.py",
    "records_management/models/records_bin.py",
    "records_management/models/records_chain_of_custody.py",
    "records_management/models/records_container_movement.py",
    "records_management/models/records_container_type.py",
    "records_management/models/records_container_type_converter.py",
    "records_management/models/records_department_billing_contact.py",
    "records_management/models/records_digital_scan.py",
    "records_management/models/records_document.py",
    "records_management/models/records_management_base_menus.py",
    "records_management/models/records_permanent_flag_wizard.py",
    "records_management/models/records_policy_version.py",
    "records_management/models/records_retention_policy.py",
    "records_management/models/records_vehicle.py",
    "records_management/models/res_partner.py",
    "records_management/models/revenue_forecaster.py",
    "records_management/models/service_item.py",
    "records_management/models/shredding_certificate.py",
    "records_management/models/shredding_equipment.py",
    "records_management/models/shredding_hard_drive.py",
    "records_management/models/shredding_inventory.py",
    "records_management/models/shredding_inventory_item.py",
    "records_management/models/shredding_service.py",
    "records_management/models/shredding_team.py",
    "records_management/models/stock_lot.py",
    "records_management/models/stock_move_sms_validation.py",
    "records_management/models/transitory_field_config.py",
    "records_management/models/unlock_service_history.py",
    "records_management/models/visitor_pos_wizard.py",
]


def main():
    print("🚀 Starting comprehensive syntax error fixing...")
    print(f"📋 Total files to process: {len(error_files)}")

    fixed_count = 0
    remaining_errors = []

    for file_path in error_files:
        if os.path.exists(file_path):
            print(f"\n🔧 Processing: {file_path}")

            # Try to fix the file
            was_fixed = fix_missing_commas_and_parentheses(file_path)

            # Check if syntax is now valid
            if check_syntax(file_path):
                print(f"✅ SYNTAX VALID: {file_path}")
                fixed_count += 1
            else:
                print(f"⚠️  NEEDS MORE WORK: {file_path}")
                remaining_errors.append(file_path)
        else:
            print(f"❌ FILE NOT FOUND: {file_path}")

    print(f"\n📊 RESULTS:")
    print(f"✅ Fixed files: {fixed_count}/{len(error_files)}")
    print(f"⚠️  Remaining issues: {len(remaining_errors)}")

    if remaining_errors:
        print(f"\n📋 Files still needing attention:")
        for i, file_path in enumerate(remaining_errors, 1):
            print(f"{i:2d}. {file_path}")


if __name__ == "__main__":
    main()
