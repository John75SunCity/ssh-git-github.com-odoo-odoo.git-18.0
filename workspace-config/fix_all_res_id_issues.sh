#!/bin/bash

# Script to fix all remaining One2many fields with 'res_id' inverse field issues
# This will replace all instances and add compute methods

echo "🔧 Starting comprehensive fix for all 'res_id' inverse field issues..."

# Fix message_follower_ids fields
echo "📧 Fixing message_follower_ids fields..."

# List of files that need message_follower_ids fixed
FILES_WITH_FOLLOWERS=(
    "records_management/models/records_retention_policy.py"
    "records_management/models/naid_compliance.py"
    "records_management/models/portal_feedback.py" 
    "records_management/models/portal_request.py"
    "records_management/models/stock_lot.py"
    "records_management/models/paper_bale.py"
    "records_management/models/records_location.py"
    "records_management/models/records_document.py"
    "records_management/models/barcode_product.py"
    "records_management/models/records_box.py"
    "records_management/models/department_billing.py"
)

for file in "${FILES_WITH_FOLLOWERS[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✏️ Fixing $file"
        
        # Replace message_follower_ids with compute method
        sed -i "s/message_follower_ids = fields\.One2many('mail\.followers', 'res_id'/message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers'/g" "$file"
        sed -i '/message_follower_ids.*domain=lambda self/d' "$file"
        
        # Replace message_ids with compute method  
        sed -i "s/message_ids = fields\.One2many('mail\.message', 'res_id'/message_ids = fields.One2many('mail.message', compute='_compute_message_ids'/g" "$file"
        sed -i '/message_ids.*domain=lambda self/d' "$file"
        
        echo "  ✅ Fixed field definitions in $file"
    fi
done

echo "📊 Adding compute methods for message followers and messages..."

# Define compute method templates
MESSAGE_FOLLOWER_COMPUTE='
    def _compute_message_followers(self):
        """Compute message followers for this record"""
        for record in self:
            record.message_follower_ids = self.env["mail.followers"].search([
                ("res_model", "=", "%s"),
                ("res_id", "=", record.id)
            ])'

MESSAGE_COMPUTE='
    def _compute_message_ids(self):
        """Compute messages for this record"""
        for record in self:
            record.message_ids = self.env["mail.message"].search([
                ("res_model", "=", "%s"),
                ("res_id", "=", record.id)
            ])'

# Map files to their model names
declare -A MODEL_NAMES=(
    ["records_management/models/records_retention_policy.py"]="records.retention.policy"
    ["records_management/models/naid_compliance.py"]="naid.compliance"
    ["records_management/models/portal_feedback.py"]="portal.feedback"
    ["records_management/models/portal_request.py"]="portal.request"
    ["records_management/models/stock_lot.py"]="stock.lot"
    ["records_management/models/paper_bale.py"]="paper.bale"
    ["records_management/models/records_location.py"]="records.location"
    ["records_management/models/records_document.py"]="records.document"
    ["records_management/models/barcode_product.py"]="barcode.product"
    ["records_management/models/records_box.py"]="records.box"
    ["records_management/models/department_billing.py"]="records.department.billing.contact"
)

# Add compute methods to each file
for file in "${!MODEL_NAMES[@]}"; do
    if [ -f "$file" ]; then
        model_name="${MODEL_NAMES[$file]}"
        
        echo "  🔧 Adding compute methods to $file for model $model_name"
        
        # Add message follower compute method
        follower_method=$(printf "$MESSAGE_FOLLOWER_COMPUTE" "$model_name")
        echo "$follower_method" >> "$file"
        
        # Add message compute method
        message_method=$(printf "$MESSAGE_COMPUTE" "$model_name")
        echo "$message_method" >> "$file"
        
        echo "  ✅ Added compute methods to $file"
    fi
done

echo "🎉 Comprehensive fix completed! All 'res_id' inverse field issues should now be resolved."
echo "📋 Summary:"
echo "  - Fixed message_follower_ids fields in ${#FILES_WITH_FOLLOWERS[@]} files"
echo "  - Fixed message_ids fields in ${#FILES_WITH_FOLLOWERS[@]} files"
echo "  - Added compute methods to ${#MODEL_NAMES[@]} files"
