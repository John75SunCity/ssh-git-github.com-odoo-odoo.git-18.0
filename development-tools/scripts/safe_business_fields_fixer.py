#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safe Business Fields Fixer for Records Management
Systematically adds missing business-specific fields while maintaining 
Odoo standards and Records Management business logic.
"""

import os
import re
import sys
from collections import defaultdict

# Records Management specific field mappings
RECORDS_MANAGEMENT_FIELDS = {
    'paper.bale': {
        'bale_number': 'fields.Char(string="Bale Number", tracking=True, index=True)',
        'contamination_percentage': 'fields.Float(string="Contamination %", digits=(5,2))',
        'moisture_reading': 'fields.Float(string="Moisture Content %", digits=(5,2))',
        'quality_grade': 'fields.Selection([("a", "Grade A"), ("b", "Grade B"), ("c", "Grade C")], string="Quality Grade")',
        'revenue_potential': 'fields.Monetary(string="Revenue Potential", currency_field="currency_id")',
        'carbon_footprint_saved': 'fields.Float(string="Carbon Saved (kg CO2)", digits=(10,2))',
        'trees_saved_equivalent': 'fields.Integer(string="Trees Saved Equivalent")',
        'water_saved': 'fields.Float(string="Water Saved (liters)", digits=(10,2))',
        'processing_time': 'fields.Float(string="Processing Time (hours)", digits=(6,2))',
    },
    'shredding.service': {
        'destruction_status': 'fields.Selection([("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")], string="Destruction Status")',
        'witness_company': 'fields.Char(string="Witness Company")',
        'witness_name': 'fields.Char(string="Witness Name")',
        'naid_compliance_level': 'fields.Selection([("aaa", "NAID AAA"), ("aa", "NAID AA"), ("a", "NAID A")], string="NAID Compliance")',
        'destruction_method_detail': 'fields.Text(string="Destruction Method Details")',
        'pre_destruction_weight': 'fields.Float(string="Pre-Destruction Weight (lbs)", digits=(8,2))',
        'post_destruction_weight': 'fields.Float(string="Post-Destruction Weight (lbs)", digits=(8,2))',
    },
    'records.container': {
        'security_seal_number': 'fields.Char(string="Security Seal Number", tracking=True)',
        'last_inventory_date': 'fields.Date(string="Last Inventory Date")',
        'next_inspection_due': 'fields.Date(string="Next Inspection Due")',
        'temperature_controlled': 'fields.Boolean(string="Temperature Controlled", default=False)',
        'humidity_controlled': 'fields.Boolean(string="Humidity Controlled", default=False)',
        'fire_suppression': 'fields.Boolean(string="Fire Suppression Available", default=False)',
        'access_restrictions': 'fields.Text(string="Access Restrictions")',
        'insurance_value': 'fields.Monetary(string="Insurance Value", currency_field="currency_id")',
    },
    'records.location': {
        'climate_controlled': 'fields.Boolean(string="Climate Controlled", default=False)',
        'security_level': 'fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High"), ("maximum", "Maximum")], string="Security Level")',
        'fire_protection_system': 'fields.Char(string="Fire Protection System")',
        'access_card_required': 'fields.Boolean(string="Access Card Required", default=False)',
        'biometric_access': 'fields.Boolean(string="Biometric Access", default=False)',
        'surveillance_cameras': 'fields.Integer(string="Number of Cameras")',
        'last_security_audit': 'fields.Date(string="Last Security Audit")',
        'next_security_audit_due': 'fields.Date(string="Next Security Audit Due")',
    },
    'portal.request': {
        'estimated_completion': 'fields.Datetime(string="Estimated Completion")',
        'processing_notes': 'fields.Text(string="Processing Notes")',
        'special_instructions': 'fields.Text(string="Special Instructions")',
        'requires_approval': 'fields.Boolean(string="Requires Approval", default=False)',
        'urgency_level': 'fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], string="Urgency")',
        'customer_feedback': 'fields.Text(string="Customer Feedback")',
        'related_tasks_count': 'fields.Integer(string="Related Tasks", compute="_compute_related_tasks_count")',
        'staff_signature': 'fields.Binary(string="Staff Signature")',
        'naid_audit_required': 'fields.Boolean(string="NAID Audit Required", default=False)',
    },
    'pickup.request': {
        'route_optimized': 'fields.Boolean(string="Route Optimized", default=False)',
        'gps_coordinates': 'fields.Char(string="GPS Coordinates")',
        'access_instructions': 'fields.Text(string="Access Instructions")',
        'loading_dock_available': 'fields.Boolean(string="Loading Dock Available", default=False)',
        'equipment_needed': 'fields.Text(string="Special Equipment Needed")',
        'hazardous_materials': 'fields.Boolean(string="Hazardous Materials", default=False)',
        'weekend_pickup': 'fields.Boolean(string="Weekend Pickup Available", default=False)',
        'after_hours_pickup': 'fields.Boolean(string="After Hours Pickup", default=False)',
    },
    'naid.certificate': {
        'chain_of_custody_id': 'fields.Many2one("naid.chain.custody", string="Chain of Custody")',
        'custodian_name': 'fields.Char(string="Custodian Name")',
        'witness_name': 'fields.Char(string="Witness Name")',
        'environmental_compliance': 'fields.Boolean(string="Environmental Compliance", default=True)',
        'carbon_neutral_destruction': 'fields.Boolean(string="Carbon Neutral Destruction", default=False)',
        'recycling_percentage': 'fields.Float(string="Recycling Percentage", digits=(5,2))',
    },
    'records.billing.config': {
        'auto_invoice_generation': 'fields.Boolean(string="Auto Invoice Generation", default=True)',
        'billing_cycle_days': 'fields.Integer(string="Billing Cycle (days)", default=30)',
        'late_fee_percentage': 'fields.Float(string="Late Fee %", digits=(5,2))',
        'discount_early_payment': 'fields.Float(string="Early Payment Discount %", digits=(5,2))',
        'minimum_billing_amount': 'fields.Monetary(string="Minimum Billing Amount", currency_field="currency_id")',
        'tax_exempt': 'fields.Boolean(string="Tax Exempt", default=False)',
        'billing_frequency': 'fields.Selection([("weekly", "Weekly"), ("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annually", "Annually")], string="Billing Frequency")',
    },
    'records.document': {
        'digitized': 'fields.Boolean(string="Digitized", default=False)',
        'digital_scan_ids': 'fields.One2many("records.digital.scan", "document_id", string="Digital Scans")',
        'chain_of_custody_ids': 'fields.One2many("records.chain.of.custody", "document_id", string="Chain of Custody")',
        'audit_trail_ids': 'fields.One2many("naid.audit.log", "document_id", string="Audit Trail")',
        'compliance_verified': 'fields.Boolean(string="Compliance Verified", default=False)',
        'destruction_authorized_by': 'fields.Many2one("res.users", string="Destruction Authorized By")',
        'destruction_date': 'fields.Datetime(string="Destruction Date")',
        'destruction_method': 'fields.Char(string="Destruction Method")',
        'naid_destruction_verified': 'fields.Boolean(string="NAID Destruction Verified", default=False)',
    },
}

def get_model_file_path(model_name):
    """Get the file path for a model"""
    model_file = model_name.replace('.', '_') + '.py'
    return f'/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/{model_file}'

def check_field_exists(model_file, field_name):
    """Check if field already exists in model"""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"{field_name} = fields." in content or f"{field_name}=" in content
    except FileNotFoundError:
        return False

def add_field_to_model(model_file, field_name, field_definition):
    """Add field to model file with proper Odoo formatting"""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find a good insertion point - after existing fields but before methods
        insertion_patterns = [
            r'(\n    # ={70,}\n    # [A-Z\s]+ METHODS\n    # ={70,})',  # Before methods section
            r'(\n    @api\.)',  # Before first api method
            r'(\n    def )',   # Before first method
            r'(\nclass \w+)',  # Before next class (end of current class)
        ]
        
        insert_pos = None
        for pattern in insertion_patterns:
            match = re.search(pattern, content)
            if match:
                insert_pos = match.start()
                break
        
        if insert_pos is None:
            # Fallback: insert before the last line
            insert_pos = content.rfind('\n')
        
        # Create the field definition with proper formatting
        field_text = f"""
    # Added by Safe Business Fields Fixer
    {field_name} = {field_definition}
