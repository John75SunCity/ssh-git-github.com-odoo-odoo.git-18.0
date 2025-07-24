#!/bin/bash

# Script to add compute methods for activity_ids to all models that need them
# This script will add the compute method to the end of each model file

# Define the compute method template
COMPUTE_METHOD='
    # Compute method for activity_ids One2many field
    def _compute_activity_ids(self):
        """Compute activities for this record"""
        for record in self:
            record.activity_ids = self.env["mail.activity"].search([
                ("res_model", "=", "%s"),
                ("res_id", "=", record.id)
            ])'

# List of model files and their model names
declare -A MODEL_FILES=(
    ["records_management/models/records_document.py"]="records.document"
    ["records_management/models/records_retention_policy.py"]="records.retention.policy"
    ["records_management/models/portal_request.py"]="portal.request"
    ["records_management/models/billing.py"]="records.billing"
    ["records_management/models/stock_lot.py"]="stock.lot"
    ["records_management/models/records_location.py"]="records.location"
    ["records_management/models/paper_bale.py"]="paper.bale"
    ["records_management/models/naid_compliance.py"]="naid.compliance"
    ["records_management/models/barcode_product.py"]="barcode.product"
    ["records_management/models/department_billing.py"]="records.department.billing.contact"
    ["records_management/models/records_box.py"]="records.box"
)

# Add compute methods to each file
for file in "${!MODEL_FILES[@]}"; do
    model_name="${MODEL_FILES[$file]}"
    
    # Check if file exists
    if [ -f "$file" ]; then
        echo "Adding compute method to $file for model $model_name"
        
        # Create the specific compute method for this model
        specific_compute=$(printf "$COMPUTE_METHOD" "$model_name")
        
        # Append the compute method to the end of the file
        echo "$specific_compute" >> "$file"
        
        echo "✅ Added compute method to $file"
    else
        echo "❌ File $file not found"
    fi
done

echo "🎉 All compute methods added successfully!"
