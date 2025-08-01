#!/bin/bash
# Fix ir.model.access.csv by removing references to non-existent models

cd /workspaces/ssh-git-github.com-odoo-odoo.git-18.0

# Backup the original file
cp records_management/security/ir.model.access.csv records_management/security/ir.model.access.csv.backup

# Remove lines with non-existent models
sed -i '/pickup\.route\.stop/d' records_management/security/ir.model.access.csv
sed -i '/shredding\.base\.rates/d' records_management/security/ir.model.access.csv  
sed -i '/key\.restriction\.wizard/d' records_management/security/ir.model.access.csv

echo "✅ Removed references to non-existent models:"
echo "   - pickup.route.stop" 
echo "   - shredding.base.rates"
echo "   - key.restriction.wizard"

# Check if customer.inventory model exists
if ! grep -r "_name.*=.*['\"]customer\.inventory['\"]" records_management/models/; then
    echo "⚠️  customer.inventory model not found, removing from CSV..."
    sed -i '/customer\.inventory/d' records_management/security/ir.model.access.csv
fi

echo "✅ CSV cleanup completed"
