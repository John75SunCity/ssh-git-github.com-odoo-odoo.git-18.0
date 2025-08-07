#!/bin/bash

# Comprehensive syntax error fixer for records_management module
# Based on common patterns detected in error analysis

echo "🔧 Fixing syntax errors in records_management module..."

# List of files with missing comma patterns (most common error)
FILES_WITH_COMMA_ERRORS=(
    "records_management/models/naid_destruction_record.py"
    "records_management/models/advanced_billing.py"
    "records_management/models/base_rates.py"
    "records_management/models/partner_bin_key.py"
    "records_management/models/product_template.py"
    "records_management/models/revenue_forecaster.py"
    "records_management/models/records_billing_config.py"
    "records_management/models/customer_negotiated_rates.py"
    "records_management/models/naid_compliance_support_models.py"
    "records_management/models/records_chain_of_custody.py"
    "records_management/models/barcode_product.py"
    "records_management/models/records_management_base_menus.py"
    "records_management/models/records_container.py"
    "records_management/models/service_item.py"
    "records_management/models/document_retrieval_support_models.py"
    "records_management/models/document_retrieval_work_order.py"
    "records_management/models/shredding_hard_drive.py"
)

# Function to fix missing comma after field definition
fix_missing_comma_pattern() {
    local file="$1"
    echo "  Fixing missing commas in: $file"
    
    # Pattern 1: Missing comma at end of line with closing parenthesis
    sed -i 's/), required=True$/), required=True/g' "$file"
    sed -i 's/), string=".*"$/&/g' "$file"
    
    # Pattern 2: Field definition missing closing parenthesis
    # This requires more careful parsing - for now, just identify them
    python -c "
import re
import sys

try:
    with open('$file', 'r') as f:
        lines = f.readlines()
    
    modified = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Look for fields.* patterns missing closing parenthesis
        if 'fields.' in line and '(' in line and line.count('(') > line.count(')'):
            # This line likely starts a field definition
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If next line looks like another field or method, we need to close this field
                if (next_line.startswith(('def ', 'class ', '@api', '#')) or 
                    ('fields.' in next_line and '=' in next_line)):
                    # Add closing parenthesis to current line
                    line = line.rstrip() + '\n'
                    if not line.rstrip().endswith(')'):
                        line = line.rstrip() + ')\n'
        modified.append(line)
        i += 1
    
    with open('$file', 'w') as f:
        f.writelines(modified)
        
except Exception as e:
    print(f'Error processing {sys.argv[1]}: {e}', file=sys.stderr)
"
}

# Fix each file
for file in "${FILES_WITH_COMMA_ERRORS[@]}"; do
    if [[ -f "$file" ]]; then
        fix_missing_comma_pattern "$file"
    else
        echo "  ⚠️  File not found: $file"
    fi
done

echo "✅ Syntax error fixing complete!"
echo "🚀 Run the following to test:"
echo "cd /workspaces/ssh-git-github.com-odoo-odoo.git-18.0"
echo "find records_management/models -name '*.py' -exec python -m py_compile {} \\;"
