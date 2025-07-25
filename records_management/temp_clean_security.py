#!/usr/bin/env python3

# Read current security file
with open('security/ir.model.access.csv', 'r') as f:
    lines = f.readlines()

# Models mentioned in the error that might not exist yet
problematic_models = {
    'model_records_deletion_request',
    'model_records_user_invitation_wizard', 
    'model_records_bulk_user_import',
    'model_records_billing_config',
    'model_records_billing_period', 
    'model_records_billing_line',
    'model_records_service_pricing',
    'model_records_service_pricing_break',
    'model_records_product',
    'model_records_billing_automation',
    'model_res_partner_department_billing',
    'model_records_barcode_config',
    'model_records_barcode_history'
}

# Create a backup and filtered version
clean_lines = []
removed_count = 0

for line in lines:
    if line.startswith('id,name'):  # Header
        clean_lines.append(line)
        continue
    
    # Check if this line references a problematic model
    parts = line.split(',')
    if len(parts) >= 3:
        model_ref = parts[2].strip()  # model_id:id column
        
        if model_ref in problematic_models:
            print(f'Temporarily removing line for: {model_ref}')
            removed_count += 1
        else:
            clean_lines.append(line)
    else:
        clean_lines.append(line)

print(f'Original lines: {len(lines)}')
print(f'Clean lines: {len(clean_lines)}')
print(f'Temporarily removed {removed_count} lines')

# Create backup
with open('security/ir.model.access.csv.backup', 'w') as f:
    f.writelines(lines)

# Write temporary cleaned file
with open('security/ir.model.access.csv', 'w') as f:
    f.writelines(clean_lines)

print('Created backup and cleaned security file for testing')
