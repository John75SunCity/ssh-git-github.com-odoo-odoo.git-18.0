#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Business Fields Fixer - Phase 2
Adds additional missing business fields found in view references
"""

import os
import re

# Extended business fields based on view analysis
EXTENDED_BUSINESS_FIELDS = {
    'res.partner': {
        'active_bin_key_count': 'fields.Integer(string="Active Bin Keys", compute="_compute_active_bin_key_count")',
        'emergency_contact': 'fields.Char(string="Emergency Contact")',
        'has_bin_key': 'fields.Boolean(string="Has Bin Key", compute="_compute_has_bin_key")',
        'key_restriction_status': 'fields.Selection([("allowed", "Allowed"), ("restricted", "Restricted"), ("suspended", "Suspended")], string="Key Restriction Status")',
        'unlock_service_count': 'fields.Integer(string="Unlock Service Count", compute="_compute_unlock_service_count")',
        'total_unlock_charges': 'fields.Monetary(string="Total Unlock Charges", currency_field="currency_id", compute="_compute_total_unlock_charges")',
        'billing_account_number': 'fields.Char(string="Billing Account Number", index=True)',
        'service_level': 'fields.Selection([("standard", "Standard"), ("premium", "Premium"), ("enterprise", "Enterprise")], string="Service Level")',
    },
    'shred.bin': {
        'actual_weight': 'fields.Float(string="Actual Weight (lbs)", digits=(8,2))',
        'can_downsize': 'fields.Boolean(string="Can Downsize", default=False)',
        'can_upsize': 'fields.Boolean(string="Can Upsize", default=False)',
        'next_size_down': 'fields.Char(string="Next Size Down")',
        'next_size_up': 'fields.Char(string="Next Size Up")',
        'request_type': 'fields.Selection([("pickup", "Pickup"), ("exchange", "Exchange"), ("resize", "Resize")], string="Request Type")',
        'service_type': 'fields.Selection([("scheduled", "Scheduled"), ("on_demand", "On Demand"), ("emergency", "Emergency")], string="Service Type")',
        'urgency': 'fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], string="Urgency")',
    },
    'maintenance.equipment': {
        'naid_certified': 'fields.Boolean(string="NAID Certified", default=False)',
        'naid_certification_date': 'fields.Date(string="NAID Certification Date")',
        'naid_certification_expiry': 'fields.Date(string="NAID Certification Expiry")',
        'shredding_capacity_per_hour': 'fields.Float(string="Shredding Capacity (lbs/hour)", digits=(8,2))',
        'maintenance_frequency': 'fields.Selection([("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly"), ("quarterly", "Quarterly")], string="Maintenance Frequency")',
        'records_department_id': 'fields.Many2one("records.department", string="Records Department")',
        'destruction_service_ids': 'fields.One2many("shredding.service", "equipment_id", string="Destruction Services")',
    },
    'pickup.route.stop': {
        'contact_person': 'fields.Char(string="Contact Person")',
        'contact_phone': 'fields.Char(string="Contact Phone")',
        'contact_email': 'fields.Char(string="Contact Email")',
        'access_instructions': 'fields.Text(string="Access Instructions")',
        'estimated_duration': 'fields.Float(string="Estimated Duration (hours)", digits=(4,2))',
        'estimated_weight': 'fields.Float(string="Estimated Weight (lbs)", digits=(8,2))',
        'actual_weight': 'fields.Float(string="Actual Weight (lbs)", digits=(8,2))',
        'delivery_instructions': 'fields.Text(string="Delivery Instructions")',
        'customer_signature': 'fields.Binary(string="Customer Signature")',
        'driver_signature': 'fields.Binary(string="Driver Signature")',
        'photos_taken': 'fields.Integer(string="Photos Taken")',
        'verification_code': 'fields.Char(string="Verification Code")',
    },
    'bin.key': {
        'key_number': 'fields.Char(string="Key Number", required=True, index=True)',
        'bin_location': 'fields.Char(string="Bin Location")',
        'assigned_to': 'fields.Many2one("res.partner", string="Assigned To")',
        'issue_date': 'fields.Date(string="Issue Date")',
        'return_date': 'fields.Date(string="Return Date")',
        'security_deposit_required': 'fields.Boolean(string="Security Deposit Required", default=False)',
        'security_deposit_amount': 'fields.Monetary(string="Security Deposit Amount", currency_field="currency_id")',
        'emergency_access': 'fields.Boolean(string="Emergency Access", default=False)',
        'last_maintenance_date': 'fields.Date(string="Last Maintenance Date")',
        'next_maintenance_due': 'fields.Date(string="Next Maintenance Due")',
    },
    'product.template': {
        'detailed_type': 'fields.Selection([("consu", "Consumable"), ("service", "Service"), ("product", "Storable Product")], string="Product Type")',
        'list_price': 'fields.Float(string="Sales Price", digits="Product Price")',
        'standard_price': 'fields.Float(string="Cost", digits="Product Price")',
        'categ_id': 'fields.Many2one("product.category", string="Product Category")',
        'uom_id': 'fields.Many2one("uom.uom", string="Unit of Measure")',
        'uom_po_id': 'fields.Many2one("uom.uom", string="Purchase Unit of Measure")',
        'sale_ok': 'fields.Boolean(string="Can be Sold", default=True)',
        'purchase_ok': 'fields.Boolean(string="Can be Purchased", default=True)',
        'naid_compliance_level': 'fields.Selection([("aaa", "NAID AAA"), ("aa", "NAID AA"), ("a", "NAID A")], string="NAID Compliance")',
        'service_type': 'fields.Selection([("storage", "Storage"), ("retrieval", "Retrieval"), ("destruction", "Destruction"), ("scanning", "Scanning")], string="Service Type")',
    },
    'fsm.task': {
        'container_ids': 'fields.Many2many("records.container", string="Containers")',
        'total_cubic_feet': 'fields.Float(string="Total Cubic Feet", compute="_compute_totals")',
        'total_weight': 'fields.Float(string="Total Weight (lbs)", compute="_compute_totals")',
        'naid_compliant': 'fields.Boolean(string="NAID Compliant", default=True)',
        'chain_of_custody_required': 'fields.Boolean(string="Chain of Custody Required", default=False)',
        'destruction_certificate_required': 'fields.Boolean(string="Destruction Certificate Required", default=False)',
        'customer_signature': 'fields.Binary(string="Customer Signature")',
        'technician_signature': 'fields.Binary(string="Technician Signature")',
        'compliance_verified': 'fields.Boolean(string="Compliance Verified", default=False)',
    },
    'account.move.line': {
        'records_related': 'fields.Boolean(string="Records Related", default=False)',
        'records_service_type': 'fields.Selection([("storage", "Storage"), ("retrieval", "Retrieval"), ("destruction", "Destruction")], string="Records Service Type")',
        'container_count': 'fields.Integer(string="Container Count")',
        'shredding_weight': 'fields.Float(string="Shredding Weight (lbs)", digits=(8,2))',
        'pickup_request_id': 'fields.Many2one("pickup.request", string="Pickup Request")',
        'destruction_service_id': 'fields.Many2one("shredding.service", string="Destruction Service")',
        'storage_location_id': 'fields.Many2one("records.location", string="Storage Location")',
        'naid_audit_required': 'fields.Boolean(string="NAID Audit Required", default=False)',
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

        # Find insertion point
        insertion_patterns = [
            r'(\n    # ={70,}\n    # [A-Z\s]+ METHODS\n    # ={70,})',
            r'(\n    @api\.)',
            r'(\n    def )',
            r'(\n\n    # Added by)',  # After previous additions
        ]

        insert_pos = None
        for pattern in insertion_patterns:
            match = re.search(pattern, content)
            if match:
                insert_pos = match.start()
                break

        if insert_pos is None:
            # Find last field and insert after it
            field_pattern = r'(\n    \w+\s*=\s*fields\.\w+\([^)]*(?:\([^)]*\))*[^)]*\))'
            field_matches = list(re.finditer(field_pattern, content))
            if field_matches:
                insert_pos = field_matches[-1].end()
            else:
                insert_pos = content.rfind('\n')

        field_text = f"""
    {field_name} = {field_definition}"""

        content = content[:insert_pos] + field_text + content[insert_pos:]

        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"  ⚠️  Error adding {field_name} to {model_file}: {e}")
        return False

def main():
    print("🔧 ENHANCED BUSINESS FIELDS FIXER - PHASE 2")
    print("=" * 60)
    print("Adding extended business fields based on view analysis")
    print()

    total_added = 0
    total_skipped = 0

    for model_name, fields_dict in EXTENDED_BUSINESS_FIELDS.items():
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
                else:
                    print(f"  ❌ Failed to add {field_name}")

    print()
    print("🎯 PHASE 2 SUMMARY")
    print("=" * 60)
    print(f"Additional fields added: {total_added}")
    print(f"Fields already existed: {total_skipped}")
    print("✅ Enhanced business fields addition complete!")

if __name__ == "__main__":
    main()