"""
        
        content = content[:insert_pos] + field_text + content[insert_pos:]
        
        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"  ⚠️  Error adding {field_name} to {model_file}: {e}")
        return False

def add_compute_method_if_needed(model_file, field_name, field_definition):
    """Add compute method if field has compute parameter"""
    if 'compute=' in field_definition:
        compute_match = re.search(r'compute=["\']([^"\']+)["\']', field_definition)
        if compute_match:
            method_name = compute_match.group(1)
            
            # Check if method already exists
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if f"def {method_name}(" not in content:
                    # Add a basic compute method
                    compute_method = f"""
    @api.depends('{field_name}')
    def {method_name}(self):
        \"\"\"Compute {field_name.replace('_', ' ').title()}\"\"\"
        for record in self:
            # TODO: Implement business logic for {field_name}
            record.{field_name} = 0  # Default value
"""
                    
                    # Find insertion point for methods
                    method_pattern = r'(\n    # ={70,}\n    # [A-Z\s]+ METHODS\n    # ={70,})'
                    match = re.search(method_pattern, content)
                    if match:
                        insert_pos = match.end()
                        content = content[:insert_pos] + compute_method + content[insert_pos:]
                        
                        with open(model_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        print(f"    ➕ Added compute method {method_name}")
            except Exception as e:
                print(f"    ⚠️  Could not add compute method {method_name}: {e}")

def main():
    print("🔧 SAFE BUSINESS FIELDS FIXER FOR RECORDS MANAGEMENT")
    print("=" * 60)
    print("Adding business-specific fields with Odoo standards compliance")
    print()
    
    total_added = 0
    total_skipped = 0
    
    for model_name, fields_dict in RECORDS_MANAGEMENT_FIELDS.items():
        model_file = get_model_file_path(model_name)
        
        if not os.path.exists(model_file):
            print(f"⚠️  Model file {model_file} not found, skipping...")
            continue
            
        print(f"📄 Processing {model_name}...")
        
        for field_name, field_definition in fields_dict.items():
            if check_field_exists(model_file, field_name):
                print(f"  ✅ {field_name} already exists")
                total_skipped += 1
            else:
                if add_field_to_model(model_file, field_name, field_definition):
                    print(f"  ➕ Added {field_name}")
                    total_added += 1
                    
                    # Add compute method if needed
                    add_compute_method_if_needed(model_file, field_name, field_definition)
                else:
                    print(f"  ❌ Failed to add {field_name}")
    
    print()
    print("🎯 SUMMARY")
    print("=" * 60)
    print(f"Fields added: {total_added}")
    print(f"Fields already existed: {total_skipped}")
    print("✅ Safe business fields addition complete!")

if __name__ == "__main__":
    main()
