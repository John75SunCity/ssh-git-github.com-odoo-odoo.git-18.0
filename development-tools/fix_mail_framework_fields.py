#!/usr/bin/env python3
"""
Fix Mail Framework Fields Script

This script automatically adds the required mail framework fields to all models
that inherit from mail.thread or mail.activity.mixin but are missing the required fields.
"""

import os
import re

MAIL_FRAMEWORK_FIELDS = '''
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
    )'''

def fix_model_file(filepath):
    """Add missing mail framework fields to a model file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if model inherits from mail.thread or mail.activity.mixin
    has_mail_inherit = 'mail.thread' in content or 'mail.activity.mixin' in content
    
    if not has_mail_inherit:
        return False, "No mail inheritance"
    
    # Check which fields are missing
    has_activity_ids = 'activity_ids = fields.One2many' in content
    has_message_follower_ids = 'message_follower_ids = fields.One2many' in content  
    has_message_ids = 'message_ids = fields.One2many' in content
    
    if has_activity_ids and has_message_follower_ids and has_message_ids:
        return False, "All fields present"
    
    # Find the best place to insert the fields (before last method or at the end of class)
    lines = content.split('\n')
    insert_line = len(lines)
    
    # Look for the last field definition or method
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if (line.startswith('def ') or 
            line.startswith('@api.') or
            '= fields.' in line):
            insert_line = i + 1
            break
    
    # Insert the mail framework fields
    lines.insert(insert_line, MAIL_FRAMEWORK_FIELDS)
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True, "Fields added successfully"

def main():
    """Main function to process all model files."""
    models_dir = 'records_management/models'
    
    if not os.path.exists(models_dir):
        print(f"Error: {models_dir} directory not found")
        return
    
    fixed_count = 0
    total_count = 0
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            total_count += 1
            
            try:
                success, message = fix_model_file(filepath)
                if success:
                    print(f"✅ {filename}: {message}")
                    fixed_count += 1
                else:
                    print(f"ℹ️  {filename}: {message}")
                    
            except Exception as e:
                print(f"❌ {filename}: Error - {e}")
    
    print(f"\n📊 Summary: Fixed {fixed_count}/{total_count} model files")

if __name__ == "__main__":
    main()
