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

    # Priority for label customization (required by demo data)
    priority = fields.Integer(string="Priority", default=10)

    # Label Customization Fields (comprehensive - auto-generated)
    label_authorized_by = fields.Char(string="Authorized By Label")
    label_client_reference = fields.Char(string="Client Reference Label")
    label_compliance_notes = fields.Char(string="Compliance Notes Label")
    label_confidentiality = fields.Char(string="Confidentiality Label")
    label_config_id = fields.Char(string="Config Id Label")
    label_container_number = fields.Char(string="Container Number Label")
    label_content_description = fields.Char(string="Content Description Label")
    label_count = fields.Char(string="Count Label")
    label_created_by_dept = fields.Char(string="Created By Dept Label")
    label_customization = fields.Char(string="Customization Label")
    label_customization_form = fields.Char(string="Customization Form Label")
    label_customization_manager = fields.Char(string="Customization Manager Label")
    label_customization_portal = fields.Char(string="Customization Portal Label")
    label_customization_search = fields.Char(string="Customization Search Label")
    label_customization_tree = fields.Char(string="Customization Tree Label")
    label_customization_user = fields.Char(string="Customization User Label")
    label_customization_views = fields.Char(string="Customization Views Label")
    label_customizer = fields.Char(string="Customizer Label")
    label_date_from = fields.Char(string="Date From Label")
    label_date_to = fields.Char(string="Date To Label")
    label_demo_data = fields.Char(string="Demo Data Label")
    label_destruction_date = fields.Char(string="Destruction Date Label")
    label_file_count = fields.Char(string="File Count Label")
    label_filing_system = fields.Char(string="Filing System Label")
    label_folder_type = fields.Char(string="Folder Type Label")
    label_hierarchy_display = fields.Char(string="Hierarchy Display Label")
    label_item_description = fields.Char(string="Item Description Label")
    label_manager = fields.Char(string="Manager Label")
    label_parent_container = fields.Char(string="Parent Container Label")
    label_portal = fields.Char(string="Portal Label")
    label_preset = fields.Char(string="Preset Label")
    label_project_code = fields.Char(string="Project Code Label")
    label_record_type = fields.Char(string="Record Type Label")
    label_report = fields.Char(string="Report Label")
    label_sequence_from = fields.Char(string="Sequence From Label")
    label_sequence_to = fields.Char(string="Sequence To Label")
    label_size_estimate = fields.Char(string="Size Estimate Label")
    label_special_handling = fields.Char(string="Special Handling Label")
    label_template = fields.Char(string="Template Label")
    label_user = fields.Char(string="User Label")
    label_weight_estimate = fields.Char(string="Weight Estimate Label")


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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)
