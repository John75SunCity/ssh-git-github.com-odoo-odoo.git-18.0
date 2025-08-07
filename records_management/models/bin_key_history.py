# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BinKeyHistory(models.Model):
    _name = "bin.key.history"
    _description = "Bin Key History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Reference", required=True, default="New")
    partner_bin_key_id = fields.Many2one(
        "partner.bin.key", string="Partner Bin Key", required=True
    )
    action_type = fields.Selection(
        [
            ("created", "Created"),
            ("assigned", "Assigned"),
            ("returned", "Returned"),
            ("lost", "Lost"),
            ("replaced", "Replaced"),
            ("deactivated", "Deactivated"),
        ],
        string="Action Type",
        required=True,
        tracking=True,
    )

    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True)
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    notes = fields.Text(string="Notes")

    # Location tracking
    location_id = fields.Many2one("records.location", string="Location")

    # Control fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    active = fields.Boolean(string="Active", default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("bin.key.history") or "New"
                )
        return super().create(vals_list)
