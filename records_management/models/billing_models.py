# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class RecordsBillingConfig(models.Model):
    """Configuration for records management billing"""
    _name = 'records.billing.config'
    _description = 'Records Billing Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Configuration Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Billing cycles
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Billing Cycle', default='monthly', required=True, tracking=True)
    
    # Billing day
    billing_day = fields.Integer(string='Billing Day of Month', default=1, 
                                help='Day of the month when billing is generated')
    
    # Auto-billing settings
    auto_generate_invoices = fields.Boolean(string='Auto Generate Invoices', default=True, tracking=True)
    auto_send_invoices = fields.Boolean(string='Auto Send Invoices', default=False, tracking=True)
    
    # Default terms
    default_payment_terms = fields.Many2one('account.payment.term', string='Default Payment Terms')
    
    # Late fee settings
    apply_late_fees = fields.Boolean(string='Apply Late Fees', default=False, tracking=True)
    late_fee_percentage = fields.Float(string='Late Fee Percentage', default=0.0)
    late_fee_grace_days = fields.Integer(string='Grace Period (Days)', default=0)

class RecordsBillingPeriod(models.Model):
    """Billing periods for records management"""
    _name = 'records.billing.period'
    _description = 'Records Billing Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'

    name = fields.Char(string='Period Name', required=True, tracking=True)
    billing_config_id = fields.Many2one('records.billing.config', string='Billing Configuration', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    # Period dates
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Billing lines
    billing_line_ids = fields.One2many('records.billing.line', 'billing_period_id', string='Billing Lines')
    
    # Totals
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_totals', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    @api.depends('billing_line_ids.amount')
    def _compute_totals(self):
        for period in self:
            period.total_amount = sum(period.billing_line_ids.mapped('amount'))

class RecordsBillingLine(models.Model):
    """Individual billing line items"""
    _name = 'records.billing.line'
    _description = 'Records Billing Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    billing_period_id = fields.Many2one('records.billing.period', string='Billing Period', required=True, ondelete='cascade')
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    
    # Service details
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('scanning', 'Scanning'),
        ('delivery', 'Delivery'),
        ('other', 'Other')
    ], string='Service Type', required=True, tracking=True)
    
    description = fields.Text(string='Description', required=True)
    
    # Quantities and pricing
    quantity = fields.Float(string='Quantity', default=1.0, tracking=True)
    unit_price = fields.Monetary(string='Unit Price', tracking=True)
    amount = fields.Monetary(string='Amount', compute='_compute_amount', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', related='billing_period_id.company_id.currency_id')
    
    # References
    box_id = fields.Many2one('records.box', string='Related Box')
    service_request_id = fields.Many2one('records.service.request', string='Related Service Request')
    
    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price

class RecordsServicePricing(models.Model):
    """Service pricing configuration"""
    _name = 'records.service.pricing'
    _description = 'Records Service Pricing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Pricing Name', required=True, tracking=True)
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('scanning', 'Scanning'),
        ('delivery', 'Delivery'),
        ('other', 'Other')
    ], string='Service Type', required=True, tracking=True)
    
    # Pricing model
    pricing_model = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('tiered', 'Tiered Pricing'),
        ('volume', 'Volume Based')
    ], string='Pricing Model', default='fixed', required=True, tracking=True)
    
    # Basic pricing
    base_price = fields.Monetary(string='Base Price', tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    # Validity
    valid_from = fields.Date(string='Valid From', default=fields.Date.today, tracking=True)
    valid_to = fields.Date(string='Valid To', tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Pricing breaks
    pricing_break_ids = fields.One2many('records.service.pricing.break', 'pricing_id', string='Pricing Breaks')

class RecordsServicePricingBreak(models.Model):
    """Pricing breaks for tiered pricing"""
    _name = 'records.service.pricing.break'
    _description = 'Records Service Pricing Break'

    pricing_id = fields.Many2one('records.service.pricing', string='Pricing', required=True, ondelete='cascade')
    
    # Quantity ranges
    quantity_from = fields.Float(string='Quantity From', default=0.0)
    quantity_to = fields.Float(string='Quantity To')
    
    # Pricing
    unit_price = fields.Monetary(string='Unit Price')
    currency_id = fields.Many2one('res.currency', related='pricing_id.currency_id')
    
    # Discounts
    discount_percentage = fields.Float(string='Discount %', default=0.0)

class RecordsProduct(models.Model):
    """Records management specific products"""
    _name = 'records.product'
    _description = 'Records Product'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Product Name', required=True, tracking=True)
    code = fields.Char(string='Product Code', tracking=True)
    description = fields.Text(string='Description')
    
    # Product type
    product_type = fields.Selection([
        ('box', 'Storage Box'),
        ('service', 'Service'),
        ('material', 'Material'),
        ('equipment', 'Equipment')
    ], string='Product Type', required=True, tracking=True)
    
    # Pricing
    list_price = fields.Monetary(string='List Price', tracking=True)
    cost_price = fields.Monetary(string='Cost Price', tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    # Status
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Related product if any
    product_id = fields.Many2one('product.product', string='Related Odoo Product')

class RecordsBillingAutomation(models.Model):
    """Automation rules for billing"""
    _name = 'records.billing.automation'
    _description = 'Records Billing Automation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Automation Rule Name', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Trigger conditions
    trigger_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('box_added', 'Box Added'),
        ('service_completed', 'Service Completed'),
        ('manual', 'Manual Only')
    ], string='Trigger Type', required=True, tracking=True)
    
    # Rule configuration
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('scanning', 'Scanning'),
        ('delivery', 'Delivery'),
        ('other', 'Other')
    ], string='Service Type', tracking=True)
    
    # Auto-pricing
    pricing_id = fields.Many2one('records.service.pricing', string='Default Pricing')
    
    # Conditions
    apply_to_all_customers = fields.Boolean(string='Apply to All Customers', default=True)
    customer_ids = fields.Many2many('res.partner', string='Specific Customers')
    
    # Execution
    last_execution = fields.Datetime(string='Last Execution', readonly=True)
    next_execution = fields.Datetime(string='Next Execution', readonly=True)
