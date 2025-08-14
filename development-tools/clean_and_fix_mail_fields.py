#!/usr/bin/env python3
"""
Clean and Fix Mail Framework Fields

This script removes all incorrectly placed mail framework fields 
and adds them in the correct location within each model file.
"""

import os
import re

def clean_and_fix_mail_fields(filepath):
    """Remove incorrectly placed mail framework fields and add them properly."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove ALL existing mail framework field blocks (both correct and incorrect)
    # This regex removes the entire block from the comment to the last field
    content = re.sub(
        r'\s*# ={10,}.*?MAIL FRAMEWORK FIELDS.*?={10,}.*?help="Communication history for this record"\s*\)\s*',
        '\n',
        content,
        flags=re.DOTALL | re.MULTILINE
    )
    
    # Also remove any standalone mail framework fields that might be floating around
    content = re.sub(r'\s*activity_ids = fields\.One2many\(\s*"mail\.activity".*?\)\s*', '', content, flags=re.DOTALL)
    content = re.sub(r'\s*message_follower_ids = fields\.One2many\(\s*"mail\.followers".*?\)\s*', '', content, flags=re.DOTALL)
    content = re.sub(r'\s*message_ids = fields\.One2many\(\s*"mail\.message".*?\)\s*', '', content, flags=re.DOTALL)
    
    # Check if model inherits from mail.thread or mail.activity.mixin
    has_mail_inherit = 'mail.thread' in content or 'mail.activity.mixin' in content
    
    if not has_mail_inherit:
        # Write cleaned content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return False, "No mail inheritance - cleaned file"
    
    # Find the best place to add mail framework fields
    lines = content.split('\n')
    insert_pos = -1
    
    # Look for the last field definition before any methods
    for i, line in enumerate(lines):
        # Skip if we're in a method or decorator
        if line.strip().startswith('def ') or line.strip().startswith('@'):
            break
        # Look for field definitions
        if '= fields.' in line and not line.strip().startswith('#'):
            insert_pos = i + 1
    
    if insert_pos == -1:
        # If no field found, look for the end of the class attributes section
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                insert_pos = i
                break
    
    if insert_pos == -1:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return False, "Could not find insertion point - cleaned file"
    
    # Determine proper indentation
    indent = "    "  # Default 4 spaces
    for i in range(max(0, insert_pos - 5), insert_pos):
        if i < len(lines) and '=' in lines[i]:
            match = re.match(r'^(\s*)', lines[i])
            if match:
                indent = match.group(1)
                break
    
    # Prepare the mail framework fields with proper indentation
    mail_fields = f'''
{indent}# ============================================================================
{indent}# MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
{indent}# ============================================================================
{indent}activity_ids = fields.One2many(
{indent}    "mail.activity",
{indent}    "res_id",
{indent}    string="Activities",
{indent}    domain=lambda self: [("res_model", "=", self._name)],
{indent}    help="Related activities for this record"
{indent})

{indent}message_follower_ids = fields.One2many(
{indent}    "mail.followers",
{indent}    "res_id",
{indent}    string="Followers",
{indent}    domain=lambda self: [("res_model", "=", self._name)],
{indent}    help="Users following this record"
{indent})

{indent}message_ids = fields.One2many(
{indent}    "mail.message",
{indent}    "res_id",
{indent}    string="Messages",
{indent}    domain=lambda self: [("model", "=", self._name)],
{indent}    help="Communication history for this record"
{indent})
'''
    
    # Insert the fields
    lines.insert(insert_pos, mail_fields)
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True, "Mail framework fields added correctly"

def main():
    """Main function."""
    models_dir = 'records_management/models'
    
    # List of files that had syntax errors
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
            success, message = clean_and_fix_mail_fields(filepath)
            if success:
                print(f"✅ {filename}: {message}")
                fixed_count += 1
            else:
                print(f"ℹ️  {filename}: {message}")
                
        except Exception as e:
            print(f"❌ {filename}: Error - {e}")
    
    print(f"\n📊 Summary: Fixed {fixed_count}/{len(error_files)} files")

if __name__ == "__main__":
    main()
