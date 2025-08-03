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

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()

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

    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Record")
        return super().create(vals)
