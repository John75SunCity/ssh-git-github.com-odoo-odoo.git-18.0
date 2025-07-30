# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Billing(models.Model):
    _name = "records.billing"
    _description = "General Billing Model"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "invoice_date desc"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Billing Reference', required=True, tracking=True,
                    default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Billing Manager',
                            default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True)

    # ==========================================
    # BILLING DETAILS
    # ==========================================
    invoice_date = fields.Date(string='Invoice Date', default=fields.Date.today, required=True, tracking=True)
    due_date = fields.Date(string='Due Date', tracking=True)
    period_start = fields.Date(string='Billing Period Start', tracking=True)
    period_end = fields.Date(string='Billing Period End', tracking=True)

    # ==========================================
    # AMOUNTS
    # ==========================================
    subtotal = fields.Float(string='Subtotal', tracking=True)
    tax_amount = fields.Float(string='Tax Amount', tracking=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True, tracking=True)
    paid_amount = fields.Float(string='Paid Amount', tracking=True)
    balance_due = fields.Float(string='Balance Due', compute='_compute_balance_due', store=True)

    # ==========================================
    # STATUS AND WORKFLOW
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    billing_type = fields.Selection([
        ('monthly', 'Monthly Storage'),
        ('service', 'Service Billing'),
        ('destruction', 'Destruction Service'),
        ('pickup', 'Pickup Service'),
        ('other', 'Other')
    ], string='Billing Type', default='monthly', required=True, tracking=True)

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    invoice_id = fields.Many2one('account.move', string='Related Invoice', tracking=True)
    service_ids = fields.One2many('records.billing.service', 'billing_id', string='Billing Services')

    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string='Notes', tracking=True)
    internal_notes = fields.Text(string='Internal Notes')
    discount_amount = fields.Float(string="Discount Amount", default=0.0, help="Discount amount")
    payment_status = fields.Char(string="Payment Status", help="Payment status")

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('subtotal', 'tax_amount')
    def _compute_total_amount(self):
        """Calculate total amount including tax"""
        for record in self:
            record.total_amount = record.subtotal + record.tax_amount

    @api.depends('total_amount', 'paid_amount')
    def _compute_balance_due(self):
        """Calculate outstanding balance"""
        for record in self:
            record.balance_due = record.total_amount - record.paid_amount

    # ==========================================
    # ONCHANGE METHODS
    # ==========================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update department domain when customer changes"""
        if self.partner_id:
            return {
                'domain': {
                    'department_id': [('customer_id', '=', self.partner_id.id)]
                }
            }

    @api.onchange('period_start', 'period_end')
    def _onchange_billing_period(self):
        """Validate billing period dates"""
        if self.period_start and self.period_end and self.period_start > self.period_end:
            return {
                'warning': {
                    'title': _('Invalid Period'),
                    'message': _('Period start date cannot be after period end date.')
                }
            }

    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    def action_send_invoice(self):
        """Send invoice to customer"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Only draft invoices can be sent'))
        self.write({'state': 'sent'})
        self.message_post(body=_('Invoice sent to customer'))

    def action_mark_paid(self):
        """Mark invoice as paid"""
        self.ensure_one()
        if self.state not in ['sent', 'partial', 'overdue']:
            raise ValidationError(_('Cannot mark this invoice as paid'))
        self.write({
            'state': 'paid',
            'paid_amount': self.total_amount
        })
        self.message_post(body=_('Invoice marked as paid'))

    def action_cancel(self):
        """Cancel the billing record"""
        self.ensure_one()
        if self.state == 'paid':
            raise ValidationError(_('Cannot cancel paid invoices'))
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Billing record cancelled'))

    # ==========================================
    # CREATE/WRITE METHODS
    # ==========================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.billing') or _('New')
        return super().create(vals_list)

    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains('subtotal', 'tax_amount', 'total_amount')
    def _check_amounts(self):
        """Validate monetary amounts"""
        for record in self:
            if record.subtotal < 0:
                raise ValidationError(_('Subtotal cannot be negative'))
            if record.tax_amount < 0:
                raise ValidationError(_('Tax amount cannot be negative'))
            if record.total_amount < 0:
                raise ValidationError(_('Total amount cannot be negative'))

    @api.constrains('period_start', 'period_end')
    def _check_billing_period(self):
        """Validate billing period"""
        for record in self:
            if record.period_start and record.period_end:
                if record.period_start > record.period_end:
                    raise ValidationError(_('Billing period start cannot be after period end'))
