# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockPickingRecordsExtension(models.Model):
    _name = 'stock.picking.records.extension'
    _description = 'Stock Picking Records Extension'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(
        string='Extension Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Link to stock picking
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Stock Picking',
        required=True,
        ondelete='cascade'
    )
    
    # Records management specific fields
    container_ids = fields.Many2many(
        comodel_name='records.container',
        string='Related Containers'
    )
    
    document_ids = fields.Many2many(
        comodel_name='records.document',
        string='Related Documents'
    )
    
    # Additional tracking
    pickup_scheduled_date = fields.Datetime(
        string='Pickup Scheduled Date',
        tracking=True
    )
    
    pickup_actual_date = fields.Datetime(
        string='Pickup Actual Date',
        tracking=True
    )
    
    destruction_required = fields.Boolean(
        string='Destruction Required',
        default=False,
        tracking=True
    )
    
    destruction_date = fields.Datetime(
        string='Destruction Date',
        tracking=True
    )
    
    # Chain of custody
    custody_transfer_ids = fields.One2many(
        comodel_name='custody.transfer.event',
        inverse_name='picking_extension_id',
        string='Custody Transfers'
    )
    
    # NAID compliance
    naid_compliant = fields.Boolean(
        string='NAID Compliant',
        default=True,
        tracking=True
    )
    
    naid_certificate_id = fields.Many2one(
        comodel_name='naid.certificate',
        string='NAID Certificate'
    )
    
    # State management
    records_state = fields.Selection([
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('stored', 'Stored'),
        ('destroyed', 'Destroyed')
    ], string='Records State', default='pending', tracking=True)
    
    # Notes
    special_instructions = fields.Text(
        string='Special Instructions'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.records.extension') or _('New')
        return super().create(vals_list)
    
    def action_start_transit(self):
        self.ensure_one()
        self.records_state = 'in_transit'
    
    def action_confirm_receipt(self):
        self.ensure_one()
        self.records_state = 'received'
        self.pickup_actual_date = fields.Datetime.now()
    
    def action_store_records(self):
        self.ensure_one()
        self.records_state = 'stored'
    
    def action_destroy_records(self):
        self.ensure_one()
        if self.destruction_required:
            self.records_state = 'destroyed'
            self.destruction_date = fields.Datetime.now()
