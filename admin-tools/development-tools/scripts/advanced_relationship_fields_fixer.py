#!/usr/bin/env python3
"""
Advanced Relationship Fields Fixer - Phase 4

Focuses on complex business relationships, workflow fields, and advanced
functionality that couldn't be detected in earlier phases.
"""

import os
import re

def add_advanced_fields_to_model(file_path, model_name, additional_fields):
    """Add advanced relationship and workflow fields to a model"""
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
    new_fields_section = "\n"

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

        print(f"  ➕ Added {added_count} advanced fields to {model_name}")
    else:
        print(f"  ✅ All advanced fields already exist in {model_name}")

    return added_count

def main():
    """Add advanced relationship and workflow fields to Records Management models"""
    print("🔧 ADVANCED RELATIONSHIP FIELDS FIXER - PHASE 4")
    print("=" * 60)

    base_path = "records_management/models"
    total_added = 0

    # Advanced field definitions for key models
    advanced_fields_map = {
        "fsm_task.py": {
            "partner_id": "fields.Many2one('res.partner', string='Customer', help='Customer for this task')",
            "location_id": "fields.Many2one('records.location', string='Task Location', help='Location where task is performed')",
            "container_count": "fields.Integer(string='Container Count', help='Number of containers involved')",
            "container_type": "fields.Selection([('type_01', 'Standard Box'), ('type_02', 'Legal Box'), ('type_03', 'Map Box'), ('type_04', 'Odd Size'), ('type_06', 'Pathology')], string='Container Type')",
            "access_instructions": "fields.Text(string='Access Instructions', help='Special access instructions for location')",
            "actual_start_time": "fields.Datetime(string='Actual Start Time', help='When work actually started')",
            "actual_end_time": "fields.Datetime(string='Actual End Time', help='When work actually ended')",
            "assigned_date": "fields.Date(string='Assigned Date', help='Date task was assigned')",
            "assigned_technician": "fields.Many2one('hr.employee', string='Assigned Technician', help='Technician assigned to task')",
            "completion_date": "fields.Datetime(string='Completion Date', help='When task was completed')",
            "estimated_duration": "fields.Float(string='Estimated Duration (Hours)', digits=(6, 2), help='Estimated time to complete')",
            "event_description": "fields.Text(string='Event Description', help='Description of what happened')",
            "event_timestamp": "fields.Datetime(string='Event Timestamp', help='When event occurred')",
            "event_type": "fields.Selection([('pickup', 'Pickup'), ('delivery', 'Delivery'), ('shredding', 'Shredding'), ('retrieval', 'Retrieval')], string='Event Type')",
            "follow_up_required": "fields.Boolean(string='Follow-up Required', help='Whether follow-up is needed')",
            "location_address": "fields.Text(string='Location Address', help='Full address of location')",
            "naid_audit_log_ids": "fields.One2many('naid.audit.log', 'fsm_task_id', string='NAID Audit Logs')",
            "photos": "fields.Many2many('ir.attachment', string='Photos', help='Photos taken during task')",
            "required_skills": "fields.Text(string='Required Skills', help='Skills required for this task')",
            "required_tools": "fields.Text(string='Required Tools', help='Tools required for this task')",
            "service_location": "fields.Char(string='Service Location', help='Location description')",
            "special_requirements": "fields.Text(string='Special Requirements', help='Any special requirements')",
            "task_status": "fields.Selection([('new', 'New'), ('assigned', 'Assigned'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Task Status')",
            "volume_cf": "fields.Float(string='Volume (CF)', digits=(12, 3), help='Volume in cubic feet')",
            "weight_lbs": "fields.Float(string='Weight (lbs)', digits=(12, 2), help='Weight in pounds')",
            "work_order_count": "fields.Integer(string='Work Orders Count', compute='_compute_work_order_count')",
            "work_order_ids": "fields.One2many('file.retrieval.work.order', 'fsm_task_id', string='Work Orders')",
            "work_order_type": "fields.Selection([('retrieval', 'Document Retrieval'), ('destruction', 'Destruction'), ('container_access', 'Container Access')], string='Work Order Type')",
        },

        "work_order_coordinator.py": {
            "active_work_orders": "fields.Integer(string='Active Work Orders', compute='_compute_active_work_orders')",
            "assigned_equipment_ids": "fields.Many2many('maintenance.equipment', string='Assigned Equipment')",
            "average_completion_time": "fields.Float(string='Avg Completion Time (Hours)', digits=(6, 2), compute='_compute_average_completion_time')",
            "certification_count": "fields.Integer(string='Certifications Count', compute='_compute_certification_count')",
            "certification_ids": "fields.One2many('hr.employee.certification', 'coordinator_id', string='Certifications')",
            "current_work_order_ids": "fields.One2many('file.retrieval.work.order', 'coordinator_id', string='Current Work Orders')",
            "department_id": "fields.Many2one('records.department', string='Department')",
            "email": "fields.Char(string='Email', help='Contact email')",
            "emergency_contact": "fields.Char(string='Emergency Contact', help='Emergency contact person')",
            "emergency_phone": "fields.Char(string='Emergency Phone', help='Emergency contact phone')",
            "employee_id": "fields.Many2one('hr.employee', string='Employee Record')",
            "equipment_authorizations": "fields.Text(string='Equipment Authorizations', help='Equipment user is authorized to operate')",
            "is_active": "fields.Boolean(string='Currently Active', default=True)",
            "last_login": "fields.Datetime(string='Last Login', help='Last system login')",
            "last_maintenance_date": "fields.Date(string='Last Maintenance Training', help='Last equipment maintenance training')",
            "last_performance_review": "fields.Date(string='Last Performance Review')",
            "mobile": "fields.Char(string='Mobile Phone')",
            "next_maintenance_due": "fields.Date(string='Next Maintenance Due', help='Next equipment maintenance training due')",
            "next_training_date": "fields.Date(string='Next Training Date')",
            "on_time_completion_rate": "fields.Float(string='On-Time Completion Rate (%)', digits=(5, 2), compute='_compute_on_time_completion_rate')",
            "overtime_approved": "fields.Boolean(string='Overtime Approved', help='Authorized for overtime work')",
            "pending_assignments": "fields.Integer(string='Pending Assignments', compute='_compute_pending_assignments')",
            "phone": "fields.Char(string='Work Phone')",
            "safety_incidents": "fields.Integer(string='Safety Incidents', help='Number of recorded safety incidents')",
            "time_zone": "fields.Selection([('EST', 'Eastern'), ('CST', 'Central'), ('MST', 'Mountain'), ('PST', 'Pacific')], string='Time Zone')",
            "tool_certifications": "fields.Text(string='Tool Certifications', help='Certified tools and equipment')",
            "total_hours_logged": "fields.Float(string='Total Hours Logged', digits=(8, 2), compute='_compute_total_hours_logged')",
            "training_completed": "fields.Date(string='Initial Training Completed')",
            "vehicle_access": "fields.Boolean(string='Vehicle Access', help='Authorized to operate company vehicles')",
            "weekend_availability": "fields.Boolean(string='Weekend Availability', help='Available for weekend work')",
            "work_order_type": "fields.Selection([('retrieval', 'Document Retrieval'), ('destruction', 'Destruction'), ('container_access', 'Container Access')], string='Specialization')",
            "work_schedule": "fields.Selection([('full_time', 'Full Time'), ('part_time', 'Part Time'), ('contract', 'Contract'), ('on_call', 'On Call')], string='Work Schedule')",
        },

        "system_flowchart_wizard.py": {
            "animation_enabled": "fields.Boolean(string='Animation Enabled', default=True)",
            "cache_results": "fields.Boolean(string='Cache Results', default=True, help='Cache diagram data for performance')",
            "color_scheme": "fields.Selection([('default', 'Default'), ('dark', 'Dark'), ('light', 'Light'), ('colorblind', 'Colorblind Friendly')], string='Color Scheme', default='default')",
            "config_valid": "fields.Boolean(string='Configuration Valid', compute='_compute_config_valid')",
            "edge_style": "fields.Selection([('solid', 'Solid'), ('dashed', 'Dashed'), ('dotted', 'Dotted')], string='Edge Style', default='solid')",
            "enabled_components_count": "fields.Integer(string='Enabled Components', compute='_compute_enabled_components_count')",
            "estimated_load_time": "fields.Float(string='Estimated Load Time (seconds)', digits=(6, 2), compute='_compute_estimated_load_time')",
            "export_format": "fields.Selection([('png', 'PNG'), ('svg', 'SVG'), ('pdf', 'PDF'), ('html', 'HTML')], string='Export Format', default='png')",
            "export_quality": "fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('ultra', 'Ultra')], string='Export Quality', default='medium')",
            "export_timestamp": "fields.Datetime(string='Last Export', help='When diagram was last exported')",
            "generated_config": "fields.Text(string='Generated Configuration', help='Auto-generated diagram configuration')",
            "help_position": "fields.Selection([('top', 'Top'), ('bottom', 'Bottom'), ('left', 'Left'), ('right', 'Right'), ('overlay', 'Overlay')], string='Help Position', default='overlay')",
            "include_metadata": "fields.Boolean(string='Include Metadata', default=True, help='Include model metadata in diagram')",
            "label_position": "fields.Selection([('top', 'Top'), ('bottom', 'Bottom'), ('center', 'Center')], string='Label Position', default='center')",
            "layout_style": "fields.Selection([('hierarchical', 'Hierarchical'), ('circular', 'Circular'), ('force', 'Force-directed'), ('grid', 'Grid')], string='Layout Style', default='hierarchical')",
            "max_nodes": "fields.Integer(string='Maximum Nodes', default=50, help='Maximum number of nodes to display')",
            "node_size": "fields.Selection([('small', 'Small'), ('medium', 'Medium'), ('large', 'Large'), ('auto', 'Auto')], string='Node Size', default='medium')",
            "performance_mode": "fields.Boolean(string='Performance Mode', help='Optimize for large datasets')",
            "preview_data": "fields.Text(string='Preview Data', help='Preview of diagram data')",
            "rm_configurator_enabled": "fields.Boolean(string='RM Configurator Enabled', help='Include RM module configurator options')",
            "search_scenario": "fields.Selection([('basic', 'Basic Search'), ('advanced', 'Advanced Search'), ('relationship', 'Relationship Mapping')], string='Search Scenario', default='basic')",
            "show_access_rights": "fields.Boolean(string='Show Access Rights', help='Display access control information')",
            "show_audit_trails": "fields.Boolean(string='Show Audit Trails', help='Display audit trail connections')",
            "show_companies": "fields.Boolean(string='Show Companies', default=True)",
            "show_computed_fields": "fields.Boolean(string='Show Computed Fields', help='Display computed field information')",
            "show_context_help": "fields.Boolean(string='Show Context Help', default=True)",
            "show_departments": "fields.Boolean(string='Show Departments', default=True)",
            "show_models": "fields.Boolean(string='Show Models', default=True)",
            "show_relationships": "fields.Boolean(string='Show Relationships', default=True)",
            "show_security_rules": "fields.Boolean(string='Show Security Rules', help='Display security rule information')",
            "show_tooltips": "fields.Boolean(string='Show Tooltips', default=True)",
            "show_tutorial": "fields.Boolean(string='Show Tutorial', default=False)",
            "show_users": "fields.Boolean(string='Show Users', default=False)",
            "show_workflows": "fields.Boolean(string='Show Workflows', default=True)",
            "step": "fields.Integer(string='Current Step', default=1)",
            "target_company": "fields.Many2one('res.company', string='Target Company')",
            "target_model": "fields.Char(string='Target Model', help='Focus on specific model')",
            "target_user": "fields.Many2one('res.users', string='Target User')",
            "total_companies": "fields.Integer(string='Total Companies', compute='_compute_total_companies')",
            "total_models": "fields.Integer(string='Total Models', compute='_compute_total_models')",
            "total_relationships": "fields.Integer(string='Total Relationships', compute='_compute_total_relationships')",
            "total_users": "fields.Integer(string='Total Users', compute='_compute_total_users')",
            "tutorial_auto_advance": "fields.Boolean(string='Auto-advance Tutorial', default=False)",
            "tutorial_auto_start": "fields.Boolean(string='Auto-start Tutorial', default=False)",
            "tutorial_highlights": "fields.Boolean(string='Tutorial Highlights', default=True)",
            "tutorial_step": "fields.Integer(string='Tutorial Step', default=1)",
            "view_id": "fields.Many2one('ir.ui.view', string='View Configuration')",
            "zoom_level": "fields.Float(string='Zoom Level', digits=(3, 2), default=1.0, help='Current zoom level of diagram')",
        },

        "shredding_hard_drive.py": {
            "bulk_serial_input": "fields.Text(string='Bulk Serial Input', help='Paste multiple serial numbers (one per line)')",
            "scan_count": "fields.Integer(string='Scans Count', compute='_compute_scan_count')",
            "scan_location": "fields.Selection([('customer_site', 'Customer Site'), ('facility', 'Our Facility'), ('transport', 'In Transport')], string='Scan Location')",
            "scan_notes": "fields.Text(string='Scan Notes', help='Notes from scanning process')",
            "scanned_at_customer_by": "fields.Many2one('hr.employee', string='Scanned at Customer By')",
            "scanned_serials": "fields.Text(string='Scanned Serial Numbers', help='Serial numbers that were successfully scanned')",
            "verified_at_facility_by": "fields.Many2one('hr.employee', string='Verified at Facility By')",
            "verified_at_facility_date": "fields.Datetime(string='Verified at Facility Date')",
            "verified_before_destruction": "fields.Boolean(string='Verified Before Destruction', help='Confirmed verified before destruction')",
        },

        "document_retrieval_item.py": {
            "effective_priority": "fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High'), ('3', 'Very High')], string='Effective Priority', compute='_compute_effective_priority')",
            "retrieval_cost": "fields.Monetary(string='Retrieval Cost', currency_field='currency_id', help='Cost to retrieve this item')",
        },

        "naid_compliance_checklist.py": {
            "category": "fields.Selection([('documentation', 'Documentation'), ('equipment', 'Equipment'), ('personnel', 'Personnel'), ('facility', 'Facility'), ('process', 'Process')], string='Category', required=True)",
            "checklist_item_ids": "fields.One2many('naid.compliance.checklist.item', 'checklist_id', string='Checklist Items')",
            "is_required": "fields.Boolean(string='Required', default=True, help='Whether this checklist is mandatory')",
            "sequence": "fields.Integer(string='Sequence', default=10, help='Order of checklist execution')",
        },

        "mobile_bin_key_wizard.py": {
            "contact_id": "fields.Many2one('res.partner', string='Emergency Contact', help='Emergency contact for key holder')",
        },

        "records_digital_scan.py": {
            "scanned_by": "fields.Many2one('hr.employee', string='Scanned By', help='Employee who performed the scan')",
        },

        "account_move_line.py": {
            "inherit_id": "fields.Many2one('account.move.line', string='Inherited Line', help='Parent accounting line')",
        },
    }

    # Process each model
    for file_name, fields_to_add in advanced_fields_map.items():
        file_path = os.path.join(base_path, file_name)
        model_name = file_name.replace('.py', '').replace('_', '.')

        print(f"\n📄 Processing {file_name}...")
        added = add_advanced_fields_to_model(file_path, model_name, fields_to_add)
        total_added += added

    print(f"\n🎯 PHASE 4 SUMMARY: Added {total_added} advanced relationship fields")
    print("=" * 60)

if __name__ == "__main__":
    main()
