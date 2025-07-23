#!/usr/bin/env python3
"""
PHASE 2 BATCH 2: Complete remaining models - Updated
"""

import os
import re

# Remaining Phase 2 field definitions
PHASE_2_BATCH_2 = {
    'records.retention.policy': {
        'file': 'models/records_retention_policy.py',
        'fields': {
            # Compliance Management
            'compliance_framework': "fields.Selection([('sox', 'Sarbanes-Oxley'), ('hipaa', 'HIPAA'), ('gdpr', 'GDPR'), ('pci', 'PCI-DSS'), ('iso27001', 'ISO 27001'), ('nist', 'NIST'), ('custom', 'Custom')], string='Compliance Framework')",
            'regulatory_citation': "fields.Text('Regulatory Citation', help='Specific law, regulation, or standard citation')",
            'compliance_officer_approval': "fields.Boolean('Compliance Officer Approval Required', default=True)",
            'legal_counsel_review': "fields.Boolean('Legal Counsel Review Required', default=False)",
            'audit_trail_required': "fields.Boolean('Audit Trail Required', default=True)",
            'exception_approval_required': "fields.Boolean('Exception Approval Required', default=True)",
            
            # Policy Audit & Review
            'last_review_date': "fields.Date('Last Review Date')",
            'review_cycle_months': "fields.Integer('Review Cycle (Months)', default=12)",
            'next_mandatory_review': "fields.Date('Next Mandatory Review', compute='_compute_next_review')",
            'policy_version': "fields.Char('Policy Version', default='1.0')",
            'version_history_ids': "fields.One2many('records.policy.version', 'policy_id', string='Version History')",
            'approval_workflow_id': "fields.Many2one('records.approval.workflow', string='Approval Workflow')",
            'stakeholder_notification': "fields.Boolean('Stakeholder Notification Required', default=True)",
            
            # Risk Management
            'risk_assessment_required': "fields.Boolean('Risk Assessment Required', default=False)",
            'risk_level': "fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Risk Level', default='medium')",
            'impact_assessment': "fields.Text('Impact Assessment')",
            'mitigation_measures': "fields.Text('Risk Mitigation Measures')",
            'exception_count': "fields.Integer('Exception Count', compute='_compute_exception_count')",
            'violation_count': "fields.Integer('Violation Count', compute='_compute_violation_count')"
        }
    },
    
    'shredding.service': {
        'file': 'models/shredding_service.py',
        'fields': {
            # NAID Compliance
            'naid_certificate_id': "fields.Many2one('naid.certificate', string='NAID Certificate')",
            'naid_compliance_level': "fields.Selection([('aaa', 'NAID AAA'), ('aa', 'NAID AA'), ('a', 'NAID A')], string='NAID Compliance Level')",
            'destruction_standard': "fields.Selection([('dod_5220', 'DoD 5220.22-M'), ('nist_800_88', 'NIST 800-88'), ('iso_27040', 'ISO/IEC 27040'), ('custom', 'Custom Standard')], string='Destruction Standard')",
            'witness_verification_required': "fields.Boolean('Witness Verification Required', default=True)",
            'photo_documentation_required': "fields.Boolean('Photo Documentation Required', default=True)",
            'video_documentation_required': "fields.Boolean('Video Documentation Required', default=False)",
            
            # Audit & Documentation
            'certificate_of_destruction_id': "fields.Many2one('records.destruction.certificate', string='Certificate of Destruction')",
            'audit_trail_ids': "fields.One2many('records.audit.log', 'shredding_service_id', string='Audit Trail')",
            'compliance_documentation_ids': "fields.One2many('ir.attachment', 'res_id', string='Compliance Documentation', domain=[('res_model', '=', 'shredding.service')])",
            'destruction_method_verified': "fields.Boolean('Destruction Method Verified', default=False)",
            'chain_of_custody_maintained': "fields.Boolean('Chain of Custody Maintained', default=False)",
            'environmental_compliance': "fields.Boolean('Environmental Compliance Verified', default=False)",
            
            # Quality Control
            'quality_control_performed': "fields.Boolean('Quality Control Performed', default=False)",
            'quality_control_date': "fields.Datetime('Quality Control Date')",
            'quality_control_officer_id': "fields.Many2one('res.users', string='Quality Control Officer')",
            'particle_size_verified': "fields.Boolean('Particle Size Verified', default=False)",
            'contamination_check': "fields.Boolean('Contamination Check Performed', default=False)",
            'equipment_calibration_verified': "fields.Boolean('Equipment Calibration Verified', default=False)"
        }
    },
    
    'records.location': {
        'file': 'models/records_location.py',
        'fields': {
            # Security Compliance
            'security_audit_ids': "fields.One2many('records.security.audit', 'location_id', string='Security Audits')",
            'last_security_audit': "fields.Date('Last Security Audit')",
            'security_certification': "fields.Selection([('none', 'None'), ('basic', 'Basic Security'), ('enhanced', 'Enhanced Security'), ('maximum', 'Maximum Security')], string='Security Certification', default='basic')",
            'access_control_system': "fields.Boolean('Access Control System', default=False)",
            'surveillance_system': "fields.Boolean('Surveillance System', default=False)",
            'alarm_system': "fields.Boolean('Alarm System', default=False)",
            'fire_detection_system': "fields.Boolean('Fire Detection System', default=False)",
            
            # Environmental Compliance
            'environmental_controls_verified': "fields.Boolean('Environmental Controls Verified', default=False)",
            'temperature_controlled': "fields.Boolean('Temperature Controlled', default=False)",
            'humidity_controlled': "fields.Boolean('Humidity Controlled', default=False)",
            'pest_control_program': "fields.Boolean('Pest Control Program', default=False)",
            'hazmat_compliance': "fields.Boolean('HAZMAT Compliance', default=False)",
            
            # Audit & Inspection
            'inspection_required': "fields.Boolean('Regular Inspection Required', default=True)",
            'inspection_frequency': "fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')], string='Inspection Frequency', default='monthly')",
            'last_inspection_date': "fields.Date('Last Inspection Date')",
            'next_inspection_date': "fields.Date('Next Inspection Date', compute='_compute_next_inspection')",
            'inspection_log_ids': "fields.One2many('records.location.inspection', 'location_id', string='Inspection Log')",
            'compliance_violations_count': "fields.Integer('Compliance Violations', compute='_compute_violations_count')"
        }
    }
}

