#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility and Operational Fields Fixer - Phase 3
Adds utility fields for operational efficiency and common business operations
"""

import os
import re

# Utility and operational fields for enhanced functionality
UTILITY_OPERATIONAL_FIELDS = {
    'records.retention.policy': {
        'policy_version': 'fields.Char(string="Policy Version", default="1.0")',
        'effective_date': 'fields.Date(string="Effective Date", required=True)',
        'review_date': 'fields.Date(string="Review Date")',
        'approval_status': 'fields.Selection([("draft", "Draft"), ("approved", "Approved"), ("expired", "Expired")], string="Approval Status")',
        'legal_basis': 'fields.Text(string="Legal Basis")',
        'risk_level': 'fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High")], string="Risk Level")',
        'compliance_rate': 'fields.Float(string="Compliance Rate %", digits=(5,2), compute="_compute_compliance_rate")',
    },
    'paper.bale.recycling': {
        'load_shipment_id': 'fields.Many2one("paper.load.shipment", string="Load Shipment")',
        'bale_number': 'fields.Char(string="Bale Number", required=True, index=True)',
        'weight_lbs': 'fields.Float(string="Weight (lbs)", digits=(8,2))',
        'weight_net': 'fields.Float(string="Net Weight (lbs)", digits=(8,2))',
        'moisture_level': 'fields.Float(string="Moisture Level %", digits=(5,2))',
        'contamination_notes': 'fields.Text(string="Contamination Notes")',
        'processed_from_service': 'fields.Many2one("shredding.service", string="Processed From Service")',
        'storage_location': 'fields.Char(string="Storage Location")',
        'weighed_by': 'fields.Many2one("hr.employee", string="Weighed By")',
        'scale_reading': 'fields.Float(string="Scale Reading", digits=(8,2))',
        'load_number': 'fields.Char(string="Load Number")',
        'gps_coordinates': 'fields.Char(string="GPS Coordinates")',
        'status': 'fields.Selection([("pending", "Pending"), ("processed", "Processed"), ("shipped", "Shipped")], string="Status")',
    },
    'temp.inventory': {
        'inventory_id': 'fields.Many2one("records.inventory.dashboard", string="Related Inventory")',
        'document_type_id': 'fields.Many2one("records.document.type", string="Document Type")',
        'container_type': 'fields.Selection([("type_01", "Standard Box"), ("type_02", "Legal Box"), ("type_03", "Map Box")], string="Container Type")',
        'movement_type': 'fields.Selection([("in", "Incoming"), ("out", "Outgoing"), ("transfer", "Transfer")], string="Movement Type")',
    },
    'shredding.hard_drive': {
        'scan_count': 'fields.Integer(string="Scan Count")',
        'scan_location': 'fields.Char(string="Scan Location")',
        'scan_notes': 'fields.Text(string="Scan Notes")',
        'scanned_at_customer_by': 'fields.Many2one("hr.employee", string="Scanned At Customer By")',
        'scanned_serials': 'fields.Text(string="Scanned Serials")',
        'verified_at_facility_by': 'fields.Many2one("hr.employee", string="Verified At Facility By")',
        'verified_at_facility_date': 'fields.Datetime(string="Verified At Facility Date")',
        'verified_before_destruction': 'fields.Boolean(string="Verified Before Destruction", default=False)',
        'bulk_serial_input': 'fields.Text(string="Bulk Serial Input", help="Input multiple serial numbers separated by lines")',
    },
    'work.order.coordinator': {
        'coordinator_type': 'fields.Selection([("internal", "Internal"), ("external", "External"), ("contractor", "Contractor")], string="Coordinator Type")',
        'certification_type': 'fields.Selection([("naid", "NAID"), ("iso", "ISO"), ("other", "Other")], string="Certification Type")',
        'skill_level': 'fields.Selection([("junior", "Junior"), ("senior", "Senior"), ("expert", "Expert")], string="Skill Level")',
        'specialization': 'fields.Selection([("destruction", "Destruction"), ("storage", "Storage"), ("retrieval", "Retrieval")], string="Specialization")',
        'naid_certified': 'fields.Boolean(string="NAID Certified", default=False)',
        'background_check_date': 'fields.Date(string="Background Check Date")',
        'safety_training_date': 'fields.Date(string="Safety Training Date")',
        'productivity_score': 'fields.Float(string="Productivity Score", digits=(5,2))',
        'quality_score': 'fields.Float(string="Quality Score", digits=(5,2))',
        'customer_satisfaction': 'fields.Float(string="Customer Satisfaction", digits=(5,2))',
        'years_experience': 'fields.Integer(string="Years Experience")',
    },
    'document.retrieval.item': {
        'effective_priority': 'fields.Selection([("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Very High")], string="Effective Priority", compute="_compute_effective_priority")',
        'retrieval_cost': 'fields.Monetary(string="Retrieval Cost", currency_field="currency_id", compute="_compute_retrieval_cost")',
    },
    'records.billing.contact': {
        'service_type': 'fields.Selection([("primary", "Primary"), ("billing", "Billing"), ("technical", "Technical"), ("emergency", "Emergency")], string="Contact Type")',
    },
    'records.permanent.flag.wizard': {
        'action_type': 'fields.Selection([("set", "Set Flag"), ("remove", "Remove Flag")], string="Action Type")',
        'box_id': 'fields.Many2one("records.container", string="Container")',
        'permanent_flag': 'fields.Boolean(string="Permanent Flag")',
        'permanent_flag_set_by': 'fields.Many2one("res.users", string="Flag Set By")',
        'permanent_flag_set_date': 'fields.Datetime(string="Flag Set Date")',
        'user_password': 'fields.Char(string="User Password", help="Password verification for security")',
    },
    'fsm.reschedule.wizard': {
        'reschedule_reason': 'fields.Text(string="Reschedule Reason", required=True)',
        'schedule_date': 'fields.Datetime(string="New Schedule Date", required=True)',
    },
    'naid.audit.log': {
        'event_level': 'fields.Selection([("info", "Info"), ("warning", "Warning"), ("error", "Error"), ("critical", "Critical")], string="Event Level")',
        'res_id': 'fields.Integer(string="Related Record ID")',
        'chain_of_custody_id': 'fields.Many2one("records.chain.of.custody", string="Chain of Custody")',
        'naid_compliance_id': 'fields.Many2one("naid.compliance", string="NAID Compliance Record")',
        'event_date': 'fields.Datetime(string="Event Date", default=lambda self: fields.Datetime.now())',
    },
    'system.diagram.data': {
        'generation_time': 'fields.Float(string="Generation Time (seconds)", digits=(6,2))',
        'node_spacing': 'fields.Integer(string="Node Spacing", default=100)',
        'edge_length': 'fields.Integer(string="Edge Length", default=150)',
        'layout_algorithm': 'fields.Selection([("hierarchical", "Hierarchical"), ("spring", "Spring"), ("circular", "Circular")], string="Layout Algorithm")',
        'include_inactive': 'fields.Boolean(string="Include Inactive", default=False)',
        'group_by_module': 'fields.Boolean(string="Group By Module", default=True)',
        'max_depth': 'fields.Integer(string="Maximum Depth", default=3)',
        'exclude_system_models': 'fields.Boolean(string="Exclude System Models", default=True)',
        'last_access': 'fields.Datetime(string="Last Access")',
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

        # Find insertion point - look for existing business fields section
        insertion_patterns = [
            r'(\n    # ={70,}\n    # [A-Z\s]*BUSINESS[A-Z\s]* FIELDS\n    # ={70,})',
            r'(\n    # ={70,}\n    # [A-Z\s]+ METHODS\n    # ={70,})',
            r'(\n    @api\.)',
            r'(\n    def )',
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
    print("🔧 UTILITY & OPERATIONAL FIELDS FIXER - PHASE 3")
    print("=" * 60)
    print("Adding utility and operational fields for enhanced functionality")
    print()

    total_added = 0
    total_skipped = 0

    for model_name, fields_dict in UTILITY_OPERATIONAL_FIELDS.items():
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
    print("🎯 PHASE 3 SUMMARY")
    print("=" * 60)
    print(f"Utility fields added: {total_added}")
    print(f"Fields already existed: {total_skipped}")
    print("✅ Utility and operational fields addition complete!")

if __name__ == "__main__":
    main()
