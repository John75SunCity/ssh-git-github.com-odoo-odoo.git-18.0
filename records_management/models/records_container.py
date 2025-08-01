# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RecordsContainer(models.Model):
    _name = 'records.container'
    _description = 'Records Container'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Container Number', required=True)
    container_type = fields.Selection([
        ('box', 'Box'),
        ('file', 'File'),
        ('binder', 'Binder')
    ], string='Container Type', required=True)
    location_id = fields.Many2one('records.location', string='Location')
    customer_id = fields.Many2one('res.partner', string='Customer')
    customer_inventory_id = fields.Many2one('customer.inventory', string='Customer Inventory')
    capacity = fields.Float(string='Capacity')
    current_usage = fields.Float(string='Current Usage')
    creation_date = fields.Date(string='Creation Date', default=fields.Date.today)
    destruction_date = fields.Date(string='Destruction Date')
    state = fields.Selection([
        ('active', 'Active'),
        ('stored', 'Stored'),
        ('destroyed', 'Destroyed')
    ], default='active')
