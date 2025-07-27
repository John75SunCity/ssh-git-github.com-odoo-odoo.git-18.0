# -*- coding: utf-8 -*-
"""
Customer Feedback Management
"""

from odoo import models, fields, api, _


class CustomerFeedback(models.Model):
    """
    Customer Feedback Management
    """
    
    _name = 'customer.feedback'
    _description = 'Customer Feedback Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'
    
    # Core fields
    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    
    # TODO: Add specific fields for this model
    # Note: This is a minimal version - original fields need to be restored
