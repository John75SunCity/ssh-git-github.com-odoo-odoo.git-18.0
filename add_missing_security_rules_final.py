#!/usr/bin/env python3
"""
Add missing security access rules for Records Management module
"""

import csv
import os

def add_missing_security_rules():
    """Add missing security access rules for models that don't have them"""

    # Path to the security CSV file
    security_file = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    # Missing models that need access rules
    missing_models = [
        'destruction.item',
        'inventory.item.destruction.line',
        'records.storage.box',
        'shredding.certificate',
        'naid.equipment.standard',
        'stock.lot.attribute.value',
        'payment.split.line',
        'payment.split',
        'mobile.bin.key.wizard',
        'revenue.forecast',
        'records.destruction.job',
        'records.destruction.line',
        'field.label.customization',
        'retrieval.metric',
        'bin.issue.record',
        'media.type',
        'records.approval.workflow.line',
        'records.retention.policy.version',
        'customer.category',
        'naid.custody.event',
        'report.records_management.revenue_forecasting_report',
        'records.deletion.request',
        'destruction.certificate',
        'file.retrieval.item',
        'scan.retrieval',
        'inventory.item.destruction',
        'shred.bin',
        'records.inventory.dashboard',
        'records.bulk.user.import',
        'naid.audit.log',
        'records.retention.rule',
        'records.promotional.discount',
        'paper.model_bale',
        'certificate.template.data',
        'records.location',
        'container.access.work.order',
        'stock.move.sms.validation',
        'paper.bale.movement',
        'barcode.pricing.tier',
        'full.customization.name',
        'service.item',
        'work.order.retrieval',
        'report.records_management.report_customer_inventory',
        'customer.inventory.report.wizard',
        'pickup.schedule.wizard',
        'system.diagram.data',
        'required.document',
        'scan.retrieval.work.order',
        'feedback.improvement.area',
        'records.destruction',
        'records.billing',
        'naid.compliance.checklist',
        'customer.inventory.report.line',
        'paper.load.shipment',
        'records.digital.scan',
        'scan.digital.asset',
        'partner.bin.key',
        'document.search.attempt'
    ]

    # Read existing security rules
    existing_rules = []
    if os.path.exists(security_file):
        with open(security_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            existing_rules = list(reader)

    # Get existing model IDs to avoid duplicates
    existing_model_ids = set()
    for row in existing_rules[1:]:  # Skip header
        if row and len(row) >= 3:
            existing_model_ids.add(row[2])  # model_id:id column

    # Create new access rules for missing models
    new_rules = []
    for model in missing_models:
        model_id = f"model_records_management_{model.replace('.', '_')}"

        # Skip if already exists
        if model_id in existing_model_ids:
            continue

        # Add user access rule
        user_rule = [
            f"access_records_management_{model.replace('.', '_')}_user",
            f"records_management.{model}.user",
            model_id,
            "records_management.group_records_user",
            "1", "1", "1", "0"
        ]
        new_rules.append(user_rule)

        # Add manager access rule
        manager_rule = [
            f"access_records_management_{model.replace('.', '_')}_manager",
            f"records_management.{model}.manager",
            model_id,
            "records_management.group_records_manager",
            "1", "1", "1", "1"
        ]
        new_rules.append(manager_rule)

    # Append new rules to existing file
    if new_rules:
        with open(security_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for rule in new_rules:
                writer.writerow(rule)

        print(f"✅ Added {len(new_rules)} security access rules for {len(missing_models)} models")
        return len(new_rules)
    else:
        print("ℹ️ No new security rules needed - all models already have access rules")
        return 0

if __name__ == "__main__":
    added_count = add_missing_security_rules()
    print(f"Security access rules update complete. Added {added_count} new rules.")
