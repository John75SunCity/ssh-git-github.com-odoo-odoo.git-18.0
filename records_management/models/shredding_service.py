# -*- coding: utf-8 -*-
"""
Shredding Service Management
"""

from odoo import models, fields, api, _


class ShreddingService(models.Model):
    """
    Shredding Service Management
    """
    
    _name = 'shred.svc'
    _description = 'Shredding Service Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = "name"
    
    # Core fields
    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    
    # TODO: Add specific fields for this model
    # Note: This is a minimal version - original fields need to be restored