def add_fields_to_model_file(file_path, model_name, fields_dict):
    """Add Phase 2 fields to a specific model file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\\n')
        
        # Find the best insertion point - look for different patterns
        insertion_patterns = [
            r'^\\s*[a-zA-Z_][a-zA-Z0-9_]*\\s*=\\s*fields\\.',  # Standard field pattern
            r'^\\s*[a-zA-Z_][a-zA-Z0-9_]*\\s*=.*fields\\.',     # Alternative field pattern
            r'^\\s*#.*Phase.*1.*Fields',                        # After Phase 1 comment
        ]
        
        last_field_line = -1
        for pattern in insertion_patterns:
            for i, line in enumerate(lines):
                if re.match(pattern, line):
                    last_field_line = i
        
        # If we still can't find fields, look for end of __init__ or before first method
        if last_field_line == -1:
            for i, line in enumerate(lines):
                # Look for start of methods (functions starting with def)
                if re.match(r'^\\s*def\\s+', line) or re.match(r'^\\s*@api\\.', line):
                    last_field_line = i - 1
                    break
        
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
        new_content = '\\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
        
    except Exception as e:
        print(f"❌ Error adding fields to {file_path}: {e}")
        return False

def main():
    """Main implementation function"""
    base_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    print("🚀 PHASE 2 BATCH 2 STARTING...")
    print("Adding Remaining Audit & Compliance Fields")
    print("=" * 60)
    
    total_fields_added = 0
    models_updated = 0
    
    for model_name, config in PHASE_2_BATCH_2.items():
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
            
            # List first 5 fields added
            field_names = list(config['fields'].keys())
            for i, field_name in enumerate(field_names[:5]):
                print(f"      - {field_name}")
            if len(field_names) > 5:
                print(f"      ... and {len(field_names) - 5} more")
        else:
            print(f"   ❌ Failed to add fields")
    
    print(f"\\n📊 PHASE 2 BATCH 2 SUMMARY:")
    print(f"   Models updated: {models_updated}")
    print(f"   Total fields added: {total_fields_added}")
    print(f"   Success rate: {(models_updated / len(PHASE_2_BATCH_2)) * 100:.1f}%")
    
    # Calculate total Phase 2 progress
    batch1_fields = 42  # From previous batch
    total_phase2_fields = batch1_fields + total_fields_added
    
    print(f"\\n✅ PHASE 2 COMPLETION STATUS:")
    print(f"   Batch 1 fields: {batch1_fields}")
    print(f"   Batch 2 fields: {total_fields_added}")
    print(f"   Total Phase 2 fields: {total_phase2_fields}/97")
    print(f"   Phase 2 progress: {(total_phase2_fields/97)*100:.1f}%")
    
    if total_fields_added > 0:
        print(f"\\n🎉 PHASE 2 BATCH 2 COMPLETE!")
        print(f"📋 Next steps:")
        print(f"   1. Validate all Phase 2 models")
        print(f"   2. Add computed method implementations")
        print(f"   3. Update progress tracking")
        print(f"   4. Prepare Phase 3 or test module")

if __name__ == "__main__":
    main()
