#!/bin/bash

# Comprehensive syntax fixer for missing closing parentheses
# This script fixes the most common pattern: missing ) before next field

echo "🔧 FIXING SYNTAX ERRORS - BATCH PROCESSING"
echo "============================================"

cd /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models

# Function to fix missing closing parentheses in Python field definitions
fix_missing_parentheses() {
    local file="$1"
    echo "Processing: $file"
    
    # Common pattern: field definition missing closing parenthesis before next field
    # Look for: ) followed by field_name = instead of )\n    field_name =
    
    python3 -c "
import re

with open('$file', 'r') as f:
    content = f.read()

original = content

# Fix pattern: missing ) before next field definition
# Pattern 1: default=something\n    next_field = fields.
content = re.sub(
    r'(default=[^,)]*)\n(\s+)([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*fields\.)',
    r'\1\n\2)\n\2\3',
    content,
    flags=re.MULTILINE
)

# Pattern 2: string=\"Something\"\n    next_field = fields.
content = re.sub(
    r'(string=[^,)]*)\n(\s+)([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*fields\.)',
    r'\1\n\2)\n\2\3',
    content,
    flags=re.MULTILINE
)

# Pattern 3: help=\"Something\"\n    next_field = fields.
content = re.sub(
    r'(help=[^,)]*)\n(\s+)([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*fields\.)',
    r'\1\n\2)\n\2\3',
    content,
    flags=re.MULTILINE
)

if content != original:
    with open('$file', 'w') as f:
        f.write(content)
    print('  ✅ Fixed missing parentheses')
else:
    print('  ⏭️  No parentheses fixes needed')
"
}

# Files to process (first batch - missing comma/parentheses errors)
files=(
    "customer_feedback.py"
    "customer_inventory.py"
    "customer_inventory_report.py"
    "document_retrieval_support_models.py"
    "document_retrieval_work_order.py"
    "fsm_task.py"
    "integration_error.py"
    "key_restriction_checker.py"
    "load.py"
    "location_report_wizard.py"
    "maintenance_extensions.py"
    "naid_certificate.py"
    "naid_compliance_support_models.py"
    "partner_bin_key.py"
    "payment_split.py"
    "photo.py"
    "pickup_route.py"
    "portal_feedback.py"
    "portal_feedback_support_models.py"
    "portal_request.py"
    "pos_config.py"
    "processing_log.py"
    "product_template.py"
    "records_access_log.py"
    "records_billing_config.py"
    "records_billing_contact.py"
    "records_bin.py"
    "records_chain_of_custody.py"
    "records_container_movement.py"
    "records_container_type.py"
    "records_container_type_converter.py"
    "records_department_billing_contact.py"
    "records_digital_scan.py"
    "records_document.py"
    "records_management_base_menus.py"
    "records_permanent_flag_wizard.py"
    "records_retention_policy.py"
    "records_vehicle.py"
    "res_partner.py"
    "revenue_forecaster.py"
    "service_item.py"
    "shredding_certificate.py"
    "shredding_hard_drive.py"
    "shredding_inventory.py"
    "shredding_inventory_item.py"
    "shredding_service.py"
    "shredding_team.py"
    "transitory_field_config.py"
    "unlock_service_history.py"
    "visitor_pos_wizard.py"
)

fixed_count=0
total_count=${#files[@]}

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        fix_missing_parentheses "$file"
        ((fixed_count++))
    else
        echo "⚠️  File not found: $file"
    fi
done

echo ""
echo "🎯 BATCH 1 COMPLETE: $fixed_count/$total_count files processed"
echo "============================================"
