# -*- coding: utf-8 -*-
"""
Mobile Bin Key Management Wizard
"""

from odoo import models, fields, api, _


class MobileBinKeyWizard(models.Model):
    """
    Mobile Bin Key Management Wizard
    """

    _name = "mobile.bin.key.wizard"
    _description = "Mobile Bin Key Management Wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
    
    def action_execute(self):
        """Execute the mobile bin key action"""
        self.ensure_one()
        # Implementation based on action_type field
        action_type = getattr(self, 'action_type', 'quick_lookup')
        
        if action_type == 'quick_lookup':
            # Refresh lookup data
            self.message_post(body=_('Lookup data refreshed'))
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mobile.bin.wiz',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            # Execute other actions
            self.write({'state': 'done'})
            self.message_post(body=_('Mobile bin key action executed'))
            return {'type': 'ir.actions.act_window_close'}
