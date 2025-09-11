#!/usr/bin/env python3
"""
Fix Common Syntax Errors Script
Systematically fixes common syntax errors that prevent module loading
"""

import os
import re
import glob

def fix_missing_comma_errors(filepath):
    """Fix missing comma errors in field definitions"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        fixed = False
        
        for i, line in enumerate(lines):
            # Look for field definitions missing commas
            if re.search(r'^\s+\w+\s*=\s*fields\.\w+\([^)]*\)$', line):
                # This line ends a field definition but might need a comma
                # Check if the next non-empty line is another field or method
                next_line_idx = i + 1
                while next_line_idx < len(lines) and not lines[next_line_idx].strip():
                    next_line_idx += 1
                
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    # If next line is another field definition, add comma
                    if (re.match(r'^\w+\s*=\s*fields\.', next_line) or
                        re.match(r'^@api\.|^def\s+', next_line)):
                        if not line.rstrip().endswith(','):
                            lines[i] = line.rstrip() + ','
                            fixed = True
        
        if fixed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            return True, "Fixed missing comma errors"
        
        return False, "No comma errors found"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_indentation_errors(filepath):
    """Fix unexpected indentation errors"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        fixed = False
        
        for i, line in enumerate(lines):
            # Look for common indentation issues
            if line.strip() and not line.startswith(' ' * 4) and not line.startswith('\t'):
                # Check if this should be indented (inside a class or method)
                context_indent = 0
                for j in range(i-1, -1, -1):
                    prev_line = lines[j].strip()
                    if prev_line and not prev_line.startswith('#'):
                        if prev_line.startswith('class ') or prev_line.startswith('def '):
                            context_indent = 4
                            break
                        elif lines[j].startswith('    '):
                            context_indent = 4
                            break
                        elif not lines[j].startswith(' '):
                            break
                
                # If we're in a class/method context and line should be indented
                if context_indent > 0 and line and not line.startswith('#'):
                    if not line.startswith(' '):
                        lines[i] = ' ' * context_indent + line
                        fixed = True
        
        if fixed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            return True, "Fixed indentation errors"
        
        return False, "No indentation errors found"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_syntax_errors_in_file(filepath):
    """Fix syntax errors in a single file"""
    filename = os.path.basename(filepath)
    results = []
    
    # Try fixing comma errors first
    success, message = fix_missing_comma_errors(filepath)
    if success:
        results.append(f"✅ {message}")
    
    # Try fixing indentation errors
    success, message = fix_indentation_errors(filepath)
    if success:
        results.append(f"✅ {message}")
    
    return results

def main():
    """Main function"""
    # List of files with known syntax errors
    error_files = [
        'bin_key_history.py',
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
        'records_inventory_dashboard.py',
        'records_access_log.py',
        'portal_feedback.py',
        'portal_feedback_action.py',
        'records_billing_contact.py',
        'advanced_billing_line.py',
        'records_retention_rule.py',
        'naid_compliance_checklist_item.py',
        'file_retrieval_work_order_item.py',
        'records_billing_profile.py'
    ]
    
    print("🔧 Fixing common syntax errors...\n")
    
    fixed_count = 0
    for filename in error_files:
        filepath = f'records_management/models/{filename}'
        if os.path.exists(filepath):
            print(f"🔧 Processing {filename}...")
            results = fix_syntax_errors_in_file(filepath)
            if results:
                for result in results:
                    print(f"   {result}")
                fixed_count += 1
            else:
                print(f"   ⏭️  No automatic fixes available")
        else:
            print(f"   ❌ File not found: {filepath}")
    
    print(f"\n📊 Summary: Attempted fixes on {fixed_count}/{len(error_files)} files")
    print("\n🎯 Next steps:")
    print("1. Run syntax validation again")
    print("2. Manually fix any remaining errors") 
    print("3. Try module loading again")

if __name__ == '__main__':
    main()
