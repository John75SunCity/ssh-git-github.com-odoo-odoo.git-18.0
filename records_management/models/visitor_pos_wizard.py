# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class VisitorPosWizard(models.TransientModel):
    _name = 'visitor.pos.wizard'
    _description = 'Visitor Pos Wizard'
    
    # Wizard Fields
    name = fields.Char(string='Name', required=True)
    
    # Selection Options
    action_type = fields.Selection([
        ('execute', 'Execute'),
        ('cancel', 'Cancel')
    ], string='Action', default='execute')
    
    # Text Fields
    notes = fields.Text(string='Notes')
    
    def action_execute(self):
        """Execute the wizard action."""
        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        """Cancel the wizard."""
        return {'type': 'ir.actions.act_window_close'}
