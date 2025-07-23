#!/usr/bin/env python3
"""
PHASE 2 FIELD ADDITION SCRIPT
Systematically adds audit and compliance fields to models
"""

import os
import re

# Import Phase 2 field definitions
PHASE_2_FIELDS = {
    'records.document': {
        'file': 'models/records_document.py',
        'fields': {
            # Audit Trail Fields
            'audit_log_ids': "fields.One2many('records.audit.log', 'document_id', string='Audit Logs')",
            'last_audit_date': "fields.Datetime('Last Audit Date', readonly=True)",
            'audit_required': "fields.Boolean('Audit Required', default=False)",
            'audit_frequency': "fields.Selection([('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Audit Frequency')",
            
            # Compliance Fields
            'compliance_status': "fields.Selection([('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('pending_review', 'Pending Review')], string='Compliance Status', default='pending_review')",
            'compliance_notes': "fields.Text('Compliance Notes')",
            'regulatory_classification': "fields.Selection([('public', 'Public'), ('confidential', 'Confidential'), ('restricted', 'Restricted'), ('classified', 'Classified')], string='Regulatory Classification')",
            'data_subject_request': "fields.Boolean('Data Subject Request', default=False, help='GDPR/Privacy related document')",
            'retention_hold': "fields.Boolean('Retention Hold', default=False, help='Legal hold preventing destruction')",
            'legal_review_required': "fields.Boolean('Legal Review Required', default=False)",
            'legal_review_date': "fields.Date('Legal Review Date')",
            'legal_reviewer_id': "fields.Many2one('res.users', string='Legal Reviewer')",
            
            # Security & Access Control
            'access_log_ids': "fields.One2many('records.access.log', 'document_id', string='Access Logs')",
            'encryption_required': "fields.Boolean('Encryption Required', default=False)",
            'encryption_status': "fields.Selection([('none', 'Not Encrypted'), ('in_transit', 'Encrypted in Transit'), ('at_rest', 'Encrypted at Rest'), ('both', 'Fully Encrypted')], string='Encryption Status', default='none')",
            'access_level': "fields.Selection([('public', 'Public'), ('internal', 'Internal'), ('restricted', 'Restricted'), ('confidential', 'Confidential')], string='Access Level', default='internal')",
            'authorized_users': "fields.Many2many('res.users', string='Authorized Users')",
            'authorized_groups': "fields.Many2many('res.groups', string='Authorized Groups')",
            
            # Chain of Custody
            'custody_log_ids': "fields.One2many('records.chain.custody', 'document_id', string='Chain of Custody')",
            'current_custodian_id': "fields.Many2one('res.users', string='Current Custodian')",
            'custody_verified': "fields.Boolean('Custody Verified', default=False)",
            'custody_verification_date': "fields.Datetime('Custody Verification Date')"
        }
    },
    
    'records.box': {
        'file': 'models/records_box.py',
        'fields': {
            # Audit Fields
            'audit_log_ids': "fields.One2many('records.audit.log', 'box_id', string='Audit Logs')",
            'last_audit_date': "fields.Datetime('Last Audit Date', readonly=True)",
            'audit_required': "fields.Boolean('Audit Required', default=True)",
            'physical_audit_required': "fields.Boolean('Physical Audit Required', default=False)",
            'inventory_verified': "fields.Boolean('Inventory Verified', default=False)",
            'inventory_verification_date': "fields.Date('Inventory Verification Date')",
            'inventory_discrepancies': "fields.Text('Inventory Discrepancies')",
            
            # Compliance Tracking
            'compliance_status': "fields.Selection([('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('pending_review', 'Pending Review')], string='Compliance Status', default='pending_review')",
            'naid_certified': "fields.Boolean('NAID Certified Storage', default=False)",
            'iso_certified': "fields.Boolean('ISO Certified Storage', default=False)",
            'security_clearance_required': "fields.Selection([('none', 'None'), ('basic', 'Basic'), ('secret', 'Secret'), ('top_secret', 'Top Secret')], string='Security Clearance Required', default='none')",
            'environmental_controls': "fields.Boolean('Environmental Controls', default=False)",
            'fire_suppression': "fields.Boolean('Fire Suppression System', default=False)",
            
            # Chain of Custody for Boxes
            'custody_log_ids': "fields.One2many('records.chain.custody', 'box_id', string='Chain of Custody')",
            'current_custodian_id': "fields.Many2one('res.users', string='Current Custodian')",
            'transfer_log_ids': "fields.One2many('records.box.transfer', 'box_id', string='Transfer Log')",
            'witness_required': "fields.Boolean('Witness Required for Transfer', default=False)",
            'tamper_evident_seal': "fields.Char('Tamper Evident Seal Number')",
            'seal_verified': "fields.Boolean('Seal Verified', default=False)",
            'seal_verification_date': "fields.Datetime('Seal Verification Date')"
        }
    }
}

def add_fields_to_model_file(file_path, model_name, fields_dict):
    """Add Phase 2 fields to a specific model file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Find the last Phase 1 field or regular field definition line
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
        lines.insert(insert_position, '    # Phase 2 Audit & Compliance Fields - Added by automated script')
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
    
    print("🚀 PHASE 2 FIELD ADDITION STARTING...")
    print("Adding Audit & Compliance Fields")
    print("=" * 60)
    
    total_fields_added = 0
    models_updated = 0
    
    # Start with first 2 models to test the approach
    models_to_process = ['records.document', 'records.box']
    
    for model_name in models_to_process:
        if model_name in PHASE_2_FIELDS:
            config = PHASE_2_FIELDS[model_name]
            file_path = os.path.join(base_path, config['file'])
            
            if not os.path.exists(file_path):
                print(f"❌ Model file not found: {file_path}")
                continue
                
            print(f"\\n📝 Processing {model_name}...")
            print(f"   File: {config['file']}")
            print(f"   Fields to add: {len(config['fields'])}")
            
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
    
    print(f"\\n📊 PHASE 2 PARTIAL IMPLEMENTATION SUMMARY:")
    print(f"   Models updated: {models_updated}")
    print(f"   Total fields added: {total_fields_added}")
    print(f"   Success rate: {(models_updated / len(models_to_process)) * 100:.1f}%")
    
    if total_fields_added > 0:
        print(f"\\n✅ PHASE 2 BATCH 1 COMPLETE!")
        print(f"📋 Next steps:")
        print(f"   1. Validate syntax of updated models")
        print(f"   2. Continue with remaining 3 models")
        print(f"   3. Add computed method implementations")
        print(f"   4. Update progress tracking")
    else:
        print(f"\\n❌ PHASE 2 BATCH 1 FAILED - No fields were added")

if __name__ == "__main__":
    main()
