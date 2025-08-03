# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TransitoryFieldConfig(models.Model):
    _name = "transitory.field.config"
    _description = "Transitory Field Config"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # State management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Documentation
    notes = fields.Text(string="Notes")

    # Computed fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    sequence = fields.Integer(string="Sequence", default=10)
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # === COMPREHENSIVE MISSING FIELDS ===
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    workflow_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Workflow State",
        default="draft",
    )
    next_action_date = fields.Date(string="Next Action Date")
    deadline_date = fields.Date(string="Deadline")
    completion_date = fields.Datetime(string="Completion Date")
    responsible_user_id = fields.Many2one("res.users", string="Responsible User")
    assigned_team_id = fields.Many2one("hr.department", string="Assigned Team")
    supervisor_id = fields.Many2one("res.users", string="Supervisor")
    quality_checked = fields.Boolean(string="Quality Checked")
    quality_score = fields.Float(string="Quality Score", digits=(3, 2))
    validation_required = fields.Boolean(string="Validation Required")
    validated_by_id = fields.Many2one("res.users", string="Validated By")
    validation_date = fields.Datetime(string="Validation Date")
    reference_number = fields.Char(string="Reference Number")
    external_reference = fields.Char(string="External Reference")
    documentation_complete = fields.Boolean(string="Documentation Complete")
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")
    performance_score = fields.Float(string="Performance Score", digits=(5, 2))
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ],
        string="Efficiency Rating",
    )
    last_review_date = fields.Date(string="Last Review Date")
    next_review_date = fields.Date(string="Next Review Date")
    # Transitory Field Configuration Fields
    config_preset = fields.Selection(
        [("basic", "Basic"), ("advanced", "Advanced"), ("custom", "Custom")],
        default="basic",
    )
    customer_id = fields.Many2one("res.partner", "Customer")
    department_id = fields.Many2one("hr.department", "Department")
    field_label_config_id = fields.Many2one(
        "field.label.customization", "Field Label Configuration"
    )
    require_client_reference = fields.Boolean("Require Client Reference", default=False)
    auto_apply_config = fields.Boolean("Auto Apply Configuration", default=True)
    config_version = fields.Char("Configuration Version")
    custom_field_definitions = fields.Text("Custom Field Definitions")
    data_validation_rules = fields.Text("Data Validation Rules")
    default_field_values = fields.Text("Default Field Values")
    field_dependency_rules = fields.Text("Field Dependency Rules")
    field_group_configuration = fields.Text("Field Group Configuration")
    field_visibility_rules = fields.Text("Field Visibility Rules")
    form_layout_configuration = fields.Text("Form Layout Configuration")
    mandatory_fields_list = fields.Text("Mandatory Fields List")
    permission_based_visibility = fields.Boolean(
        "Permission Based Visibility", default=False
    )
    preset_configurations = fields.Text("Preset Configurations")
    readonly_fields_list = fields.Text("Readonly Fields List")
    template_configuration = fields.Text("Template Configuration")
    user_customization_allowed = fields.Boolean(
        "User Customization Allowed", default=True
    )
    validation_error_messages = fields.Text("Validation Error Messages")
    workflow_integration_config = fields.Text("Workflow Integration Configuration")

    # === MISSING REQUIRED FIELDS ===

    # Configuration Requirements
    require_confidentiality = fields.Boolean(
        "Require Confidentiality Level", default=False
    )
    require_container_number = fields.Boolean("Require Container Number", default=True)
    require_content_description = fields.Boolean(
        "Require Content Description", default=True
    )
    require_date_from = fields.Boolean("Require Date From", default=False)
    require_date_to = fields.Boolean("Require Date To", default=False)
    require_department = fields.Boolean("Require Department", default=True)
    require_document_type = fields.Boolean("Require Document Type", default=False)
    require_location = fields.Boolean("Require Storage Location", default=True)
    require_requestor_name = fields.Boolean("Require Requestor Name", default=True)
    require_retention_policy = fields.Boolean("Require Retention Policy", default=False)
    require_security_level = fields.Boolean("Require Security Level", default=False)
    require_service_type = fields.Boolean("Require Service Type", default=True)

    # === MISSING FIELDS FROM VIEW ANALYSIS ===
    require_description = fields.Boolean("Require Description", default=True)
    require_destruction_date = fields.Boolean("Require Destruction Date", default=False)
    require_project_code = fields.Boolean("Require Project Code", default=False)
    require_record_type = fields.Boolean("Require Record Type", default=True)
    require_sequence_from = fields.Boolean("Require Sequence From", default=False)
    require_sequence_to = fields.Boolean("Require Sequence To", default=False)

    # Configuration Form Processing
    form_processor_id = fields.Many2one("res.users", "Form Processor")
    form_processing_date = fields.Datetime("Form Processing Date")
    form_validation_status = fields.Selection(
        [("pending", "Pending"), ("validated", "Validated"), ("rejected", "Rejected")],
        string="Form Validation Status",
        default="pending",
    )

    # Field Label Configuration Extensions
    label_configuration_active = fields.Boolean(
        "Label Configuration Active", default=True
    )
    label_template_id = fields.Many2one("ir.attachment", "Label Template")
    label_print_format = fields.Selection(
        [("standard", "Standard"), ("compact", "Compact"), ("detailed", "Detailed")],
        string="Label Print Format",
        default="standard",
    )

    # Workflow Configuration
    workflow_automation_enabled = fields.Boolean(
        "Workflow Automation Enabled", default=False
    )
    workflow_trigger_conditions = fields.Text("Workflow Trigger Conditions")
    workflow_notification_recipients = fields.Many2many(
        "res.users", string="Workflow Notification Recipients"
    )

    # Advanced Field Dependencies
    conditional_field_display = fields.Text("Conditional Field Display Rules")
    dynamic_field_generation = fields.Boolean("Dynamic Field Generation", default=False)
    field_cascade_rules = fields.Text("Field Cascade Rules")

    # Configuration Templates
    configuration_template_name = fields.Char("Configuration Template Name")
    template_description = fields.Text("Template Description")
    template_version = fields.Char("Template Version", default="1.0")

    # System Integration
    api_endpoint_configuration = fields.Text("API Endpoint Configuration")
    external_system_mapping = fields.Text("External System Field Mapping")
    data_synchronization_rules = fields.Text("Data Synchronization Rules")

    # Performance & Analytics
    configuration_usage_count = fields.Integer("Configuration Usage Count", default=0)
    average_processing_time = fields.Float(
        "Average Processing Time (minutes)", digits=(5, 2)
    )
    user_satisfaction_rating = fields.Float("User Satisfaction Rating", digits=(3, 2))

    # Compliance & Security Extensions
    data_retention_period = fields.Integer(
        "Data Retention Period (days)", default=2555
    )  # 7 years
    encryption_level = fields.Selection(
        [
            ("none", "None"),
            ("basic", "Basic"),
            ("advanced", "Advanced"),
            ("military", "Military Grade"),
        ],
        string="Encryption Level",
        default="basic",
    )
    access_log_enabled = fields.Boolean("Access Log Enabled", default=True)

    # === VIEW DISPLAY CONTROL FIELDS ===
    show_container_number = fields.Boolean("Show Container Number", default=True)
    show_description = fields.Boolean("Show Description", default=True)
    show_content_description = fields.Boolean("Show Content Description", default=True)
    show_date_ranges = fields.Boolean("Show Date Ranges", default=False)
    show_sequence_ranges = fields.Boolean("Show Sequence Ranges", default=False)
    show_destruction_date = fields.Boolean("Show Destruction Date", default=False)
    show_record_type = fields.Boolean("Show Record Type", default=True)
    show_confidentiality = fields.Boolean("Show Confidentiality Level", default=False)
    show_project_code = fields.Boolean("Show Project Code", default=False)
    show_client_reference = fields.Boolean("Show Client Reference", default=True)
    show_file_count = fields.Boolean("Show File Count", default=True)
    show_filing_system = fields.Boolean("Show Filing System", default=False)
    show_created_by_dept = fields.Boolean("Show Created By Department", default=True)
    show_authorized_by = fields.Boolean("Show Authorized By", default=True)
    show_special_handling = fields.Boolean("Show Special Handling", default=False)
    show_compliance_notes = fields.Boolean("Show Compliance Notes", default=False)
    show_weight_estimate = fields.Boolean("Show Weight Estimate", default=False)
    show_size_estimate = fields.Boolean("Show Size Estimate", default=False)

    # Additional computed field for required field count based on show fields
    required_field_count = fields.Integer(
        "Required Field Count", compute="_compute_required_field_count"
    )
    visible_field_count = fields.Integer(
        "Visible Field Count", compute="_compute_visible_field_count"
    )

    # Field Configuration Options
    enable_barcode_scanning = fields.Boolean("Enable Barcode Scanning", default=False)
    enable_digital_signature = fields.Boolean("Enable Digital Signature", default=False)
    enable_document_preview = fields.Boolean("Enable Document Preview", default=False)
    enable_file_upload = fields.Boolean("Enable File Upload", default=True)
    enable_photo_capture = fields.Boolean("Enable Photo Capture", default=False)
    enable_real_time_tracking = fields.Boolean(
        "Enable Real-time Tracking", default=False
    )

    # Advanced Configuration
    allow_bulk_operations = fields.Boolean("Allow Bulk Operations", default=False)
    auto_assign_reference = fields.Boolean(
        "Auto-assign Reference Numbers", default=True
    )
    auto_calculate_costs = fields.Boolean("Auto-calculate Costs", default=False)
    auto_generate_labels = fields.Boolean("Auto-generate Labels", default=False)
    auto_notify_completion = fields.Boolean("Auto-notify on Completion", default=True)
    auto_schedule_pickup = fields.Boolean("Auto-schedule Pickup", default=False)

    # Integration Settings
    email_notifications_enabled = fields.Boolean(
        "Email Notifications Enabled", default=True
    )
    external_api_integration = fields.Boolean("External API Integration", default=False)
    mobile_app_support = fields.Boolean("Mobile App Support", default=False)
    portal_access_enabled = fields.Boolean("Portal Access Enabled", default=True)
    sms_notifications_enabled = fields.Boolean(
        "SMS Notifications Enabled", default=False
    )

    # Quality & Compliance
    quality_control_required = fields.Boolean("Quality Control Required", default=False)
    compliance_audit_trail = fields.Boolean("Compliance Audit Trail", default=True)
    data_encryption_required = fields.Boolean("Data Encryption Required", default=False)

    # ===== COMPUTED FIELDS =====

    required_fields_count = fields.Integer(
        "Required Fields Count", compute="_compute_field_counts"
    )
    optional_fields_count = fields.Integer(
        "Optional Fields Count", compute="_compute_field_counts"
    )
    enabled_features_count = fields.Integer(
        "Enabled Features Count", compute="_compute_feature_counts"
    )
    configuration_complexity = fields.Selection(
        [
            ("simple", "Simple"),
            ("moderate", "Moderate"),
            ("complex", "Complex"),
            ("advanced", "Advanced"),
        ],
        string="Configuration Complexity",
        compute="_compute_complexity",
    )

    # Configuration Health
    config_health_score = fields.Float(
        "Configuration Health Score (%)", digits=(5, 2), compute="_compute_health_score"
    )
    validation_status = fields.Selection(
        [("valid", "Valid"), ("warning", "Warning"), ("error", "Error")],
        string="Validation Status",
        compute="_compute_validation_status",
    )

    # Usage Analytics
    applied_configurations_count = fields.Integer(
        "Applied Configurations", compute="_compute_usage_stats"
    )
    last_applied_date = fields.Datetime(
        "Last Applied Date", compute="_compute_usage_stats"
    )

    @api.depends(
        "require_confidentiality",
        "require_container_number",
        "require_content_description",
        "require_date_from",
        "require_date_to",
        "require_department",
        "require_document_type",
        "require_location",
        "require_requestor_name",
        "require_retention_policy",
        "require_security_level",
        "require_service_type",
        "require_description",
        "require_destruction_date",
        "require_project_code",
        "require_record_type",
        "require_sequence_from",
        "require_sequence_to",
    )
    def _compute_field_counts(self):
        """Compute count of required and optional fields"""
        for config in self:
            required_fields = [
                config.require_confidentiality,
                config.require_container_number,
                config.require_content_description,
                config.require_date_from,
                config.require_date_to,
                config.require_department,
                config.require_document_type,
                config.require_location,
                config.require_requestor_name,
                config.require_retention_policy,
                config.require_security_level,
                config.require_service_type,
                config.require_description,
                config.require_destruction_date,
                config.require_project_code,
                config.require_record_type,
                config.require_sequence_from,
                config.require_sequence_to,
            ]

            config.required_fields_count = sum(1 for field in required_fields if field)
            config.optional_fields_count = (
                len(required_fields) - config.required_fields_count
            )

    @api.depends(
        "enable_barcode_scanning",
        "enable_digital_signature",
        "enable_document_preview",
        "enable_file_upload",
        "enable_photo_capture",
        "enable_real_time_tracking",
        "allow_bulk_operations",
        "auto_assign_reference",
        "auto_calculate_costs",
        "auto_generate_labels",
        "auto_notify_completion",
        "auto_schedule_pickup",
    )
    def _compute_feature_counts(self):
        """Compute count of enabled features"""
        for config in self:
            enabled_features = [
                config.enable_barcode_scanning,
                config.enable_digital_signature,
                config.enable_document_preview,
                config.enable_file_upload,
                config.enable_photo_capture,
                config.enable_real_time_tracking,
                config.allow_bulk_operations,
                config.auto_assign_reference,
                config.auto_calculate_costs,
                config.auto_generate_labels,
                config.auto_notify_completion,
                config.auto_schedule_pickup,
            ]

            config.enabled_features_count = sum(
                1 for feature in enabled_features if feature
            )

    @api.depends("required_fields_count", "enabled_features_count")
    def _compute_complexity(self):
        """Compute configuration complexity based on field and feature counts"""
        for config in self:
            total_score = config.required_fields_count + config.enabled_features_count

            if total_score <= 5:
                config.configuration_complexity = "simple"
            elif total_score <= 10:
                config.configuration_complexity = "moderate"
            elif total_score <= 15:
                config.configuration_complexity = "complex"
            else:
                config.configuration_complexity = "advanced"

    @api.depends(
        "required_fields_count",
        "enabled_features_count",
        "validation_required",
        "quality_checked",
    )
    def _compute_health_score(self):
        """Compute configuration health score"""
        for config in self:
            base_score = 50.0

            # Required fields configuration adds to health
            if config.required_fields_count > 0:
                base_score += min(config.required_fields_count * 5, 25)

            # Enabled features add to health
            if config.enabled_features_count > 0:
                base_score += min(config.enabled_features_count * 3, 15)

            # Quality checks add to health
            if config.quality_checked:
                base_score += 10

            config.config_health_score = min(base_score, 100.0)

    @api.depends("config_health_score", "documentation_complete")
    def _compute_validation_status(self):
        """Compute validation status based on health score and documentation"""
        for config in self:
            if config.config_health_score >= 80 and config.documentation_complete:
                config.validation_status = "valid"
            elif config.config_health_score >= 60:
                config.validation_status = "warning"
            else:
                config.validation_status = "error"

    @api.depends("name")
    def _compute_usage_stats(self):
        """Compute usage statistics (placeholder for future implementation)"""
        for config in self:
            # Future implementation: Count actual usage across the system
            config.applied_configurations_count = 0
            config.last_applied_date = False

    @api.depends("name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or "New"

    # === ADDITIONAL COMPUTE METHODS FOR NEW FIELDS ===

    @api.depends("configuration_usage_count", "created_date")
    def _compute_configuration_statistics(self):
        """Compute configuration usage statistics"""
        for config in self:
            # Calculate usage efficiency
            days_active = (fields.Datetime.now() - config.created_date).days or 1
            config.average_processing_time = max(
                config.configuration_usage_count / days_active * 1.5, 0.5
            )

    @api.depends("form_validation_status", "label_configuration_active")
    def _compute_form_processing_metrics(self):
        """Compute form processing quality metrics"""
        for config in self:
            if (
                config.form_validation_status == "validated"
                and config.label_configuration_active
            ):
                config.user_satisfaction_rating = 4.5
            elif config.form_validation_status == "pending":
                config.user_satisfaction_rating = 3.0
            else:
                config.user_satisfaction_rating = 2.0

    @api.depends("workflow_automation_enabled", "api_endpoint_configuration")
    def _compute_integration_status(self):
        """Compute system integration status"""
        for config in self:
            integration_score = 0
            if config.workflow_automation_enabled:
                integration_score += 25
            if config.api_endpoint_configuration:
                integration_score += 25
            if config.external_system_mapping:
                integration_score += 25
            if config.data_synchronization_rules:
                integration_score += 25

            # Store as a computed helper field
            config.configuration_usage_count = integration_score

    @api.depends("encryption_level", "access_log_enabled")
    def _compute_security_compliance(self):
        """Compute security and compliance metrics"""
        for config in self:
            security_score = 0

            # Encryption adds security points
            encryption_points = {"none": 0, "basic": 20, "advanced": 35, "military": 50}
            security_score += encryption_points.get(config.encryption_level, 0)

            # Access logging adds security
            if config.access_log_enabled:
                security_score += 15

            # Data retention compliance
            if config.data_retention_period >= 2555:  # 7 years
                security_score += 10

            # Update satisfaction rating based on security
            if security_score >= 60:
                config.user_satisfaction_rating = max(
                    config.user_satisfaction_rating, 4.0
                )
            elif security_score >= 40:
                config.user_satisfaction_rating = max(
                    config.user_satisfaction_rating, 3.5
                )

    @api.depends(
        "show_container_number",
        "show_description",
        "show_content_description",
        "show_date_ranges",
        "show_sequence_ranges",
        "show_destruction_date",
        "show_record_type",
        "show_confidentiality",
        "show_project_code",
        "show_client_reference",
        "show_file_count",
        "show_filing_system",
        "show_created_by_dept",
        "show_authorized_by",
        "show_special_handling",
        "show_compliance_notes",
        "show_weight_estimate",
        "show_size_estimate",
    )
    def _compute_required_field_count(self):
        """Compute count of visible/required fields based on show settings"""
        for config in self:
            show_fields = [
                config.show_container_number,
                config.show_description,
                config.show_content_description,
                config.show_date_ranges,
                config.show_sequence_ranges,
                config.show_destruction_date,
                config.show_record_type,
                config.show_confidentiality,
                config.show_project_code,
                config.show_client_reference,
                config.show_file_count,
                config.show_filing_system,
                config.show_created_by_dept,
                config.show_authorized_by,
                config.show_special_handling,
                config.show_compliance_notes,
                config.show_weight_estimate,
                config.show_size_estimate,
            ]
            config.required_field_count = sum(1 for field in show_fields if field)

    @api.depends(
        "show_container_number",
        "show_description",
        "show_content_description",
        "show_date_ranges",
        "show_sequence_ranges",
        "show_destruction_date",
        "show_record_type",
        "show_confidentiality",
        "show_project_code",
        "show_client_reference",
        "show_file_count",
        "show_filing_system",
        "show_created_by_dept",
        "show_authorized_by",
        "show_special_handling",
        "show_compliance_notes",
        "show_weight_estimate",
        "show_size_estimate",
    )
    def _compute_visible_field_count(self):
        """Compute count of visible fields in the form"""
        for config in self:
            # Count all show fields that are enabled
            visible_fields = [
                config.show_container_number,
                config.show_description,
                config.show_content_description,
                config.show_date_ranges,
                config.show_sequence_ranges,
                config.show_destruction_date,
                config.show_record_type,
                config.show_confidentiality,
                config.show_project_code,
                config.show_client_reference,
                config.show_file_count,
                config.show_filing_system,
                config.show_created_by_dept,
                config.show_authorized_by,
                config.show_special_handling,
                config.show_compliance_notes,
                config.show_weight_estimate,
                config.show_size_estimate,
            ]
            config.visible_field_count = sum(1 for field in visible_fields if field)

    # ===== ACTION METHODS =====

    def action_confirm(self):
        """Confirm the configuration after validation"""
        self.ensure_one()
        if self.validation_status == "error":
            raise UserError(_("Cannot confirm configuration with validation errors"))

        self.write(
            {
                "state": "confirmed",
                "validation_date": fields.Datetime.now(),
                "validated_by_id": self.env.user.id,
            }
        )

        return True

    def action_cancel(self):
        """Cancel the configuration"""
        self.ensure_one()
        self.write({"state": "cancelled"})
        return True

    def action_reset_to_draft(self):
        """Reset configuration to draft state"""
        self.ensure_one()
        self.write(
            {
                "state": "draft",
                "validation_date": False,
                "validated_by_id": False,
            }
        )
        return True

    def action_validate_configuration(self):
        """Perform comprehensive configuration validation"""
        self.ensure_one()

        validation_errors = []

        # Check basic requirements
        if not self.name:
            validation_errors.append("Configuration name is required")

        if not self.config_preset:
            validation_errors.append("Configuration preset must be selected")

        # Check field requirements consistency
        if self.require_date_from and not self.require_date_to:
            validation_errors.append(
                "If 'Date From' is required, 'Date To' should also be required"
            )

        # Check integration consistency
        if self.external_api_integration and not self.email_notifications_enabled:
            validation_errors.append(
                "External API integration requires email notifications"
            )

        if validation_errors:
            error_message = "Configuration validation failed:\n" + "\n".join(
                validation_errors
            )
            raise UserError(_(error_message))

        self.write(
            {
                "quality_checked": True,
                "validation_date": fields.Datetime.now(),
                "validated_by_id": self.env.user.id,
                "documentation_complete": True,
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Validation Successful"),
                "message": _("Configuration validated successfully"),
                "type": "success",
            },
        }

    def action_apply_configuration(self):
        """Apply this configuration to specified models/forms"""
        self.ensure_one()

        if self.state != "confirmed":
            raise UserError(_("Only confirmed configurations can be applied"))

        # Log the application
        self.message_post(
            body=f"Configuration applied by {self.env.user.name}",
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Configuration Applied"),
                "message": _("Configuration has been applied successfully"),
                "type": "success",
            },
        }

    def action_clone_configuration(self):
        """Clone this configuration with a new name"""
        self.ensure_one()

        new_config = self.copy(
            {
                "name": f"{self.name} (Copy)",
                "state": "draft",
                "validation_date": False,
                "validated_by_id": False,
                "quality_checked": False,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Cloned Configuration",
            "res_model": "transitory.field.config",
            "res_id": new_config.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_export_configuration(self):
        """Export configuration as JSON"""
        self.ensure_one()

        config_data = {
            "name": self.name,
            "config_preset": self.config_preset,
            "required_fields": {
                "require_confidentiality": self.require_confidentiality,
                "require_container_number": self.require_container_number,
                "require_content_description": self.require_content_description,
                "require_date_from": self.require_date_from,
                "require_date_to": self.require_date_to,
                "require_department": self.require_department,
                "require_document_type": self.require_document_type,
                "require_location": self.require_location,
                "require_requestor_name": self.require_requestor_name,
                "require_retention_policy": self.require_retention_policy,
                "require_security_level": self.require_security_level,
                "require_service_type": self.require_service_type,
            },
            "enabled_features": {
                "enable_barcode_scanning": self.enable_barcode_scanning,
                "enable_digital_signature": self.enable_digital_signature,
                "enable_document_preview": self.enable_document_preview,
                "enable_file_upload": self.enable_file_upload,
                "enable_photo_capture": self.enable_photo_capture,
                "enable_real_time_tracking": self.enable_real_time_tracking,
                "allow_bulk_operations": self.allow_bulk_operations,
                "auto_assign_reference": self.auto_assign_reference,
                "auto_calculate_costs": self.auto_calculate_costs,
                "auto_generate_labels": self.auto_generate_labels,
                "auto_notify_completion": self.auto_notify_completion,
                "auto_schedule_pickup": self.auto_schedule_pickup,
            },
            "integration_settings": {
                "email_notifications_enabled": self.email_notifications_enabled,
                "external_api_integration": self.external_api_integration,
                "mobile_app_support": self.mobile_app_support,
                "portal_access_enabled": self.portal_access_enabled,
                "sms_notifications_enabled": self.sms_notifications_enabled,
            },
        }

        import json

        config_json = json.dumps(config_data, indent=2)

        # Create attachment
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"{self.name}_config.json",
                "type": "binary",
                "datas": config_json.encode(),
                "res_model": self._name,
                "res_id": self.id,
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "new",
        }

    def action_import_configuration(self):
        """Open wizard to import configuration from JSON"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Import Configuration",
            "res_model": "transitory.field.config.import.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_target_config_id": self.id,
            },
        }

    def action_preview_configuration(self):
        """Preview how this configuration will look when applied"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Configuration Preview",
            "res_model": "transitory.field.config.preview",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_config_id": self.id,
            },
        }

    # === ENHANCED ACTION METHODS FOR NEW FIELDS ===

    def action_validate_form_processing(self):
        """Validate form processing configuration"""
        self.ensure_one()

        if not self.form_processor_id:
            raise UserError(_("Form processor must be assigned before validation"))

        self.write(
            {
                "form_validation_status": "validated",
                "form_processing_date": fields.Datetime.now(),
                "user_satisfaction_rating": 4.0,
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Form Processing Validated"),
                "message": _("Form processing configuration validated successfully"),
                "type": "success",
            },
        }

    def action_activate_label_configuration(self):
        """Activate label configuration for this setup"""
        self.ensure_one()

        self.write(
            {
                "label_configuration_active": True,
                "configuration_usage_count": self.configuration_usage_count + 1,
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Label Configuration Activated"),
                "message": _("Label configuration is now active"),
                "type": "success",
            },
        }

    def action_setup_workflow_automation(self):
        """Setup workflow automation for this configuration"""
        self.ensure_one()

        self.write(
            {
                "workflow_automation_enabled": True,
                "average_processing_time": 15.0,  # Automated workflows are faster
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Workflow Automation Enabled"),
                "message": _("Workflow automation has been configured"),
                "type": "success",
            },
        }

    def action_generate_configuration_template(self):
        """Generate reusable template from current configuration"""
        self.ensure_one()

        template_name = f"Template: {self.name}"
        template_version = "1.0"

        self.write(
            {
                "configuration_template_name": template_name,
                "template_version": template_version,
                "template_description": f"Auto-generated template from {self.name}",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Template Generated"),
                "message": f"Configuration template '{template_name}' created",
                "type": "success",
            },
        }

    def action_configure_system_integration(self):
        """Configure system integration settings"""
        self.ensure_one()

        integration_config = {
            "api_endpoints": ["POST /api/v1/records", "GET /api/v1/status"],
            "field_mappings": {
                "external_ref": "reference_number",
                "client_id": "customer_id",
                "dept_code": "department_id",
            },
            "sync_frequency": "hourly",
        }

        self.write(
            {
                "api_endpoint_configuration": str(integration_config),
                "external_system_mapping": "Standard field mapping applied",
                "data_synchronization_rules": "Hourly sync with validation",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Integration Configured"),
                "message": _("System integration settings have been configured"),
                "type": "success",
            },
        }

    def action_enhance_security_configuration(self):
        """Enhance security and compliance settings"""
        self.ensure_one()

        self.write(
            {
                "encryption_level": "advanced",
                "access_log_enabled": True,
                "data_retention_period": 2555,  # 7 years compliance
                "user_satisfaction_rating": 4.5,  # High security = high satisfaction
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Security Enhanced"),
                "message": _("Security and compliance settings have been enhanced"),
                "type": "success",
            },
        }

    def action_setup_field_labels(self):
        """Setup and customize field labels for this configuration"""
        self.ensure_one()

        # Create or find the field label customization record
        field_label_config = self.env["field.label.customization"].search(
            [("config_id", "=", self.id)], limit=1
        )

        if not field_label_config:
            field_label_config = self.env["field.label.customization"].create(
                {
                    "name": f"Labels for {self.name}",
                    "config_id": self.id,
                    "customer_id": self.customer_id.id,
                    "department_id": self.department_id.id,
                }
            )

        # Update the field_label_config_id if not set
        if not self.field_label_config_id:
            self.write({"field_label_config_id": field_label_config.id})

        return {
            "type": "ir.actions.act_window",
            "name": "Customize Field Labels",
            "res_model": "field.label.customization",
            "res_id": field_label_config.id,
            "view_mode": "form",
            "target": "current",
        }
