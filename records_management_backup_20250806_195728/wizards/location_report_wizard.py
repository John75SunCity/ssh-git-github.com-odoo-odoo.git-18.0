# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LocationReportWizard(models.TransientModel):
    _name = 'location.report.wizard'
    _description = 'Location Report Wizard'
    
    # Core fields
    name = fields.Char(string='Name', required=True)
    
    # Action method
    def action_execute(self):
        """Execute the wizard action."""
        return {'type': 'ir.actions.act_window_close'}
