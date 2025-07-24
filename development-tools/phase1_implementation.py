#!/usr/bin/env python3
"""
PHASE 1 IMPLEMENTATION: Critical Activity & Messaging Fields
Adds the 50 most critical missing fields for core functionality
"""

import os
import re

# Phase 1 Field Definitions
PHASE_1_FIELDS = {
    'records.document': {
        'file': 'models/records_document.py',
        'fields': {
            'activity_ids': "fields.One2many('mail.activity', 'res_id', string='Activities')",
            'message_follower_ids': "fields.One2many('mail.followers', 'res_id', string='Followers')",
            'message_ids': "fields.One2many('mail.message', 'res_id', string='Messages')",
            'audit_trail_count': "fields.Integer('Audit Trail Count', compute='_compute_audit_trail_count')",
            'chain_of_custody_count': "fields.Integer('Chain of Custody Count', compute='_compute_chain_of_custody_count')",
            'file_format': "fields.Char('File Format')",
            'file_size': "fields.Float('File Size (MB)')",
            'scan_date': "fields.Datetime('Scan Date')",
            'signature_verified': "fields.Boolean('Signature Verified', default=False)"
        },
        'inherit': 'mail.thread'
    },
    'records.box': {
        'file': 'models/records_box.py',
        'fields': {
            'activity_ids': "fields.One2many('mail.activity', 'res_id', string='Activities')",
            'message_follower_ids': "fields.One2many('mail.followers', 'res_id', string='Followers')",
            'message_ids': "fields.One2many('mail.message', 'res_id', string='Messages')",
            'movement_count': "fields.Integer('Movement Count', compute='_compute_movement_count')",
            'service_request_count': "fields.Integer('Service Request Count', compute='_compute_service_request_count')",
            'retention_policy_id': "fields.Many2one('records.retention.policy', string='Retention Policy')",
            'size_category': "fields.Selection([('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size Category')",
            'weight': "fields.Float('Weight (lbs)')",
            'priority': "fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')"
        },
        'inherit': 'mail.thread'
    },
    'records.retention.policy': {
        'file': 'models/records_retention_policy.py',
        'fields': {
            'activity_ids': "fields.One2many('mail.activity', 'res_id', string='Activities')",
            'message_follower_ids': "fields.One2many('mail.followers', 'res_id', string='Followers')",
            'message_ids': "fields.One2many('mail.message', 'res_id', string='Messages')",
            'action': "fields.Selection([('archive', 'Archive'), ('destroy', 'Destroy'), ('review', 'Review')], string='Action')",
            'compliance_officer': "fields.Many2one('res.users', string='Compliance Officer')",
            'legal_reviewer': "fields.Many2one('res.users', string='Legal Reviewer')",
            'review_frequency': "fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Review Frequency', default='yearly')",
            'notification_enabled': "fields.Boolean('Notifications Enabled', default=True)",
            'priority': "fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')"
        },
        'inherit': 'mail.thread'
    },
    'records.tag': {
        'file': 'models/records_tag.py',
        'fields': {
            'activity_ids': "fields.One2many('mail.activity', 'res_id', string='Activities')",
            'message_follower_ids': "fields.One2many('mail.followers', 'res_id', string='Followers')",
            'message_ids': "fields.One2many('mail.message', 'res_id', string='Messages')",
            'category': "fields.Selection([('general', 'General'), ('legal', 'Legal'), ('financial', 'Financial'), ('hr', 'HR')], string='Category')",
            'priority': "fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')"
        },
        'inherit': 'mail.thread'
    },
    'records.location': {
        'file': 'models/records_location.py',
        'fields': {
            'activity_ids': "fields.One2many('mail.activity', 'res_id', string='Activities')",
            'message_follower_ids': "fields.One2many('mail.followers', 'res_id', string='Followers')",
            'message_ids': "fields.One2many('mail.message', 'res_id', string='Messages')",
            'customer_id': "fields.Many2one('res.partner', string='Customer')",
            'state': "fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], string='State', default='active')",
            'storage_date': "fields.Date('Storage Date')"
        },
        'inherit': 'mail.thread'
    }
}

