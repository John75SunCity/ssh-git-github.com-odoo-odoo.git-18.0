# -*- coding: utf-8 -*-
"""
Records Box - Minimal Version
"""

from odoo import models, fields, api, _


class RecordsBox(models.Model):
    """
    Minimal Records Box Model
    """
    
    _name = 'records.box'
    _description = 'Records Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
    # Minimal required fields
    name = fields.Char(string='Box Number', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    
    # Basic state
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='State', default='draft', tracking=True)
    
    def action_activate(self):
        """Activate the box"""
        self.write({'state': 'active'})
    
    def action_archive(self):
        """Archive the box"""
        self.write({'state': 'archived'})
