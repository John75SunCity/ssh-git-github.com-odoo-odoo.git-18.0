# -*- coding: utf-8 -*-
"""
Wizard to Link POS Transaction to Visitor
"""

from odoo import models, fields, api, _


class VisitorPosWizard(models.Model):
    """
    Wizard to Link POS Transaction to Visitor
    """

    _name = "visitor.pos.wizard"
    _description = "Wizard to Link POS Transaction to Visitor"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Visitor Information
    visitor_id = fields.Many2one('visitor', string='Visitor', required=True)
    visitor_name = fields.Char(string='Visitor Name', related='visitor_id.name', readonly=True)
    visitor_email = fields.Char(string='Email', related='visitor_id.email', readonly=True)
    visitor_phone = fields.Char(string='Phone', related='visitor_id.phone', readonly=True)
    check_in_time = fields.Datetime(string='Check-in Time')
    purpose_of_visit = fields.Char(string='Purpose of Visit')

    # POS Configuration
    pos_config_id = fields.Many2one('pos.config', string='POS Configuration')
    pos_session_id = fields.Many2one('pos.session', string='POS Session')
    cashier_id = fields.Many2one('res.users', string='Cashier')
    service_location = fields.Char(string='Service Location')
    processing_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')

    # Customer Data Management
    existing_customer_id = fields.Many2one('res.partner', string='Existing Customer')
    create_new_customer = fields.Boolean(string='Create New Customer', default=False)
    customer_record_created = fields.Boolean(string='Customer Record Created', default=False)
    customer_record_id = fields.Many2one('res.partner', string='Customer Record')

    # Service Configuration
    service_type = fields.Selection([
        ('shredding', 'Document Shredding'),
        ('storage', 'Document Storage'),
        ('retrieval', 'Document Retrieval'),
        ('scanning', 'Document Scanning'),
        ('consultation', 'Consultation')
    ], string='Service Type')
    
    product_id = fields.Many2one('product.product', string='Service Product')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
    discount_percent = fields.Float(string='Discount %')

    # Transaction Information
    pos_order_id = fields.Many2one('pos.order', string='POS Order')
    pos_order_created = fields.Boolean(string='POS Order Created', default=False)
    transaction_id = fields.Char(string='Transaction ID')
    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')

    # Financial Calculations
    base_amount = fields.Float(string='Base Amount', compute='_compute_amounts')
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_amounts')
    subtotal = fields.Float(string='Subtotal', compute='_compute_amounts')
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_amounts')
    total_amount = fields.Float(string='Total Amount', compute='_compute_amounts')

    # Service Requirements
    documentation_required = fields.Boolean(string='Documentation Required', default=False)
    certification_required = fields.Boolean(string='Certification Required', default=False)
    witness_required = fields.Boolean(string='Witness Required', default=False)
    chain_of_custody_required = fields.Boolean(string='Chain of Custody Required', default=False)

    # Processing Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    processing_start_time = fields.Datetime(string='Processing Start Time')
    processing_end_time = fields.Datetime(string='Processing End Time')
    total_processing_time = fields.Float(string='Total Processing Time (minutes)', compute='_compute_processing_time')

    # Error Handling
    error_message = fields.Text(string='Error Message')
    error_details = fields.Text(string='Error Details')

    # Additional fields for comprehensive functionality
    estimated_service_time = fields.Float(string='Estimated Service Time (minutes)')
    special_requirements = fields.Text(string='Special Requirements')
    internal_notes = fields.Text(string='Internal Notes')
    
    @api.depends('quantity', 'unit_price', 'discount_percent')
    def _compute_amounts(self):
        for record in self:
            record.base_amount = record.quantity * record.unit_price
            record.discount_amount = record.base_amount * (record.discount_percent / 100.0)
            record.subtotal = record.base_amount - record.discount_amount
            # Simplified tax calculation - you may need to use proper tax computation
            record.tax_amount = record.subtotal * 0.1  # Assuming 10% tax
            record.total_amount = record.subtotal + record.tax_amount

    @api.depends('processing_start_time', 'processing_end_time')
    def _compute_processing_time(self):
        for record in self:
            if record.processing_start_time and record.processing_end_time:
                delta = record.processing_end_time - record.processing_start_time
                record.total_processing_time = delta.total_seconds() / 60.0
            else:
                record.total_processing_time = 0.0

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
