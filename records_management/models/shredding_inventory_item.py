# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ShreddingInventoryItem(models.Model):
    _name = 'shredding.inventory.item'
    _description = 'Shredding Inventory Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(
        string='Item Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "New"
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Container and Document references
    container_ids = fields.Many2many(
        comodel_name='records.container',
        string='Related Containers'
    )
    
    document_id = fields.Many2one(
        comodel_name='records.document',
        string='Document',
        tracking=True
    )
    
    # Location tracking
    current_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Current Location',
        required=True,
        tracking=True
    )
    
    # State management
    state = fields.Selection([
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('shredded', 'Shredded'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='State', default='pending', tracking=True)
    
    # Cost tracking
    total_cost = fields.Monetary(
        string='Total Cost',
        currency_field='currency_id',
        compute='_compute_total_cost',
        store=True
    )
    
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Work order reference
    work_order_id = fields.Many2one(
        comodel_name='work.order.shredding',
        string='Shredding Work Order',
        tracking=True
    )
    
    # Batch assignment
    batch_id = fields.Many2one(
        comodel_name='shredding.inventory.batch',
        string='Shredding Batch',
        tracking=True
    )
    
    # Customer and company
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    # Scheduling
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        tracking=True
    )
    
    completed_date = fields.Datetime(
        string='Completed Date',
        tracking=True
    )
    
    # Weight and quantity
    weight = fields.Float(
        string='Weight (lbs)',
        digits=(12, 2)
    )
    
    quantity = fields.Integer(
        string='Quantity',
        default=1
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')
    
    @api.depends('document_id', 'container_ids', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.document_id:
                record.display_name = f"{record.name} - {record.document_id.name}"
            elif record.container_ids:
                container_names = ', '.join(record.container_ids.mapped('name'))
                record.display_name = f"{record.name} - {container_names}"
            else:
                record.display_name = record.name or _('New')
    
    @api.depends('weight', 'quantity')
    def _compute_total_cost(self):
        for record in self:
            # Calculate cost based on weight and quantity
            # This would typically use shredding rates
            base_rate = 0.50  # Default rate per pound
            record.total_cost = (record.weight or 0) * (record.quantity or 1) * base_rate
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.inventory.item') or _('New')
        return super().create(vals_list)
    
    def action_schedule(self):
        self.ensure_one()
        self.state = 'scheduled'
        if not self.scheduled_date:
            self.scheduled_date = fields.Datetime.now()
    
    def action_start_shredding(self):
        self.ensure_one()
        self.state = 'in_progress'
    
    def action_complete_shredding(self):
        self.ensure_one()
        self.state = 'shredded'
    
    def action_mark_completed(self):
        self.ensure_one()
        self.state = 'completed'
        self.completed_date = fields.Datetime.now()
    
    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'
