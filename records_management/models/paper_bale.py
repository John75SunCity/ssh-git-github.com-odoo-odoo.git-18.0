# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PaperBale(models.Model):
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Bale Number', required=True)
    weight = fields.Float(string='Weight (kg)')
    creation_date = fields.Date(string='Creation Date', default=fields.Date.today)
    load_id = fields.Many2one('load', string='Load')
    recycling_facility = fields.Char(string='Recycling Facility')
    state = fields.Selection([
        ('created', 'Created'),
        ('shipped', 'Shipped'),
        ('recycled', 'Recycled')
    ], default='created')
