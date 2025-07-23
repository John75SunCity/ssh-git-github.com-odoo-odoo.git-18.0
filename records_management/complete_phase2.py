#!/usr/bin/env python3
"""
COMPLETE PHASE 2: Add remaining audit & compliance fields to the final 5 models
"""

REMAINING_PHASE2_FIELDS = {
    'shredding.service': {
        'file': 'models/shredding_service.py',
        'fields': {
            # Audit & Compliance Fields
            'audit_required': "fields.Boolean('Audit Required', default=True)",
            'audit_completed': "fields.Boolean('Audit Completed', default=False)",
            'audit_date': "fields.Date('Audit Date')",
            'auditor_id': "fields.Many2one('res.users', string='Auditor')",
            'compliance_status': "fields.Selection([('pending', 'Pending'), ('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant')], string='Compliance Status', default='pending')",
            'regulatory_approval': "fields.Boolean('Regulatory Approval', default=False)",
            'naid_certification': "fields.Boolean('NAID Certification', default=False)",
            'iso_certification': "fields.Boolean('ISO Certification', default=False)",
            'audit_notes': "fields.Text('Audit Notes')",
            'compliance_notes': "fields.Text('Compliance Notes')",
            'risk_level': "fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Risk Level', default='medium')"
        }
    },
    'res.partner': {
        'file': 'models/res_partner.py',
        'fields': {
            # Customer Audit & Compliance Fields
            'audit_required': "fields.Boolean('Customer Audit Required', default=False)",
            'last_audit_date': "fields.Date('Last Audit Date')",
            'next_audit_date': "fields.Date('Next Audit Date')",
            'compliance_score': "fields.Float('Compliance Score (%)', default=0.0)",
            'compliance_status': "fields.Selection([('compliant', 'Compliant'), ('warning', 'Warning'), ('non_compliant', 'Non-Compliant')], string='Compliance Status', default='compliant')",
            'regulatory_requirements': "fields.Text('Regulatory Requirements')",
            'audit_frequency': "fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Audit Frequency', default='yearly')",
            'risk_classification': "fields.Selection([('low', 'Low Risk'), ('medium', 'Medium Risk'), ('high', 'High Risk')], string='Risk Classification', default='low')",
            'background_check_required': "fields.Boolean('Background Check Required', default=False)",
            'security_clearance_level': "fields.Selection([('none', 'None'), ('basic', 'Basic'), ('confidential', 'Confidential'), ('secret', 'Secret')], string='Security Clearance', default='none')"
        }
    },
    'pickup.request': {
        'file': 'models/pickup_request.py', 
        'fields': {
            # Service Audit & Compliance Fields
            'audit_trail_required': "fields.Boolean('Audit Trail Required', default=True)",
            'chain_of_custody_required': "fields.Boolean('Chain of Custody Required', default=True)",
            'witness_required': "fields.Boolean('Witness Required', default=False)",
            'compliance_verified': "fields.Boolean('Compliance Verified', default=False)",
            'security_level': "fields.Selection([('standard', 'Standard'), ('high', 'High Security'), ('confidential', 'Confidential')], string='Security Level', default='standard')",
            'background_check_verified': "fields.Boolean('Background Check Verified', default=False)",
            'access_authorization': "fields.Text('Access Authorization Details')",
            'regulatory_compliance': "fields.Text('Regulatory Compliance Notes')",
            'risk_assessment': "fields.Selection([('low', 'Low Risk'), ('medium', 'Medium Risk'), ('high', 'High Risk')], string='Risk Assessment', default='low')",
            'approval_required': "fields.Boolean('Management Approval Required', default=False)",
            'approved_by': "fields.Many2one('res.users', string='Approved By')",
            'approval_date': "fields.Date('Approval Date')"
        }
    },
    'records.document.type': {
        'file': 'models/records_document_type.py',
        'fields': {
            # Document Type Audit & Compliance Fields  
            'audit_required': "fields.Boolean('Audit Required for this Type', default=False)",
            'compliance_level': "fields.Selection([('standard', 'Standard'), ('sensitive', 'Sensitive'), ('confidential', 'Confidential'), ('classified', 'Classified')], string='Compliance Level', default='standard')",
            'retention_mandatory': "fields.Boolean('Retention Policy Mandatory', default=True)",
            'destruction_approval_required': "fields.Boolean('Destruction Approval Required', default=False)",
            'witness_destruction': "fields.Boolean('Witness Required for Destruction', default=False)",
            'regulatory_category': "fields.Selection([('financial', 'Financial'), ('legal', 'Legal'), ('hr', 'Human Resources'), ('medical', 'Medical'), ('government', 'Government')], string='Regulatory Category')",
            'access_restriction': "fields.Selection([('public', 'Public'), ('internal', 'Internal Only'), ('restricted', 'Restricted'), ('confidential', 'Confidential')], string='Access Restriction', default='internal')",
            'encryption_required': "fields.Boolean('Encryption Required', default=False)",
            'audit_log_retention': "fields.Integer('Audit Log Retention (Years)', default=7)",
            'compliance_review_frequency': "fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Compliance Review Frequency', default='yearly')"
        }
    },
    'customer.inventory.report': {
        'file': 'models/customer_inventory_report.py',
        'fields': {
            # Report Audit & Compliance Fields
            'audit_trail_enabled': "fields.Boolean('Audit Trail Enabled', default=True)",
            'data_accuracy_verified': "fields.Boolean('Data Accuracy Verified', default=False)",
            'verified_by': "fields.Many2one('res.users', string='Verified By')",
            'verification_date': "fields.Date('Verification Date')",
            'compliance_checked': "fields.Boolean('Compliance Checked', default=False)",
            'discrepancy_found': "fields.Boolean('Discrepancy Found', default=False)",
            'discrepancy_notes': "fields.Text('Discrepancy Notes')",
            'approval_status': "fields.Selection([('draft', 'Draft'), ('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')], string='Approval Status', default='draft')",
            'approved_by': "fields.Many2one('res.users', string='Approved By')",
            'approval_date': "fields.Date('Approval Date')",
            'regulatory_compliant': "fields.Boolean('Regulatory Compliant', default=True)",
            'audit_notes': "fields.Text('Audit Notes')"
        }
    }
}

