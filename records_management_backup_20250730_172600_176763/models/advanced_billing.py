# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AdvancedBilling(models.Model):
    _name = 'advanced.billing'
    _description = 'Advanced Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # Core fields
    name = fields.Char(string='Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    # Billing fields
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    billing_period_id = fields.Many2one('advanced.billing.period', string='Billing Period')
    currency_id = fields.Many2one('res.currency', string='Currency')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')

    # State management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)

    # Mail thread fields
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    action_generate_invoice = fields.Char(string='Action Generate Invoice')
    action_generate_service_lines = fields.Char(string='Action Generate Service Lines')
    action_generate_storage_lines = fields.Char(string='Action Generate Storage Lines')
    amount = fields.Char(string='Amount')
    auto_generate_service_invoices = fields.Char(string='Auto Generate Service Invoices')
    auto_generate_storage_invoices = fields.Char(string='Auto Generate Storage Invoices')
    auto_send_invoices = fields.Char(string='Auto Send Invoices')
    billing_contact_ids = fields.One2many('billing.contact', 'advanced_billing_id', string='Billing Contact Ids')
    billing_day = fields.Char(string='Billing Day')
    billing_direction = fields.Char(string='Billing Direction')
    billing_profile_id = fields.Many2one('billing.profile', string='Billing Profile Id')
    billing_type = fields.Selection([], string='Billing Type')  # TODO: Define selection options
    box_id = fields.Many2one('box', string='Box Id')
    button_box = fields.Char(string='Button Box')
    description = fields.Char(string='Description')
    email = fields.Char(string='Email')
    generate_monthly_billing = fields.Char(string='Generate Monthly Billing')
    invoice_date = fields.Date(string='Invoice Date')
    invoice_due_days = fields.Char(string='Invoice Due Days')
    period_end_date = fields.Date(string='Period End Date')
    period_start_date = fields.Date(string='Period Start Date')
    phone = fields.Char(string='Phone')
    prepaid_balance = fields.Char(string='Prepaid Balance')
    prepaid_discount_percent = fields.Float(string='Prepaid Discount Percent', digits=(12, 2))
    prepaid_enabled = fields.Char(string='Prepaid Enabled')
    prepaid_months = fields.Char(string='Prepaid Months')
    primary_contact = fields.Char(string='Primary Contact')
    quantity = fields.Char(string='Quantity')
    receive_service_invoices = fields.Char(string='Receive Service Invoices')
    receive_statements = fields.Char(string='Receive Statements')
    receive_storage_invoices = fields.Char(string='Receive Storage Invoices')
    res_model = fields.Char(string='Res Model')
    retrieval_work_order_id = fields.Many2one('retrieval.work.order', string='Retrieval Work Order Id')
    service_amount = fields.Float(string='Service Amount', digits=(12, 2))
    service_billing_cycle = fields.Char(string='Service Billing Cycle')
    service_date = fields.Date(string='Service Date')
    service_line_ids = fields.One2many('service.line', 'advanced_billing_id', string='Service Line Ids')
    shredding_work_order_id = fields.Many2one('shredding.work.order', string='Shredding Work Order Id')
    storage_advance_months = fields.Char(string='Storage Advance Months')
    storage_amount = fields.Float(string='Storage Amount', digits=(12, 2))
    storage_bill_in_advance = fields.Char(string='Storage Bill In Advance')
    storage_billing_cycle = fields.Char(string='Storage Billing Cycle')
    storage_line_ids = fields.One2many('storage.line', 'advanced_billing_id', string='Storage Line Ids')
    target = fields.Char(string='Target')
    toggle_active = fields.Boolean(string='Toggle Active', default=False)
    total_amount = fields.Float(string='Total Amount', digits=(12, 2))
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    unit_price = fields.Float(string='Unit Price', digits=(12, 2))
    view_mode = fields.Char(string='View Mode')

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('amount'))

    # Action methods
    def action_confirm(self):
        """Confirm billing"""
        self.ensure_one()
        self.write({'state': 'confirmed'})

    def action_generate_invoice(self):
        """Generate invoice"""
        self.ensure_one()
        # Invoice generation logic here
        self.write({'state': 'invoiced'})

    def action_cancel(self):
        """Cancel billing"""
        self.ensure_one()
        self.write({'state': 'cancelled'})


class AdvancedBillingLine(models.Model):
    _name = 'advanced.billing.line'
    _description = 'Advanced Billing Line'

    billing_id = fields.Many2one('advanced.billing', string='Billing', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price')
    price_total = fields.Float(string='Total', compute='_compute_price_total', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.price_unit


class RecordsAdvancedBillingPeriod(models.Model):
    _name = 'records.advanced.billing.period'
    _description = 'Advanced Billing Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    billing_ids = fields.One2many('advanced.billing', 'billing_period_id', string='Billings')
