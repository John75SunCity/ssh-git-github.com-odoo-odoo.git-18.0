#!/usr/bin/env python3
"""
MISSING FIELDS IMPLEMENTATION SCRIPT
Systematically adds the most critical missing fields to their respective models
"""

import os

# Critical missing fields that are commonly referenced across views
CRITICAL_MISSING_FIELDS = {
    'records.retention.policy': [
        'retention_unit',  # Already added but confirming
        'action',
        'applicable_document_type_ids',
        'compliance_officer',
        'compliance_rate',
        'legal_reviewer',
        'review_frequency',
        'notification_enabled',
        'priority'
    ],
    'records.document': [
        'activity_ids',
        'message_follower_ids', 
        'message_ids',
        'audit_trail_count',
        'chain_of_custody_count',
        'compliance_verified',
        'file_format',
        'file_size',
        'resolution',
        'scan_date',
        'signature_verified'
    ],
    'records.box': [
        'activity_ids',
        'message_follower_ids',
        'message_ids', 
        'movement_count',
        'service_request_count',
        'retention_policy_id',
        'size_category',
        'weight',
        'priority'
    ],
    'records.tag': [
        'description',  # The one we already found
        'activity_ids',
        'message_follower_ids',
        'message_ids',
        'category',
        'priority',
        'auto_assign',
        'icon'
    ],
    'records.location': [
        'activity_ids',
        'message_follower_ids',
        'message_ids',
        'customer_id',
        'state',
        'storage_date'
    ]
}

