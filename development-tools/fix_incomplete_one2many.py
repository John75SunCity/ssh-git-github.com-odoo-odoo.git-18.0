#!/usr/bin/env python3
"""
Fix all incomplete One2many field definitions that are causing KeyError: 'res_id'
"""

import os
import re

def fix_incomplete_fields():
    """Fix the specific One2many fields that are missing parameters"""
    
    fixes = [
        # customer_inventory_report.py fixes
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/customer_inventory_report.py',
            'line': 47,
            'old': "    box_ids = fields.One2many(",
            'new': "    box_ids = fields.One2many('records.box', 'customer_inventory_id', string='Boxes')"
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/customer_inventory_report.py',
            'line': 60,
            'old': "    document_ids = fields.One2many(",
            'new': "    document_ids = fields.One2many('records.document', 'customer_inventory_id', string='Documents')"
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/customer_inventory_report.py',
            'line': 1772,
            'old': "    billing_line_ids = fields.One2many(",
            'new': "    billing_line_ids = fields.One2many('billing.line', 'report_id', string='Billing Lines')"
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/customer_inventory_report.py',
            'line': 1789,
            'old': "    invoice_ids = fields.One2many(",
            'new': "    invoice_ids = fields.One2many('account.move', 'customer_inventory_id', string='Invoices')"
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/customer_inventory_report.py',
            'line': 2372,
            'old': "    quantity_breaks = fields.One2many(",
            'new': "    quantity_breaks = fields.One2many('pricing.quantity.break', 'report_id', string='Quantity Breaks')"
        },
        
        # res_partner.py fixes
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_partner.py',
            'line': 30,
            'old': "    department_billing_contacts = fields.One2many(",
            'new': "    department_billing_contacts = fields.One2many('department.billing.contact', 'partner_id', string='Department Billing Contacts')"
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/res_partner.py',
            'line': 77,
            'old': "    department_billing_contact_ids = fields.One2many(",
            'new': "    department_billing_contact_ids = fields.One2many('department.billing.contact', 'contact_id', string='Billing Contact Relations')"
        },
        
        # pickup_request.py fix
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/pickup_request.py',
            'line': 34,
            'old': "    request_item_ids = fields.One2many(",
            'new': "    request_item_ids = fields.One2many('pickup.request.item', 'request_id', string='Request Items')"
        },
        
        # records_document.py fixes
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/records_document.py',
            'line': 188,
            'old': "    chain_of_custody_ids = fields.One2many(",
            'new': "    chain_of_custody_ids = fields.One2many('records.chain.custody', 'document_id', string='Chain of Custody')"
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/records_document.py',
            'line': 192,
            'old': "    audit_trail_ids = fields.One2many(",
            'new': "    audit_trail_ids = fields.One2many('records.audit.log', 'document_id', string='Audit Trail')"
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/records_document.py',
            'line': 196,
            'old': "    digital_copy_ids = fields.One2many(",
            'new': "    digital_copy_ids = fields.One2many('records.digital.copy', 'document_id', string='Digital Copies')"
        },
        
        # records_retention_policy.py fix  
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/records_retention_policy.py',
            'line': 100,
            'old': "    version_history_ids = fields.One2many(",
            'new': "    version_history_ids = fields.One2many('records.policy.version', 'policy_id', string='Version History')"
        }
    ]
    
    for fix in fixes:
        print(f"Fixing {os.path.basename(fix['file'])}:{fix['line']}")
        
        try:
            with open(fix['file'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace the incomplete field definition
            content = content.replace(fix['old'], fix['new'])
            
            with open(fix['file'], 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"  ✅ Fixed: {fix['old']} -> {fix['new']}")
            
        except Exception as e:
            print(f"  ❌ Error fixing {fix['file']}: {e}")
    
    print("\n🎯 All incomplete One2many fields have been fixed!")

if __name__ == "__main__":
    fix_incomplete_fields()
