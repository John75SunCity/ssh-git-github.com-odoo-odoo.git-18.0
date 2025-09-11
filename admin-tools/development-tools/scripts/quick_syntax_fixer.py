#!/usr/bin/env python3
"""
Quick fixer for the most common syntax errors introduced by duplicate field removal
Fixes "unexpected indent" errors by checking the context
"""

import os
import re
from pathlib import Path

def fix_file(file_path):
    """Fix common syntax errors in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        changed = False
        
        for i, line in enumerate(lines):
            # Check for "unexpected indent" pattern after field removal
            if i > 0 and line.strip().startswith(('compute=', 'store=', 'string=', 'help=', 'default=')):
                # This is likely an orphaned field parameter after duplicate removal
                # Check if previous line is incomplete field definition
                prev_line = lines[i-1].strip()
                if not prev_line.endswith((',', '(', '[', '=')) and not 'fields.' in prev_line:
                    # Skip this orphaned parameter line
                    print(f"  Removing orphaned parameter: {line.strip()}")
                    changed = True
                    continue
            
            # Check for lines that start with closing brackets/parentheses
            if line.strip().startswith((']', ')', '},')) and i > 0:
                # Check if this is an unmatched closing bracket
                prev_line = lines[i-1].strip()
                if prev_line.endswith(('=', ',', '[', '(')):
                    # This is likely an unmatched closing bracket
                    print(f"  Removing unmatched bracket: {line.strip()}")
                    changed = True
                    continue
            
            fixed_lines.append(line)
        
        if changed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix common syntax errors"""
    models_dir = Path('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models')
    
    # Files with known syntax errors
    error_files = [
        'billing_automation.py',
        'billing_models.py', 
        'document_retrieval_work_order.py',
        'hr_employee_naid.py',
        'pickup_request.py',
        'portal_request.py',
        'records_department_billing_contact.py',
        'records_location.py',
        'shredding_bin_models.py',
        'shredding_inventory.py',
        'shredding_rates.py',
        'visitor_pos_wizard.py',
        'work_order_shredding.py'
    ]
    
    print("🔧 Fixing common syntax errors from duplicate removal...")
    print("=" * 60)
    
    fixed_count = 0
    
    for filename in error_files:
        file_path = models_dir / filename
        if file_path.exists():
            print(f"\n📄 Fixing: {filename}")
            if fix_file(file_path):
                fixed_count += 1
                print(f"  ✅ Fixed")
            else:
                print(f"  ℹ️  No changes needed")
        else:
            print(f"  ❌ File not found: {filename}")
    
    print(f"\n📊 Summary: Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
