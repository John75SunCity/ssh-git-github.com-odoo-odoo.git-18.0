"""
Billing Period Model

Manages billing periods for monthly storage fee invoicing.
Each period represents a billing cycle (typically one calendar month).

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BillingPeriod(models.Model):
    _name = "billing.period"
    _description = "Billing Period"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(required=True, tracking=True)
    start_date = fields.Date(required=True, tracking=True)
    end_date = fields.Date(required=True, tracking=True)
    active = fields.Boolean(default=True)
    note = fields.Text()
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        readonly=True
    )
    
    # ============================================================================
    # STATE & WORKFLOW
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('processing', 'Processing'),
        ('invoiced', 'Invoiced'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    invoice_date = fields.Date(
        string='Invoice Date',
        help="Date when invoices for this period should be generated (typically 1st of next month)"
    )
    
    # ============================================================================
    # INVOICE TRACKING
    # ============================================================================
    invoice_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='billing_period_id',
        string='Generated Invoices'
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count'
    )
    total_invoiced = fields.Monetary(
        string='Total Invoiced',
        currency_field='currency_id',
        compute='_compute_invoice_totals'
    )
    
    # ============================================================================
    # BILLING STATISTICS
    # ============================================================================
    containers_billed = fields.Integer(
        string='Containers Billed',
        compute='_compute_billing_stats',
        help='Total number of containers included in this billing period'
    )
    new_containers = fields.Integer(
        string='New Containers (Setup Fees)',
        compute='_compute_billing_stats',
        help='Number of new containers charged setup fees in this period'
    )
    customers_billed = fields.Integer(
        string='Customers Billed',
        compute='_compute_billing_stats'
    )
    
    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('date_check', 'CHECK(end_date >= start_date)', 'End date must be after start date.'),
        ('name_company_uniq', 'UNIQUE(name, company_id)', 'Billing period name must be unique per company.'),
    ]
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for period in self:
            period.invoice_count = len(period.invoice_ids)
    
    @api.depends('invoice_ids', 'invoice_ids.amount_total')
    def _compute_invoice_totals(self):
        for period in self:
            period.total_invoiced = sum(period.invoice_ids.mapped('amount_total'))
    
    def _compute_billing_stats(self):
        """Compute billing statistics for the period"""
        for period in self:
            # Count containers billed in this period
            containers = self.env['records.container'].search([
                ('last_storage_billing_period_id', '=', period.id)
            ])
            period.containers_billed = len(containers)
            
            # Count new containers (setup fee charged in this period)
            new_containers = self.env['records.container'].search([
                ('setup_fee_date', '>=', period.start_date),
                ('setup_fee_date', '<=', period.end_date),
            ])
            period.new_containers = len(new_containers)
            
            # Count unique customers
            period.customers_billed = len(containers.mapped('partner_id'))
    
    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for period in self:
            if period.end_date < period.start_date:
                raise ValidationError(_('End date must be after start date.'))
    
    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_open(self):
        """Open the billing period for invoicing"""
        for period in self:
            if period.state != 'draft':
                raise UserError(_('Only draft periods can be opened.'))
            period.state = 'open'
    
    def action_close(self):
        """Close the billing period"""
        for period in self:
            period.state = 'closed'
    
    def action_view_invoices(self):
        """View invoices generated for this billing period"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Period Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('billing_period_id', '=', self.id)],
            'context': {'default_billing_period_id': self.id},
        }
    
    def action_generate_invoices(self):
        """Open wizard to generate monthly storage invoices"""
        self.ensure_one()
        if self.state not in ('open', 'processing'):
            raise UserError(_('Period must be open to generate invoices.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Monthly Storage Invoices'),
            'res_model': 'monthly.storage.billing.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_billing_period_id': self.id,
                'default_start_date': self.start_date,
                'default_end_date': self.end_date,
            },
        }
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    @api.model
    def get_or_create_current_period(self):
        """Get or create billing period for current month"""
        today = fields.Date.today()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1)) - relativedelta(days=1)
        
        period = self.search([
            ('start_date', '=', start_of_month),
            ('end_date', '=', end_of_month),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        
        if not period:
            period = self.create({
                'name': start_of_month.strftime('%B %Y'),
                'start_date': start_of_month,
                'end_date': end_of_month,
                'invoice_date': end_of_month + relativedelta(days=1),
                'state': 'open',
            })
        
        return period
    
    @api.model
    def create_next_period(self):
        """Create billing period for next month"""
        today = fields.Date.today()
        start_of_next_month = (today.replace(day=1) + relativedelta(months=1))
        end_of_next_month = (start_of_next_month + relativedelta(months=1)) - relativedelta(days=1)
        
        existing = self.search([
            ('start_date', '=', start_of_next_month),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        
        if existing:
            return existing
        
        return self.create({
            'name': start_of_next_month.strftime('%B %Y'),
            'start_date': start_of_next_month,
            'end_date': end_of_next_month,
            'invoice_date': end_of_next_month + relativedelta(days=1),
            'state': 'draft',
        })
