#!/usr/bin/env python3
"""
Add Missing Security Access Rules for Records Management Module
This script adds security access rules for all missing models in the ir.model.access.csv file.
"""

import os
import csv
import sys

def add_missing_security_rules():
    """Add missing security access rules for all models"""

    # Path to the security CSV file
    csv_path = "records_management/security/ir.model.access.csv"

    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"❌ Security CSV file not found: {csv_path}")
        return False

    # Read existing access rules
    existing_rules = set()
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        for row in reader:
            if row and len(row) >= 2:
                existing_rules.add(row[1])  # model name is in column 1

    print(f"📊 Found {len(existing_rules)} existing access rules")

    # List of missing models that need access rules
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

    # Filter out models that already have rules
    models_to_add = [model for model in missing_models if model not in existing_rules]

    if not models_to_add:
        print("✅ All models already have access rules!")
        return True

    print(f"🔧 Adding access rules for {len(models_to_add)} missing models")

    # Prepare new rules
    new_rules = []
    for model in models_to_add:
        # Add user access rule
        new_rules.append([
            f"access_{model.replace('.', '_')}_user",
            model,
            "records_management.group_records_user",
            "1", "1", "1", "0"
        ])
        # Add manager access rule
        new_rules.append([
            f"access_{model.replace('.', '_')}_manager",
            model,
            "records_management.group_records_manager",
            "1", "1", "1", "1"
        ])

    # Append new rules to CSV file
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for rule in new_rules:
                writer.writerow(rule)

        print(f"✅ Successfully added {len(new_rules)} access rules for {len(models_to_add)} models")
        return True

    except Exception as e:
        print(f"❌ Error adding access rules: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Adding Missing Security Access Rules for Records Management Module")
    print("=" * 70)

    success = add_missing_security_rules()

    if success:
        print("\n✅ Security access rules update completed successfully!")
        print("📋 Next steps:")
        print("   1. Run validation again to check remaining issues")
        print("   2. Fix translation pattern warnings")
        print("   3. Address model structure issues")
    else:
        print("\n❌ Failed to update security access rules")
        sys.exit(1)
