# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    _description = "Res Config Settings"

    # Example of a configuration field
    module_records_management_setting = fields.Boolean(
        "Example Setting", config_parameter="records_management.setting"
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
