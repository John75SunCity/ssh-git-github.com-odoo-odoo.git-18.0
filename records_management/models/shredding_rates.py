# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ShreddingRates(models.Model):
    _name = 'shredding.rates'
    _description = 'Shredding Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
    # Core fields
    name = fields.Char(string='Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'), 
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)
    
    # Standard message/activity fields
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
    
    # TODO: Add specific fields for this model
