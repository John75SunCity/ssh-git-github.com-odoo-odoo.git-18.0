# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RecordsContainerMovement(models.Model):
    _name = "records.container.movement"
    _description = "Records Container Movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    container_id = fields.Many2one(
        "records.container", string="Container", required=True, tracking=True
    )
    from_location_id = fields.Many2one(
        "records.location", string="From Location", tracking=True
    )
    to_location_id = fields.Many2one(
        "records.location", string="To Location", tracking=True
    )
    movement_date = fields.Datetime(
        string="Movement Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )
    movement_type = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("relocation", "Relocation"),
            ("transfer", "Transfer"),
            ("return", "Return"),
        ],
        string="Movement Type",
        required=True,
        tracking=True,
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
