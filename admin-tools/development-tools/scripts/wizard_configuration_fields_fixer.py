#!/usr/bin/env python3
"""
Wizard and Configuration Fields Fixer - Phase 5

Adds specialized fields for wizards, configuration models, and complex
business processes that require advanced field relationships.
"""

import os
import re

def add_specialized_fields_to_model(file_path, model_name, additional_fields):
    """Add specialized fields to wizard and configuration models"""
    if not os.path.exists(file_path):
        print(f"  ⚠️  Model file {os.path.basename(file_path)} not found, skipping...")
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    added_count = 0

    # Find the best insertion point (after the last field definition)
    field_pattern = r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*fields\.[^=\n]*(?:\([^)]*\))?)'
    matches = list(re.finditer(field_pattern, content))

    if not matches:
        print(f"  ⚠️  No field pattern found in {os.path.basename(file_path)}")
        return 0

    # Find insertion point (after last field but before compute methods)
    compute_pattern = r'\s*@api\.(depends|model|multi)'
    compute_match = re.search(compute_pattern, content)

    if compute_match:
        insertion_point = compute_match.start()
    else:
        # Insert after last field
        last_field_match = matches[-1]
        insertion_point = last_field_match.end()

    # Build the new fields section
    new_fields_section = "\n    # ============================================================================\n"
    new_fields_section += "    # SPECIALIZED CONFIGURATION FIELDS\n"
    new_fields_section += "    # ============================================================================\n"

    for field_name, field_def in additional_fields.items():
        # Check if field already exists
        if re.search(rf'\b{field_name}\s*=\s*fields\.', content):
            continue

        new_fields_section += f"    {field_name} = {field_def}\n"
        added_count += 1

    if added_count > 0:
        # Insert the new fields
        new_content = content[:insertion_point] + new_fields_section + content[insertion_point:]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"  ➕ Added {added_count} specialized fields to {model_name}")
    else:
        print(f"  ✅ All specialized fields already exist in {model_name}")

    return added_count