def add_phase2_fields_to_model(model_name, config):
    """Add Phase 2 audit & compliance fields to a model"""
    file_path = f"/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/{config['file']}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the last field definition
        lines = content.split('\\n')
        last_field_line = -1
        
        for i, line in enumerate(lines):
            if ' = fields.' in line and not line.strip().startswith('#'):
                last_field_line = i
        
        if last_field_line == -1:
            print(f"❌ Could not find field insertion point in {file_path}")
            return False
            
        # Insert Phase 2 fields after the last field
        insert_position = last_field_line + 1
        
        # Add comment header
        lines.insert(insert_position, '')
        insert_position += 1
        lines.insert(insert_position, '    # Phase 2 Audit & Compliance Fields - Added by automated script')
        insert_position += 1
        
        # Add each field
        for field_name, field_definition in config['fields'].items():
            field_line = f"    {field_name} = {field_definition}"
            lines.insert(insert_position, field_line)
            insert_position += 1
            
        # Add blank line after
        lines.insert(insert_position, '')
        
        # Write back to file
        new_content = '\\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
        
    except Exception as e:
        print(f"❌ Error adding fields to {file_path}: {e}")
        return False

def main():
    """Complete Phase 2 implementation"""
    print("🎯 COMPLETING PHASE 2: AUDIT & COMPLIANCE FIELDS...")
    print("=" * 60)
    
    total_fields_added = 0
    models_updated = 0
    
    for model_name, config in REMAINING_PHASE2_FIELDS.items():
        print(f"\\n📝 Processing {model_name}...")
        print(f"   File: {config['file']}")
        print(f"   Fields to add: {len(config['fields'])}")
        
        if add_phase2_fields_to_model(model_name, config):
            print(f"   ✅ Added {len(config['fields'])} audit & compliance fields")
            total_fields_added += len(config['fields'])
            models_updated += 1
            
            # List the fields added
            for field_name in config['fields'].keys():
                print(f"      - {field_name}")
        else:
            print(f"   ❌ Failed to add fields")
    
    print(f"\\n📊 PHASE 2 COMPLETION SUMMARY:")
    print(f"   Models updated: {models_updated}")
    print(f"   New fields added: {total_fields_added}")
    print(f"   Total Phase 2 fields: {42 + total_fields_added}/97")
    print(f"   Phase 2 completion: {((42 + total_fields_added) / 97) * 100:.1f}%")
    
    if total_fields_added > 0:
        print(f"\\n✅ PHASE 2 COMPLETE!")
        print(f"📋 Next steps:")
        print(f"   1. Update COMPREHENSIVE_REFERENCE.md progress tracking")
        print(f"   2. Validate all model syntax")
        print(f"   3. Begin Phase 3 (Computed & Analytics Fields)")
        print(f"   4. Test module installation")
    else:
        print(f"\\n❌ PHASE 2 COMPLETION FAILED")

if __name__ == "__main__":
    main()
