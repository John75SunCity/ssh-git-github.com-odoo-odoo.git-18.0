# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FieldLabelCustomization(models.Model):
    _name = "field.label.customization"
    _description = "Field Label Customization"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
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

    priority = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="medium",
    )

    # ============================================================================
    # CUSTOMIZATION SPECIFICATIONS
    # ============================================================================
    model_name = fields.Char(string="Model Name", required=True)
    field_name = fields.Char(string="Field Name", required=True)
    original_label = fields.Char(string="Original Label")
    custom_label = fields.Char(string="Custom Label", required=True)

    # Label configuration
    label_template = fields.Selection(
        [
            ("standard", "Standard"),
            ("verbose", "Verbose"),
            ("abbreviated", "Abbreviated"),
            ("technical", "Technical"),
        ],
        string="Label Template",
        default="standard",
    )

    label_language = fields.Selection(
        [("en", "English"), ("es", "Spanish"), ("fr", "French")],
        string="Language",
        default="en",
    )

    label_size = fields.Selection(
        [("small", "Small"), ("medium", "Medium"), ("large", "Large")],
        string="Label Size",
        default="medium",
    )

    # ============================================================================
    # SCOPE AND APPLICATION
    # ============================================================================
    scope = fields.Selection(
        [
            ("global", "Global"),
            ("company", "Company"),
            ("user", "User Specific"),
            ("department", "Department"),
        ],
        string="Scope",
        default="company",
    )

    department_ids = fields.Many2many("hr.department", string="Departments")
    user_ids = fields.Many2many("res.users", string="Specific Users")

    # ============================================================================
    # COMPLIANCE AND INDUSTRY
    # ============================================================================
    industry_type = fields.Selection(
        [
            ("healthcare", "Healthcare"),
            ("finance", "Finance"),
            ("legal", "Legal"),
            ("manufacturing", "Manufacturing"),
            ("education", "Education"),
            ("government", "Government"),
            ("generic", "Generic"),
        ],
        string="Industry Type",
        default="generic",
    )

    compliance_framework = fields.Selection(
        [
            ("hipaa", "HIPAA"),
            ("gdpr", "GDPR"),
            ("sox", "SOX"),
            ("iso27001", "ISO 27001"),
            ("naid", "NAID AAA"),
            ("custom", "Custom"),
        ],
        string="Compliance Framework",
    )

    security_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Security Classification",
        default="internal",
    )

    # ============================================================================
    # DEPLOYMENT & VERSIONING
    # ============================================================================
    deployment_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("deployed", "Deployed"),
            ("failed", "Failed"),
            ("rolled_back", "Rolled Back"),
        ],
        string="Deployment Status",
        default="pending",
        tracking=True,
    )

    version = fields.Char(string="Version", default="1.0")
    deployment_date = fields.Datetime(string="Deployment Date")
    rollback_date = fields.Datetime(string="Rollback Date")

    # ============================================================================
    # VALIDATION & TESTING
    # ============================================================================
    validation_rules = fields.Text(string="Validation Rules")
    test_results = fields.Text(string="Test Results")
    approval_required = fields.Boolean(string="Approval Required", default=False)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Datetime(string="Approval Date")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Mail framework fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("deployment_status", "deployment_date")
    def _compute_is_deployed(self):
        for record in self:
            record.is_deployed = (
                record.deployment_status == "deployed" and record.deployment_date
            )

    @api.depends("model_name", "field_name", "custom_label")
    def _compute_full_customization_name(self):
        for record in self:
            if record.model_name and record.field_name:
                record.full_customization_name = (
                    f"{record.model_name}.{record.field_name}: {record.custom_label}"
                )
            else:
                record.full_customization_name = record.name

    is_deployed = fields.Boolean(compute="_compute_is_deployed", string="Is Deployed")
    full_customization_name = fields.Char(
        compute="_compute_full_customization_name", string="Full Customization Name"
    )

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("field.label.customization")
                    or "FLC/"
                )
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_deploy(self):
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active customizations can be deployed."))

        success = self._execute_deployment()
        if success:
            self.write(
                {
                    "deployment_status": "deployed",
                    "deployment_date": fields.Datetime.now(),
                }
            )
        else:
            self.write({"deployment_status": "failed"})

    def action_rollback(self):
        self.ensure_one()
        if not self.is_deployed:
            raise UserError(_("Only deployed customizations can be rolled back."))

        success = self._execute_rollback()
        if success:
            self.write(
                {
                    "deployment_status": "rolled_back",
                    "rollback_date": fields.Datetime.now(),
                }
            )

    def action_test(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Test Label Customization",
            "res_model": "field.label.test.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_customization_id": self.id},
        }

    def action_preview(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Preview Label Changes",
            "res_model": "field.label.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_customization_id": self.id},
        }

    # ============================================================================
    # DEPLOYMENT METHODS
    # ============================================================================
    def _execute_deployment(self):
        """Execute label customization deployment"""
        try:
            # Implementation for label deployment
            return True
        except Exception:
            return False

    def _execute_rollback(self):
        """Execute customization rollback"""
        try:
            # Implementation for rollback
            return True
        except Exception:
            return False

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("model_name", "field_name")
    def _check_field_exists(self):
        for record in self:
            if record.model_name and record.field_name:
                # Validate that the model and field exist
                try:
                    model = self.env[record.model_name]
                    if record.field_name not in model._fields:
                        raise ValidationError(
                            _(
                                f"Field '{record.field_name}' does not exist in model '{record.model_name}'."
                            )
                        )
                except KeyError:
                    raise ValidationError(
                        _(f"Model '{record.model_name}' does not exist.")
                    )

    @api.constrains("custom_label")
    def _check_custom_label_length(self):
        for record in self:
            if record.custom_label and len(record.custom_label) > 100:
                raise ValidationError(_("Custom label cannot exceed 100 characters."))
