#!/usr/bin/env python3
"""
Fix Syntax Errors from Mail Framework Fields Addition

This script fixes the syntax errors created when adding mail framework fields.
It removes the incorrect insertions and adds them properly.
"""

import os
import re

CORRECT_MAIL_FRAMEWORK_FIELDS = '''
    # ============================================================================
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
        help="Related activities for this record"
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
        help="Users following this record"
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
        help="Communication history for this record"
    )
'''

def fix_syntax_error_file(filepath):
    """Fix syntax errors in a model file by properly placing mail framework fields."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any badly placed mail framework blocks
    content = re.sub(
        r'\n\s*# ={10,}\s*\n\s*# MAIL FRAMEWORK FIELDS.*?\n\s*# ={10,}\s*\n.*?help="Communication history for this record"\s*\n\s*\)',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Check if model inherits from mail.thread or mail.activity.mixin
    has_mail_inherit = 'mail.thread' in content or 'mail.activity.mixin' in content
    
    if not has_mail_inherit:
        return False, "No mail inheritance"
    
    # Check if any mail framework fields exist
    has_activity_ids = 'activity_ids = fields.One2many' in content
    has_message_follower_ids = 'message_follower_ids = fields.One2many' in content
    has_message_ids = 'message_ids = fields.One2many' in content
    
    if has_activity_ids and has_message_follower_ids and has_message_ids:
        return False, "All fields already present"
    
    # Find the class definition and the end of field definitions
    lines = content.split('\n')
    class_found = False
    fields_section_end = -1
    indent_level = ""
    
    for i, line in enumerate(lines):
        # Find the class definition
        if line.strip().startswith('class ') and 'models.Model' in line:
            class_found = True
            # Get the indentation level (next line after class should be indented)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                indent_match = re.match(r'^(\s*)', next_line)
                if indent_match:
                    indent_level = indent_match.group(1)
        
        # Find the last field definition within the class
        if class_found and line.strip():
            if ('= fields.' in line and 
                not line.strip().startswith('#') and
                not line.strip().startswith('def ') and
                not line.strip().startswith('@')):
                fields_section_end = i
    
    if fields_section_end == -1:
        return False, "Could not find field section"
    
    # Add fields after the last field definition
    formatted_fields = CORRECT_MAIL_FRAMEWORK_FIELDS.replace('    ', indent_level)
    lines.insert(fields_section_end + 1, formatted_fields)
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True, "Fields added successfully"

def main():
    """Main function to fix syntax errors."""
    models_dir = 'records_management/models'
    
    # List of files with syntax errors from the validation
    error_files = [
        'installer.py', 'bin_key_history.py', 'document_retrieval_item.py',
        'naid_destruction_record.py', 'customer_negotiated_rate.py', 'base_rates.py',
        'records_approval_step.py', 'records_container_transfer.py', 'discount_rule.py',
        'records_billing_config.py', 'stock_picking.py', 'naidaudit_log.py',
        'department_billing.py', 'customer_category.py', 'survey_improvement_action.py',
        'records_container.py', 'billing_automation.py', 'required_document.py',
        'records_storage_department_user.py', 'scrm_records_management.py',
        'records_location_inspection.py', 'naid_custody.py', 'portal_feedback_escalation.py',
        'paper_load_shipment.py', 'bale.py', 'billing.py', 'records_approval_workflow.py',
        'survey_feedback_theme.py', 'invoice_generation_log.py', 'records_promotional_discount.py',
        'shredding_service.py', 'naid_performance_history.py', 'records_security_audit.py',
        'bin_key_management.py', 'portal_feedback_communication.py', 'portal_feedback_action.py',
        'work_order_retrieval.py', 'naidcompliance_checklist.py', 'records_audit_log.py',
        'signed_document.py', 'paper_bale_inspection.py', 'records_retrieval_work_order.py',
        'records_policy_version.py'
    ]
    
    fixed_count = 0
    
    for filename in error_files:
        filepath = os.path.join(models_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"⚠️  {filename}: File not found")
            continue
        
        try:
            success, message = fix_syntax_error_file(filepath)
            if success:
                print(f"✅ {filename}: {message}")
                fixed_count += 1
            else:
                print(f"ℹ️  {filename}: {message}")
                
        except Exception as e:
            print(f"❌ {filename}: Error - {e}")
    
    print(f"\n📊 Summary: Fixed {fixed_count}/{len(error_files)} files with syntax errors")

if __name__ == "__main__":
    main()
