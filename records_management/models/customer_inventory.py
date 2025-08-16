# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerInventory(models.Model):
    _name = 'customer.inventory'
    _description = 'Customer Inventory'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
        # Core fields
    name = fields.Char(string='Name', required=True,,
    tracking=True),
    company_id = fields.Many2one('res.company', string='Company',,
    default=lambda self: self.env.company),
    user_id = fields.Many2one('res.users', string='User',,
    default=lambda self: self.env.user),
    active = fields.Boolean(string='Active',,
    default=True),
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'), 
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    
    
        # Standard message/activity fields
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages',,
    auto_join=True),
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities',,
    auto_join=True),
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers',,
    auto_join=True),
    card = fields.Char(string='Card'),
    help = fields.Char(string='Help'),
    last_updated = fields.Char(string='Last Updated'),
    partner_id = fields.Many2one('res.partner',,
    string='Partner Id'),
    res_model = fields.Char(string='Res Model'),
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress')), ('completed', 'Completed')], string='Status', default='new')
    total_containers = fields.Char(string='Total Containers'),
    total_documents = fields.Char(string='Total Documents'),
    view_mode = fields.Char(string='View Mode')

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_containers(self):
        for record in self:
            record.total_containers = sum(record.line_ids.mapped('amount'))

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_documents(self):
        for record in self:
            record.total_documents = sum(record.line_ids.mapped('amount'))
    
    # TODO: Add specific fields for this model:
        pass
