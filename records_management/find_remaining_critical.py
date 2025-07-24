#!/usr/bin/env python3
"""
Find remaining critical One2many field issues that are most likely to cause KeyError
"""

import os
import re

def scan_for_problematic_fields():
    """Find One2many fields that don't use compute methods and likely cause KeyError"""
    problematic_fields = []
    
    models_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Find One2many fields that DON'T use compute=
            one2many_pattern = r"fields\.One2many\([^)]*?(?:'([^']+)'[^)]*?,\s*'([^']+)'[^)]*?)?\)"
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'fields.One2many(' in line and 'compute=' not in line:
                    # Skip commented lines
                    if line.strip().startswith('#'):
                        continue
                    
                    # Extract the field definition (may span multiple lines)
                    field_def = line.strip()
                    line_num = i
                    
                    # If line doesn't end with ), it's a multi-line field
                    if not line.rstrip().endswith(')'):
                        j = i
                        while j < len(lines) and not lines[j].rstrip().endswith(')'):
                            j += 1
                            if j < len(lines):
                                field_def += ' ' + lines[j].strip()
                    
                    # Skip mail.activity, mail.followers, mail.message fields
                    if any(mail_field in field_def for mail_field in ['mail.activity', 'mail.followers', 'mail.message']):
                        continue
                        
                    # Skip ir.attachment fields
                    if 'ir.attachment' in field_def:
                        continue
                    
                    problematic_fields.append({
                        'file': filename,
                        'line': line_num,
                        'field_def': field_def
                    })
    
    return problematic_fields

def main():
    print("=== FINDING REMAINING CRITICAL ONE2MANY ISSUES ===\n")
    
    problematic = scan_for_problematic_fields()
    
    if not problematic:
        print("🎉 NO REMAINING CRITICAL ISSUES FOUND!")
        return
    
    print(f"Found {len(problematic)} potentially problematic One2many fields:\n")
    
    for field in problematic:
        print(f"📄 {field['file']}:{field['line']}")
        print(f"   {field['field_def'][:100]}{'...' if len(field['field_def']) > 100 else ''}")
        print()
    
    print(f"\n🔍 Total critical fields to review: {len(problematic)}")

if __name__ == "__main__":
    main()
