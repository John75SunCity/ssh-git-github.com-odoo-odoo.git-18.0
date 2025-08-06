# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    _description = "Res Config Settings"

    # Example of a configuration field
    module_records_management_setting = fields.Boolean(
        "Example Setting", config_parameter="records_management.setting"
    )

    # Documentation
    notes = fields.Text(string="Notes")

    # Action methods
    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
