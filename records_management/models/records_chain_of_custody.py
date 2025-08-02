# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RecordsChainOfCustody(models.Model):
    _name = "records.chain.of.custody"
    _description = "Records Chain Of Custody"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    description = fields.Text(string="Description")
    customer_id = fields.Many2one("res.partner", string="Customer")
    custody_event = fields.Char(string="Custody Event")
    key = fields.Char(string="Key")
    value = fields.Char(string="Value")
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="medium",
    )
    request_type = fields.Selection(
        [
            ("pickup", "Pickup"),
            ("delivery", "Delivery"),
            ("transfer", "Transfer"),
            ("destruction", "Destruction"),
        ],
        string="Request Type",
    )
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

    @api.depends("name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or "New"

    # Action methods
    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
