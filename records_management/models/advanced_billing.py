# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class RecordsCustomerBillingProfile(models.Model):
    """Customer-specific billing profiles with flexible cycles and timing"""
    _name = 'records.customer.billing.profile'
    _description = 'Customer Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'partner_id, name'

    # Core identification
    name = fields.Char(string='Profile Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True, tracking=True)
    
    # Billing timing configuration
    storage_billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
        ('prepaid', 'Prepaid (Custom Period)')
    ], string='Storage Billing Cycle')
    
    service_billing_cycle = fields.Selection([
        ('monthly', 'Monthly in Arrears'),
        ('weekly', 'Weekly in Arrears'),
        ('immediate', 'Immediate Upon Completion')
    ], string='Service Billing Cycle')
    
    # Storage billing configuration
    storage_bill_in_advance = fields.Boolean(string='Bill Storage in Advance', default=True, tracking=True,
                                            help="When enabled, storage fees are billed forward. When disabled, billed in arrears.")
    
    storage_advance_months = fields.Integer(string='Storage Advance Months', default=1, tracking=True,
                                           help="Number of months to bill in advance for storage")
    
    # Billing timing
    billing_day = fields.Integer(string='Billing Day of Month', default=1, tracking=True,
                                help="Day of the month when invoices are generated")
    invoice_due_days = fields.Integer(string='Invoice Due Days', default=30, tracking=True)
    
    # Prepaid storage configuration
    prepaid_enabled = fields.Boolean(string='Enable Prepaid Storage', tracking=True)
    prepaid_months = fields.Integer(string='Prepaid Months', default=12, tracking=True)
    prepaid_discount_percent = fields.Float(string='Prepaid Discount %', tracking=True)
    prepaid_balance = fields.Float(string='Prepaid Balance', compute='_compute_prepaid_balance', store=True)
    
    # Auto-billing settings
    auto_generate_storage_invoices = fields.Boolean(string='Auto Generate Storage Invoices', default=True, tracking=True)
    auto_generate_service_invoices = fields.Boolean(string='Auto Generate Service Invoices', default=True, tracking=True)
    auto_send_invoices = fields.Boolean(string='Auto Send Invoices', default=False, tracking=True)
    
    # Payment terms
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', tracking=True)
    
    # Billing contacts
    billing_contact_ids = fields.One2many('records.billing.contact', 'billing_profile_id', string='Billing Contacts')
    
    # Company
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Service tracking fields (missing from views
    box_id = fields.Many2one(
        'records.box',
        string='Records Box',
        help='Associated records box for billing')
    retrieval_work_order_id = fields.Many2one(
        'document.retrieval.work.order',
        string='Retrieval Work Order',
        help='Associated retrieval work order')
    service_date = fields.Date(
        string='Service Date',
        help='Date when the service was provided')
    shredding_work_order_id = fields.Many2one(
        'work.order.shredding',
        string='Shredding Work Order',
        help='Associated shredding work order')
    unit_price = fields.Float(
        string='Unit Price',
        digits='Product Price',
        help='Unit price for billing calculation'
)
    @api.depends('name', 'partner_id.name')
    def _compute_display_name(self):
        for record in self:
            partner_name = record.partner_id.name if record.partner_id else 'No Customer'
            record.display_name = f"{record.name} - {partner_name}"
    
    @api.depends('prepaid_enabled')  # Will be enhanced with actual balance calculation
    def _compute_prepaid_balance(self:
        for record in self:
            # TODO: Calculate actual prepaid balance from payments and usage
            record.prepaid_balance = 0.0
    
    def get_next_billing_date(self, billing_type='storage', reference_date=None:
        """Calculate next billing date based on billing cycle"""
        self.ensure_one()
        if not reference_date:
            reference_date = fields.Date.today()
        
        if billing_type == 'storage':
            cycle = self.storage_billing_cycle
        else:
            cycle = self.service_billing_cycle
        
        # Start from the billing day of current month
        next_date = reference_date.replace(day=self.billing_day
        
        # If we've passed this month's billing day, move to next cycle
        if reference_date.day >= self.billing_day:
            if cycle == 'monthly':
                next_date = next_date + relativedelta(months=1
            elif cycle == 'quarterly':
                next_date = next_date + relativedelta(months=3)
            elif cycle == 'semi_annual':
                next_date = next_date + relativedelta(months=6)
            elif cycle == 'annual':
                next_date = next_date + relativedelta(months=12)
        
        return next_date
    
    def get_billing_period_dates(self, billing_type='storage', invoice_date=None):
        """Get the period dates for billing"""
        self.ensure_one()
        if not invoice_date:
            invoice_date = fields.Date.today()
        
        if billing_type == 'storage' and self.storage_bill_in_advance:
            # Storage billed in advance
            if self.storage_billing_cycle == 'monthly':
                start_date = invoice_date.replace(day=1
                end_date = start_date + relativedelta(months=self.storage_advance_months) - timedelta(days=1)
            elif self.storage_billing_cycle == 'quarterly':
                start_date = invoice_date.replace(day=1)
                end_date = start_date + relativedelta(months=3) - timedelta(days=1)
            else:
                start_date = invoice_date.replace(day=1)
                end_date = start_date + relativedelta(months=1) - timedelta(days=1)
        else:
            # Services billed in arrears
            end_date = invoice_date.replace(day=1 - timedelta(days=1)  # Last day of previous month
            start_date = end_date.replace(day=1  # First day of previous month
        
        return start_date, end_date

class RecordsBillingContact(models.Model):
    """Billing contacts for customer profiles"""
    _name = 'records.billing.contact'
    _description = 'Billing Contact'
    _rec_name = 'name'
    _order = 'sequence, name'

    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    billing_profile_id = fields.Many2one('records.customer.billing.profile', string='Billing Profile', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Contact types
    receive_storage_invoices = fields.Boolean(string='Receive Storage Invoices', default=True)
    receive_service_invoices = fields.Boolean(string='Receive Service Invoices', default=True)
    receive_statements = fields.Boolean(string='Receive Statements', default=True)
    primary_contact = fields.Boolean(string='Primary Contact')
    

class RecordsAdvancedBillingPeriod(models.Model):
    """Enhanced billing periods supporting dual billing timing"""
    _name = 'records.advanced.billing.period'
    _description = 'Advanced Billing Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_date desc'
    _rec_name = 'display_name'

    # Core identification
    
    # Billing type and timing
    billing_type = fields.Selection([
        ('storage', 'Storage Billing',
        ('service', 'Service Billing'),
        ('combined', 'Combined Billing')
    ), string='Billing Type')
    
    # Period dates (what's being billed for
    period_start_date = fields.Date(string='Period Start Date', required=True, tracking=True)
    period_end_date = fields.Date(string='Period End Date', required=True, tracking=True)
    
    # Billing direction
    billing_direction = fields.Selection([
        ('advance', 'In Advance',
        ('arrears', 'In Arrears')
    ), string='Billing Direction')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft',
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ), string='State', default='draft', tracking=True)
    
    # Financial information
    storage_amount = fields.Monetary(string='Storage Amount', tracking=True)
    service_amount = fields.Monetary(string='Service Amount', tracking=True)
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one('res.currency', related='billing_profile_id.company_id.currency_id')
    
    # Billing lines
    storage_line_ids = fields.One2many('records.billing.line', 'billing_period_id', 
                                      domain=[('line_type', '=', 'storage'], string='Storage Lines')
    service_line_ids = fields.One2many('records.billing.line', 'billing_period_id', 
                                      domain=[('line_type', '=', 'service')], string='Service Lines')
    
    # Invoice reference
    invoice_id = fields.Many2one('account.move', string='Invoice', tracking=True)
    
    # Company
    
    @api.depends('name', 'partner_id.name', 'billing_type'
    def _compute_display_name(self):
        for record in self:
            partner_name = record.partner_id.name if record.partner_id else 'No Customer'
            record.display_name = f"{record.name} - {partner_name} ({record.billing_type})"
    
    @api.depends('billing_type', 'invoice_date', 'period_start_date')
    def _compute_billing_direction(self):
        for record in self:
            if record.billing_type == 'storage':
                record.billing_direction = 'advance' if record.billing_profile_id.storage_bill_in_advance else 'arrears'
            else:
                record.billing_direction = 'arrears'
    
    @api.depends('storage_amount', 'service_amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.storage_amount + record.service_amount
    
    def action_generate_storage_lines(self):
        """Generate storage billing lines for the period"""
        self.ensure_one()
        if self.billing_type not in ['storage', 'combined']:
            raise UserError(_('Storage lines can only be generated for storage or combined billing.'))
        
        # Clear existing storage lines
        self.storage_line_ids.unlink(
        
        # Get storage items (boxes for this customer during the period
        box_domain = [
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ['stored', 'active'])]
        ]
        
        # For advance billing, we bill based on current storage
        # For arrears billing, we bill based on storage during the period
        if self.billing_direction == 'advance':
            # Current storage as of invoice date
            boxes = self.env['records.box'].search(box_domain
        else:
            # Storage during the period (more complex - would need storage history
            boxes = self.env['records.box'].search(box_domain)
        
        # Create billing lines for each box
        storage_lines = []
        for box in boxes:
            # Get storage rate for this box type/customer
            rate = self._get_storage_rate(box
            
            storage_lines.append({
                'billing_period_id': self.id,
                'line_type': 'storage',
                'description': f'Storage - {box.name} ({box.document_type_id.name if box.document_type_id else "Standard Box"})',
                'box_id': box.id,
                'quantity': 1.0,
                'unit_price': rate,
                'period_start_date': self.period_start_date,
                'period_end_date': self.period_end_date,
            })
        
        if storage_lines:
            self.env['records.billing.line'].create(storage_lines)
        
        # Update storage amount
        self.storage_amount = sum(line['quantity'] * line['unit_price'] for line in storage_lines
    
    def action_generate_service_lines(self):
        """Generate service billing lines for the period"""
        self.ensure_one()
        if self.billing_type not in ['service', 'combined']:
            raise UserError(_('Service lines can only be generated for service or combined billing.'))
        
        # Clear existing service lines
        self.service_line_ids.unlink(
        
        # Get completed work orders during the period
        work_order_domain = [
            ('partner_id', '=', self.partner_id.id,
            ('state', '=', 'completed'),]
            ('actual_completion_time', '>=', fields.Datetime.combine(self.period_start_date, datetime.min.time())),
            ('actual_completion_time', '<=', fields.Datetime.combine(self.period_end_date, datetime.max.time()))
        ]
        
        # Check both retrieval and shredding work orders
        retrieval_orders = self.env['document.retrieval.work.order'].search(work_order_domain
        shredding_orders = self.env['work.order.shredding'].search(work_order_domain)
        
        service_lines = []
        
        # Process retrieval work orders
        for order in retrieval_orders:
            service_lines.append({
                'billing_period_id': self.id,
                'line_type': 'service',
                'description': f'Document Retrieval - {order.name}',
                'retrieval_work_order_id': order.id,
                'quantity': 1.0,
                'unit_price': order.total_cost,
                'service_date': order.actual_completion_time.date(,
            })
        
        # Process shredding work orders
        for order in shredding_orders:
            service_lines.append({
                'billing_period_id': self.id,
                'line_type': 'service',
                'description': f'Shredding Service - {order.name} ({order.shredding_workflow}',
                'shredding_work_order_id': order.id,
                'quantity': 1.0,
                'unit_price': order.total_cost,
                'service_date': order.actual_completion_time.date(),
            })
        
        if service_lines:
            self.env['records.billing.line'].create(service_lines)
        
        # Update service amount
        self.service_amount = sum(line['quantity'] * line['unit_price'] for line in service_lines
    
    def _get_storage_rate(self, box):
        """Get storage rate for a specific box"""
        # This would integrate with your storage pricing model
        # For now, return a default rate
        return 10.0  # Default $10 per box per month
    
    def action_generate_invoice(self:
        """Generate invoice from billing period"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_('Billing period must be confirmed before generating invoice.'))
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.invoice_date,
            'invoice_line_ids': [],
        }
        
        # Add storage lines
        for line in self.storage_line_ids:
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'name': line.description,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'account_id': self._get_storage_account(.id,
            }))
        
        # Add service lines
        for line in self.service_line_ids:
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'name': line.description,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'account_id': self._get_service_account(.id,
            }))
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced'
        })
        
        return {
            'name': _('Generated Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }
    
    def _get_storage_account(self):
        """Get account for storage revenue"""
        # Return default storage revenue account
        return self.env['account.account'].search([('code', '=', '400100'], limit=1) or \
               self.env['account.account'].search([('internal_type', '=', 'receivable')], limit=1)
    
    def _get_service_account(self):
        """Get account for service revenue"""
        # Return default service revenue account
        return self.env['account.account'].search([('code', '=', '400200'], limit=1) or \
               self.env['account.account'].search([('internal_type', '=', 'receivable')], limit=1)
