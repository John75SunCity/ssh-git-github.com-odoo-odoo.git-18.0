#!/usr/bin/env python3
"""
Remove invalid model entries from ir.model.access.csv

This script removes entries for models that don't exist in the system.
"""

import csv
import os
import sys
from pathlib import Path

# List of valid models in the records_management module (based on actual _name definitions)
VALID_MODELS = {
    # Core models
    'records.container', 'records.document', 'records.location', 'records.billing',
    'records.department', 'records.request', 'records.destruction', 'records.category',
    'records.tag', 'records.center.location', 'records.deletion.request', 'records.digital.scan',
    'records.document.type', 'records.inventory.dashboard', 'records.policy.version',
    'records.retention.policy', 'records.retention.rule', 'records.retrieval.work.order',
    'records.security.audit', 'records.series', 'records.service.type', 'records.storage.box',
    'records.storage.department.user', 'records.survey.user.input', 'records.tag.category',
    'records.usage.tracking', 'records.vehicle', 'records.chain.of.custody',

    # Portal and feedback models
    'portal.feedback', 'portal.feedback.action', 'portal.feedback.analytic',
    'portal.feedback.communication', 'portal.feedback.escalation', 'portal.feedback.resolution',
    'portal.request', 'portal.request.line', 'customer.feedback', 'customer.category',

    # Shredding models
    'shredding.service', 'shredding.certificate', 'shredding.hard.drive', 'shredding.inventory.batch',
    'shredding.picklist.item', 'shredding.rate', 'shredding.service.bin', 'shredding.service.event',
    'shredding.service.log', 'shredding.service.photo', 'shredding.team',

    # Billing and payment models
    'payment.split', 'payment.split.line', 'records.billing.config', 'records.billing.rate',
    'records.department.billing.approval', 'records.department.billing.contact',
    'records.promotional.discount', 'billing.period', 'discount.rule',

    # NAID compliance models
    'naid.audit.log', 'naid.audit.requirement', 'naid.certificate', 'naid.certificate.item',
    'naid.certification.level', 'naid.compliance.action.plan', 'naid.compliance.alert',
    'naid.compliance.checklist', 'naid.compliance.checklist.item', 'naid.compliance.policy',
    'naid.custody', 'naid.custody.event', 'naid.destruction.record', 'naid.equipment.standard',
    'naid.operator.certification', 'naid.performance.history', 'naid.risk.assessment',
    'naid.training.requirement',

    # Mobile and photo models
    'mobile.photo', 'mobile.dashboard.widget', 'mobile.dashboard.widget.category',
    'mobile.bin.key.wizard', 'photo',

    # Service and work order models
    'service.item', 'work.order.coordinator', 'work.order.retrieval', 'work.order.shredding',
    'unlock.service.history', 'unlock.service.part', 'records.installer',

    # Pickup and route models
    'pickup.location', 'pickup.request', 'pickup.request.item', 'pickup.request.line',
    'pickup.route', 'pickup.route.stop', 'pickup.schedule.wizard',

    # Container and retrieval models
    'container.retrieval', 'container.retrieval.item', 'records.container.content.line',
    'records.container.line', 'records.container.log', 'records.container.movement',
    'records.container.transfer', 'records.container.transfer.line', 'records.container.type',
    'records.container.type.converter', 'paper.bale', 'paper.bale.line', 'paper.bale.load',
    'paper.bale.movement', 'paper.bale.recycling', 'paper.load.shipment',

    # FSM models
    'fsm.notification', 'fsm.notification.manager',

    # Revenue and analytics models
    'revenue.analytic', 'revenue.forecast', 'revenue.forecast.line', 'revenue.forecasting.reports',
    'retrieval.metric', 'processing.log', 'processing.log.resolution.wizard',

    # Signed document models
    'signed.document', 'signed.document.audit',

    # Route and optimization models
    'route.optimizer',

    # Scan and digital asset models
    'scan.digital.asset', 'scan.retrieval', 'scan.retrieval.item', 'scan.retrieval.work.order',

    # Temp inventory models
    'temp.inventory', 'temp.inventory.audit', 'temp.inventory.movement', 'temp.inventory.reject.wizard',

    # Transitory models
    'transitory.item', 'transitory.field.config',

    # Wizard models
    'bin.issue.record', 'bin.issue.report.wizard', 'custom.box.volume.calculator',
    'customer.inventory.report.wizard', 'field.label.helper.wizard', 'fsm.reschedule.wizard.placeholder',
    'hard.drive.scan.wizard', 'key.restriction.checker', 'location.report.wizard',
    'permanent.flag.wizard', 'rate.change.confirmation.wizard', 'records.container.type.converter.wizard',
    'records.document.flag.permanent.wizard', 'records.location.report.wizard',
    'records.permanent.flag.wizard', 'records.user.invitation.wizard', 'shredding.bin.barcode.wizard',
    'shredding.bin.sequence.reset.wizard', 'system.flowchart.wizard', 'unlock.service.reschedule.wizard',
    'records.bulk.user.import', 'visitor.pos.wizard', 'wizard.template', 'work.order.bin.assignment.wizard',

    # Approval workflow models
    'records.approval.step', 'records.approval.workflow', 'records.approval.workflow.line',

    # Access and visitor models
    'container.access.visitor', 'container.access.photo', 'visitor', 'records.access.log',

    # Partner and key models
    'partner.bin.key', 'res.partner.key.restriction',

    # Stock and inventory models
    'stock.lot.attribute', 'stock.lot.attribute.option', 'stock.lot.attribute.value',
    'stock.move.sms.validation',

    # Survey models
    'survey.feedback.theme', 'survey.improvement.action',

    # System models
    'system.diagram.data', 'workflow.visualization.manager',

    # Required document models
    'required.document',

    # Base models
    'base.rates', 'base.rate',

    # Location and group models
    'location.group',

    # Barcode models
    'barcode.product',

    # Media models
    'media.type',

    # Key inventory models
    'key.inventory',

    # File retrieval models
    'file.retrieval.item',

    # Destruction models
    'destruction.item',

    # Advanced models
    'advanced.billing',

    # Paper models
    'paper.model_bale', 'paper.model_load', 'paper.model_shipment',

    # Shred models
    'shred.model_bin',

    # Certificate models
    'certificate.template.data',

    # Missing models (from missing_models.py)
    'fsm.notification.manager', 'naid.certificate', 'shredding.certificate',

    # Standard Odoo models (external dependencies)
    'hr.employee', 'maintenance.equipment', 'maintenance.team', 'project.task',
    'res.users', 'res.partner', 'res.company', 'res.currency', 'res.country', 'res.country.state',
    'account.move', 'sale.order', 'mail.message', 'ir.attachment', 'fleet.vehicle',
    'stock.location', 'stock.lot', 'survey.user_input', 'ir.model', 'ir.model.fields',
    'ir.rule', 'ir.ui.view', 'ir.actions.act_window', 'ir.actions.report'
}

