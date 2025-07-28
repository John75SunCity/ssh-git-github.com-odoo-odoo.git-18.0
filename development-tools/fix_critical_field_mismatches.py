#!/usr/bin/env python3
"""
Fix Critical Field Mismatches
Systematically address the most critical missing field issues
"""

import os
import re

def get_missing_fields_for_model(model_name):
    """Get missing fields for a specific model from the analysis output"""
    critical_models = {
        'visitor.pos.wizard': [
            'wizard_start_time', 'service_configuration_time', 'customer_processing_time',
            'estimated_volume', 'document_count', 'shredding_type', 'supervisor_approval',
            'receipt_email', 'invoice_required', 'pickup_required', 'scanning_required',
            'express_service', 'express_surcharge', 'witness_verification', 'audit_level',
            'compliance_officer', 'naid_compliance_required', 'naid_certificate_required',
            'certificate_required', 'audit_required', 'audit_notes', 'confidentiality_level',
            'chain_of_custody', 'chain_of_custody_id', 'destruction_method', 'retention_period',
            'digitization_format', 'final_verification_by', 'quality_check_by', 'processed_by',
            'payment_terms', 'customer_credit_limit', 'customer_payment_terms', 'tax_id',
            'payment_split_ids', 'invoice_generated', 'invoice_id', 'payment_method_id',
            'amount', 'total_discount', 'total_processing_time', 'duration_seconds',
            'integration_error_ids', 'processing_log_ids', 'processing_priority', 'error_type',
            'error_time', 'resolved', 'resolution_notes', 'step_name', 'step_description',
            'step_status', 'step_time', 'required_document_ids', 'service_item_ids',
            'naid_audit_created', 'naid_audit_id', 'records_request_created', 'records_request_id'
        ],
        'portal.feedback': [
            'customer_segment', 'customer_tier', 'feedback_category', 'feedback_type',
            'sentiment_analysis', 'priority', 'urgency_level', 'escalated', 'escalation_date',
            'escalation_reason', 'escalated_to', 'assigned_to', 'responded_by', 'response_date',
            'response_method', 'resolution_category', 'resolution_date', 'resolved_by',
            'satisfaction_level', 'likelihood_to_recommend', 'likelihood_to_return',
            'nps_score', 'csat_score', 'ces_score', 'overall_rating', 'service_quality_rating',
            'response_time_rating', 'communication_rating', 'value_for_money_rating',
            'staff_professionalism_rating', 'positive_aspects', 'negative_aspects',
            'improvement_suggestions', 'competitive_mention', 'retention_risk', 'revenue_impact',
            'trend_analysis', 'keyword_tags', 'followup_required', 'followup_date',
            'followup_method', 'followup_assigned_to', 'followup_activity_ids',
            'improvement_opportunity', 'improvement_action_count', 'related_ticket_count',
            'customer_feedback_count', 'impact_assessment', 'root_cause_category',
            'internal_actions', 'response_time_hours', 'resolution_time_hours'
        ],
        'naid.compliance': [
            'naid_level', 'certificate_number', 'certificate_type', 'issue_date', 'expiry_date',
            'issuing_authority', 'certificate_status', 'certificate_valid', 'audit_required',
            'audit_frequency', 'last_audit_date', 'next_audit_date', 'audit_type', 'audit_scope',
            'audit_result', 'auditor_name', 'third_party_auditor', 'compliance_score',
            'operational_score', 'physical_security_score', 'security_score', 'documentation_score',
            'overall_compliance_score', 'compliance_status', 'compliance_verified', 'risk_level',
            'compliance_trend', 'days_since_last_audit', 'days_until_expiry', 'auto_renewal',
            'renewal_reminder', 'expiry_notification', 'management_alerts', 'compliance_alerts',
            'notification_recipients', 'regulatory_notifications', 'facility_name', 'facility_manager',
            'security_officer', 'compliance_officer', 'responsible_person', 'personnel_screening',
            'background_checks', 'training_completed', 'security_clearance', 'equipment_certification',
            'surveillance_system', 'access_control_verified', 'secure_storage', 'information_handling',
            'process_verification', 'quality_control', 'incident_management', 'material_type',
            'destruction_method', 'destruction_verification', 'chain_of_custody', 'witness_present',
            'verification_method', 'benchmark', 'variance', 'trend', 'metric_type', 'score',
            'measurement_date', 'last_verified', 'certificate_tracking', 'certificate_issued',
            'certification_date', 'destruction_date', 'audit_date', 'audit_reminder',
            'findings_count', 'escalation_contacts', 'client_name', 'naid_member_id'
        ],
        'fsm.task': [
            'task_type', 'assigned_technician', 'scheduled_date', 'start_time', 'end_time',
            'duration', 'location_address', 'location_coordinates', 'contact_person',
            'contact_phone', 'contact_email', 'special_instructions', 'equipment_required',
            'materials_required', 'estimated_duration', 'actual_start_time', 'actual_completion_time',
            'completion_status', 'completion_notes', 'issues_encountered', 'follow_up_required',
            'next_service_scheduled', 'customer_satisfaction', 'photos_required', 'photo_attachment',
            'signature_required', 'customer_signature_obtained', 'safety_requirements',
            'confidentiality_level', 'boxes_to_retrieve', 'documents_to_deliver',
            'deliverables_completed', 'chain_of_custody_required', 'barcode_scanning',
            'gps_tracking_enabled', 'offline_sync_enabled', 'mobile_update_ids', 'update_type',
            'timestamp', 'current_location', 'location_update_count', 'arrival_time',
            'departure_time', 'travel_time', 'work_time', 'total_time_spent', 'efficiency_score',
            'billable', 'billable_amount', 'billable_to_customer', 'labor_cost', 'material_cost',
            'total_cost', 'time_log_ids', 'time_log_count', 'material_usage_ids', 'material_count',
            'material_name', 'quantity_used', 'unit_cost', 'supplier', 'parking_instructions',
            'facility_access_code', 'backup_contact', 'backup_technician', 'primary_contact',
            'communication_log_ids', 'communication_type', 'communication_date', 'response_required',
            'email_updates_enabled', 'sms_updates_enabled', 'notify_customer_on_arrival',
            'notify_customer_on_completion', 'task_checklist_ids', 'checklist_item', 'required',
            'completed', 'activity_type', 'task_status', 'quality_rating', 'supervisor'
        ]
    }
    
    return critical_models.get(model_name, [])

