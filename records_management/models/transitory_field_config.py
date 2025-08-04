# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class TransitoryFieldConfig(models.Model):
    _name = "transitory.field.config"
    _description = "Transitory Field Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Configuration Name", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Configuration Code", index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # Framework Required Fields
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CONFIGURATION DETAILS
    # ============================================================================

    # Configuration Type
    config_preset = fields.Selection(
        [
            ("basic", "Basic Configuration"),
            ("advanced", "Advanced Configuration"),
            ("custom", "Custom Configuration"),
            ("template", "Template Configuration"),
        ],
        string="Configuration Type",
        default="basic",
        required=True,
    )

    config_version = fields.Char(string="Configuration Version", default="1.0")
    template_configuration = fields.Text(string="Template Configuration")
    auto_apply_config = fields.Boolean(string="Auto Apply Configuration", default=True)

    # Target Configuration
    target_model = fields.Selection(
        [
            ("portal.request", "Portal Request"),
            ("records.container", "Records Container"),
            ("pickup.request", "Pickup Request"),
            ("work.order", "Work Order"),
            ("customer.feedback", "Customer Feedback"),
        ],
        string="Target Model",
        required=True,
    )

    # User & Department Settings
    customer_id = fields.Many2one("res.partner", string="Customer")
    department_id = fields.Many2one("hr.department", string="Department")
    user_customization_allowed = fields.Boolean(
        string="Allow User Customization", default=True
    )
    permission_based_visibility = fields.Boolean(
        string="Permission Based Visibility", default=False
    )

    # ============================================================================
    # FIELD REQUIREMENTS CONFIGURATION
    # ============================================================================

    # Document & Records Requirements
    require_client_reference = fields.Boolean(string="Client Reference", default=False)
    require_container_number = fields.Boolean(string="Container Number", default=True)
    require_content_description = fields.Boolean(
        string="Content Description", default=True
    )
    require_document_type = fields.Boolean(string="Document Type", default=False)
    require_record_type = fields.Boolean(string="Record Type", default=True)
    require_description = fields.Boolean(string="Description", default=True)

    # Location & Storage Requirements
    require_location = fields.Boolean(string="Storage Location", default=True)
    require_department = fields.Boolean(string="Department", default=True)
    require_service_type = fields.Boolean(string="Service Type", default=True)

    # Date Requirements
    require_date_from = fields.Boolean(string="Date From", default=False)
    require_date_to = fields.Boolean(string="Date To", default=False)
    require_destruction_date = fields.Boolean(string="Destruction Date", default=False)

    # Security & Compliance Requirements
    require_confidentiality = fields.Boolean(
        string="Confidentiality Level", default=False
    )
    require_security_level = fields.Boolean(string="Security Level", default=False)
    require_retention_policy = fields.Boolean(string="Retention Policy", default=False)

    # Personnel Requirements
    require_requestor_name = fields.Boolean(string="Requestor Name", default=True)
    require_project_code = fields.Boolean(string="Project Code", default=False)

    # ============================================================================
    # FIELD CONFIGURATION RULES
    # ============================================================================

    # Field Lists (JSON or Text format)
    mandatory_fields_list = fields.Text(
        string="Mandatory Fields List",
        help="JSON list of mandatory field names",
    )
    readonly_fields_list = fields.Text(
        string="Readonly Fields List",
        help="JSON list of readonly field names",
    )
    hidden_fields_list = fields.Text(
        string="Hidden Fields List",
        help="JSON list of hidden field names",
    )

    # Field Rules
    field_visibility_rules = fields.Text(
        string="Field Visibility Rules",
        help="JSON configuration for conditional field visibility",
    )
    field_dependency_rules = fields.Text(
        string="Field Dependency Rules",
        help="JSON configuration for field dependencies",
    )
    data_validation_rules = fields.Text(
        string="Data Validation Rules",
        help="JSON configuration for field validation",
    )
    default_field_values = fields.Text(
        string="Default Field Values",
        help="JSON configuration for default values",
    )

    # Custom Definitions
    custom_field_definitions = fields.Text(
        string="Custom Field Definitions",
        help="JSON definition of custom fields",
    )
    validation_error_messages = fields.Text(
        string="Custom Validation Messages",
        help="JSON configuration for custom error messages",
    )

    # ============================================================================
    # LAYOUT & UI CONFIGURATION
    # ============================================================================

    # Form Layout
    form_layout_configuration = fields.Text(
        string="Form Layout Configuration",
        help="JSON configuration for form layout",
    )
    field_group_configuration = fields.Text(
        string="Field Group Configuration",
        help="JSON configuration for field grouping",
    )

    # Integration Settings
    workflow_integration_config = fields.Text(
        string="Workflow Integration Config",
        help="JSON configuration for workflow integration",
    )

    # ============================================================================
    # QUALITY & VALIDATION
    # ============================================================================

    # Quality Control
    quality_checked = fields.Boolean(string="Quality Checked", default=False)
    quality_score = fields.Float(string="Quality Score", digits=(3, 2))
    validation_required = fields.Boolean(string="Validation Required", default=True)
    validated_by_id = fields.Many2one("res.users", string="Validated By")
    validation_date = fields.Datetime(string="Validation Date")

    # Documentation
    documentation_complete = fields.Boolean(
        string="Documentation Complete", default=False
    )
    notes = fields.Text(string="Configuration Notes")

    # ============================================================================
    # REFERENCES & RELATIONSHIPS
    # ============================================================================

    # External References
    reference_number = fields.Char(string="Reference Number")
    external_reference = fields.Char(string="External Reference")

    # Related Configurations
    field_label_config_id = fields.Many2one(
        "field.label.customization", string="Field Label Configuration"
    )
    parent_config_id = fields.Many2one(
        "transitory.field.config",
        string="Parent Configuration",
    )
    child_config_ids = fields.One2many(
        "transitory.field.config",
        "parent_config_id",
        string="Child Configurations",
    )

    # Attachments
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")

    # ============================================================================
    # DATES & SCHEDULING
    # ============================================================================

    # Configuration Lifecycle
    created_date = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
    )
    updated_date = fields.Datetime(string="Last Updated Date")
    activation_date = fields.Datetime(string="Activation Date")
    expiry_date = fields.Datetime(string="Expiry Date")

    # Review Cycle
    last_review_date = fields.Date(string="Last Review Date")
    next_review_date = fields.Date(string="Next Review Date")
    review_frequency = fields.Integer(string="Review Frequency (Days)", default=90)

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================

    # Usage Statistics
    usage_count = fields.Integer(
        string="Usage Count",
        compute="_compute_usage_statistics",
        store=True,
    )
    performance_score = fields.Float(
        string="Performance Score",
        digits=(5, 2),
        compute="_compute_performance_metrics",
        store=True,
    )
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ],
        string="Efficiency Rating",
        compute="_compute_performance_metrics",
        store=True,
    )

    # Configuration Complexity
    complexity_score = fields.Float(
        string="Configuration Complexity",
        compute="_compute_complexity_metrics",
        store=True,
        digits=(3, 2),
    )

    # Health Metrics
    health_score = fields.Float(
        string="Configuration Health Score",
        compute="_compute_health_metrics",
        store=True,
        digits=(3, 2),
    )

    # ============================================================================
    # COMPUTED DISPLAY FIELDS
    # ============================================================================

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("name", "config_preset", "target_model", "state")
    def _compute_display_name(self):
        """Compute display name for configuration"""
        for record in self:
            parts = [record.name]
            if record.config_preset:
                parts.append(f"({record.config_preset.title()})")
            if record.target_model:
                model_name = dict(record._fields["target_model"].selection).get(
                    record.target_model
                )
                parts.append(f"- {model_name}")
            record.display_name = " ".join(parts)

    @api.depends(
        "mandatory_fields_list", "readonly_fields_list", "field_visibility_rules"
    )
    def _compute_complexity_metrics(self):
        """Compute configuration complexity score"""
        for record in self:
            complexity = 0.0

            # Base complexity from field requirements
            field_requirements = [
                record.require_client_reference,
                record.require_container_number,
                record.require_content_description,
                record.require_document_type,
                record.require_location,
                record.require_department,
                record.require_confidentiality,
                record.require_security_level,
            ]
            complexity += sum(field_requirements) * 0.1

            # Additional complexity from custom configurations
            if record.custom_field_definitions:
                complexity += 0.5
            if record.field_dependency_rules:
                complexity += 0.3
            if record.data_validation_rules:
                complexity += 0.2

            record.complexity_score = min(complexity, 10.0)  # Cap at 10.0

    @api.depends("quality_score", "validation_required", "documentation_complete")
    def _compute_health_metrics(self):
        """Compute configuration health score"""
        for record in self:
            health = 0.0

            # Quality score contribution (40%)
            if record.quality_score:
                health += (record.quality_score / 10.0) * 4.0

            # Validation status (30%)
            if record.validation_required:
                if record.validated_by_id and record.validation_date:
                    health += 3.0
                else:
                    health += 1.0  # Penalty for required but not validated
            else:
                health += 3.0  # No validation required is good

            # Documentation completeness (30%)
            if record.documentation_complete:
                health += 3.0
            elif record.notes:
                health += 1.5  # Partial documentation

            record.health_score = min(health, 10.0)

    @api.depends("child_config_ids")
    def _compute_usage_statistics(self):
        """Compute usage statistics"""
        for record in self:
            # This would be computed based on actual usage tracking
            # For now, use child configurations as proxy
            record.usage_count = len(record.child_config_ids)

    @api.depends("usage_count", "health_score", "complexity_score")
    def _compute_performance_metrics(self):
        """Compute performance metrics"""
        for record in self:
            # Calculate performance based on usage, health, and complexity
            if record.complexity_score > 0:
                performance = (
                    record.health_score * record.usage_count
                ) / record.complexity_score
            else:
                performance = record.health_score

            record.performance_score = min(performance, 100.0)

            # Determine efficiency rating
            if performance >= 8.0:
                record.efficiency_rating = "excellent"
            elif performance >= 6.0:
                record.efficiency_rating = "good"
            elif performance >= 4.0:
                record.efficiency_rating = "fair"
            else:
                record.efficiency_rating = "poor"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_activate_config(self):
        """Activate the configuration"""
        self.ensure_one()
        if not self.validation_required or (
            self.validated_by_id and self.validation_date
        ):
            self.write(
                {
                    "state": "active",
                    "activation_date": fields.Datetime.now(),
                }
            )
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Configuration Activated"),
                    "message": _("Configuration has been activated successfully."),
                    "type": "success",
                },
            }
        else:
            raise UserError(_("Configuration must be validated before activation."))

    def action_validate_config(self):
        """Validate the configuration"""
        self.ensure_one()
        self.write(
            {
                "validated_by_id": self.env.user.id,
                "validation_date": fields.Datetime.now(),
                "quality_checked": True,
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Configuration Validated"),
                "message": _("Configuration has been validated successfully."),
                "type": "success",
            },
        }

    def action_create_child_config(self):
        """Create a child configuration based on this one"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Child Configuration"),
            "res_model": "transitory.field.config",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_parent_config_id": self.id,
                "default_name": f"{self.name} - Child",
                "default_config_preset": self.config_preset,
                "default_target_model": self.target_model,
            },
        }

    def action_apply_configuration(self):
        """Apply this configuration to target models"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active configurations can be applied."))

        # This would implement the actual application logic
        # For now, just mark as applied
        self.message_post(body=_("Configuration applied to %s") % self.target_model)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Configuration Applied"),
                "message": _("Configuration has been applied successfully."),
                "type": "success",
            },
        }

    def action_schedule_review(self):
        """Schedule next configuration review"""
        self.ensure_one()
        next_review = fields.Date.today() + fields.timedelta(days=self.review_frequency)

        self.write(
            {
                "last_review_date": fields.Date.today(),
                "next_review_date": next_review,
            }
        )

        # Create calendar event for review
        self.env["calendar.event"].create(
            {
                "name": f"Configuration Review - {self.name}",
                "start": next_review,
                "allday": True,
                "user_id": self.user_id.id,
                "description": f"Scheduled review for configuration {self.name}",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Review Scheduled"),
                "message": _("Next review scheduled for %s") % next_review,
                "type": "success",
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("expiry_date", "activation_date")
    def _check_date_logic(self):
        """Ensure expiry date is after activation date"""
        for record in self:
            if record.expiry_date and record.activation_date:
                if record.expiry_date <= record.activation_date:
                    raise ValidationError(
                        _("Expiry date must be after activation date.")
                    )

    @api.constrains("parent_config_id")
    def _check_parent_recursion(self):
        """Prevent recursive parent relationships"""
        if not self._check_recursion():
            raise ValidationError(
                _("You cannot create recursive configuration hierarchies.")
            )

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults"""
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("transitory.field.config")
                    or "TFC"
                )

            # Set next review date if not provided
            if not vals.get("next_review_date") and vals.get("review_frequency"):
                vals["next_review_date"] = fields.Date.today() + fields.timedelta(
                    days=vals["review_frequency"]
                )

        return super().create(vals_list)

    def write(self, vals):
        """Override write to track changes"""
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Configuration status changed from %s to %s")
                    % (old_state, new_state)
                )

        # Update timestamp when configuration changes
        vals["updated_date"] = fields.Datetime.now()

        return super().write(vals)
