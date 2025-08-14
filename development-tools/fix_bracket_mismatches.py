#!/usr/bin/env python3
"""
Fix Bracket Mismatch Errors
Fixes opening { with closing ) errors and other bracket mismatches
"""

import os
import re

def fix_bracket_mismatches(filepath):
    """Fix bracket and parenthesis mismatches"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix common bracket mismatches
        # Replace { followed by ) with properly matched parentheses
        content = re.sub(r'{\s*([^{}]*?)\s*\)', r'(\1)', content)
        
        # Fix [ followed by ) - should be ]
        content = re.sub(r'\[\s*([^\[\]]*?)\s*\)', r'[\1]', content)
        
        # Fix ( followed by } - should be )
        content = re.sub(r'\(\s*([^()]*?)\s*\}', r'(\1)', content)
        
        # Look for unmatched brackets in field definitions
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Check for field definitions with bracket issues
            if re.search(r'=\s*fields\.\w+\(', line):
                # Count brackets
                open_paren = line.count('(')
                close_paren = line.count(')')
                open_bracket = line.count('[')
                close_bracket = line.count(']')
                open_brace = line.count('{')
                close_brace = line.count('}')
                
                # If we have mismatched brackets, try to fix
                if open_brace > 0 and close_paren > close_brace:
                    # Replace { with (
                    line = line.replace('{', '(')
                    line = line.replace('}', ')')
            
            fixed_lines.append(line)
        
        fixed_content = '\n'.join(fixed_lines)
        
        if fixed_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True, "Fixed bracket mismatches"
        
        return False, "No bracket mismatches found"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_specific_syntax_errors():
    """Fix known syntax errors"""
    error_files = [
        'stock_lot_attribute_value.py',
        'document_retrieval_item.py', 
        'portal_feedback_analytic.py',
        'naid_compliance_action_plan.py',
        'naid_compliance_support_models.py',
        'barcode_product.py',
        'naid_risk_assessment.py',
        'base_rate.py',
        'records_location.py',
        'product_container_type.py',
        'records_customer_billing_profile.py',
        'approval_history.py',
        'naid_compliance_alert.py',
        'records_access_log.py',
        'portal_feedback.py',
        'records_billing_contact.py',
        'advanced_billing_line.py',
        'records_retention_rule.py',
        'naid_compliance_checklist_item.py',
        'file_retrieval_work_order_item.py',
        'records_billing_profile.py'
    ]
    
    print("🔧 Fixing bracket and parenthesis mismatches...\n")
    
    fixed_count = 0
    
    for filename in error_files:
        filepath = f'records_management/models/{filename}'
        if os.path.exists(filepath):
            print(f"🔧 Processing {filename}...")
            success, message = fix_bracket_mismatches(filepath)
            if success:
                print(f"   ✅ {message}")
                fixed_count += 1
            else:
                print(f"   ⏭️  {message}")
        else:
            print(f"   ❌ File not found: {filename}")
    
    print(f"\n📊 Summary: Fixed bracket mismatches in {fixed_count} files")
    
    # Also try to fix some specific indentation issues
    print("\n🔧 Fixing indentation issues...")
    
    indent_files = [
        'records_inventory_dashboard.py',
        'portal_feedback_action.py'
    ]
    
    for filename in indent_files:
        filepath = f'records_management/models/{filename}'
        if os.path.exists(filepath):
            fix_indentation_issues(filepath)

def fix_indentation_issues(filepath):
    """Fix basic indentation issues"""
    filename = os.path.basename(filepath)
    print(f"🔧 Processing indentation in {filename}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        in_class = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Track if we're inside a class
            if stripped.startswith('class ') and stripped.endswith(':'):
                in_class = True
                fixed_lines.append(line)
                continue
            
            # If we're in a class and line isn't properly indented
            if in_class and stripped and not stripped.startswith('#'):
                if not line.startswith('    ') and not line.startswith('\t'):
                    # Check if this should be a class-level item
                    if (stripped.startswith('_name') or 
                        stripped.startswith('_description') or
                        stripped.startswith('_inherit') or
                        '= fields.' in stripped or
                        stripped.startswith('def ')):
                        # Add proper indentation
                        fixed_lines.append('    ' + stripped + '\n')
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            
            # Reset class tracking at module level
            if not line.startswith(' ') and not line.startswith('\t') and stripped and not stripped.startswith('#'):
                if not stripped.startswith('class ') and not stripped.startswith('from ') and not stripped.startswith('import '):
                    in_class = False
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            
        print(f"   ✅ Fixed indentation issues")
        
    except Exception as e:
        print(f"   ❌ Error fixing indentation: {e}")

if __name__ == '__main__':
    fix_specific_syntax_errors()
