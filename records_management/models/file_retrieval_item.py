# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FileRetrievalItem(models.Model):
    _name = 'file.retrieval.item'
    _description = 'File Retrieval Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(
        string='Retrieval Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # File information
    file_name = fields.Char(
        string='File Name',
        required=True,
        tracking=True
    )
    
    file_path = fields.Char(
        string='File Path',
        tracking=True
    )
    
    file_size = fields.Float(
        string='File Size (MB)',
        digits=(12, 2)
    )
    
    # Retrieval details
    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Container',
        required=True,
        tracking=True
    )
    
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    
    requested_date = fields.Datetime(
        string='Requested Date',
        default=fields.Datetime.now,
        required=True
    )
    
    retrieved_date = fields.Datetime(
        string='Retrieved Date',
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('in_progress', 'In Progress'),
        ('retrieved', 'Retrieved'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)
    
    # Staff assignment
    assigned_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        tracking=True
    )
    
    # Notes and comments
    notes = fields.Text(
        string='Retrieval Notes'
    )
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('file.retrieval.item') or _('New')
        return super().create(vals_list)
    
    def action_request(self):
        self.ensure_one()
        self.state = 'requested'
    
    def action_start_retrieval(self):
        self.ensure_one()
        self.state = 'in_progress'
    
    def action_complete_retrieval(self):
        self.ensure_one()
        self.state = 'retrieved'
        self.retrieved_date = fields.Datetime.now()
    
    def action_deliver(self):
        self.ensure_one()
        self.state = 'delivered'
    
    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'
