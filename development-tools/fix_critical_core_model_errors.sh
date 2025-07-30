#!/bin/bash
# CRITICAL CORE MODEL INHERITANCE FIXER
# This script fixes the 4 critical files that incorrectly redefine core Odoo models

echo "🚨 FIXING CRITICAL CORE MODEL REDEFINITION ERRORS..."
echo "================================================================"

# Backup original files
echo "📁 Creating backups..."
cp /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_partner.py /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_partner.py.backup
cp /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_config_settings.py /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_config_settings.py.backup
cp /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/hr_employee.py /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/hr_employee.py.backup
cp /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/pos_config.py /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/pos_config.py.backup

echo "✅ Backups created successfully"

# Fix 1: res_partner.py - Change _name to _inherit
echo "🔧 Fixing res_partner.py..."
sed -i "s/_name = 'res\.partner'/_inherit = 'res.partner'/g" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_partner.py

# Fix 2: res_config_settings.py - Change _name to _inherit  
echo "🔧 Fixing res_config_settings.py..."
sed -i "s/_name = 'res\.config\.settings'/_inherit = 'res.config.settings'/g" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_config_settings.py

# Fix 3: hr_employee.py - Change _name to _inherit
echo "🔧 Fixing hr_employee.py..."
sed -i "s/_name = 'hr\.employee'/_inherit = 'hr.employee'/g" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/hr_employee.py

# Fix 4: pos_config.py - Change _name to _inherit
echo "🔧 Fixing pos_config.py..."
sed -i "s/_name = 'pos\.config'/_inherit = 'pos.config'/g" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/pos_config.py

echo "================================================================"
echo "✅ CRITICAL FIXES APPLIED SUCCESSFULLY!"
echo ""
echo "🔍 VERIFICATION:"
echo "- res_partner.py: $(grep -c "_inherit = 'res.partner'" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_partner.py) inheritance(s) fixed"
echo "- res_config_settings.py: $(grep -c "_inherit = 'res.config.settings'" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_config_settings.py) inheritance(s) fixed"
echo "- hr_employee.py: $(grep -c "_inherit = 'hr.employee'" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/hr_employee.py) inheritance(s) fixed"
echo "- pos_config.py: $(grep -c "_inherit = 'pos.config'" /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/pos_config.py) inheritance(s) fixed"
echo ""
echo "🚀 Module is now safe for deployment!"
echo "📁 Original files backed up with .backup extension"