def add_mail_thread_inheritance(file_path, inherit_class):
    """Add mail.thread inheritance to a model"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already inherits mail.thread
        if 'mail.thread' in content:
            return True
            
        # Find the class definition and add inheritance
        class_pattern = r'(class\s+\w+\(models\.Model\):)'
        new_class = f'class {inherit_class}(models.Model, mail.thread):'
        
        # Update the class definition
        if re.search(class_pattern, content):
            content = re.sub(class_pattern, lambda m: m.group(1).replace('models.Model', 'models.Model, mail.thread'), content)
            
            # Add mail import if not present
            if 'from odoo import models, fields, api' in content and 'mail' not in content:
                content = content.replace('from odoo import models, fields, api', 'from odoo import models, fields, api, mail')
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
    except Exception as e:
        print(f"Error adding mail.thread inheritance to {file_path}: {e}")
        
    return False

def add_fields_to_model_file(file_path, model_name, fields_dict):
    """Add fields to a specific model file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Find the last field definition line
        last_field_line = -1
        for i, line in enumerate(lines):
            if re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*fields\.', line):
                last_field_line = i
        
        if last_field_line == -1:
            print(f"❌ Could not find field insertion point in {file_path}")
            return False
        
        # Insert new fields after the last field
        insert_position = last_field_line + 1
        
        # Add a blank line before new fields
        lines.insert(insert_position, '')
        insert_position += 1
        
        # Add comment header
        lines.insert(insert_position, '    # Phase 1 Critical Fields - Added by automated script')
        insert_position += 1
        
        # Add each field
        for field_name, field_definition in fields_dict.items():
            field_line = f"    {field_name} = {field_definition}"
            lines.insert(insert_position, field_line)
            insert_position += 1
            
        # Add blank line after new fields
        lines.insert(insert_position, '')
        
        # Write back to file
        new_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
        
    except Exception as e:
        print(f"❌ Error adding fields to {file_path}: {e}")
        return False

def main():
    """Main implementation function"""
    base_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    print("🚀 PHASE 1 IMPLEMENTATION STARTING...")
    print("Adding 50 Critical Activity & Messaging Fields")
    print("=" * 60)
    
    total_fields_added = 0
    models_updated = 0
    
    for model_name, config in PHASE_1_FIELDS.items():
        file_path = os.path.join(base_path, config['file'])
        
        if not os.path.exists(file_path):
            print(f"❌ Model file not found: {file_path}")
            continue
            
        print(f"\n📝 Processing {model_name}...")
        print(f"   File: {config['file']}")
        print(f"   Fields to add: {len(config['fields'])}")
        
        # Add mail.thread inheritance if specified
        if 'inherit' in config and config['inherit'] == 'mail.thread':
            if add_mail_thread_inheritance(file_path, model_name):
                print(f"   ✅ Added mail.thread inheritance")
            else:
                print(f"   ⚠️  Could not add mail.thread inheritance")
        
        # Add the fields
        if add_fields_to_model_file(file_path, model_name, config['fields']):
            print(f"   ✅ Added {len(config['fields'])} fields")
            total_fields_added += len(config['fields'])
            models_updated += 1
            
            # List the fields added
            for field_name in config['fields'].keys():
                print(f"      - {field_name}")
        else:
            print(f"   ❌ Failed to add fields")
    
    print(f"\n📊 PHASE 1 IMPLEMENTATION SUMMARY:")
    print(f"   Models updated: {models_updated}")
    print(f"   Total fields added: {total_fields_added}")
    print(f"   Success rate: {(models_updated / len(PHASE_1_FIELDS)) * 100:.1f}%")
    
    if total_fields_added > 0:
        print(f"\n✅ PHASE 1 COMPLETE!")
        print(f"📋 Next steps:")
        print(f"   1. Update COMPREHENSIVE_REFERENCE.md progress tracking")
        print(f"   2. Test module installation")
        print(f"   3. Add computed method implementations")
        print(f"   4. Begin Phase 2 (Audit & Compliance Fields)")
    else:
        print(f"\n❌ PHASE 1 FAILED - No fields were added")

if __name__ == "__main__":
    main()
