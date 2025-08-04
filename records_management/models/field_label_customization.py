# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FieldLabelCustomization(models.Model):
    _name = "field.label.customization"
    _description = "Field Label Customization"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    # === ADDITIONAL COMPUTE METHODS ===
    @api.depends("usage_count", "last_used_date")
    def _compute_popularity_score(self):
        """Compute popularity score based on usage"""
        for record in self:
            base_score = min(record.usage_count * 10, 1000)  # Cap at 1000
            if record.last_used_date:
                days_since_use = (fields.Datetime.now() - record.last_used_date).days
                recency_factor = max(0, 100 - days_since_use)  # Decreases over time
                record.popularity_score = base_score + recency_factor
            else:
                record.popularity_score = base_score

    # === ONCHANGE METHODS ===
    @api.onchange("industry_type")
    def _onchange_industry_type(self):
        """Update compliance framework based on industry type"""
        industry_compliance_mapping = {
            "healthcare": "hipaa",
            "financial": "sox",
            "education": "ferpa",
            "government": "naid",
            "corporate": "iso27001",
        }
        if self.industry_type and self.industry_type in industry_compliance_mapping:
            self.compliance_framework = industry_compliance_mapping[self.industry_type]

    @api.onchange("compliance_framework")
    def _onchange_compliance_framework(self):
        """Update security settings based on compliance framework"""
        high_security_frameworks = ["hipaa", "sox", "naid"]
        if self.compliance_framework in high_security_frameworks:
            self.security_classification = "confidential"
            self.access_control_enabled = True
            self.label_approval_required = True

    @api.onchange("machine_learning_enabled")
    def _onchange_machine_learning_enabled(self):
        """Enable smart suggestions when ML is enabled"""
        if self.machine_learning_enabled:
            self.smart_field_suggestions = True
            self.usage_statistics_enabled = True

    # === VALIDATION METHODS ===
    @api.constrains("label_inheritance_depth")
    def _check_inheritance_depth(self):
        """Validate inheritance depth is reasonable"""
        for record in self:
            if (
                record.label_inheritance_depth < 0
                or record.label_inheritance_depth > 10
            ):
                raise ValidationError(
                    _("Label inheritance depth must be between 0 and 10.")
                )

    @api.constrains("webhook_notification_url")
    def _check_webhook_url(self):
        """Validate webhook URL format"""
        import re

        for record in self:
            if record.webhook_notification_url:
                url_pattern = r"^https?://.+"
                if not re.match(url_pattern, record.webhook_notification_url):
                    raise ValidationError(
                        _("Webhook URL must start with http:// or https://")
                    )

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()

        # Track usage when configuration is applied
        if vals.get("state") == "active":
            vals["usage_count"] = (vals.get("usage_count", 0) or self.usage_count) + 1
            vals["last_used_date"] = fields.Datetime.now()

        return super().write(vals)

    # Field Label Customization Fields
    customer_id = fields.Many2one("res.partner", "Customer")
    customized_label_count = fields.Integer("Customized Label Count", default=0)
    department_id = fields.Many2one("hr.department", "Department")
    label_authorized_by = fields.Many2one("res.users", "Label Authorized By")
    label_client_reference = fields.Char("Label Client Reference")
    auto_apply_labels = fields.Boolean("Auto Apply Labels", default=False)
    custom_field_mapping = fields.Text("Custom Field Mapping")
    default_label_template = fields.Selection(
        [("standard", "Standard"), ("compact", "Compact"), ("detailed", "Detailed")],
        default="standard",
    )
    department_specific_labels = fields.Boolean(
        "Department Specific Labels", default=False
    )
    field_group_customization = fields.Text("Field Group Customization")
    label_approval_required = fields.Boolean("Label Approval Required", default=False)
    label_configuration_version = fields.Char("Label Configuration Version")
    label_format_template = fields.Text("Label Format Template")
    label_language_preference = fields.Selection(
        [("en", "English"), ("es", "Spanish"), ("fr", "French")], default="en"
    )
    label_position_rules = fields.Text("Label Position Rules")
    label_preview_enabled = fields.Boolean("Label Preview Enabled", default=True)
    label_printing_preferences = fields.Text("Label Printing Preferences")
    label_size_customization = fields.Selection(
        [("small", "Small"), ("medium", "Medium"), ("large", "Large")], default="medium"
    )
    label_style_customization = fields.Text("Label Style Customization")
    label_translation_enabled = fields.Boolean(
        "Label Translation Enabled", default=False
    )
    multi_language_support = fields.Boolean("Multi-language Support", default=False)
    permission_based_labels = fields.Boolean("Permission Based Labels", default=False)
    qr_code_integration = fields.Boolean("QR Code Integration", default=False)
    template_inheritance_enabled = fields.Boolean(
        "Template Inheritance Enabled", default=False
    )
    user_specific_customization = fields.Boolean(
        "User Specific Customization", default=False
    )
    validation_rules_enabled = fields.Boolean("Validation Rules Enabled", default=False)

    # === COMPREHENSIVE MISSING BUSINESS FIELDS ===

    # Advanced Label Configuration
    label_inheritance_depth = fields.Integer(
        string="Label Inheritance Depth",
        default=1,
        help="Maximum depth for label template inheritance",
    )
    label_cache_enabled = fields.Boolean(
        string="Label Cache Enabled",
        default=True,
        help="Enable caching for improved performance",
    )
    label_versioning_enabled = fields.Boolean(
        string="Label Versioning Enabled",
        default=False,
        help="Track versions of label configurations",
    )
    current_version = fields.Char(
        string="Current Version",
        default="1.0",
        help="Current version of the label configuration",
    )

    # Industry and Context Specific
    industry_type = fields.Selection(
        [
            ("corporate", "Corporate"),
            ("financial", "Financial"),
            ("healthcare", "Healthcare"),
            ("legal", "Legal"),
            ("manufacturing", "Manufacturing"),
            ("education", "Education"),
            ("government", "Government"),
            ("nonprofit", "Non-Profit"),
        ],
        string="Industry Type",
        help="Industry context for label customization",
    )

    compliance_framework = fields.Selection(
        [
            ("sox", "Sarbanes-Oxley"),
            ("hipaa", "HIPAA"),
            ("gdpr", "GDPR"),
            ("ferpa", "FERPA"),
            ("naid", "NAID"),
            ("iso27001", "ISO 27001"),
            ("custom", "Custom Framework"),
        ],
        string="Compliance Framework",
        help="Compliance framework requiring specific labeling",
    )

    # Advanced User Experience
    accessibility_features = fields.Boolean(
        string="Accessibility Features",
        default=False,
        help="Enable accessibility features for labels",
    )
    color_coding_scheme = fields.Text(
        string="Color Coding Scheme", help="JSON configuration for color-coded labels"
    )
    font_size_preference = fields.Selection(
        [
            ("xs", "Extra Small"),
            ("sm", "Small"),
            ("md", "Medium"),
            ("lg", "Large"),
            ("xl", "Extra Large"),
        ],
        string="Font Size Preference",
        default="md",
        help="Default font size for labels",
    )

    # Integration and API Fields
    api_integration_enabled = fields.Boolean(
        string="API Integration Enabled",
        default=False,
        help="Allow external systems to use these label configurations",
    )
    webhook_notification_url = fields.Char(
        string="Webhook Notification URL",
        help="URL to notify when label configuration changes",
    )
    external_system_sync = fields.Boolean(
        string="External System Sync",
        default=False,
        help="Synchronize with external labeling systems",
    )
    last_sync_date = fields.Datetime(
        string="Last Sync Date",
        help="Last successful synchronization with external systems",
    )

    # Analytics and Reporting
    usage_statistics_enabled = fields.Boolean(
        string="Usage Statistics Enabled",
        default=True,
        help="Track usage statistics for this configuration",
    )
    usage_count = fields.Integer(
        string="Usage Count",
        default=0,
        help="Number of times this configuration has been applied",
    )
    last_used_date = fields.Datetime(
        string="Last Used Date", help="Date when this configuration was last used"
    )
    performance_metrics = fields.Text(
        string="Performance Metrics", help="JSON data with performance metrics"
    )
    popularity_score = fields.Float(
        string="Popularity Score",
        compute="_compute_popularity_score",
        store=True,
        help="Computed popularity score based on usage and recency",
    )

    # Security and Permissions
    security_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Security Classification",
        default="internal",
        help="Security classification for label configuration",
    )

    access_control_enabled = fields.Boolean(
        string="Access Control Enabled",
        default=False,
        help="Enable fine-grained access control",
    )
    allowed_group_ids = fields.Many2many(
        "res.groups",
        string="Allowed Groups",
        help="Groups allowed to use this configuration",
    )
    restricted_field_ids = fields.Many2many(
        "ir.model.fields",
        string="Restricted Fields",
        help="Fields that require special permissions",
    )

    # Field-Specific Customizations
    field_priority_mapping = fields.Text(
        string="Field Priority Mapping",
        help="JSON mapping of field priorities for display ordering",
    )
    conditional_display_rules = fields.Text(
        string="Conditional Display Rules",
        help="Rules for conditional field display based on context",
    )
    field_grouping_rules = fields.Text(
        string="Field Grouping Rules", help="Rules for grouping related fields together"
    )
    smart_field_suggestions = fields.Boolean(
        string="Smart Field Suggestions",
        default=False,
        help="Enable AI-powered field suggestions",
    )

    # Workflow Integration
    workflow_trigger_enabled = fields.Boolean(
        string="Workflow Trigger Enabled",
        default=False,
        help="Trigger workflows when labels are applied",
    )
    approval_workflow_id = fields.Many2one(
        "workflow.definition",
        string="Approval Workflow",
        help="Workflow for approving label changes",
    )
    notification_recipients = fields.Many2many(
        "res.users",
        string="Notification Recipients",
        help="Users to notify when configuration changes",
    )

    # Advanced Features
    machine_learning_enabled = fields.Boolean(
        string="Machine Learning Enabled",
        default=False,
        help="Use ML for intelligent label suggestions",
    )
    auto_translation_enabled = fields.Boolean(
        string="Auto Translation Enabled",
        default=False,
        help="Automatically translate labels to user language",
    )
    label_template_library = fields.Text(
        string="Label Template Library", help="JSON library of reusable label templates"
    )
    custom_css_styles = fields.Text(
        string="Custom CSS Styles", help="Custom CSS for label appearance"
    )

    # Field Label Customization Fields

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    # =============================================================================
    # FIELD LABEL CUSTOMIZATION ACTION METHODS
    # =============================================================================

    def action_apply_corporate_preset(self):
        """Apply corporate industry preset labels."""
        self.ensure_one()
        # Apply corporate-specific field label configuration
        preset_values = {
            "name": "Corporate Industry Preset",
            "description": "Field labels optimized for corporate document management",
            "state": "active",
        }
        self.write(preset_values)
        self.message_post(body=_("Corporate industry preset applied successfully."))
        return True

    def action_apply_financial_preset(self):
        """Apply financial industry preset labels."""
        self.ensure_one()
        preset_values = {
            "name": "Financial Industry Preset",
            "description": "Field labels optimized for financial services document management",
            "state": "active",
        }
        self.write(preset_values)
        self.message_post(body=_("Financial industry preset applied successfully."))
        return True

    def action_apply_healthcare_preset(self):
        """Apply healthcare industry preset labels."""
        self.ensure_one()
        preset_values = {
            "name": "Healthcare Industry Preset",
            "description": "Field labels optimized for healthcare document management with HIPAA compliance",
            "state": "active",
        }
        self.write(preset_values)
        self.message_post(body=_("Healthcare industry preset applied successfully."))
        return True

    def action_apply_legal_preset(self):
        """Apply legal industry preset labels."""
        self.ensure_one()
        preset_values = {
            "name": "Legal Industry Preset",
            "description": "Field labels optimized for legal document management",
            "state": "active",
        }
        self.write(preset_values)
        self.message_post(body=_("Legal industry preset applied successfully."))
        return True

    def action_reset_to_defaults(self):
        """Reset field labels to default system values."""
        self.ensure_one()
        default_values = {
            "name": "Default System Labels",
            "description": "Standard field labels restored to system defaults",
            "state": "draft",
        }
        self.write(default_values)
        self.message_post(body=_("Field labels reset to system defaults."))
        return True

    def action_setup_field_labels(self):
        """Setup custom field labels configuration."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Setup Field Labels"),
            "res_model": "field.label.customization",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_state": "draft",
                "focus_field": "description",
            },
        }

    def action_setup_transitory_config(self):
        """Setup transitory field configuration."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Setup Transitory Configuration"),
            "res_model": "transitory.field.config",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_customization_id": self.id,
                "default_name": f"Transitory Config for {self.name}",
            },
        }

    # === ADVANCED ACTION METHODS ===

    def action_clone_configuration(self):
        """Clone this configuration with a new name"""
        self.ensure_one()
        cloned_config = self.copy(
            {
                "name": f"{self.name} (Copy)",
                "state": "draft",
                "usage_count": 0,
                "last_used_date": False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Cloned Configuration"),
            "res_model": "field.label.customization",
            "res_id": cloned_config.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_export_configuration(self):
        """Export configuration as JSON"""
        self.ensure_one()
        export_data = {
            "name": self.name,
            "description": self.description,
            "industry_type": self.industry_type,
            "compliance_framework": self.compliance_framework,
            "label_format_template": self.label_format_template,
            "field_priority_mapping": self.field_priority_mapping,
            "conditional_display_rules": self.conditional_display_rules,
            "custom_css_styles": self.custom_css_styles,
        }

        # Create attachment with exported data
        import json

        attachment = self.env["ir.attachment"].create(
            {
                "name": f"label_config_export_{self.name}.json",
                "datas": json.dumps(export_data, indent=2).encode(),
                "res_model": self._name,
                "res_id": self.id,
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "new",
        }

    def action_sync_external_systems(self):
        """Synchronize with external labeling systems"""
        self.ensure_one()
        if not self.external_system_sync:
            raise UserError(
                _("External system sync is not enabled for this configuration.")
            )

        # Update sync timestamp
        self.last_sync_date = fields.Datetime.now()

        # Log sync attempt
        self.message_post(
            body=_("External system synchronization initiated."),
            subject=_("Label Configuration Sync"),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sync Initiated"),
                "message": _("External system synchronization has been started."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_generate_usage_report(self):
        """Generate detailed usage report"""
        self.ensure_one()

        # Create usage report content
        report_content = f"""
        Usage Report for: {self.name}
        ================================
        Total Usage Count: {self.usage_count}
        Last Used: {self.last_used_date or 'Never'}
        Popularity Score: {self.popularity_score:.2f}
        Industry Type: {self.industry_type or 'Not specified'}
        Security Classification: {self.security_classification}
        Active Users: {len(self.allowed_group_ids.users) if self.allowed_group_ids else 'All users'}
        """

        self.message_post(body=report_content, subject=_("Usage Report Generated"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Report Generated"),
                "message": _(
                    "Usage report has been generated and attached to this record."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_optimize_performance(self):
        """Optimize configuration for better performance"""
        self.ensure_one()

        # Enable caching and optimization features
        optimization_values = {
            "label_cache_enabled": True,
            "usage_statistics_enabled": True,
            "performance_metrics": '{"optimization_applied": true, "date": "'
            + str(fields.Datetime.now())
            + '"}',
        }

        self.write(optimization_values)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Optimization Applied"),
                "message": _("Performance optimization settings have been applied."),
                "type": "success",
                "sticky": False,
            },
        }

    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Record")
        return super().create(vals)