def is_valid_model(model_id):
    """Check if a model ID is valid"""
    # Remove the 'model_' prefix if present (our corrected format)
    if model_id.startswith('model_'):
        model_id = model_id[6:]  # Remove 'model_' prefix

    # Check if it's in our valid models list
    return model_id in VALID_MODELS

def clean_csv_file(csv_path):
    """Remove invalid model entries from the CSV file"""
    print(f"Cleaning {csv_path}...")

    # Read the CSV file
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("CSV file is empty")
        return

    # Check header
    header = rows[0]
    if not header or len(header) < 3 or header[2] != 'model_id':
        print("Invalid CSV format - expected 'model_id' in column 3")
        return

    # Filter out invalid model entries
    original_count = len(rows) - 1  # Exclude header
    valid_rows = [header]  # Keep header
    removed_count = 0

    for row in rows[1:]:  # Skip header
        if row and len(row) >= 3:
            model_id = row[2]
            if is_valid_model(model_id):
                valid_rows.append(row)
            else:
                removed_count += 1
                print(f"Removed invalid model: {model_id}")

    # Write back the cleaned CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(valid_rows)

    print(f"Removed {removed_count} invalid model entries from {csv_path}")
    print(f"Kept {len(valid_rows) - 1} valid entries")

def main():
    """Main function"""
    if not sys.argv or len(sys.argv) != 2:
        print("Usage: python clean_invalid_models.py <csv_file>")
        sys.exit(1)

    csv_file = Path(sys.argv[1])
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        sys.exit(1)

    clean_csv_file(csv_file)

if __name__ == '__main__':
    main()
