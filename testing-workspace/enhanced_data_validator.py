#!/usr/bin/env python3
"""
Enhanced Data File Validat    # Map model names to file paths
    model_file_map = {
        'records.tag': 'records_management/models/records_tag.py',
        'records.location': 'records_management/models/records_location.py',
        'records.retention.policy': 'records_management/models/records_retention_policy.py',
        'records.container': 'records_management/models/records_container.py',
        'shredding.service': 'records_management/models/shredding_service.py',
        'paper.bale.recycling': 'records_management/models/paper_bale_recycling.py',
        'records.chain.of.custody': 'records_management/models/records_chain_of_custody.py',
        'portal.request': 'records_management/models/portal_request.py',
        'customer.feedback': 'records_management/models/customer_feedback.py',
        'naid.compliance': 'records_management/models/naid_compliance.py',
        'records.document.type': 'records_management/models/records_document_type.py',
        'records.customer.billing.profile': 'records_management/models/customer_billing_profile.py',
        'records.billing.contact': 'records_management/models/customer_billing_profile.py',
        'field.label.customization': 'records_management/models/field_label_customization.py',
    }odels
============================================

Updated validator that recognizes core Odoo models and only reports
issues with custom models that actually need fixing.
"""

import os
import re
import xml.etree.ElementTree as ET

# Core Odoo models that are always available
CORE_ODOO_MODELS = {
    "res.partner",
    "res.company",
    "res.users",
    "res.groups",
    "res.country",
    "ir.config_parameter",
    "ir.model",
    "ir.model.fields",
    "ir.model.access",
    "ir.sequence",
    "ir.cron",
    "sms.template",
    "survey.survey",
    "survey.question",
    "survey.question.answer",
    "product.product",
    "product.template",
    "product.category",
    "mail.template",
    "mail.message",
    "mail.thread",
    "account.move",
    "account.move.line",
    "account.account",
    "stock.location",
    "stock.picking",
    "stock.move",
    "sale.order",
    "sale.order.line",
    "purchase.order",
}


def get_model_fields(model_name):
    """Get field definitions for a model from its Python file"""
    if model_name in CORE_ODOO_MODELS:
        return set()  # Core models - don't validate fields

    # Map model names to file paths
    model_file_map = {
        "records.tag": "records_management/models/records_tag.py",
        "records.location": "records_management/models/records_location.py",
        "records.retention.policy": "records_management/models/records_retention_policy.py",
        "records.container": "records_management/models/records_container.py",
        "shredding.service": "records_management/models/shredding_service.py",
        "paper.bale.recycling": "records_management/models/paper_bale_recycling.py",
        "records.chain.of.custody": "records_management/models/records_chain_of_custody.py",
        "portal.request": "records_management/models/portal_request.py",
        "customer.feedback": "records_management/models/customer_feedback.py",
        "naid.compliance": "records_management/models/naid_compliance.py",
        "records.billing.contact": "records_management/models/records_billing_contact.py",
    }

    file_path = model_file_map.get(model_name)
    if not file_path or not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Extract field names using regex
        field_pattern = r"(\w+)\s*=\s*fields\."
        fields = set(re.findall(field_pattern, content))
        return fields
    except Exception as e:
        print(f"   ⚠️  Error reading {file_path}: {e}")
        return set()


def validate_data_file(file_path):
    """Validate a single data file"""
    print(f"📄 Validating: {os.path.basename(file_path)}")

    if not os.path.exists(file_path):
        print(f"   ❌ File not found: {file_path}")
        return []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"   ❌ XML Parse Error: {e}")
        return [f"XML Parse Error in {os.path.basename(file_path)}: {e}"]

    issues = []

    # Find all record elements
    for record in root.findall(".//record"):
        model = record.get("model")
        record_id = record.get("id", "unknown")

        if not model:
            continue

        # Skip core models - they're always valid
        if model in CORE_ODOO_MODELS:
            continue

        # Get expected fields for this model
        expected_fields = get_model_fields(model)

        if expected_fields is None:
            issues.append(f"Unknown model '{model}' (record: {record_id})")
            continue

        # Check each field in the record
        for field_elem in record.findall("field"):
            field_name = field_elem.get("name")
            if field_name and field_name not in expected_fields:
                issues.append(
                    f"Model '{model}' missing field '{field_name}' (record: {record_id})"
                )

    if issues:
        for issue in issues:
            print(f"   ❌ {issue}")
    else:
        print(f"   ✅ All field references valid")

    return issues


def main():
    print("🎯 ENHANCED DATA FILE VALIDATION")
    print("=" * 50)
    print(f"ℹ️  Core models recognized: {len(CORE_ODOO_MODELS)}")
    print()

    base_path = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/data"
    )

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
        "model_records.xml",
        "feedback_survey_data.xml",
        "advanced_billing_demo.xml",
        "field_label_demo_data.xml",
    ]

    all_issues = []

    for data_file in data_files:
        file_path = os.path.join(base_path, data_file)
        issues = validate_data_file(file_path)
        all_issues.extend(issues)

    print("\n📊 ENHANCED VALIDATION SUMMARY")
    print("=" * 50)
    print(f"🚨 Custom Model Issues: {len(all_issues)}")

    if all_issues:
        print("\n🚨 CUSTOM MODEL FIELD ISSUES:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. ❌ {issue}")
    else:
        print("✅ All custom model fields validated successfully!")

    return len(all_issues)


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