def add_fields_to_model(model_file_path, model_name, missing_fields):
    """Add missing fields to a model file"""
    if not os.path.exists(model_file_path):
        print(f"⚠️  Model file not found: {model_file_path}")
        return False
    
    # Read the current file
    with open(model_file_path, 'r') as f:
        content = f.read()
    
    # Find the class definition
    class_pattern = rf'class\s+\w+\(.*?\):\s*""".*?""".*?_name\s*=\s*["\']({re.escape(model_name)})["\']'
    class_match = re.search(class_pattern, content, re.DOTALL)
    
    if not class_match:
        print(f"⚠️  Could not find class definition for {model_name}")
        return False
    
    # Add missing fields before the last method definition
    fields_to_add = []
    
    if model_name == 'portal.feedback':
        fields_to_add = [
            "# Customer Information",
            "customer_segment = fields.Selection([('basic', 'Basic'), ('premium', 'Premium'), ('enterprise', 'Enterprise')], string='Customer Segment')",
            "customer_tier = fields.Selection([('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], string='Customer Tier')",
            "",
            "# Feedback Classification", 
            "feedback_category = fields.Selection([('service', 'Service'), ('product', 'Product'), ('billing', 'Billing'), ('support', 'Support')], string='Category')",
            "feedback_type = fields.Selection([('complaint', 'Complaint'), ('suggestion', 'Suggestion'), ('compliment', 'Compliment'), ('inquiry', 'Inquiry')], string='Type')",
            "sentiment_analysis = fields.Selection([('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')], string='Sentiment')",
            "priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], string='Priority')",
            "urgency_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Urgency')",
            "",
            "# Escalation Management",
            "escalated = fields.Boolean(string='Escalated', default=False)",
            "escalation_date = fields.Datetime(string='Escalation Date')",
            "escalation_reason = fields.Text(string='Escalation Reason')",
            "escalated_to = fields.Many2one('res.users', string='Escalated To')",
            "",
            "# Assignment and Response",
            "assigned_to = fields.Many2one('res.users', string='Assigned To')",
            "responded_by = fields.Many2one('res.users', string='Responded By')",
            "response_date = fields.Datetime(string='Response Date')",
            "response_method = fields.Selection([('email', 'Email'), ('phone', 'Phone'), ('meeting', 'Meeting'), ('chat', 'Chat')], string='Response Method')",
            "",
            "# Resolution",
            "resolution_category = fields.Selection([('resolved', 'Resolved'), ('duplicate', 'Duplicate'), ('wont_fix', 'Won\\'t Fix'), ('deferred', 'Deferred')], string='Resolution Category')",
            "resolution_date = fields.Datetime(string='Resolution Date')",
            "resolved_by = fields.Many2one('res.users', string='Resolved By')",
            "",
            "# Satisfaction Metrics",
            "satisfaction_level = fields.Selection([('very_unsatisfied', 'Very Unsatisfied'), ('unsatisfied', 'Unsatisfied'), ('neutral', 'Neutral'), ('satisfied', 'Satisfied'), ('very_satisfied', 'Very Satisfied')], string='Satisfaction Level')",
            "likelihood_to_recommend = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], string='Likelihood to Recommend')",
            "likelihood_to_return = fields.Selection([('very_unlikely', 'Very Unlikely'), ('unlikely', 'Unlikely'), ('neutral', 'Neutral'), ('likely', 'Likely'), ('very_likely', 'Very Likely')], string='Likelihood to Return')",
            "",
            "# Survey Scores",
            "nps_score = fields.Integer(string='NPS Score')",
            "csat_score = fields.Float(string='CSAT Score')",
            "ces_score = fields.Float(string='CES Score')",
            "",
            "# Detailed Ratings",
            "overall_rating = fields.Float(string='Overall Rating')",
            "service_quality_rating = fields.Float(string='Service Quality Rating')",
            "response_time_rating = fields.Float(string='Response Time Rating')",
            "communication_rating = fields.Float(string='Communication Rating')",
            "value_for_money_rating = fields.Float(string='Value for Money Rating')",
            "staff_professionalism_rating = fields.Float(string='Staff Professionalism Rating')",
            "",
            "# Qualitative Feedback",
            "positive_aspects = fields.Text(string='Positive Aspects')",
            "negative_aspects = fields.Text(string='Negative Aspects')",
            "improvement_suggestions = fields.Text(string='Improvement Suggestions')",
            "competitive_mention = fields.Text(string='Competitive Mention')",
            "",
            "# Business Impact",
            "retention_risk = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Retention Risk')",
            "revenue_impact = fields.Float(string='Revenue Impact')",
            "trend_analysis = fields.Text(string='Trend Analysis')",
            "keyword_tags = fields.Char(string='Keyword Tags')",
            "",
            "# Follow-up",
            "followup_required = fields.Boolean(string='Follow-up Required', default=False)",
            "followup_date = fields.Date(string='Follow-up Date')",
            "followup_method = fields.Selection([('email', 'Email'), ('phone', 'Phone'), ('meeting', 'Meeting')], string='Follow-up Method')",
            "followup_assigned_to = fields.Many2one('res.users', string='Follow-up Assigned To')",
            "",
            "# Improvement Tracking",
            "improvement_opportunity = fields.Boolean(string='Improvement Opportunity', default=False)",
            "improvement_action_count = fields.Integer(string='Improvement Action Count', default=0)",
            "related_ticket_count = fields.Integer(string='Related Ticket Count', default=0)",
            "customer_feedback_count = fields.Integer(string='Customer Feedback Count', default=0)",
            "",
            "# Analysis",
            "impact_assessment = fields.Text(string='Impact Assessment')",
            "root_cause_category = fields.Selection([('process', 'Process'), ('system', 'System'), ('training', 'Training'), ('resource', 'Resource')], string='Root Cause Category')",
            "internal_actions = fields.Text(string='Internal Actions')",
            "",
            "# Time Tracking",
            "response_time_hours = fields.Float(string='Response Time (Hours)')",
            "resolution_time_hours = fields.Float(string='Resolution Time (Hours)')"
        ]
    
    # Find a good place to insert the fields (before the last method or at the end of field definitions)
    method_pattern = r'\n    def '
    method_matches = list(re.finditer(method_pattern, content))
    
    if method_matches:
        insert_position = method_matches[0].start()
    else:
        # Insert before the end of the class
        insert_position = len(content) - 20  # Rough estimate
    
    # Create the field definitions
    field_definitions = '\n    ' + '\n    '.join(fields_to_add) + '\n'
    
    # Insert the fields
    new_content = content[:insert_position] + field_definitions + content[insert_position:]
    
    # Write back to file
    try:
        with open(model_file_path, 'w') as f:
            f.write(new_content)
        print(f"✅ Added {len([f for f in fields_to_add if '=' in f])} fields to {model_name}")
        return True
    except Exception as e:
        print(f"❌ Error writing to {model_file_path}: {e}")
        return False

def main():
    """Main function to fix critical field mismatches"""
    print("🔧 FIXING CRITICAL FIELD MISMATCHES")
    print("=" * 50)
    
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    
    critical_fixes = [
        ('portal.feedback', f"{base_path}/portal_feedback.py"),
        # Add more models as needed
    ]
    
    for model_name, file_path in critical_fixes:
        print(f"\n🎯 Processing {model_name}...")
        missing_fields = get_missing_fields_for_model(model_name)
        if missing_fields:
            success = add_fields_to_model(file_path, model_name, missing_fields)
            if success:
                print(f"   ✅ Successfully updated {model_name}")
            else:
                print(f"   ❌ Failed to update {model_name}")
        else:
            print(f"   ℹ️  No missing fields defined for {model_name}")
    
    print("\n" + "=" * 50)
    print("🏁 FIELD MISMATCH FIXES COMPLETED")

if __name__ == "__main__":
    main()
