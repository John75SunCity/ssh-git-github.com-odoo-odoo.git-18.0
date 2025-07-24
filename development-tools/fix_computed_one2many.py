#!/usr/bin/env python3
"""
Remove Problematic Computed One2many Fields
These fields are causing KeyError: 'res_id' because they point to non-existent models
or models without proper res_id relationships
"""

import os
import re

def remove_problematic_fields():
    """Remove computed One2many fields that cause res_id errors"""
    
    fixes = [
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/naid_compliance.py',
            'pattern': r'\s*audit_history_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/naid_compliance.py',
            'pattern': r'\s*certificate_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/naid_compliance.py',
            'pattern': r'\s*destruction_record_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/naid_compliance.py',
            'pattern': r'\s*performance_history_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/naid_compliance.py',
            'pattern': r'\s*compliance_checklist_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/product.py',
            'pattern': r'\s*pricing_rule_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        },
        {
            'file': '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/product.py',
            'pattern': r'\s*sales_analytics_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        },
    ]
    
    total_fixes = 0
    
    for fix in fixes:
        file_path = fix['file']
        pattern = fix['pattern']
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    total_fixes += 1
                    print(f"✅ Fixed {os.path.basename(file_path)}")
                    
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    print(f"\n🎯 Removed {total_fixes} problematic computed One2many fields")
    print("⚠️  These fields were pointing to non-existent models or missing res_id relationships")

if __name__ == "__main__":
    remove_problematic_fields()
