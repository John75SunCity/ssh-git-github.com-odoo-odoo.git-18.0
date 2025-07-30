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
    action_activate = fields.Char(string='Action Activate')
    discount_percentage = fields.Char(string='Discount Percentage')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date')
    external_per_bin_rate = fields.Float(string='External Per Bin Rate', digits=(12, 2))
    external_service_call_rate = fields.Float(string='External Service Call Rate', digits=(12, 2))
    managed_permanent_removal_rate = fields.Float(string='Managed Permanent Removal Rate', digits=(12, 2))
    managed_retrieval_rate = fields.Float(string='Managed Retrieval Rate', digits=(12, 2))
    managed_service_call_rate = fields.Float(string='Managed Service Call Rate', digits=(12, 2))
    managed_shredding_rate = fields.Float(string='Managed Shredding Rate', digits=(12, 2))
    partner_id = fields.Many2one('res.partner', string='Partner Id')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    use_custom_external_rates = fields.Char(string='Use Custom External Rates')
    use_custom_managed_rates = fields.Char(string='Use Custom Managed Rates')
    view_mode = fields.Char(string='View Mode')
    
    # TODO: Add specific fields for this model
