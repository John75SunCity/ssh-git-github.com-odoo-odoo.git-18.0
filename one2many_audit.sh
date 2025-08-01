#!/bin/bash
# One2many Relationship Audit Script

echo "=== One2many Relationship Audit ==="
echo "Checking custom model relationships (excluding mail.* models)..."
echo ""

# Define relationships to check (model_name:inverse_field)
relationships=(
    "records.billing.service:billing_id"
    "records.billing.contact:billing_profile_id" 
    "records.box:customer_inventory_id"
    "records.document:customer_inventory_id"
    "bin.key.history:partner_bin_key_id"
    "unlock.service.history:partner_bin_key_id"
    "photo:mobile_bin_key_wizard_id"
)

echo "=== CUSTOM RELATIONSHIP AUDIT ==="
for rel in "${relationships[@]}"; do
    model=$(echo $rel | cut -d: -f1)
    field=$(echo $rel | cut -d: -f2)
    
    echo "Checking: $model should have field '$field'"
    
    # Convert model name to file name
    file_pattern=$(echo $model | sed 's/\./_/g')
    
    # Look for the model file
    model_file=$(find records_management/models -name "*${file_pattern}*" -o -name "*$(echo $model | cut -d. -f2)*" | head -1)
    
    if [ -n "$model_file" ]; then
        echo "  ✓ Model file found: $model_file"
        if grep -q "$field" "$model_file"; then
            echo "  ✓ Inverse field '$field' found"
        else
            echo "  ❌ MISSING inverse field '$field'"
        fi
    else
        echo "  ❌ MISSING model file for '$model'"
    fi
    echo ""
done
