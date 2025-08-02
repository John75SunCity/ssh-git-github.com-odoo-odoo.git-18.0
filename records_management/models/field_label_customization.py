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

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

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
