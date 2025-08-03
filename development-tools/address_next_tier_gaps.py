#!/usr/bin/env python3
"""
Address Next Tier Field Gaps Script
===================================
Systematically addresses the next tier of highest-priority field gaps.
Targets models with 20+ missing fields.
"""

import os
import sys


def add_fields_to_model(file_path, fields_to_add):
    """Add fields to a specific model file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the class definition
        lines = content.split("\n")

        # Find where to insert fields (after existing field definitions)
        insert_index = -1
        for i, line in enumerate(lines):
            if "fields." in line and "=" in line and not line.strip().startswith("#"):
                insert_index = i + 1

        if insert_index == -1:
            # Look for class definition instead
            for i, line in enumerate(lines):
                if line.strip().startswith("class ") and "models.Model" in line:
                    insert_index = i + 5  # After class definition and inheritance
                    break

        if insert_index == -1:
            print(f"❌ Could not find insertion point in {file_path}")
            return False

        # Insert fields
        for field_definition in fields_to_add:
            lines.insert(insert_index, f"    {field_definition}")
            insert_index += 1

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"✅ Added {len(fields_to_add)} fields to {os.path.basename(file_path)}")
        return True

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def get_next_tier_definitions():
    """Define comprehensive field sets for next tier priority models."""

    return {
        # Paper Bale - 55 missing fields
        "paper_bale.py": [
            "# Paper Bale Management Fields",
            "action_date = fields.Date('Action Date')",
            "action_type = fields.Selection([('sort', 'Sort'), ('compress', 'Compress'), ('transport', 'Transport')], 'Action Type')",
            "carbon_neutral = fields.Boolean('Carbon Neutral', default=False)",
            "chain_of_custody_verified = fields.Boolean('Chain of Custody Verified', default=False)",
            "confidentiality_level = fields.Selection([('public', 'Public'), ('internal', 'Internal'), ('confidential', 'Confidential')], default='internal')",
            "contamination_assessment = fields.Text('Contamination Assessment')",
            "contamination_level = fields.Selection([('none', 'None'), ('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='none')",
            "customer_approval_required = fields.Boolean('Customer Approval Required', default=False)",
            "customer_notification_sent = fields.Boolean('Customer Notification Sent', default=False)",
            "destruction_method_verified = fields.Boolean('Destruction Method Verified', default=False)",
            "environmental_impact_assessment = fields.Text('Environmental Impact Assessment')",
            "estimated_processing_time = fields.Float('Estimated Processing Time (Hours)')",
            "final_weight_verified = fields.Boolean('Final Weight Verified', default=False)",
            "gps_pickup_location = fields.Char('GPS Pickup Location')",
            "handling_requirements = fields.Text('Handling Requirements')",
            "load_optimization_notes = fields.Text('Load Optimization Notes')",
            "moisture_content_percentage = fields.Float('Moisture Content %', default=0.0)",
            "packaging_requirements = fields.Text('Packaging Requirements')",
            "pre_processing_required = fields.Boolean('Pre-processing Required', default=False)",
            "processing_completion_date = fields.Date('Processing Completion Date')",
            "processing_facility_id = fields.Many2one('processing.facility', 'Processing Facility')",
            "quality_control_passed = fields.Boolean('Quality Control Passed', default=False)",
            "recycling_category = fields.Selection([('office_paper', 'Office Paper'), ('newsprint', 'Newsprint'), ('cardboard', 'Cardboard'), ('mixed', 'Mixed')], default='mixed')",
            "recycling_certificate_required = fields.Boolean('Recycling Certificate Required', default=True)",
            "security_level_required = fields.Selection([('standard', 'Standard'), ('secure', 'Secure'), ('confidential', 'Confidential')], default='standard')",
            "sorting_completion_date = fields.Date('Sorting Completion Date')",
            "sorting_required = fields.Boolean('Sorting Required', default=True)",
            "storage_duration_days = fields.Integer('Storage Duration (Days)', default=30)",
            "temperature_requirements = fields.Text('Temperature Requirements')",
            "transportation_method = fields.Selection([('truck', 'Truck'), ('rail', 'Rail'), ('container', 'Container')], default='truck')",
            "volume_optimization_ratio = fields.Float('Volume Optimization Ratio', default=1.0)",
            "waste_stream_classification = fields.Selection([('commercial', 'Commercial'), ('industrial', 'Industrial'), ('institutional', 'Institutional')], default='commercial')",
            "weight_verification_method = fields.Selection([('scale', 'Scale'), ('estimate', 'Estimate')], default='scale')",
        ],
        # Portal Feedback - 52 missing fields
        "portal_feedback.py": [
            "# Portal Feedback System Fields",
            "activity_date = fields.Date('Activity Date')",
            "activity_exception_decoration = fields.Selection([('warning', 'Warning'), ('danger', 'Danger')], 'Activity Exception Decoration')",
            "activity_state = fields.Selection([('overdue', 'Overdue'), ('today', 'Today'), ('planned', 'Planned')], 'Activity State')",
            "activity_type = fields.Selection([('call', 'Call'), ('meeting', 'Meeting'), ('todo', 'To Do')], 'Activity Type')",
            "followup_activity_ids = fields.One2many('mail.activity', 'res_id', 'Follow-up Activities', domain=[('res_model', '=', 'portal.feedback')])",
            "completed = fields.Boolean('Completed', default=False)",
            "csat_score = fields.Integer('CSAT Score', help='Customer Satisfaction Score (1-10)')",
            "customer_email = fields.Char('Customer Email')",
            "customer_feedback_count = fields.Integer('Customer Feedback Count', default=0)",
            "customer_phone = fields.Char('Customer Phone')",
            "escalation_level = fields.Selection([('none', 'None'), ('level_1', 'Level 1'), ('level_2', 'Level 2'), ('level_3', 'Level 3')], default='none')",
            "feedback_category_id = fields.Many2one('feedback.category', 'Feedback Category')",
            "feedback_channel = fields.Selection([('portal', 'Portal'), ('email', 'Email'), ('phone', 'Phone'), ('survey', 'Survey')], default='portal')",
            "feedback_complexity = fields.Selection([('simple', 'Simple'), ('moderate', 'Moderate'), ('complex', 'Complex')], default='simple')",
            "feedback_impact_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')",
            "feedback_priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium')",
            "feedback_resolution_time = fields.Float('Resolution Time (Hours)')",
            "feedback_subcategory_id = fields.Many2one('feedback.subcategory', 'Feedback Subcategory')",
            "feedback_type = fields.Selection([('compliment', 'Compliment'), ('complaint', 'Complaint'), ('suggestion', 'Suggestion'), ('inquiry', 'Inquiry')], default='inquiry')",
            "follow_up_required = fields.Boolean('Follow-up Required', default=False)",
            "internal_escalation_required = fields.Boolean('Internal Escalation Required', default=False)",
            "nps_score = fields.Integer('NPS Score', help='Net Promoter Score (-100 to 100)')",
            "quality_rating = fields.Selection([('1', '1 - Poor'), ('2', '2 - Fair'), ('3', '3 - Good'), ('4', '4 - Very Good'), ('5', '5 - Excellent')], 'Quality Rating')",
            "resolution_notes = fields.Text('Resolution Notes')",
            "response_deadline = fields.Datetime('Response Deadline')",
            "response_sent = fields.Boolean('Response Sent', default=False)",
            "response_time_target = fields.Float('Response Time Target (Hours)', default=24.0)",
            "satisfaction_rating = fields.Selection([('very_dissatisfied', 'Very Dissatisfied'), ('dissatisfied', 'Dissatisfied'), ('neutral', 'Neutral'), ('satisfied', 'Satisfied'), ('very_satisfied', 'Very Satisfied')], 'Satisfaction Rating')",
            "service_improvement_suggestion = fields.Text('Service Improvement Suggestion')",
            "stakeholder_notification_required = fields.Boolean('Stakeholder Notification Required', default=False)",
        ],
        # NAID Compliance - 43 missing fields
        "naid_compliance.py": [
            "# NAID Compliance Management Fields",
            "audit_result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail'), ('conditional', 'Conditional')], 'Audit Result')",
            "audit_scope = fields.Selection([('full', 'Full Audit'), ('partial', 'Partial'), ('focused', 'Focused')], default='full')",
            "audit_type = fields.Selection([('initial', 'Initial'), ('surveillance', 'Surveillance'), ('recertification', 'Recertification')], default='surveillance')",
            "auditor_name = fields.Char('Auditor Name')",
            "benchmark = fields.Selection([('aaa', 'NAID AAA'), ('aa', 'NAID AA'), ('a', 'NAID A')], default='aaa')",
            "certificate_expiration_date = fields.Date('Certificate Expiration Date')",
            "certificate_issue_date = fields.Date('Certificate Issue Date')",
            "certificate_number = fields.Char('Certificate Number')",
            "certificate_status = fields.Selection([('active', 'Active'), ('expired', 'Expired'), ('suspended', 'Suspended'), ('revoked', 'Revoked')], default='active')",
            "compliance_documentation_complete = fields.Boolean('Compliance Documentation Complete', default=False)",
            "compliance_manager_id = fields.Many2one('hr.employee', 'Compliance Manager')",
            "compliance_officer_id = fields.Many2one('hr.employee', 'Compliance Officer')",
            "compliance_review_date = fields.Date('Compliance Review Date')",
            "compliance_training_completed = fields.Boolean('Compliance Training Completed', default=False)",
            "corrective_action_plan = fields.Text('Corrective Action Plan')",
            "corrective_actions_required = fields.Boolean('Corrective Actions Required', default=False)",
            "destruction_method_approved = fields.Boolean('Destruction Method Approved', default=False)",
            "documentation_retention_period = fields.Integer('Documentation Retention Period (Years)', default=7)",
            "employee_training_records = fields.Text('Employee Training Records')",
            "equipment_certification_current = fields.Boolean('Equipment Certification Current', default=False)",
            "facility_security_assessment = fields.Text('Facility Security Assessment')",
            "internal_audit_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')], default='quarterly')",
            "last_audit_date = fields.Date('Last Audit Date')",
            "next_audit_due_date = fields.Date('Next Audit Due Date')",
            "non_conformance_count = fields.Integer('Non-conformance Count', default=0)",
            "operational_procedures_current = fields.Boolean('Operational Procedures Current', default=False)",
            "quality_management_system = fields.Selection([('iso_9001', 'ISO 9001'), ('custom', 'Custom'), ('none', 'None')], default='iso_9001')",
            "regulatory_compliance_verified = fields.Boolean('Regulatory Compliance Verified', default=False)",
            "risk_assessment_completed = fields.Boolean('Risk Assessment Completed', default=False)",
            "security_clearance_level = fields.Selection([('public', 'Public'), ('secret', 'Secret'), ('top_secret', 'Top Secret')], default='public')",
            "staff_background_checks_current = fields.Boolean('Staff Background Checks Current', default=False)",
            "surveillance_audit_frequency = fields.Selection([('quarterly', 'Quarterly'), ('semi_annual', 'Semi-annual'), ('annual', 'Annual')], default='annual')",
        ],
        # Transitory Field Config - 37 missing fields
        "transitory_field_config.py": [
            "# Transitory Field Configuration Fields",
            "config_preset = fields.Selection([('basic', 'Basic'), ('advanced', 'Advanced'), ('custom', 'Custom')], default='basic')",
            "customer_id = fields.Many2one('res.partner', 'Customer')",
            "department_id = fields.Many2one('hr.department', 'Department')",
            "field_label_config_id = fields.Many2one('field.label.customization', 'Field Label Configuration')",
            "require_client_reference = fields.Boolean('Require Client Reference', default=False)",
            "auto_apply_config = fields.Boolean('Auto Apply Configuration', default=True)",
            "config_version = fields.Char('Configuration Version')",
            "custom_field_definitions = fields.Text('Custom Field Definitions')",
            "data_validation_rules = fields.Text('Data Validation Rules')",
            "default_field_values = fields.Text('Default Field Values')",
            "field_dependency_rules = fields.Text('Field Dependency Rules')",
            "field_group_configuration = fields.Text('Field Group Configuration')",
            "field_visibility_rules = fields.Text('Field Visibility Rules')",
            "form_layout_configuration = fields.Text('Form Layout Configuration')",
            "mandatory_fields_list = fields.Text('Mandatory Fields List')",
            "permission_based_visibility = fields.Boolean('Permission Based Visibility', default=False)",
            "preset_configurations = fields.Text('Preset Configurations')",
            "readonly_fields_list = fields.Text('Readonly Fields List')",
            "template_configuration = fields.Text('Template Configuration')",
            "user_customization_allowed = fields.Boolean('User Customization Allowed', default=True)",
            "validation_error_messages = fields.Text('Validation Error Messages')",
            "workflow_integration_config = fields.Text('Workflow Integration Configuration')",
        ],
        # Load - 34 missing fields (targeting remaining framework fields)
        "load.py": [
            "# Load Management Fields",
            "activity_exception_decoration = fields.Selection([('warning', 'Warning'), ('danger', 'Danger')], 'Activity Exception Decoration')",
            "activity_state = fields.Selection([('overdue', 'Overdue'), ('today', 'Today'), ('planned', 'Planned')], 'Activity State')",
            "message_type = fields.Selection([('email', 'Email'), ('comment', 'Comment'), ('notification', 'Notification')], 'Message Type')",
            "bale_number = fields.Char('Bale Number')",
            "capacity_utilization = fields.Float('Capacity Utilization %', default=0.0)",
            "contamination_notes = fields.Text('Contamination Notes')",
            "contamination_report = fields.Text('Contamination Report')",
            "date = fields.Date('Load Date')",
            "delivery_confirmation_required = fields.Boolean('Delivery Confirmation Required', default=True)",
            "delivery_instructions = fields.Text('Delivery Instructions')",
            "driver_certification_verified = fields.Boolean('Driver Certification Verified', default=False)",
            "estimated_arrival_time = fields.Datetime('Estimated Arrival Time')",
            "load_configuration = fields.Text('Load Configuration')",
            "load_optimization_algorithm = fields.Selection([('weight', 'Weight Based'), ('volume', 'Volume Based'), ('mixed', 'Mixed')], default='mixed')",
            "load_securing_method = fields.Text('Load Securing Method')",
            "material_compatibility_verified = fields.Boolean('Material Compatibility Verified', default=False)",
            "route_optimization_data = fields.Text('Route Optimization Data')",
            "safety_inspection_completed = fields.Boolean('Safety Inspection Completed', default=False)",
            "temperature_monitoring_required = fields.Boolean('Temperature Monitoring Required', default=False)",
            "transportation_hazards = fields.Text('Transportation Hazards')",
            "vehicle_inspection_completed = fields.Boolean('Vehicle Inspection Completed', default=False)",
            "weight_distribution_notes = fields.Text('Weight Distribution Notes')",
        ],
    }


def main():
    """Main execution function."""
    print("🚀 ADDRESS NEXT TIER FIELD GAPS")
    print("=" * 60)

    # Base directory
    base_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    if not os.path.exists(base_dir):
        print(f"❌ Models directory not found: {base_dir}")
        return False

    # Get model definitions
    model_definitions = get_next_tier_definitions()

    print(f"📋 Processing {len(model_definitions)} next-tier models...")

    success_count = 0
    total_fields_added = 0

    for model_file, field_definitions in model_definitions.items():
        file_path = os.path.join(base_dir, model_file)

        if not os.path.exists(file_path):
            print(f"⚠️  Model file not found: {model_file}")
            continue

        if add_fields_to_model(file_path, field_definitions):
            success_count += 1
            total_fields_added += len([f for f in field_definitions if "=" in f])

        print()  # Empty line for readability

    print("=" * 60)
    print("✅ COMPLETION SUMMARY:")
    print(f"   📁 Models processed: {success_count}/{len(model_definitions)}")
    print(f"   📝 Total fields added: {total_fields_added}")
    print("   🎯 Target gap reduction: ~150+ fields")
    print("=" * 60)

    return success_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
