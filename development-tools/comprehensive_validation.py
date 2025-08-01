#!/usr/bin/env python3
"""
Final comprehensive validation of all fixes
"""

import os
import csv
import xml.etree.ElementTree as ET
import ast


def validate_all_fixes():
    """Validate all applied fixes"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    print("🔍 COMPREHENSIVE VALIDATION REPORT")
    print("=" * 60)

    # 1. Validate XML files
    validate_xml_files(base_path)

    # 2. Validate CSV access rules
    validate_csv_access_rules(base_path)

    # 3. Validate Python syntax
    validate_python_syntax(base_path)

    # 4. Validate model references
    validate_model_references(base_path)

    print("\n✅ COMPREHENSIVE VALIDATION COMPLETED")


def validate_xml_files(base_path):
    """Validate all XML files for syntax errors"""

    print("\n📋 XML FILE VALIDATION")
    print("-" * 30)

    xml_files = [
        "security/additional_models_access.xml",
        "data/naid_compliance_data.xml",
        "monitoring/views_config.py",  # Contains XML snippets
    ]

    for xml_file in xml_files:
        file_path = os.path.join(base_path, xml_file)
        if xml_file.endswith(".py"):
            # Skip Python files for now
            continue

        if os.path.exists(file_path):
            try:
                ET.parse(file_path)
                print(f"✅ {xml_file}: Valid XML")
            except ET.ParseError as e:
                print(f"❌ {xml_file}: XML Error - {e}")
        else:
            print(f"⚠️  {xml_file}: File not found")


def validate_csv_access_rules(base_path):
    """Validate CSV access rules"""

    print("\n📊 CSV ACCESS RULES VALIDATION")
    print("-" * 35)

    csv_file = os.path.join(base_path, "security/ir.model.access.csv")

    if not os.path.exists(csv_file):
        print("❌ CSV file not found")
        return

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            lines = list(reader)

        if not lines:
            print("❌ CSV file is empty")
            return

        header = lines[0]
        data_lines = lines[1:]

        print(f"✅ CSV file loaded: {len(data_lines)} access rules")

        # Check for duplicates
        rule_ids = [line[0].strip() for line in data_lines if len(line) >= 1]
        duplicates = set([x for x in rule_ids if rule_ids.count(x) > 1])

        if duplicates:
            print(f"⚠️  Found {len(duplicates)} duplicate rule IDs")
        else:
            print("✅ No duplicate rule IDs")

        # Check required enhanced models
        enhanced_models = [
            "model_barcode_models_enhanced",
            "model_records_deletion_request_enhanced",
            "model_records_department_billing_enhanced",
            "model_survey_user_input_enhanced",
        ]

        model_refs = [line[2].strip() for line in data_lines if len(line) >= 3]
        missing_models = [model for model in enhanced_models if model not in model_refs]

        if missing_models:
            print(f"⚠️  Missing model references: {missing_models}")
        else:
            print("✅ All enhanced model references present")

    except Exception as e:
        print(f"❌ CSV validation error: {e}")


def validate_python_syntax(base_path):
    """Validate Python files for syntax errors"""

    print("\n🐍 PYTHON SYNTAX VALIDATION")
    print("-" * 30)

    python_files = [
        "models/naid_compliance.py",
        "models/naid_audit_log.py",
        "models/hr_employee.py",
        "monitoring/models.py",
        "monitoring/__init__.py",
    ]

    for py_file in python_files:
        file_path = os.path.join(base_path, py_file)

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()

                ast.parse(source)
                print(f"✅ {py_file}: Valid Python syntax")

            except SyntaxError as e:
                print(f"❌ {py_file}: Syntax Error - Line {e.lineno}: {e.msg}")
            except Exception as e:
                print(f"❌ {py_file}: Error - {e}")
        else:
            print(f"⚠️  {py_file}: File not found")


def validate_model_references(base_path):
    """Validate that all model references are consistent"""

    print("\n🔗 MODEL REFERENCE VALIDATION")
    print("-" * 32)

    # Check cron job model references
    cron_file = os.path.join(base_path, "data/naid_compliance_data.xml")

    if os.path.exists(cron_file):
        try:
            tree = ET.parse(cron_file)
            model_refs = tree.findall(".//field[@name='model_id']")

            expected_refs = [
                "hr.model_hr_employee",  # Employee credential check
                "base.model_ir_cron",  # Audit log cleanup
                "base.model_ir_cron",  # Compliance check
            ]
            actual_refs = [ref.get("ref") for ref in model_refs]

            if actual_refs == expected_refs:
                print(
                    f"✅ Cron jobs: All {len(actual_refs)} use correct model_id references"
                )
            else:
                print(f"❌ Cron jobs: Model_id references don't match expected")
                for i, (expected, actual) in enumerate(zip(expected_refs, actual_refs)):
                    status = "✅" if expected == actual else "❌"
                    print(
                        f"   Job {i+1}: {status} Expected: {expected}, Actual: {actual}"
                    )

        except Exception as e:
            print(f"❌ Cron validation error: {e}")

    # Check monitoring model
    monitor_model = os.path.join(base_path, "monitoring/models.py")
    if os.path.exists(monitor_model):
        print("✅ Monitoring model: File exists")
    else:
        print("❌ Monitoring model: Missing models.py file")


if __name__ == "__main__":
    validate_all_fixes()
