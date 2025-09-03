#!/usr/bin/env python3
"""
Add Specific Missing Access Rules

This script adds access rules for the specific models identified as missing
by the validation tool.
"""

import os
import csv

def add_specific_access_rules(csv_path):
    """Add access rules for specific missing models"""

    # Models identified as missing from validation output
    missing_models = [
        'advanced.billing.contact',
        'advanced.billing.line',
        'advanced.billing.profile',
        'approval.history',
        'barcode.generation.history',
        'barcode.models.enhanced',
        'barcode.pricing.tier',
        'barcode.product',
        'barcode.storage.box',
        'base.rate',
        'base.rates',
        'billing.period',
        'bin.barcode.inventory',
        'bin.issue.record',
        'bin.key',
        'bin.key.history',
        'bin.key.unlock.service',
        'bin.unlock.service',
        'certificate.template.data',
        'chain.of.custody',
        'container.access.activity',
        'container.access.document',
        'container.access.photo',
        'container.access.report',
        'container.access.visitor',
        'container.access.work.order',
        'container.content',
        'container.destruction.work.order',
        'container.retrieval',
        'container.retrieval.item',
        'container.retrieval.work.order',
        'cross.department.sharing',
        'cross.department.sharing.rule',
        'custody.transfer.event',
        'customer.billing.profile',
        'customer.category',
        'customer.feedback',
        'customer.inventory',
        'customer.inventory.report',
        'customer.inventory.report.line',
        'customer.inventory.report.model',
        'customer.negotiated.rate',
        'customer.negotiated.rates',
        'customer.portal.diagram',
        'destruction.certificate',
        'destruction.item',
        'discount.rule',
        'display.name',
        'document.retrieval.equipment',
        'document.retrieval.item',
        'document.retrieval.team',
        'document.search.attempt',
        'feedback.improvement.area',
        'field.label.customization',
        'file.retrieval',
        'file.retrieval.item',
        'file.retrieval.work.order',
        'file.retrieval.work.order.item',
        'full.customization.name',
        'hard.drive.scan.wizard',
        'hard.drive.scan.wizard.line',
        'hr.employee',
        'inventory.adjustment.reason',
        'inventory.item',
        'inventory.item.destruction',
        'inventory.item.destruction.line',
        'inventory.item.location.transfer',
        'inventory.item.profile',
        'inventory.item.retrieval',
        'inventory.item.retrieval.line',
        'inventory.item.type',
        'invoice.generation.log',
        'key.inventory',
        'key.restriction.checker',
        'location.group',
        'location.report.wizard',
        'maintenance.equipment',
        'maintenance.request',
        'maintenance.team',
        'media.type',
        'mobile.bin.key.wizard',
        'mobile.dashboard.widget',
        'mobile.dashboard.widget.category',
        'mobile.photo',
        'naid.audit.requirement',
        'naid.certificate',
        'naid.certificate.item',
        'naid.certification.level',
        'naid.compliance.action.plan',
        'naid.compliance.alert',
        'naid.compliance.checklist',
        'naid.compliance.checklist.item',
        'naid.compliance.policy',
        'naid.custody',
        'naid.custody.event',
        'naid.destruction.record',
        'naid.equipment.standard',
        'naid.operator.certification',
        'naid.performance.history',
        'naid.risk.assessment',
        'naid.training.requirement',
        'naidaudit.log',
        'naidcustody.event',
        'paper.bale',
        'paper.bale.inspection',
        'paper.bale.inspection.wizard',
        'paper.bale.line',
        'paper.bale.load',
        'paper.bale.movement',
        'paper.bale.recycling',
        'paper.load.shipment',
        'paper.model_bale',
        'partner.bin.key',
        'payment.split',
        'payment.split.line',
        'photo',
        'pickup.location',
        'pickup.request',
        'pickup.request.item',
        'pickup.request.line',
        'pickup.route',
        'pickup.route.stop',
        'pickup.schedule.wizard',
        'portal.feedback',
        'portal.feedback.action',
        'portal.feedback.analytic',
        'portal.feedback.communication',
        'portal.feedback.escalation',
        'portal.feedback.resolution',
        'portal.request',
        'portal.request.line',
        'pos.config',
        'processing.log',
        'processing.log.resolution.wizard',
        'product.container.type',
        'product.product',
        'product.template',
        'project.task',
        'records.access.log',
        'records.approval.step',
        'records.approval.workflow',
        'records.approval.workflow.line',
        'records.audit.log',
        'records.billing',
        'records.billing.config',
        'records.billing.rate',
        'records.bulk.user.import',
        'records.category',
        'records.center.location',
        'records.chain.of.custody',
        'records.config.settings',
        'records.container',
        'records.container.content.line',
        'records.container.line',
        'records.container.log',
        'records.container.movement',
        'records.container.transfer',
        'records.container.transfer.line',
        'records.container.type',
        'records.container.type.converter',
        'records.deletion.request',
        'records.department',
        'records.department.billing.approval',
        'records.department.billing.contact',
        'records.department.sharing',
        'records.department.sharing.invite',
        'records.department.sharing.log',
        'records.description',
        'records.destruction',
        'records.destruction.job',
        'records.destruction.line',
        'records.digital.scan',
        'records.document',
        'records.document.type',
        'records.installer',
        'records.inventory.dashboard',
        'records.location',
        'records.location.inspection',
        'records.location.inspection.line',
        'records.location.report.wizard',
        'records.policy.version',
        'records.promotional.discount',
        'records.request',
        'records.request.line',
        'records.request.type',
        'records.retention.policy',
        'records.retention.policy.version',
        'records.retention.rule',
        'records.retrieval.work.order',
        'records.security.audit',
        'records.series',
        'records.service.type',
        'records.storage.box',
        'records.storage.department.user',
        'records.survey.user.input',
        'records.tag',
        'records.tag.category',
        'records.usage.tracking',
        'records.vehicle',
        'required.document',
        'res.config.settings',
        'res.partner',
        'res.partner.key.restriction',
        'retrieval.item.base',
        'retrieval.metric',
        'revenue.analytic',
        'revenue.forecast',
        'revenue.forecast.line',
        'revenue.forecasting.reports',
        'rm.module.configurator',
        'route.optimizer',
        'scan.digital.asset',
        'scan.retrieval',
        'scan.retrieval.item',
        'scan.retrieval.work.order',
        'service.item',
        'shred.bin',
        'shred.model_bin',
        'shredding.certificate',
        'shredding.hard.drive',
        'shredding.inventory.batch',
        'shredding.picklist.item',
        'shredding.rate',
        'shredding.service',
        'shredding.service.bin',
        'shredding.service.event',
        'shredding.service.log',
        'shredding.service.photo',
        'shredding.team',
        'signed.document',
        'signed.document.audit',
        'stock.lot',
        'stock.lot.attribute',
        'stock.lot.attribute.option',
        'stock.lot.attribute.value',
        'stock.move.sms.validation',
        'stock.picking',
        'survey.feedback.theme',
        'survey.improvement.action',
        'system.diagram.data',
        'system.flowchart.wizard',
        'temp.inventory',
        'temp.inventory.audit',
        'temp.inventory.movement',
        'temp.inventory.reject.wizard',
        'transitory.field.config',
        'transitory.item',
        'unlock.service.history',
        'unlock.service.part',
        'visitor',
        'work.order.coordinator',
        'work.order.retrieval',
        'work.order.shredding',
        'workflow.visualization.manager'
    ]

    print(f"Adding access rules for {len(missing_models)} specific models...")

    # Read existing CSV
    rows = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Ensure fieldnames is not None; use default if necessary
    if fieldnames is None:
        fieldnames = ['id', 'name', 'model_id:id', 'group_id:id', 'perm_read', 'perm_write', 'perm_create', 'perm_unlink']

    # Check which models are already in the CSV
    existing_model_ids = set()
    for row in rows:
        model_id = row.get('model_id:id', '')
        if model_id:
            existing_model_ids.add(model_id)

    # Add new access rules for missing models
    new_rows = []
    added_count = 0

    for model_name in missing_models:
        model_id_ref = f'records_management.model_{model_name.replace(".", "_")}'

        # Skip if already exists
        if model_id_ref in existing_model_ids:
            continue

        # Create user access rule
        user_rule = {
            'id': f'access_{model_name.replace(".", "_")}_user',
            'name': model_name.replace(".", " ").title(),
            'model_id:id': model_id_ref,
            'group_id:id': 'records_management.group_records_user',
            'perm_read': '1',
            'perm_write': '1',
            'perm_create': '1',
            'perm_unlink': '0'
        }

        # Create manager access rule
        manager_rule = {
            'id': f'access_{model_name.replace(".", "_")}_manager',
            'name': model_name.replace(".", " ").title(),
            'model_id:id': model_id_ref,
            'group_id:id': 'records_management.group_records_manager',
            'perm_read': '1',
            'perm_write': '1',
            'perm_create': '1',
            'perm_unlink': '1'
        }

        new_rows.extend([user_rule, manager_rule])
        added_count += 2

    # Write updated CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerows(new_rows)

    print(f"Added {added_count} new access rules to {csv_path}")
    return added_count

def main():
    """Main function"""
    base_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0"
    csv_path = os.path.join(base_dir, "records_management", "security", "ir.model.access.csv")

    added_count = add_specific_access_rules(csv_path)

    if added_count > 0:
        print(f"\n✅ Successfully added {added_count} missing access rules!")
        print("🔄 Run the validation again to check if the security errors are resolved.")
    else:
        print("\n✅ All specified models already have access rules!")

if __name__ == "__main__":
    main()