def add_fields_to_model(model_file_path, model_name, fields_to_add):
    """Add missing fields to a specific model file"""
    
    if not os.path.exists(model_file_path):
        print(f"❌ Model file not found: {model_file_path}")
        return False
        
    try:
        with open(model_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find the class definition
        class_pattern = f"class.*\\(models\\.Model\\):"
        import re
        
        # Find the end of existing field definitions
        lines = content.split('\n')
        insert_position = -1
        
        # Look for the last field definition
        for i, line in enumerate(lines):
            if re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*fields\.', line):
                insert_position = i + 1
                
        if insert_position == -1:
            print(f"❌ Could not find field insertion point in {model_file_path}")
            return False
            
        # Generate field definitions
        new_fields = []
        for field_name in fields_to_add:
            if field_name == 'activity_ids':
                new_fields.append(f"    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')")
            elif field_name == 'message_follower_ids':
                new_fields.append(f"    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')")
            elif field_name == 'message_ids':
                new_fields.append(f"    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')")
            elif field_name == 'description':
                new_fields.append(f"    description = fields.Text('Description')")
            elif field_name == 'retention_unit':
                continue  # Already added
            elif field_name == 'action':
                new_fields.append(f"    action = fields.Selection([('archive', 'Archive'), ('destroy', 'Destroy'), ('review', 'Review')], string='Action')")
            elif field_name == 'applicable_document_type_ids':
                new_fields.append(f"    applicable_document_type_ids = fields.Many2many('records.document.type', string='Applicable Document Types')")
            elif field_name == 'compliance_officer':
                new_fields.append(f"    compliance_officer = fields.Many2one('res.users', string='Compliance Officer')")
            elif field_name == 'compliance_rate':
                new_fields.append(f"    compliance_rate = fields.Float('Compliance Rate (%)', default=0.0)")
            elif field_name == 'legal_reviewer':
                new_fields.append(f"    legal_reviewer = fields.Many2one('res.users', string='Legal Reviewer')")
            elif field_name == 'review_frequency':
                new_fields.append(f"    review_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Review Frequency', default='yearly')")
            elif field_name == 'notification_enabled':
                new_fields.append(f"    notification_enabled = fields.Boolean('Notifications Enabled', default=True)")
            elif field_name == 'priority':
                new_fields.append(f"    priority = fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')")
            elif field_name == 'audit_trail_count':
                new_fields.append(f"    audit_trail_count = fields.Integer('Audit Trail Count', compute='_compute_audit_trail_count')")
            elif field_name == 'chain_of_custody_count':
                new_fields.append(f"    chain_of_custody_count = fields.Integer('Chain of Custody Count', compute='_compute_chain_of_custody_count')")
            elif field_name == 'compliance_verified':
                new_fields.append(f"    compliance_verified = fields.Boolean('Compliance Verified', default=False)")
            elif field_name == 'file_format':
                new_fields.append(f"    file_format = fields.Char('File Format')")
            elif field_name == 'file_size':
                new_fields.append(f"    file_size = fields.Float('File Size (MB)')")
            elif field_name == 'resolution':
                new_fields.append(f"    resolution = fields.Char('Resolution')")
            elif field_name == 'scan_date':
                new_fields.append(f"    scan_date = fields.Datetime('Scan Date')")
            elif field_name == 'signature_verified':
                new_fields.append(f"    signature_verified = fields.Boolean('Signature Verified', default=False)")
            elif field_name == 'movement_count':
                new_fields.append(f"    movement_count = fields.Integer('Movement Count', compute='_compute_movement_count')")
            elif field_name == 'service_request_count':
                new_fields.append(f"    service_request_count = fields.Integer('Service Request Count', compute='_compute_service_request_count')")
            elif field_name == 'retention_policy_id':
                new_fields.append(f"    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy')")
            elif field_name == 'size_category':
                new_fields.append(f"    size_category = fields.Selection([('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size Category')")
            elif field_name == 'weight':
                new_fields.append(f"    weight = fields.Float('Weight (lbs)')")
            elif field_name == 'category':
                new_fields.append(f"    category = fields.Selection([('general', 'General'), ('legal', 'Legal'), ('financial', 'Financial'), ('hr', 'HR')], string='Category')")
            elif field_name == 'auto_assign':
                new_fields.append(f"    auto_assign = fields.Boolean('Auto Assign', default=False)")
            elif field_name == 'icon':
                new_fields.append(f"    icon = fields.Char('Icon')")
            elif field_name == 'customer_id':
                new_fields.append(f"    customer_id = fields.Many2one('res.partner', string='Customer')")
            elif field_name == 'state':
                new_fields.append(f"    state = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], string='State', default='active')")
            elif field_name == 'storage_date':
                new_fields.append(f"    storage_date = fields.Date('Storage Date')")
                
        if new_fields:
            # Insert the new fields
            lines.insert(insert_position, '')  # Add blank line
            for field_def in new_fields:
                lines.insert(insert_position, field_def)
                insert_position += 1
            lines.insert(insert_position, '')  # Add blank line after
            
            # Write back to file
            new_content = '\n'.join(lines)
            with open(model_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"✅ Added {len(new_fields)} fields to {model_name}")
            return True
        else:
            print(f"⚠️  No new fields to add to {model_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {model_file_path}: {e}")
        return False

def main():
    """Main function to add critical missing fields"""
    base_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    print("🔧 ADDING CRITICAL MISSING FIELDS...")
    print("=" * 50)
    
    # Model file mappings
    model_files = {
        'records.retention.policy': 'models/records_retention_policy.py',
        'records.document': 'models/records_document.py', 
        'records.box': 'models/records_box.py',
        'records.tag': 'models/records_tag.py',
        'records.location': 'models/records_location.py'
    }
    
    success_count = 0
    total_fields_added = 0
    
    for model_name, fields in CRITICAL_MISSING_FIELDS.items():
        if model_name in model_files:
            model_file_path = os.path.join(base_path, model_files[model_name])
            print(f"\n📝 Processing {model_name}...")
            print(f"   Fields to add: {', '.join(fields)}")
            
            if add_fields_to_model(model_file_path, model_name, fields):
                success_count += 1
                total_fields_added += len([f for f in fields if f != 'retention_unit'])  # Skip already added
            
    print(f"\n📊 SUMMARY:")
    print(f"   Models updated: {success_count}")
    print(f"   Total fields added: {total_fields_added}")
    print(f"   Remaining missing fields: {1408 - total_fields_added}")
    
    print(f"\n✅ CRITICAL FIELDS IMPLEMENTATION COMPLETE!")
    print(f"📋 Next steps:")
    print(f"   1. Test module installation")
    print(f"   2. Add remaining fields as needed")
    print(f"   3. Add computed method implementations")

if __name__ == "__main__":
    main()
