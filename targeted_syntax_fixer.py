#!/usr/bin/env python3
"""
Targeted Syntax Fixer for Records Management Module
Fixes the specific patterns identified by the comprehensive syntax checker
"""

import os
import re
from pathlib import Path

def fix_class_definition(content):
    """Fix class definitions missing closing parenthesis"""
    # Pattern: class ClassName(models.Model:
    pattern = r'class\s+(\w+)\(models\.Model:'
    replacement = r'class \1(models.Model):'
    return re.sub(pattern, replacement, content)

def fix_selection_brackets(content):
    """Fix Selection fields with wrong closing brackets"""
    # Pattern: ], string="Selection Field")
    content = re.sub(r'\], string="Selection Field"\)', '], string="Selection Field")', content)
    
    # Pattern: ], string=... where ] should be )
    # Look for Selection fields ending with ] instead of )
    lines = content.split('\n')
    fixed_lines = []
    in_selection = False
    selection_start = 0
    
    for i, line in enumerate(lines):
        if 'fields.Selection([' in line:
            in_selection = True
            selection_start = i
            fixed_lines.append(line)
        elif in_selection and line.strip().endswith('], string'):
            # This is wrong - should end with ), string
            fixed_line = line.replace('], string', '), string')
            fixed_lines.append(fixed_line)
            in_selection = False
        elif in_selection and '], string=' in line:
            # Fix the bracket
            fixed_line = line.replace('], string=', '), string=')
            fixed_lines.append(fixed_line)
            in_selection = False
        elif in_selection and line.strip().endswith(']') and 'string=' in lines[i+1] if i+1 < len(lines) else False:
            # Selection list ends with ] but string definition is on next line
            fixed_line = line.replace(']', ')')
            fixed_lines.append(fixed_line)
            in_selection = False
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_missing_parentheses(content):
    """Fix missing closing parentheses in field definitions"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check for field definitions that might be missing closing parentheses
        if ('fields.' in line and '(' in line and 
            not line.strip().endswith(')') and 
            not line.strip().endswith(',') and
            not line.strip().endswith(')')):
            
            # Look ahead to see if next line starts a new field or method
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if (next_line.startswith('def ') or 
                    next_line.startswith('class ') or
                    next_line.startswith('@') or
                    'fields.' in next_line or
                    next_line.startswith('#') or
                    next_line == ''):
                    # This field definition seems incomplete
                    if not line.strip().endswith(')'):
                        line = line.rstrip() + ')'
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_specific_patterns(content):
    """Fix specific patterns found in the syntax check"""
    
    # Fix comma before closing bracket in Selection
    content = re.sub(r"',\], string=", "'], string=", content)
    
    # Fix missing comma issues
    content = re.sub(r"help='([^']+)'\n\s*([a-zA-Z_])", r"help='\1',\n    \2", content)
    
    # Fix search domain issues - missing closing bracket
    content = re.sub(r"search\(\[([^\]]+)\n", r"search\([\1])\n", content)
    
    return content

def fix_file(filepath):
    """Fix a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes in order
        content = fix_class_definition(content)
        content = fix_selection_brackets(content)
        content = fix_missing_parentheses(content)
        content = fix_specific_patterns(content)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    """Main function to fix all files with syntax errors"""
    
    # List of files with syntax errors from the comprehensive check
    error_files = [
        'records_management/models/advanced_billing.py',
        'records_management/models/barcode_models.py',
        'records_management/models/barcode_product.py',
        'records_management/models/billing_models.py',
        'records_management/models/box_contents.py',
        'records_management/models/customer_feedback.py',
        'records_management/models/customer_inventory_report.py',
        'records_management/models/department_billing.py',
        'records_management/models/destruction_item.py',
        'records_management/models/document_retrieval_work_order.py',
        'records_management/models/fsm_task.py',
        'records_management/models/hr_employee.py',
        'records_management/models/hr_employee_naid.py',
        'records_management/models/ir_module.py',
        'records_management/models/load.py',
        'records_management/models/naid_audit.py',
        'records_management/models/naid_audit_log.py',
        'records_management/models/naid_certificate.py',
        'records_management/models/naid_compliance.py',
        'records_management/models/naid_compliance_checklist.py',
        'records_management/models/naid_custody.py',
        'records_management/models/naid_custody_event.py',
        'records_management/models/naid_destruction_record.py',
        'records_management/models/naid_performance_history.py',
        'records_management/models/paper_bale.py',
        'records_management/models/paper_bale_recycling.py',
        'records_management/models/paper_load_shipment.py',
        'records_management/models/pickup_request.py',
        'records_management/models/pickup_request_item.py',
        'records_management/models/portal_feedback.py',
        'records_management/models/portal_request.py',
        'records_management/models/pos_config.py',
        'records_management/models/product.py',
        'records_management/models/records_access_log.py',
        'records_management/models/records_approval_step.py',
        'records_management/models/records_approval_workflow.py',
        'records_management/models/records_audit_log.py',
        'records_management/models/records_box.py',
        'records_management/models/records_box_movement.py',
        'records_management/models/records_box_transfer.py',
        'records_management/models/records_chain_custody.py',
        'records_management/models/records_chain_of_custody.py',
        'records_management/models/records_deletion_request.py',
        'records_management/models/records_department_billing_contact.py',
        'records_management/models/records_digital_copy.py',
        'records_management/models/records_document.py',
        'records_management/models/records_document_type.py',
        'records_management/models/records_location_inspection.py',
        'records_management/models/records_policy_version.py',
        'records_management/models/records_retention_policy.py',
        'records_management/models/records_security_audit.py',
        'records_management/models/records_storage_department_user.py',
        'records_management/models/res_partner.py',
        'records_management/models/shredding_bin_models.py',
        'records_management/models/shredding_hard_drive.py',
        'records_management/models/shredding_inventory.py',
        'records_management/models/shredding_rates.py',
        'records_management/models/shredding_service.py',
        'records_management/models/stock_lot.py',
        'records_management/models/stock_picking.py',
        'records_management/models/survey_feedback_theme.py',
        'records_management/models/survey_improvement_action.py',
        'records_management/models/survey_user_input.py',
        'records_management/models/temp_inventory.py'
    ]
    
    print("🔧 Targeted Syntax Fixer for Records Management Module")
    print("=" * 60)
    print(f"🎯 Fixing {len(error_files)} files with identified syntax errors")
    print()
    
    fixed_count = 0
    
    for i, filepath in enumerate(error_files, 1):
        if os.path.exists(filepath):
            print(f"[{i:2d}/{len(error_files)}] Fixing {filepath}...", end=" ")
            
            if fix_file(filepath):
                print("✅ FIXED")
                fixed_count += 1
            else:
                print("⚪ NO CHANGES")
        else:
            print(f"[{i:2d}/{len(error_files)}] {filepath}... ❌ NOT FOUND")
    
    print()
    print("=" * 60)
    print(f"📊 SUMMARY: Fixed {fixed_count}/{len(error_files)} files")
    print("🎯 Run comprehensive_syntax_checker.py to verify fixes")

if __name__ == "__main__":
    main()
