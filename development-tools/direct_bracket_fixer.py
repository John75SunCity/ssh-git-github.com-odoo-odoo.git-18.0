#!/usr/bin/env python3
"""
Direct Bracket Replacement Tool
Fixes specific bracket mismatches by examining context
"""

import os
import re
import ast

def fix_specific_bracket_errors(filepath):
    """Fix specific bracket errors in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Fix the most common patterns from the error messages:
        
        # Pattern 1: Opening ( with closing }
        # This usually happens in method calls that should return dictionaries
        # Find lines with opening ( followed eventually by closing }
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Look for write method calls that got messed up
            if 'write(' in line and '{' in line and '}' in line:
                # This is probably correct as write() expects a dictionary
                fixed_lines.append(line)
                continue
                
            # Look for problematic patterns where ( is opened but } is closed
            if re.search(r'\w+\s*\([^}]*\}', line):
                # Replace } with ) at the end of such patterns
                line = re.sub(r'(\w+\s*\([^}]*)\}', r'\1)', line)
            
            # Look for dictionary-like content that should use {} not ()
            if 'write(' in line and re.search(r"'[^']*':\s*[^,}]+", line) and line.count('(') > line.count('{'):
                # This looks like write with dictionary content but using parentheses
                # Convert to dictionary syntax
                match = re.search(r"write\(\s*([^)]+)\)", line)
                if match:
                    dict_content = match.group(1)
                    # If it looks like key:value pairs, wrap in {}
                    if ':' in dict_content and not dict_content.strip().startswith('['):
                        line = line.replace(f'write({dict_content})', f'write({{{dict_content}}})')
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Test syntax
        try:
            ast.parse(content)
            syntax_valid = True
            error_msg = ""
        except SyntaxError as e:
            syntax_valid = False
            error_msg = f"Line {e.lineno}: {e.msg}"
        
        if content != original_content:
            if syntax_valid:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return "fixed", "Bracket mismatches fixed successfully"
            else:
                # Save anyway and report the remaining error
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return "partial", f"Applied fixes but syntax error remains: {error_msg}"
        else:
            if syntax_valid:
                return "valid", "File already has valid syntax"
            else:
                return "error", f"File has syntax errors: {error_msg}"
                
    except Exception as e:
        return "error", f"Error processing file: {str(e)}"

def main():
    """Main function"""
    print("🔧 Direct Bracket Replacement Tool")
    print("=" * 50)
    
    error_files = [
        "stock_lot_attribute_value.py",
        "document_retrieval_item.py", 
        "portal_feedback_analytic.py",
        "naid_compliance_action_plan.py",
        "naid_compliance_support_models.py",
        "barcode_product.py",
        "naid_risk_assessment.py",
        "base_rate.py",
        "records_location.py",
        "product_container_type.py",
        "records_customer_billing_profile.py",
        "approval_history.py",
        "naid_compliance_alert.py",
        "records_inventory_dashboard.py",
        "records_access_log.py",
        "portal_feedback.py",
        "portal_feedback_action.py",
        "records_billing_contact.py",
        "records_retention_rule.py",
        "file_retrieval_work_order_item.py",
        "records_billing_profile.py"
    ]
    
    models_dir = "records_management/models"
    
    fixed_count = 0
    partial_count = 0
    valid_count = 0
    error_count = 0
    
    for filename in error_files[:5]:  # Process first 5 to test
        filepath = os.path.join(models_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"⚠️  {filename}: File not found")
            continue
            
        print(f"🔧 Processing {filename}...")
        
        result, message = fix_specific_bracket_errors(filepath)
        
        if result == "fixed":
            print(f"   ✅ {message}")
            fixed_count += 1
        elif result == "partial":
            print(f"   ⚠️  {message}")
            partial_count += 1
        elif result == "valid":
            print(f"   ✓ {message}")
            valid_count += 1
        else:
            print(f"   ❌ {message}")
            error_count += 1
    
    print(f"\n📊 Summary (first 5 files):")
    print(f"Files fixed: {fixed_count}")
    print(f"Files with partial fixes: {partial_count}")
    print(f"Files already valid: {valid_count}")
    print(f"Files with errors: {error_count}")

if __name__ == "__main__":
    main()
