# -*- coding: utf-8 -*-
"""
Advanced Billing Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AdvancedBilling(models.Model):
    """
    Advanced Billing Management
    Manages complex billing scenarios for records management services
    """
    
    _name = 'advanced.billing'
    _description = 'Advanced Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'billing_date desc, name'
    _rec_name = "name"
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Billing Reference', required=True, tracking=True,
                       default=lambda self: _('New'))
    description = fields.Text(string='Description', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Billing Manager', 
                             default=lambda self: self.env.user, tracking=True)
    
    # ==========================================
    # BILLING DETAILS
    # ==========================================
    partner_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True)
    billing_date = fields.Date(string='Billing Date', 
                              default=fields.Date.today, tracking=True)
    
    billing_period_start = fields.Date(string='Period Start', tracking=True)
    billing_period_end = fields.Date(string='Period End', tracking=True)
    billing_period_id = fields.Many2one('records.advanced.billing.period', 
                                       string='Billing Period', tracking=True)
    
    # ==========================================
    # BILLING TYPE
    # ==========================================
    billing_type = fields.Selection([
        ('monthly', 'Monthly Storage'),
        ('quarterly', 'Quarterly Storage'), 
        ('annual', 'Annual Storage'),
        ('destruction', 'Destruction Services'),
        ('pickup', 'Pickup Services'),
        ('one_time', 'One-Time Service')
    ], string='Billing Type', required=True, tracking=True)
    
    # ==========================================
    # AMOUNTS
    # ==========================================
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    
    subtotal = fields.Monetary(string='Subtotal', currency_field='currency_id',
                              compute='_compute_amounts', store=True)
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='currency_id',
                                compute='_compute_amounts', store=True)
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id',
                                  compute='_compute_amounts', store=True)
    
    # ==========================================
    # BILLING LINES
    # ==========================================
    billing_line_ids = fields.One2many('advanced.billing.line', 'billing_id',
                                       string='Billing Lines')
    
    # ==========================================
    # INVOICE INTEGRATION
    # ==========================================
    invoice_id = fields.Many2one('account.move', string='Generated Invoice', 
                                readonly=True, tracking=True)
    invoice_created = fields.Boolean(string='Invoice Created', 
                                    compute='_compute_invoice_created', store=True)
    
    # ==========================================
    # STATUS
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    # ==========================================
    # COMPUTE METHODS
    # ==========================================
    @api.depends('billing_line_ids', 'billing_line_ids.line_total')
    def _compute_amounts(self):
        for record in self:
            record.subtotal = sum(record.billing_line_ids.mapped('line_total'))
            # Simple tax calculation - 10% default
            record.tax_amount = record.subtotal * 0.10
            record.total_amount = record.subtotal + record.tax_amount
    
    @api.depends('invoice_id')
    def _compute_invoice_created(self):
        for record in self:
            record.invoice_created = bool(record.invoice_id)
    
    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_confirm(self):
        """Confirm billing"""
        self.ensure_one()
        if self.state != 'draft':
            return
        
        self.write({'state': 'confirmed'})
        self.message_post(body=_('Billing confirmed'))
    
    def action_create_invoice(self):
        """Create invoice from billing"""
        self.ensure_one()
        if self.state != 'confirmed' or self.invoice_id:
            return
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'ref': self.name,
            'invoice_line_ids': []
        }
        
        # Add invoice lines from billing lines
        for line in self.billing_line_ids:
            invoice_line_vals = {
                'name': line.description,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'account_id': line.product_id.property_account_income_id.id or 
                             self.env.company.account_default_income_account_id.id
            }
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        self.write({
            'state': 'invoiced',
            'invoice_id': invoice.id
        })
        self.message_post(body=_('Invoice created: %s') % invoice.name)
    
    def action_cancel(self):
        """Cancel billing"""
        self.ensure_one()
        if self.state in ['paid']:
            return
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Billing cancelled'))
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('advanced.billing') or _('New')
        return super().create(vals_list)


class AdvancedBillingLine(models.Model):
    """Billing line items"""
    
    _name = 'advanced.billing.line'
    _description = 'Advanced Billing Line'
    
    billing_id = fields.Many2one('advanced.billing', string='Billing', 
                                required=True, ondelete='cascade')
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text(string='Description', required=True)
    
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
    
    line_total = fields.Float(string='Line Total', 
                             compute='_compute_line_total', store=True)
    
    # Service references
    service_reference = fields.Char(string='Service Reference')
    box_count = fields.Integer(string='Box Count')
    
    @api.depends('quantity', 'unit_price')
    def _compute_line_total(self):
        for line in self:
            line.line_total = line.quantity * line.unit_price


class RecordsAdvancedBillingPeriod(models.Model):
    """
    Advanced Billing Period - Manage billing cycles and periods
    """

    _name = "records.advanced.billing.period"
    _description = "Advanced Billing Period"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "start_date desc"

    # Core fields
    name = fields.Char(string="Period Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)

    # Period definition
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    billing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
        ('custom', 'Custom')
    ], string='Billing Frequency', default='monthly', required=True, tracking=True)

    # Period status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)

    # Billing configuration
    auto_generate_invoices = fields.Boolean(string='Auto Generate Invoices', default=True)
    cutoff_day = fields.Integer(string='Cutoff Day', default=1, 
                               help='Day of month for billing cutoff')
    
    # Relationships
    billing_ids = fields.One2many('advanced.billing', 'billing_period_id', string='Billing Records')
    
    # Computed fields
    total_billing_amount = fields.Float(string='Total Billing Amount', 
                                       compute='_compute_total_billing_amount')
    billing_count = fields.Integer(string='Billing Count', compute='_compute_billing_count')

    @api.depends('billing_ids.total_amount')
    def _compute_total_billing_amount(self):
        """Calculate total billing for this period"""
        for record in self:
            record.total_billing_amount = sum(record.billing_ids.mapped('total_amount'))

    @api.depends('billing_ids')
    def _compute_billing_count(self):
        """Count billing records for this period"""
        for record in self:
            record.billing_count = len(record.billing_ids)

    def action_activate(self):
        """Activate this billing period"""
        self.ensure_one()
        self.write({'state': 'active'})
        self.message_post(body=_('Billing period activated'))

    def action_close(self):
        """Close this billing period"""
        self.ensure_one()
        self.write({'state': 'closed'})
        self.message_post(body=_('Billing period closed'))

    def action_generate_billing(self):
        """Generate billing records for this period"""
        self.ensure_one()
        # Implementation for generating billing records
        self.message_post(body=_('Billing generation started'))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate period dates"""
        for record in self:
            if record.start_date >= record.end_date:
                raise ValidationError(_('Start date must be before end date'))
