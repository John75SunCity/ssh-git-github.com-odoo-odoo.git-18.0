#!/usr/bin/env python3
"""
Address Top Priority Field Gaps Script
======================================
Systematically addresses the highest-priority field gaps identified by smart analysis.
Targets top 15 models with the most missing fields.
"""

import os
import sys


def add_fields_to_model(file_path, fields_to_add):
    """Add fields to a specific model file."""
    try:
        with open(file_path, "r") as f:
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
                    insert_index = i + 3  # After class definition
                    break

        if insert_index == -1:
            print(f"❌ Could not find insertion point in {file_path}")
            return False

        # Insert fields
        for field_definition in fields_to_add:
            lines.insert(insert_index, f"    {field_definition}")
            insert_index += 1

        # Write back to file
        with open(file_path, "w") as f:
            f.write("\n".join(lines))

        print(f"✅ Added {len(fields_to_add)} fields to {os.path.basename(file_path)}")
        return True

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def get_model_definitions():
    """Define comprehensive field sets for top priority models."""

    return {
        # 1. Records Billing Config - 95 missing fields
        "records_billing_config.py": [
            "# Advanced Billing Configuration Fields",
            "accounting_system_sync = fields.Boolean('Sync with Accounting System', default=True)",
            "amount = fields.Monetary('Total Amount', currency_field='currency_id')",
            "annual_revenue = fields.Monetary('Annual Revenue', currency_field='currency_id')",
            "audit_trail_enabled = fields.Boolean('Audit Trail Enabled', default=True)",
            "auto_apply = fields.Boolean('Auto Apply Rates', default=False)",
            "auto_billing_enabled = fields.Boolean('Auto Billing Enabled', default=True)",
            "billing_alert_threshold = fields.Float('Billing Alert Threshold', default=1000.0)",
            "billing_automation_level = fields.Selection([('manual', 'Manual'), ('semi', 'Semi-Auto'), ('full', 'Fully Automated')], default='semi')",
            "billing_cycle_id = fields.Many2one('billing.cycle', 'Billing Cycle')",
            "billing_discount_percentage = fields.Float('Billing Discount %', default=0.0)",
            "billing_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')], default='monthly')",
            "billing_method = fields.Selection([('invoice', 'Invoice'), ('auto_charge', 'Auto Charge')], default='invoice')",
            "billing_notification_enabled = fields.Boolean('Billing Notifications', default=True)",
            "billing_override_allowed = fields.Boolean('Override Allowed', default=False)",
            "billing_portal_access = fields.Boolean('Portal Access', default=True)",
            "billing_preferences = fields.Text('Billing Preferences')",
            "billing_rules_version = fields.Char('Billing Rules Version')",
            "billing_tier = fields.Selection([('basic', 'Basic'), ('premium', 'Premium'), ('enterprise', 'Enterprise')], default='basic')",
            "credit_limit_amount = fields.Monetary('Credit Limit', currency_field='currency_id')",
            "credit_limit_warning = fields.Boolean('Credit Limit Warning', default=True)",
            "currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id)",
            "custom_billing_rules = fields.Text('Custom Billing Rules')",
            "customer_category_ids = fields.Many2many('res.partner.category', 'billing_config_category_rel', 'config_id', 'category_id', 'Customer Categories')",
            "customer_tier_level = fields.Selection([('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], default='bronze')",
            "default_payment_terms_id = fields.Many2one('account.payment.term', 'Default Payment Terms')",
            "department_allocation_rules = fields.Text('Department Allocation Rules')",
            "discount_eligibility_rules = fields.Text('Discount Eligibility Rules')",
            "early_payment_discount = fields.Float('Early Payment Discount %', default=0.0)",
            "escalation_threshold_amount = fields.Monetary('Escalation Threshold', currency_field='currency_id')",
            "expense_tracking_enabled = fields.Boolean('Expense Tracking', default=True)",
            "invoice_consolidation_period = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='monthly')",
            "invoice_delivery_method = fields.Selection([('email', 'Email'), ('portal', 'Portal'), ('mail', 'Mail')], default='email')",
            "late_fee_calculation = fields.Text('Late Fee Calculation Rules')",
            "minimum_billing_amount = fields.Monetary('Minimum Billing Amount', currency_field='currency_id')",
            "payment_gateway_integration = fields.Boolean('Payment Gateway Integration', default=False)",
            "prepaid_balance_warning = fields.Boolean('Prepaid Balance Warning', default=True)",
            "pricing_tier_ids = fields.Many2many('pricing.tier', 'billing_pricing_tier_rel', 'config_id', 'tier_id', 'Pricing Tiers')",
            "pro_rata_calculation = fields.Boolean('Pro-rata Calculation', default=True)",
            "revenue_recognition_method = fields.Selection([('immediate', 'Immediate'), ('deferred', 'Deferred'), ('milestone', 'Milestone')], default='immediate')",
            "service_catalog_ids = fields.Many2many('service.catalog', 'billing_service_catalog_rel', 'config_id', 'service_id', 'Service Catalog')",
            "tax_calculation_method = fields.Selection([('inclusive', 'Tax Inclusive'), ('exclusive', 'Tax Exclusive')], default='exclusive')",
            "usage_tracking_enabled = fields.Boolean('Usage Tracking', default=True)",
            "volume_discount_enabled = fields.Boolean('Volume Discount', default=False)",
            "",
            "# Framework Integration Fields",
            "activity_ids = fields.One2many('mail.activity', 'res_id', 'Activities', domain=[('res_model', '=', 'records.billing.config')])",
            "message_follower_ids = fields.One2many('mail.followers', 'res_id', 'Followers', domain=[('res_model', '=', 'records.billing.config')])",
            "message_ids = fields.One2many('mail.message', 'res_id', 'Messages', domain=[('res_model', '=', 'records.billing.config')])",
        ],
        # 2. FSM Task - 69 missing fields
        "fsm_task.py": [
            "# FSM Task Management Fields",
            "activity_type = fields.Selection([('call', 'Call'), ('meeting', 'Meeting'), ('todo', 'To Do')], 'Activity Type')",
            "photo_attachment = fields.Binary('Photo Attachment')",
            "backup_technician = fields.Many2one('hr.employee', 'Backup Technician')",
            "barcode_scanning = fields.Boolean('Barcode Scanning Required', default=False)",
            "billable = fields.Boolean('Billable', default=True)",
            "billable_to_customer = fields.Boolean('Billable to Customer', default=True)",
            "chain_of_custody_required = fields.Boolean('Chain of Custody Required', default=False)",
            "completion_certificate = fields.Binary('Completion Certificate')",
            "completion_photos = fields.Text('Completion Photos URLs')",
            "customer_location_id = fields.Many2one('customer.location', 'Customer Location')",
            "customer_signature = fields.Binary('Customer Signature')",
            "customer_signature_date = fields.Datetime('Customer Signature Date')",
            "customer_verification_code = fields.Char('Customer Verification Code')",
            "document_collection_required = fields.Boolean('Document Collection Required', default=False)",
            "emergency_contact_id = fields.Many2one('res.partner', 'Emergency Contact')",
            "equipment_ids = fields.Many2many('fsm.equipment', 'fsm_task_equipment_rel', 'task_id', 'equipment_id', 'Equipment Required')",
            "estimated_cost = fields.Monetary('Estimated Cost', currency_field='currency_id')",
            "estimated_duration = fields.Float('Estimated Duration (Hours)', default=1.0)",
            "follow_up_required = fields.Boolean('Follow-up Required', default=False)",
            "gps_end_location = fields.Char('GPS End Location')",
            "gps_start_location = fields.Char('GPS Start Location')",
            "invoice_notes = fields.Text('Invoice Notes')",
            "location_access_code = fields.Char('Location Access Code')",
            "location_access_instructions = fields.Text('Location Access Instructions')",
            "mobile_signature = fields.Binary('Mobile Signature')",
            "naid_compliance_required = fields.Boolean('NAID Compliance Required', default=False)",
            "onsite_contact_id = fields.Many2one('res.partner', 'Onsite Contact')",
            "pre_task_checklist = fields.Text('Pre-task Checklist')",
            "priority_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium')",
            "quality_check_required = fields.Boolean('Quality Check Required', default=False)",
            "route_optimization_data = fields.Text('Route Optimization Data')",
            "safety_requirements = fields.Text('Safety Requirements')",
            "scheduled_end_date = fields.Datetime('Scheduled End Date')",
            "scheduled_start_date = fields.Datetime('Scheduled Start Date')",
            "service_category_id = fields.Many2one('service.category', 'Service Category')",
            "special_instructions = fields.Text('Special Instructions')",
            "task_checklist_completed = fields.Boolean('Task Checklist Completed', default=False)",
            "task_type_id = fields.Many2one('fsm.task.type', 'Task Type')",
            "technician_ids = fields.Many2many('hr.employee', 'fsm_task_technician_rel', 'task_id', 'technician_id', 'Assigned Technicians')",
            "travel_time_actual = fields.Float('Actual Travel Time (Hours)')",
            "travel_time_estimated = fields.Float('Estimated Travel Time (Hours)')",
            "vehicle_required = fields.Boolean('Vehicle Required', default=True)",
            "verification_photos = fields.Text('Verification Photos URLs')",
            "work_completion_notes = fields.Text('Work Completion Notes')",
        ],
        # 3. Portal Request - 64 missing fields
        "portal_request.py": [
            "# Portal Request Management Fields",
            "attachment_ids = fields.Many2many('ir.attachment', 'portal_request_attachment_rel', 'request_id', 'attachment_id', 'Attachments')",
            "access_restrictions = fields.Text('Access Restrictions')",
            "actual_date = fields.Date('Actual Date')",
            "approval_action = fields.Selection([('approve', 'Approve'), ('reject', 'Reject'), ('defer', 'Defer')], 'Approval Action')",
            "approval_deadline = fields.Date('Approval Deadline')",
            "approval_history_ids = fields.One2many('approval.history', 'request_id', 'Approval History')",
            "approval_level_required = fields.Selection([('basic', 'Basic'), ('advanced', 'Advanced'), ('executive', 'Executive')], default='basic')",
            "auto_approval_eligible = fields.Boolean('Auto Approval Eligible', default=False)",
            "billing_impact_assessment = fields.Text('Billing Impact Assessment')",
            "business_justification = fields.Text('Business Justification')",
            "compliance_approval_required = fields.Boolean('Compliance Approval Required', default=False)",
            "compliance_verification_notes = fields.Text('Compliance Verification Notes')",
            "cost_center_id = fields.Many2one('account.analytic.account', 'Cost Center')",
            "cost_impact_amount = fields.Monetary('Cost Impact', currency_field='currency_id')",
            "customer_confirmation_required = fields.Boolean('Customer Confirmation Required', default=True)",
            "customer_contact_method = fields.Selection([('email', 'Email'), ('phone', 'Phone'), ('portal', 'Portal')], default='email')",
            "customer_notification_sent = fields.Boolean('Customer Notification Sent', default=False)",
            "department_approval_required = fields.Boolean('Department Approval Required', default=False)",
            "document_verification_required = fields.Boolean('Document Verification Required', default=False)",
            "escalation_level = fields.Selection([('none', 'None'), ('supervisor', 'Supervisor'), ('manager', 'Manager'), ('director', 'Director')], default='none')",
            "estimated_completion_time = fields.Float('Estimated Completion Time (Hours)')",
            "external_reference = fields.Char('External Reference')",
            "follow_up_action_required = fields.Boolean('Follow-up Action Required', default=False)",
            "impact_assessment = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low')",
            "internal_notes = fields.Text('Internal Notes')",
            "legal_review_required = fields.Boolean('Legal Review Required', default=False)",
            "manager_approval_required = fields.Boolean('Manager Approval Required', default=False)",
            "notification_preferences = fields.Text('Notification Preferences')",
            "portal_visibility = fields.Selection([('customer', 'Customer Only'), ('department', 'Department'), ('public', 'Public')], default='customer')",
            "processing_notes = fields.Text('Processing Notes')",
            "quality_assurance_required = fields.Boolean('Quality Assurance Required', default=False)",
            "request_category_id = fields.Many2one('request.category', 'Request Category')",
            "request_complexity = fields.Selection([('simple', 'Simple'), ('moderate', 'Moderate'), ('complex', 'Complex')], default='simple')",
            "request_source = fields.Selection([('portal', 'Customer Portal'), ('email', 'Email'), ('phone', 'Phone'), ('api', 'API')], default='portal')",
            "request_subcategory_id = fields.Many2one('request.subcategory', 'Request Subcategory')",
            "resource_allocation_notes = fields.Text('Resource Allocation Notes')",
            "risk_assessment_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low')",
            "security_clearance_required = fields.Boolean('Security Clearance Required', default=False)",
            "service_level_agreement = fields.Selection([('standard', 'Standard'), ('expedited', 'Expedited'), ('priority', 'Priority')], default='standard')",
            "stakeholder_notification_list = fields.Text('Stakeholder Notification List')",
            "status_change_log = fields.Text('Status Change Log')",
            "third_party_approval_required = fields.Boolean('Third Party Approval Required', default=False)",
        ],
        # 4. Barcode Product - 60 missing fields
        "barcode_product.py": [
            "# Barcode Product Management Fields",
            "activity_exception_decoration = fields.Selection([('warning', 'Warning'), ('danger', 'Danger')], 'Activity Exception Decoration')",
            "activity_state = fields.Selection([('overdue', 'Overdue'), ('today', 'Today'), ('planned', 'Planned')], 'Activity State')",
            "batch_id = fields.Many2one('product.batch', 'Batch')",
            "bin_status = fields.Selection([('available', 'Available'), ('occupied', 'Occupied'), ('maintenance', 'Maintenance')], default='available')",
            "bin_volume = fields.Float('Bin Volume (cubic ft)', default=0.0)",
            "box_status = fields.Selection([('active', 'Active'), ('archived', 'Archived'), ('destroyed', 'Destroyed')], default='active')",
            "certificate_provided = fields.Boolean('Certificate Provided', default=False)",
            "compliance_certification_date = fields.Date('Compliance Certification Date')",
            "container_capacity = fields.Float('Container Capacity', default=0.0)",
            "container_type_classification = fields.Selection([('standard', 'Standard'), ('security', 'Security'), ('climate', 'Climate Controlled')], default='standard')",
            "creation_method = fields.Selection([('manual', 'Manual'), ('barcode_scan', 'Barcode Scan'), ('import', 'Import')], default='manual')",
            "customer_reference_code = fields.Char('Customer Reference Code')",
            "destruction_hold_status = fields.Boolean('Destruction Hold', default=False)",
            "destruction_scheduled_date = fields.Date('Scheduled Destruction Date')",
            "digital_copy_available = fields.Boolean('Digital Copy Available', default=False)",
            "document_category_id = fields.Many2one('document.category', 'Document Category')",
            "document_count_verified = fields.Integer('Verified Document Count', default=0)",
            "document_type_classification = fields.Selection([('permanent', 'Permanent'), ('temporary', 'Temporary'), ('confidential', 'Confidential')], default='temporary')",
            "environmental_conditions = fields.Selection([('standard', 'Standard'), ('climate_controlled', 'Climate Controlled'), ('fireproof', 'Fireproof')], default='standard')",
            "file_folder_type = fields.Selection([('hanging', 'Hanging'), ('manila', 'Manila'), ('expanding', 'Expanding')], default='manila')",
            "gps_location_verified = fields.Boolean('GPS Location Verified', default=False)",
            "handling_instructions = fields.Text('Handling Instructions')",
            "inventory_reconciliation_date = fields.Date('Last Inventory Reconciliation')",
            "last_access_date = fields.Datetime('Last Access Date')",
            "last_audit_date = fields.Date('Last Audit Date')",
            "last_movement_date = fields.Datetime('Last Movement Date')",
            "last_verification_date = fields.Date('Last Verification Date')",
            "legal_hold_status = fields.Boolean('Legal Hold', default=False)",
            "location_verification_required = fields.Boolean('Location Verification Required', default=False)",
            "media_type = fields.Selection([('paper', 'Paper'), ('digital', 'Digital'), ('microfilm', 'Microfilm'), ('mixed', 'Mixed')], default='paper')",
            "movement_history_ids = fields.One2many('movement.history', 'product_id', 'Movement History')",
            "physical_condition = fields.Selection([('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')], default='good')",
            "priority_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium')",
            "product_lifecycle_stage = fields.Selection([('active', 'Active'), ('inactive', 'Inactive'), ('retention', 'Retention'), ('disposal', 'Disposal')], default='active')",
            "quality_control_passed = fields.Boolean('Quality Control Passed', default=True)",
            "records_retention_category = fields.Selection([('temporary', 'Temporary'), ('permanent', 'Permanent'), ('vital', 'Vital')], default='temporary')",
            "retrieval_frequency = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('rarely', 'Rarely')], default='rarely')",
            "security_classification = fields.Selection([('public', 'Public'), ('internal', 'Internal'), ('confidential', 'Confidential'), ('restricted', 'Restricted')], default='internal')",
            "storage_environment_id = fields.Many2one('storage.environment', 'Storage Environment')",
            "tracking_method = fields.Selection([('barcode', 'Barcode'), ('rfid', 'RFID'), ('qr_code', 'QR Code')], default='barcode')",
            "verification_status = fields.Selection([('pending', 'Pending'), ('verified', 'Verified'), ('failed', 'Failed')], default='pending')",
        ],
        # 5. Shredding Service - 57 missing fields
        "shredding_service.py": [
            "# Shredding Service Management Fields",
            "action = fields.Selection([('schedule', 'Schedule'), ('complete', 'Complete'), ('cancel', 'Cancel')], 'Action')",
            "certificate_date = fields.Date('Certificate Date')",
            "certificate_notes = fields.Text('Certificate Notes')",
            "certificate_type = fields.Selection([('standard', 'Standard'), ('witnessed', 'Witnessed'), ('video', 'Video Documented')], default='standard')",
            "chain_of_custody_ids = fields.One2many('chain.of.custody', 'shredding_service_id', 'Chain of Custody')",
            "completion_verification_method = fields.Selection([('photo', 'Photo'), ('video', 'Video'), ('witness', 'Witness')], default='photo')",
            "compliance_officer_id = fields.Many2one('hr.employee', 'Compliance Officer')",
            "customer_witness_required = fields.Boolean('Customer Witness Required', default=False)",
            "destruction_location_id = fields.Many2one('destruction.location', 'Destruction Location')",
            "destruction_method_verified = fields.Boolean('Destruction Method Verified', default=False)",
            "destruction_witness_id = fields.Many2one('res.partner', 'Destruction Witness')",
            "environmental_compliance_verified = fields.Boolean('Environmental Compliance Verified', default=False)",
            "equipment_calibration_date = fields.Date('Equipment Calibration Date')",
            "equipment_serial_number = fields.Char('Equipment Serial Number')",
            "hard_drive_degaussing_required = fields.Boolean('Hard Drive Degaussing Required', default=False)",
            "material_handling_notes = fields.Text('Material Handling Notes')",
            "material_type_verification = fields.Selection([('paper_only', 'Paper Only'), ('mixed_media', 'Mixed Media'), ('electronic', 'Electronic')], default='paper_only')",
            "naid_aaa_compliance_verified = fields.Boolean('NAID AAA Compliance Verified', default=False)",
            "operator_certification_id = fields.Many2one('operator.certification', 'Operator Certification')",
            "post_destruction_cleanup_required = fields.Boolean('Post Destruction Cleanup Required', default=True)",
            "pre_destruction_audit_completed = fields.Boolean('Pre-destruction Audit Completed', default=False)",
            "quality_assurance_checklist = fields.Text('Quality Assurance Checklist')",
            "recycling_certificate_number = fields.Char('Recycling Certificate Number')",
            "security_level_required = fields.Selection([('level_1', 'Level 1'), ('level_2', 'Level 2'), ('level_3', 'Level 3')], default='level_1')",
            "service_completion_photos = fields.Text('Service Completion Photos')",
            "shredding_particle_size = fields.Selection([('strip_cut', 'Strip Cut'), ('cross_cut', 'Cross Cut'), ('micro_cut', 'Micro Cut')], default='cross_cut')",
            "temperature_monitoring_required = fields.Boolean('Temperature Monitoring Required', default=False)",
            "third_party_verification_required = fields.Boolean('Third Party Verification Required', default=False)",
            "transportation_security_verified = fields.Boolean('Transportation Security Verified', default=False)",
            "video_documentation_required = fields.Boolean('Video Documentation Required', default=False)",
            "waste_stream_tracking_number = fields.Char('Waste Stream Tracking Number')",
            "weight_verification_method = fields.Selection([('scale', 'Scale'), ('estimate', 'Estimate'), ('count', 'Count')], default='scale')",
        ],
    }


def main():
    """Main execution function."""
    print("🚀 ADDRESS TOP PRIORITY FIELD GAPS")
    print("=" * 60)

    # Base directory
    base_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    if not os.path.exists(base_dir):
        print(f"❌ Models directory not found: {base_dir}")
        return False

    # Get model definitions
    model_definitions = get_model_definitions()

    print(f"📋 Processing {len(model_definitions)} high-priority models...")

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
    print(f"✅ COMPLETION SUMMARY:")
    print(f"   📁 Models processed: {success_count}/{len(model_definitions)}")
    print(f"   📝 Total fields added: {total_fields_added}")
    print(f"   🎯 Target gap reduction: ~350+ fields")
    print("=" * 60)

    return success_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
