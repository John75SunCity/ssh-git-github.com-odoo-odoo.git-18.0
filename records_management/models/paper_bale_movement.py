# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaperBaleMovement(models.Model):
    _name = "paper.bale.movement"
    _description = "Paper Bale Movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "movement_date desc, id desc"

    bale_id = fields.Many2one(
        "paper.bale", string="Paper Bale", required=True, ondelete="cascade"
    )
    source_location_id = fields.Many2one(
        "stock.location", string="Source Location", required=True
    )
    destination_location_id = fields.Many2one(
        "stock.location", string="Destination Location", required=True
    )
    movement_date = fields.Datetime(
        string="Movement Date", required=True, default=fields.Datetime.now
    )
    responsible_user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_transit", "In Transit"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    notes = fields.Text(string="Movement Notes")

    @api.constrains("source_location_id", "destination_location_id")
    def _check_locations(self):
        for movement in self:
            if movement.source_location_id == movement.destination_location_id:
                raise ValidationError(
                    _("Source and destination locations cannot be the same.")
                )

    def action_start_transit(self):
        self.ensure_one()
        self.write({"state": "in_transit"})

    def action_complete_movement(self):
        self.ensure_one()
        self.write({"state": "completed"})
        for movement in self:
            movement.bale_id.location_id = movement.destination_location_id

    def action_cancel_movement(self):
        self.ensure_one()
        self.write({"state": "cancelled"})
