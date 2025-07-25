#!/usr/bin/env python3
import re

# Read current security file
with open('security/ir.model.access.csv', 'r') as f:
    lines = f.readlines()

# Define existing models based on our scan
existing_models = {
    'records.box', 'records.document', 'records.document.type', 'records.location',
    'records.retention.policy', 'pickup.request', 'pickup.request.item', 'records.tag',
    'shredding.service', 'destruction.item', 'customer.inventory.report', 'records.department',
    'records.storage.department.user', 'records.service.request', 'records.management.installer',
    'scrm.records.management', 'stock.move.sms.validation', 'records.department.billing.contact',
    'paper.bale', 'portal.request', 'shredding.hard.drive', 'hard.drive.scan.wizard',
    'survey.feedback.theme', 'survey.improvement.action', 'temp.inventory', 'visitor.pos.wizard',
    'records.box.type.converter', 'naid.audit.log', 'naid.compliance.policy', 'naid.chain.custody',
    'naid.custody.event', 'customer.feedback', 'records.wizard.template', 'records.bulk.operation.wizard',
    # New models we just created
    'records.deletion.request', 'records.user.invitation.wizard', 'records.bulk.user.import',
    'records.billing.config', 'records.billing.period', 'records.billing.line',
    'records.service.pricing', 'records.service.pricing.break', 'records.product',
    'records.billing.automation', 'res.partner.department.billing', 'records.barcode.config',
    'records.barcode.history', 'records_management.bale', 'records_management.load'
}

# Keep only lines for existing models or header
clean_lines = []
removed_count = 0

for line in lines:
    if line.startswith('id,name'):  # Header
        clean_lines.append(line)
        continue
    
    # Extract model name from the line
    parts = line.split(',')
    if len(parts) >= 3:
        model_ref = parts[2]  # model_id:id column
        # Convert model_* to actual model name
        if model_ref.startswith('model_'):
            model_name = model_ref[6:]  # Remove 'model_' prefix
            model_name = model_name.replace('_', '.')
            
            if model_name in existing_models:
                clean_lines.append(line)
            else:
                print(f'Removing line for non-existent model: {model_name}')
                removed_count += 1
        else:
            # Keep lines that don't follow the model_* pattern
            clean_lines.append(line)

print(f'Original lines: {len(lines)}')
print(f'Clean lines: {len(clean_lines)}')
print(f'Removed {removed_count} lines')

# Write cleaned file
with open('security/ir.model.access.csv', 'w') as f:
    f.writelines(clean_lines)

print('Security file cleaned successfully')
