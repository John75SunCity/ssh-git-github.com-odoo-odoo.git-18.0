# -*- coding: utf-8 -*-
from odoo import models, fields, api



class PermanentFlagWizard(models.TransientModel):
    _name = 'permanent.flag.wizard'
    _description = 'Permanent Flag Wizard'
    
    # Core fields
    name = fields.Char(string='Name', required=True)
    
    # Action method
    def action_execute(self):
        """Execute the wizard action."""

        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
