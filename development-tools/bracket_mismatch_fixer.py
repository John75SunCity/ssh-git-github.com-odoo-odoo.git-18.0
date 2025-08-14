#!/usr/bin/env python3
"""
Bracket Mismatch Fixer
Fixes the specific issue where { is used instead of ( in field definitions
"""

import os
import re
import ast

def fix_bracket_mismatches(content):
    """Fix { vs ( mismatches in field definitions"""
    
    # Pattern: Find lines with field definitions that use { instead of (
    # Example: state = fields.Selection({
    #          should be: state = fields.Selection([
    
    # Fix Selection fields with { instead of [
    content = re.sub(
        r'(= fields\.Selection)\s*\{',
        r'\1([',
        content
    )
    
    # Fix other field types with { instead of (
    content = re.sub(
        r'(= fields\.\w+)\s*\{',
        r'\1(',
        content
    )
    
    # Fix any remaining stray { that should be (
    # Look for patterns where { is used in field parameters
    content = re.sub(
        r'\{\s*(\'\w+\':\s*\'[^\']*\')',
        r'(\1',
        content
    )
    
    # Fix closing ] that should be ])
    content = re.sub(
        r'(\s*\],\s*string=)',
        r']), string=',
        content
    )
    
    return content

def fix_file(filepath):
    """Fix bracket mismatches in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = fix_bracket_mismatches(original_content)
        
        # Test syntax
        try:
            ast.parse(content)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            error_msg = f"Line {e.lineno}: {e.msg}"
            return "partial", f"Applied fixes but syntax error remains: {error_msg}"
        
        if content != original_content:
            if syntax_valid:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return "fixed", "Bracket mismatches fixed"
            else:
                return "partial", "Applied fixes but syntax still invalid"
        else:
            if syntax_valid:
                return "valid", "No changes needed - syntax is valid"
            else:
                return "error", "File has syntax errors but no bracket issues detected"
            
    except Exception as e:
        return "error", f"Error processing file: {str(e)}"

def main():
    """Main function"""
    print("🔧 Bracket Mismatch Fixer")
    print("=" * 40)
    
    # Files with bracket mismatch errors
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
    
    for filename in error_files:
        filepath = os.path.join(models_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"⚠️  {filename}: File not found")
            continue
        
        print(f"🔧 Processing {filename}...")
        
        result, message = fix_file(filepath)
        
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
    
    print(f"\n📊 Summary:")
    print(f"Files fixed: {fixed_count}")
    print(f"Files with partial fixes: {partial_count}")
    print(f"Files already valid: {valid_count}")
    print(f"Files with errors: {error_count}")

if __name__ == "__main__":
    main()
