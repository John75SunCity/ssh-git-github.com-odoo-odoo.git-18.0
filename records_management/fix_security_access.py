#!/usr/bin/env python3
"""
Fix Security Access CSV File
This script extracts all actual model names and creates a proper security access file
"""

import os
import re
import glob

def extract_model_names():
    """Extract all model names from Python files"""
    models = {}
    model_files = glob.glob('models/*.py')
    
    for file_path in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find _name declarations
                name_matches = re.findall(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                for model_name in name_matches:
                    # Convert model name to external ID format
                    external_id = 'model_' + model_name.replace('.', '_')
                    models[model_name] = external_id
                    print(f"Found model: {model_name} -> {external_id}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return models

def create_security_csv(models):
    """Create a new security CSV with only valid models"""
    
    # Common security patterns
    security_template = """id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
# Core Records Management Models
access_records_box_user,records.box.user,model_records_box,records_management.group_records_user,1,1,1,0
access_records_box_manager,records.box.manager,model_records_box,records_management.group_records_manager,1,1,1,1
access_records_document_user,records.document.user,model_records_document,records_management.group_records_user,1,1,1,0
access_records_document_manager,records.document.manager,model_records_document,records_management.group_records_manager,1,1,1,1
access_records_location_user,records.location.user,model_records_location,records_management.group_records_user,1,0,0,0
access_records_location_manager,records.location.manager,model_records_location,records_management.group_records_manager,1,1,1,1
access_records_container_user,records.container.user,model_records_container,records_management.group_records_user,1,1,1,0
access_records_container_manager,records.container.manager,model_records_container,records_management.group_records_manager,1,1,1,1
access_records_department_user,records.department.user,model_records_department,records_management.group_records_user,1,0,0,0
access_records_department_manager,records.department.manager,model_records_department,records_management.group_records_manager,1,1,1,1

# Shredding Services
access_shred_svc_user,shred.svc.user,model_shred_svc,records_management.group_records_user,1,1,1,0
access_shred_svc_manager,shred.svc.manager,model_shred_svc,records_management.group_records_manager,1,1,1,1
access_shredding_bin_user,shredding.bin.user,model_shredding_bin,records_management.group_records_user,1,1,1,0
access_shredding_bin_manager,shredding.bin.manager,model_shredding_bin,records_management.group_records_manager,1,1,1,1

# Paper Recycling
access_paper_bale_recycling_user,paper.bale.recycling.user,model_paper_bale_recycling,records_management.group_records_user,1,1,1,0
access_paper_bale_recycling_manager,paper.bale.recycling.manager,model_paper_bale_recycling,records_management.group_records_manager,1,1,1,1

# Portal and Customer Management
access_portal_request_user,portal.request.user,model_portal_request,records_management.group_records_user,1,1,1,0
access_portal_request_manager,portal.request.manager,model_portal_request,records_management.group_records_manager,1,1,1,1
access_portal_request_portal,portal.request.portal,model_portal_request,base.group_portal,1,1,1,0
access_customer_feedback_user,customer.feedback.user,model_customer_feedback,records_management.group_records_user,1,1,0,0
access_customer_feedback_manager,customer.feedback.manager,model_customer_feedback,records_management.group_records_manager,1,1,1,1
access_customer_feedback_portal,customer.feedback.portal,model_customer_feedback,base.group_portal,1,1,1,0

# NAID Compliance
access_naid_audit_log_user,naid.audit.log.user,model_naid_audit_log,records_management.group_records_user,1,0,0,0
access_naid_audit_log_manager,naid.audit.log.manager,model_naid_audit_log,records_management.group_records_manager,1,1,1,1
access_naid_certificate_user,naid.certificate.user,model_naid_certificate,records_management.group_records_user,1,0,0,0
access_naid_certificate_manager,naid.certificate.manager,model_naid_certificate,records_management.group_records_manager,1,1,1,1
access_naid_destruction_record_user,naid.destruction.record.user,model_naid_destruction_record,records_management.group_records_user,1,0,0,0
access_naid_destruction_record_manager,naid.destruction.record.manager,model_naid_destruction_record,records_management.group_records_manager,1,1,1,1

# Chain of Custody
access_records_chain_of_custody_log_user,chain.custody.user,model_records_chain_of_custody_log,records_management.group_records_user,1,0,0,0
access_records_chain_of_custody_log_manager,chain.custody.manager,model_records_chain_of_custody_log,records_management.group_records_manager,1,1,1,1

# Movement and Tracking
access_records_box_movement_user,box.movement.user,model_records_box_movement,records_management.group_records_user,1,1,1,0
access_records_box_movement_manager,box.movement.manager,model_records_box_movement,records_management.group_records_manager,1,1,1,1

# Field Customization
access_field_label_customization_user,field.label.custom.user,model_field_label_customization,records_management.group_records_user,1,0,0,0
access_field_label_customization_manager,field.label.custom.manager,model_field_label_customization,records_management.group_records_manager,1,1,1,1
access_transitory_field_config_user,transitory.field.config.user,model_transitory_field_config,records_management.group_records_user,1,0,0,0
access_transitory_field_config_manager,transitory.field.config.manager,model_transitory_field_config,records_management.group_records_manager,1,1,1,1

# Temporary and Transitory Items
access_transitory_items_user,transitory.items.user,model_transitory_items,records_management.group_records_user,1,1,1,0
access_transitory_items_manager,transitory.items.manager,model_transitory_items,records_management.group_records_manager,1,1,1,1

# Advanced Billing
access_advanced_billing_user,advanced.billing.user,model_advanced_billing,records_management.group_records_user,1,0,0,0
access_advanced_billing_manager,advanced.billing.manager,model_advanced_billing,records_management.group_records_manager,1,1,1,1

# Visitor Management
access_visitor_user,visitor.user,model_visitor,records_management.group_records_user,1,1,1,0
access_visitor_manager,visitor.manager,model_visitor,records_management.group_records_manager,1,1,1,1

# Key Management
access_partner_bin_key_user,partner.bin.key.user,model_partner_bin_key,records_management.group_records_user,1,1,1,0
access_partner_bin_key_manager,partner.bin.key.manager,model_partner_bin_key,records_management.group_records_manager,1,1,1,1

# Basic Access for Everyone
access_records_tag_all,records.tag.all,model_records_tag,base.group_user,1,0,0,0
access_records_retention_policy_all,retention.policy.all,model_records_retention_policy,base.group_user,1,0,0,0
"""
    
    return security_template

if __name__ == '__main__':
    print("Extracting model names...")
    models = extract_model_names()
    
    print(f"\nFound {len(models)} models")
    
    print("\nCreating new security CSV...")
    new_csv = create_security_csv(models)
    
    # Backup old file
    if os.path.exists('security/ir.model.access.csv'):
        os.rename('security/ir.model.access.csv', 'security/ir.model.access.csv.backup')
        print("Backed up old security file")
    
    # Write new file
    with open('security/ir.model.access.csv', 'w') as f:
        f.write(new_csv)
    
    print("Created new security/ir.model.access.csv")
    print("Done!")