def main():
    """Add specialized fields to wizard and configuration models"""
    print("🔧 WIZARD AND CONFIGURATION FIELDS FIXER - PHASE 5")
    print("=" * 65)

    base_path = "records_management/models"
    total_added = 0

    # Specialized field definitions for wizard and configuration models
    specialized_fields_map = {
        "records_billing_config_audit.py": {
            "approval_required": "fields.Boolean(string='Approval Required', help='Whether this change requires approval')",
            "approval_status": "fields.Selection([('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], string='Approval Status')",
            "approved_by": "fields.Many2one('res.users', string='Approved By', help='User who approved this change')",
            "billing_config_id": "fields.Many2one('records.billing.config', string='Billing Configuration', required=True)",
            "binding_model_id": "fields.Many2one('ir.model', string='Target Model')",
            "binding_view_types": "fields.Char(string='View Types', help='Comma-separated list of view types')",
            "code": "fields.Char(string='Configuration Code', help='Unique code for this configuration')",
            "field_changed": "fields.Char(string='Field Changed', help='Name of field that was modified')",
            "groups_id": "fields.Many2many('res.groups', string='User Groups', help='Groups that can access this configuration')",
            "impact_assessment": "fields.Text(string='Impact Assessment', help='Assessment of change impact')",
            "model_id": "fields.Many2one('ir.model', string='Model', help='Target model for configuration')",
        },

        "records_permanent_flag_wizard.py": {
            "action_type": "fields.Selection([('set_permanent', 'Set Permanent'), ('remove_permanent', 'Remove Permanent'), ('review_permanent', 'Review Permanent')], string='Action Type', required=True)",
            "box_id": "fields.Many2one('records.container', string='Container', help='Container to modify permanent flag')",
            "permanent_flag": "fields.Boolean(string='Permanent Flag', help='Whether to set as permanent')",
            "permanent_flag_set_by": "fields.Many2one('res.users', string='Set By', help='User setting the permanent flag')",
            "permanent_flag_set_date": "fields.Datetime(string='Set Date', help='When permanent flag was set')",
            "user_password": "fields.Char(string='User Password', help='Password confirmation for security')",
        },

        "fsm_reschedule_wizard.py": {
            "reschedule_reason": "fields.Selection([('customer_request', 'Customer Request'), ('technician_unavailable', 'Technician Unavailable'), ('equipment_issue', 'Equipment Issue'), ('weather', 'Weather'), ('emergency', 'Emergency')], string='Reschedule Reason', required=True)",
            "schedule_date": "fields.Datetime(string='New Schedule Date', required=True, help='New date and time for the task')",
        },

        "paper_bale_recycling.py": {
            "bale_number": "fields.Char(string='Bale Number', help='Unique identifier for this bale')",
            "contamination_notes": "fields.Text(string='Contamination Notes', help='Details about any contamination found')",
            "gps_coordinates": "fields.Char(string='GPS Coordinates', help='Location coordinates where bale was processed')",
            "load_number": "fields.Char(string='Load Number', help='Associated load/shipment number')",
            "load_shipment_id": "fields.Many2one('paper.load.shipment', string='Load Shipment', help='Associated shipment')",
            "moisture_level": "fields.Float(string='Moisture Level (%)', digits=(5, 2), help='Measured moisture content')",
            "processed_from_service": "fields.Many2one('shredding.service', string='Source Service', help='Shredding service that generated this bale')",
            "scale_reading": "fields.Float(string='Scale Reading', digits=(10, 2), help='Raw scale reading')",
            "status": "fields.Selection([('weighed', 'Weighed'), ('inspected', 'Inspected'), ('loaded', 'Loaded'), ('shipped', 'Shipped'), ('sold', 'Sold')], string='Status')",
            "storage_location": "fields.Char(string='Storage Location', help='Where bale is currently stored')",
            "weighed_by": "fields.Many2one('hr.employee', string='Weighed By', help='Employee who performed weighing')",
            "weight_lbs": "fields.Float(string='Weight (lbs)', digits=(10, 2), help='Weight in pounds')",
            "weight_net": "fields.Float(string='Net Weight', digits=(10, 2), help='Net weight after tare')",
        },

        "records_retention_policy.py": {
            "approval_status": "fields.Selection([('draft', 'Draft'), ('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')], string='Approval Status')",
            "changed_by": "fields.Many2one('res.users', string='Changed By', help='User who made changes')",
            "compliance_rate": "fields.Float(string='Compliance Rate (%)', digits=(5, 2), compute='_compute_compliance_rate')",
            "destruction_efficiency_rate": "fields.Float(string='Destruction Efficiency (%)', digits=(5, 2), help='Rate of successful destructions')",
            "effective_date": "fields.Date(string='Effective Date', help='When policy becomes effective')",
            "exception_count": "fields.Integer(string='Exceptions Count', compute='_compute_exception_count')",
            "is_current_version": "fields.Boolean(string='Current Version', help='Whether this is the active version')",
            "legal_basis": "fields.Text(string='Legal Basis', help='Legal justification for retention period')",
            "next_mandatory_review": "fields.Date(string='Next Mandatory Review', help='Next required review date')",
            "policy_effectiveness_score": "fields.Float(string='Effectiveness Score', digits=(5, 2), compute='_compute_policy_effectiveness_score')",
            "policy_risk_score": "fields.Float(string='Risk Score', digits=(5, 2), help='Calculated risk score')",
            "policy_status": "fields.Selection([('active', 'Active'), ('inactive', 'Inactive'), ('superseded', 'Superseded'), ('under_review', 'Under Review')], string='Policy Status')",
            "policy_version": "fields.Char(string='Policy Version', help='Version identifier')",
            "review_cycle_months": "fields.Integer(string='Review Cycle (Months)', help='How often policy should be reviewed')",
            "review_date": "fields.Date(string='Last Review Date', help='When policy was last reviewed')",
            "risk_level": "fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Risk Level')",
            "version_date": "fields.Date(string='Version Date', help='Date this version was created')",
            "version_history_ids": "fields.One2many('records.policy.version', 'policy_id', string='Version History')",
            "version_number": "fields.Integer(string='Version Number', help='Sequential version number')",
        },

        "temp_inventory.py": {
            "container_type": "fields.Selection([('type_01', 'Standard Box'), ('type_02', 'Legal Box'), ('type_03', 'Map Box'), ('type_04', 'Odd Size'), ('type_06', 'Pathology')], string='Container Type')",
            "document_type_id": "fields.Many2one('records.document.type', string='Document Type', help='Type of documents in inventory')",
            "inventory_id": "fields.Many2one('records.inventory.dashboard', string='Inventory Dashboard', help='Related inventory dashboard')",
            "movement_type": "fields.Selection([('inbound', 'Inbound'), ('outbound', 'Outbound'), ('transfer', 'Transfer'), ('adjustment', 'Adjustment')], string='Movement Type')",
        },

        "records_location.py": {
            "access_instructions": "fields.Text(string='Access Instructions', help='Special instructions for accessing this location')",
            "storage_start_date": "fields.Date(string='Storage Start Date', help='When storage began at this location')",
        },

        "product_template.py": {
            "additional_box_cost": "fields.Monetary(string='Additional Box Cost', currency_field='currency_id', help='Cost for additional boxes beyond included amount')",
            "additional_document_cost": "fields.Monetary(string='Additional Document Cost', currency_field='currency_id', help='Cost for additional documents beyond included amount')",
            "auto_invoice": "fields.Boolean(string='Auto Invoice', help='Automatically generate invoices for this service')",
            "average_sale_price": "fields.Monetary(string='Average Sale Price', currency_field='currency_id', compute='_compute_average_sale_price')",
            "base_cost": "fields.Monetary(string='Base Cost', currency_field='currency_id', help='Base cost before markups')",
            "billing_frequency": "fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually'), ('per_use', 'Per Use')], string='Billing Frequency')",
            "box_retrieval_time": "fields.Float(string='Box Retrieval Time (Hours)', digits=(6, 2), help='Standard time to retrieve a box')",
            "box_storage_included": "fields.Integer(string='Boxes Included', help='Number of boxes included in base price')",
            "can_be_expensed": "fields.Boolean(string='Can Be Expensed', help='Whether this service can be expensed')",
            "certificate_of_destruction": "fields.Boolean(string='Certificate of Destruction', help='Includes certificate of destruction')",
            "climate_controlled": "fields.Boolean(string='Climate Controlled', help='Climate controlled storage')",
            "compliance_guarantee": "fields.Boolean(string='Compliance Guarantee', help='Guaranteed compliance with regulations')",
            "customer_retention_rate": "fields.Float(string='Customer Retention Rate (%)', digits=(5, 2), help='Rate of customer retention for this service')",
            "customization_allowed": "fields.Boolean(string='Customization Allowed', help='Service can be customized')",
            "data_recovery_guarantee": "fields.Boolean(string='Data Recovery Guarantee', help='Guaranteed data recovery if needed')",
            "digital_conversion_included": "fields.Boolean(string='Digital Conversion Included', help='Includes digital scanning')",
            "document_retrieval_time": "fields.Float(string='Document Retrieval Time (Hours)', digits=(6, 2), help='Standard time to retrieve a document')",
            "document_storage_included": "fields.Integer(string='Documents Included', help='Number of documents included in base price')",
            "emergency_response_time": "fields.Float(string='Emergency Response Time (Hours)', digits=(6, 2), help='Guaranteed emergency response time')",
            "emergency_retrieval": "fields.Boolean(string='Emergency Retrieval', help='24/7 emergency retrieval available')",
            "first_sale_date": "fields.Date(string='First Sale Date', help='First time this service was sold')",
            "geographic_coverage": "fields.Char(string='Geographic Coverage', help='Geographic areas covered')",
            "labor_cost": "fields.Monetary(string='Labor Cost', currency_field='currency_id', help='Labor component of cost')",
            "last_sale_date": "fields.Date(string='Last Sale Date', help='Most recent sale of this service')",
            "material_cost": "fields.Monetary(string='Material Cost', currency_field='currency_id', help='Material component of cost')",
            "max_boxes_included": "fields.Integer(string='Max Boxes Included', help='Maximum number of boxes included')",
            "max_documents_included": "fields.Integer(string='Max Documents Included', help='Maximum number of documents included')",
            "minimum_billing_period": "fields.Integer(string='Minimum Billing Period (Months)', help='Minimum commitment period')",
            "overhead_cost": "fields.Monetary(string='Overhead Cost', currency_field='currency_id', help='Overhead component of cost')",
            "pickup_delivery_included": "fields.Boolean(string='Pickup/Delivery Included', help='Includes pickup and delivery service')",
            "price_history_count": "fields.Integer(string='Price Changes Count', compute='_compute_price_history_count')",
            "price_margin": "fields.Float(string='Price Margin (%)', digits=(5, 2), help='Profit margin percentage')",
            "profit_margin": "fields.Float(string='Profit Margin (%)', digits=(5, 2), help='Calculated profit margin')",
            "prorate_partial_periods": "fields.Boolean(string='Prorate Partial Periods', help='Prorate billing for partial periods')",
            "sales_count": "fields.Integer(string='Sales Count', compute='_compute_sales_count')",
            "sales_velocity": "fields.Float(string='Sales Velocity', digits=(8, 2), help='Rate of sales over time')",
            "same_day_service": "fields.Boolean(string='Same Day Service', help='Same day service available')",
            "security_guarantee": "fields.Boolean(string='Security Guarantee', help='Security guarantee provided')",
            "shredding_included": "fields.Boolean(string='Shredding Included', help='Secure shredding included')",
            "sla_terms": "fields.Text(string='SLA Terms', help='Service level agreement terms')",
            "standard_response_time": "fields.Float(string='Standard Response Time (Hours)', digits=(6, 2), help='Standard response time for requests')",
            "total_revenue_ytd": "fields.Monetary(string='Total Revenue YTD', currency_field='currency_id', compute='_compute_total_revenue_ytd')",
            "total_sales_ytd": "fields.Integer(string='Total Sales YTD', compute='_compute_total_sales_ytd')",
            "uptime_guarantee": "fields.Float(string='Uptime Guarantee (%)', digits=(5, 2), help='Guaranteed uptime percentage')",
            "witness_destruction": "fields.Boolean(string='Witness Destruction', help='Customer can witness destruction')",
        },

        "system_diagram_data.py": {
            "edge_length": "fields.Float(string='Edge Length', digits=(8, 2), help='Length of diagram edges')",
            "exclude_system_models": "fields.Boolean(string='Exclude System Models', help='Exclude Odoo system models from diagram')",
            "generation_time": "fields.Float(string='Generation Time (seconds)', digits=(8, 3), help='Time taken to generate diagram')",
            "group_by_module": "fields.Boolean(string='Group by Module', help='Group related models by their module')",
            "include_inactive": "fields.Boolean(string='Include Inactive', help='Include inactive records in diagram')",
            "last_access": "fields.Datetime(string='Last Access', help='When diagram was last accessed')",
            "layout_algorithm": "fields.Selection([('force', 'Force-directed'), ('hierarchical', 'Hierarchical'), ('circular', 'Circular'), ('grid', 'Grid')], string='Layout Algorithm')",
            "max_depth": "fields.Integer(string='Max Depth', help='Maximum relationship depth to display')",
            "node_spacing": "fields.Float(string='Node Spacing', digits=(6, 2), help='Spacing between diagram nodes')",
        },
    }

    # Process each model
    for file_name, fields_to_add in specialized_fields_map.items():
        file_path = os.path.join(base_path, file_name)
        model_name = file_name.replace('.py', '').replace('_', '.')

        print(f"\n📄 Processing {file_name}...")
        added = add_specialized_fields_to_model(file_path, model_name, fields_to_add)
        total_added += added

    print(f"\n🎯 PHASE 5 SUMMARY: Added {total_added} specialized configuration fields")
    print("=" * 65)

if __name__ == "__main__":
    main()
