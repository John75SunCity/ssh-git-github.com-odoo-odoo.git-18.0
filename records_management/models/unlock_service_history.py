# -*- coding: utf-8 -*-
from odoo import models, fields, api

class UnlockServiceHistory(models.Model):
    _name = "unlock.service.history"
    _description = "Unlock Service History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Reference", required=True, default="New")
    partner_bin_key_id = fields.Many2one(
        "partner.bin.key", string="Partner Bin Key", required=True
    )
    service_type = fields.Selection(
        [
            ("unlock", "Unlock"),
            ("emergency_unlock", "Emergency Unlock"),
            ("key_reset", "Key Reset"),
            ("maintenance", "Maintenance"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )

    date = fields.Datetime(
        string="Service Date", default=fields.Datetime.now, required=True
    )
    technician_id = fields.Many2one(
        "res.users", string="Technician", default=lambda self: self.env.user
    )
    customer_id = fields.Many2one("res.partner", string="Customer")

    # Service details
    reason = fields.Text(string="Reason for Service")
    resolution = fields.Text(string="Resolution")
    duration = fields.Float(string="Duration (minutes)")

    # Billing
    cost = fields.Float(string="Service Cost")
    billable = fields.Boolean(string="Billable", default=True)

    # Location tracking
    location_id = fields.Many2one("records.location", string="Service Location")

    # Control fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="scheduled",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("unlock.service.history")
                    or "New"
                )
        return super().create(vals_list)
