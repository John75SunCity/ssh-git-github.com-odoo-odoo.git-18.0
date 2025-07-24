#!/bin/bash

# Script to add missing @api.depends() decorators to compute methods

echo "🔧 Adding missing @api.depends() decorators to compute methods..."

# List of files and their compute methods that need @api.depends() decorators
declare -A METHODS=(
    # stock_lot.py methods
    ["records_management/models/stock_lot.py:_compute_quantities"]="@api.depends('quant_ids')"
    ["records_management/models/stock_lot.py:_compute_movement_metrics"]="@api.depends('stock_move_ids')"
    ["records_management/models/stock_lot.py:_compute_inventory_metrics"]="@api.depends('quant_ids')"
    ["records_management/models/stock_lot.py:_compute_current_location"]="@api.depends('quant_ids')"
    ["records_management/models/stock_lot.py:_compute_quality_metrics"]="@api.depends('quality_check_ids')"
    ["records_management/models/stock_lot.py:_compute_quant_metrics"]="@api.depends('quant_ids')"
    ["records_management/models/stock_lot.py:_compute_move_metrics"]="@api.depends('stock_move_ids')"
    ["records_management/models/stock_lot.py:_compute_value_metrics"]="@api.depends('quant_ids')"
    ["records_management/models/stock_lot.py:_compute_activity_ids"]="@api.depends()"
    ["records_management/models/stock_lot.py:_compute_message_followers"]="@api.depends()"
    ["records_management/models/stock_lot.py:_compute_message_ids"]="@api.depends()"
    
    # product.py methods
    ["records_management/models/product.py:_compute_product_metrics"]="@api.depends('stock_move_ids')"
    ["records_management/models/product.py:_compute_display_name"]="@api.depends('name', 'default_code')"
    ["records_management/models/product.py:_compute_activity_ids"]="@api.depends()"
    ["records_management/models/product.py:_compute_message_followers"]="@api.depends()"
    ["records_management/models/product.py:_compute_message_ids"]="@api.depends()"
    
    # billing.py methods
    ["records_management/models/billing.py:_compute_activity_ids"]="@api.depends()"
    
    # fsm_task.py methods
    ["records_management/models/fsm_task.py:_compute_activity_ids"]="@api.depends()"
    ["records_management/models/fsm_task.py:_compute_material_usage_ids"]="@api.depends()"
    ["records_management/models/fsm_task.py:_compute_message_followers"]="@api.depends()"
    ["records_management/models/fsm_task.py:_compute_message_ids"]="@api.depends()"
    ["records_management/models/fsm_task.py:_compute_mobile_update_ids"]="@api.depends()"
    
    # portal_request.py methods
    ["records_management/models/portal_request.py:_compute_related_request_count"]="@api.depends('related_request_ids')"
    ["records_management/models/portal_request.py:_compute_activity_ids"]="@api.depends()"
    ["records_management/models/portal_request.py:_compute_message_followers"]="@api.depends()"
    ["records_management/models/portal_request.py:_compute_message_ids"]="@api.depends()"
    
    # shredding_service.py methods
    ["records_management/models/shredding_service.py:_compute_certificate_count"]="@api.depends('certificate_ids')"
    ["records_management/models/shredding_service.py:_compute_witness_count"]="@api.depends('witness_ids')"
    ["records_management/models/shredding_service.py:_compute_activity_ids"]="@api.depends()"
    ["records_management/models/shredding_service.py:_compute_message_followers"]="@api.depends()"
    ["records_management/models/shredding_service.py:_compute_message_ids"]="@api.depends()"
    
    # hr_employee_naid.py methods
    ["records_management/models/hr_employee_naid.py:_compute_compliance_status"]="@api.depends('background_check_status', 'naid_certification_status')"
    
    # records_retention_policy.py methods
    ["records_management/models/records_retention_policy.py:_compute_activity_ids"]="@api.depends()"
    ["records_management/models/records_retention_policy.py:_compute_message_followers"]="@api.depends()"
    ["records_management/models/records_retention_policy.py:_compute_message_ids"]="@api.depends()"
    
    # pos_config.py methods
    ["records_management/models/pos_config.py:_compute_session_info"]="@api.depends('current_session_id')"
    ["records_management/models/pos_config.py:_compute_activity_ids"]="@api.depends()"
    ["records_management/models/pos_config.py:_compute_message_followers"]="@api.depends()"
    ["records_management/models/pos_config.py:_compute_message_ids"]="@api.depends()"
)

# Function to add @api.depends decorator
add_api_depends() {
    local file="$1"
    local method="$2"
    local decorator="$3"
    
    if [ -f "$file" ]; then
        echo "  🔧 Adding $decorator to $method in $file"
        
        # Use sed to add @api.depends decorator before the method definition
        sed -i "/def $method(/i\\    $decorator" "$file"
        
        echo "  ✅ Added decorator to $method"
    else
        echo "  ❌ File not found: $file"
    fi
}

# Process each method
for key in "${!METHODS[@]}"; do
    IFS=':' read -r file method <<< "$key"
    decorator="${METHODS[$key]}"
    add_api_depends "$file" "$method" "$decorator"
done

echo "🎉 Completed adding @api.depends decorators!"
echo "📊 Processed ${#METHODS[@]} compute methods"
