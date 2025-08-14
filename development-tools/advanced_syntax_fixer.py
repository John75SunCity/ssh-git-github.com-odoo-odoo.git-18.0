#!/usr/bin/env python3
"""
Advanced Syntax Fixer for Records Management
Handles specific patterns from bulk field additions
"""

import os
import re
import ast

def fix_malformed_field_definitions(content):
    """Fix field definitions where content got mixed up during bulk edits"""
    
    # Pattern 1: Many2one field with missing comodel definition
    # partner_id = fields.Many2one(
    #     [state field content]
    #     "res.partner",
    pattern1 = re.compile(
        r'(\w+_id\s*=\s*fields\.Many2one\(\s*\n)'
        r'(.*?# Workflow state management.*?help=\'[^\']*\'\))'
        r'(\s*"[^"]+",.*?\))',
        re.DOTALL
    )
    
    def fix_pattern1(match):
        field_start = match.group(1)
        misplaced_content = match.group(2)
        field_params = match.group(3)
        
        # Extract the state field from misplaced content
        state_match = re.search(
            r'(# Workflow state management.*?help=\'[^\']*\'\))', 
            misplaced_content, 
            re.DOTALL
        )
        
        if state_match:
            state_content = state_match.group(1)
            # Reconstruct properly
            fixed_many2one = field_start + field_params + "\n\n    " + state_content
            return fixed_many2one
        
        return match.group(0)
    
    content = pattern1.sub(fix_pattern1, content)
    
    return content

def fix_missing_commas_in_selections(content):
    """Fix missing commas in Selection field tuples"""
    
    # Fix patterns like: ('done', 'Done')  ], string=...
    # Should be: ('done', 'Done')], string=...
    patterns = [
        (r"\('(\w+)', '([^']+)'\)\s*\],", r"('\1', '\2')],"),
        (r"(\], string='[^']*')\s*(\w+\s*=)", r"\1, \2"),
        (r"(tracking=True)\s*(\w+\s*=)", r"\1, \2"),
        (r"(required=True)\s*(\w+\s*=)", r"\1, \2"),
        (r"(index=True)\s*(\w+\s*=)", r"\1, \2"),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_indentation_issues(content):
    """Fix indentation problems"""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Fix lines that should be indented as field definitions
        if (line.strip() and not line.startswith('    ') and 
            ('= fields.' in line or line.strip().startswith('"res.') or
             line.strip().startswith('string=') or line.strip().startswith('help='))):
            # This should be indented as a field definition
            if not line.startswith('    '):
                line = '    ' + line.lstrip()
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_bracket_issues(content):
    """Fix bracket and parenthesis issues"""
    # Replace stray } with )
    content = re.sub(r'\s*}\s*$', ')', content, flags=re.MULTILINE)
    
    return content

def validate_and_fix_file(filepath):
    """Validate and fix a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        
        # Apply fixes in order
        content = fix_malformed_field_definitions(content)
        content = fix_missing_commas_in_selections(content)
        content = fix_indentation_issues(content)
        content = fix_bracket_issues(content)
        
        # Test if the fix worked
        try:
            ast.parse(content)
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        
        # Only write if we made changes and syntax is valid
        if content != original_content:
            if syntax_valid:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return "fixed", "Syntax errors fixed successfully"
            else:
                return "partial", "Applied fixes but syntax still invalid"
        else:
            return "unchanged", "No changes made"
            
    except Exception as e:
        return "error", f"Error processing file: {str(e)}"

def main():
    """Main function"""
    print("🔧 Advanced Syntax Fixer for Records Management")
    print("=" * 60)
    
    # List of files that had syntax errors
    error_files = [
        "advanced_billing_line.py",
        "approval_history.py", 
        "barcode_product.py",
        "base_rate.py",
        "bin_key_history.py",
        "document_retrieval_item.py",
        "file_retrieval_work_order_item.py",
        "naid_compliance_action_plan.py",
        "naid_compliance_alert.py",
        "naid_compliance_checklist_item.py",
        "naid_compliance_support_models.py",
        "naid_risk_assessment.py",
        "portal_feedback.py",
        "portal_feedback_action.py",
        "portal_feedback_analytic.py",
        "product_container_type.py",
        "records_access_log.py",
        "records_billing_contact.py",
        "records_billing_profile.py",
        "records_customer_billing_profile.py",
        "records_inventory_dashboard.py",
        "records_location.py",
        "records_retention_rule.py",
        "stock_lot_attribute_value.py"
    ]
    
    models_dir = "records_management/models"
    
    fixed_count = 0
    partial_count = 0
    unchanged_count = 0
    error_count = 0
    
    for filename in error_files:
        filepath = os.path.join(models_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"⚠️  {filename}: File not found")
            continue
        
        print(f"🔧 Processing {filename}...")
        
        result, message = validate_and_fix_file(filepath)
        
        if result == "fixed":
            print(f"   ✅ {message}")
            fixed_count += 1
        elif result == "partial":
            print(f"   ⚠️  {message}")
            partial_count += 1
        elif result == "unchanged":
            print(f"   ⏭️  {message}")
            unchanged_count += 1
        else:
            print(f"   ❌ {message}")
            error_count += 1
    
    print(f"\n📊 Summary:")
    print(f"Files fixed: {fixed_count}")
    print(f"Files partially fixed: {partial_count}")
    print(f"Files unchanged: {unchanged_count}")
    print(f"Files with errors: {error_count}")
    
    if fixed_count > 0:
        print(f"\n🎉 Successfully fixed {fixed_count} files!")
        print("Run syntax validation to verify all fixes.")

if __name__ == "__main__":
    main()
