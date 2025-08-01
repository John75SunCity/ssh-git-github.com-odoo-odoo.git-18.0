# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WizardTemplate(models.TransientModel):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'wizard.template'
    _description = 'Wizard Template'
    
    # Core fields
    name = fields.Char(string='Name', required=True)
    
    # Action method
    def action_execute(self):
        """Execute the wizard action."""
        return {'type': 'ir.actions.act_window_close'}
