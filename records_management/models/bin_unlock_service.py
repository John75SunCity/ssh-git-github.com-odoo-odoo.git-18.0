# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BinUnlockService(models.Model):
    _name = "bin.unlock.service"
    _description = "Bin Unlock Service"
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
    # === COMPREHENSIVE MISSING FIELDS ===
    created_date = fields.Date(string="Date", default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string="Date", tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    service_date = fields.Date(string="Service Date")
    technician_id = fields.Many2one("hr.employee", string="Technician")
    billable = fields.Boolean(string="Billable", default=True)
    charge_amount = fields.Monetary(
        string="Charge Amount", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    completed = fields.Boolean(string="Completed", default=False)

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()

    # Bin Unlock Service Fields
    bin_location = fields.Char("Bin Location")
    customer_key_restricted = fields.Boolean("Customer Key Restricted", default=False)
    invoice_created = fields.Boolean("Invoice Created", default=False)
    items_retrieved = fields.Boolean("Items Retrieved", default=False)
    key_holder_id = fields.Many2one("res.partner", "Key Holder")
    access_authorization_verified = fields.Boolean(
        "Access Authorization Verified", default=False
    )
    backup_access_method = fields.Selection(
        [
            ("master_key", "Master Key"),
            ("code_override", "Code Override"),
            ("physical_break", "Physical Break"),
        ],
        default="master_key",
    )
    emergency_access_required = fields.Boolean(
        "Emergency Access Required", default=False
    )
    lock_mechanism_type = fields.Selection(
        [
            ("mechanical", "Mechanical"),
            ("electronic", "Electronic"),
            ("biometric", "Biometric"),
        ],
        default="mechanical",
    )
    security_log_generated = fields.Boolean("Security Log Generated", default=True)
    time_limit_exceeded = fields.Boolean("Time Limit Exceeded", default=False)
    unlock_authorization_code = fields.Char("Unlock Authorization Code")
    witness_required = fields.Boolean("Witness Required", default=False)
    # Bin Unlock Service Fields

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Record")
        return super().create(vals)
