# -*- coding: utf-8 -*-
"""
Records Billing Management Module

Manages billing records, linking services to customer invoices. This model
handles the entire billing lifecycle from draft to paid, integrating with
Odoo's accounting system.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class RecordsBilling(models.Model):
    _name = 'records.billing'
    _description = 'Records Management Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_date desc, id desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Billing Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(string='Active', default=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        tracking=True,
        help="Department associated with this billing record."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # BILLING DETAILS & DATES
    # ============================================================================
    invoice_date = fields.Date(string='Invoice Date', default=fields.Date.today, required=True)
    due_date = fields.Date(string='Due Date')
    period_start = fields.Date(string='Billing Period Start')
    period_end = fields.Date(string='Billing Period End')
    billing_type = fields.Selection([
        ('storage', 'Storage'),
        ('service', 'Service Request'),
        ('destruction', 'Destruction'),
        ('one_time', 'One-Time Fee')
    ], string='Billing Type', required=True, default='storage')

    # ============================================================================
    # FINANCIALS
    # ============================================================================
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Currency',
        readonly=True
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amounts',
        store=True
    )
    tax_amount = fields.Monetary(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_amounts',
        store=True
    )
    paid_amount = fields.Monetary(
        string='Paid Amount',
        compute='_compute_payment_status',
        store=True
    )
    balance_due = fields.Monetary(
        string='Balance Due',
        compute='_compute_payment_status',
        store=True
    )
    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid')
    ], string='Payment Status', compute='_compute_payment_status', store=True)

    # ============================================================================
    # RELATIONSHIPS & NOTES
    # ============================================================================
    invoice_id = fields.Many2one(
        'account.move',
        string='Related Invoice',
        readonly=True,
        copy=False
    )
    service_ids = fields.One2many(
        'records.billing.service',
        'billing_id',
        string='Billed Services'
    )
    notes = fields.Text(string='Notes')
    internal_notes = fields.Text(string='Internal Notes')

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('service_ids.price_subtotal', 'service_ids.price_tax', 'service_ids.price_total')
    def _compute_amounts(self):
        """Compute subtotal, tax, and total from service lines."""
        for record in self:
            record.subtotal = sum(record.service_ids.mapped('price_subtotal'))
            record.tax_amount = sum(record.service_ids.mapped('price_tax'))
            record.total_amount = sum(record.service_ids.mapped('price_total'))

    @api.depends('invoice_id.payment_state', 'total_amount')
    def _compute_payment_status(self):
        """Compute payment status and amounts based on the related invoice."""
        for record in self:
            if record.invoice_id and record.invoice_id.payment_state in ('paid', 'in_payment'):
                paid_amount = record.total_amount - record.invoice_id.amount_residual
                record.paid_amount = paid_amount
                record.balance_due = record.invoice_id.amount_residual
                if record.invoice_id.payment_state == 'paid':
                    record.payment_status = 'paid'
                    if record.state == 'invoiced':
                        record.state = 'paid'
                else:
                    record.payment_status = 'partial' if paid_amount > 0 else 'not_paid'
            else:
                record.paid_amount = 0.0
                record.balance_due = record.total_amount
                record.payment_status = 'not_paid'

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the billing record."""
        self.ensure_one()
        if not self.service_ids:
            raise UserError(_("You cannot confirm a billing record with no service lines."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Billing record confirmed."))

    def action_create_invoice(self):
        """Create a customer invoice from the billing record."""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed billing records can be invoiced."))

        invoice_lines = []
        for service in self.service_ids:
            invoice_lines.append((0, 0, {
                'product_id': service.product_id.id,
                'name': service.description,
                'quantity': service.quantity,
                'price_unit': service.price_unit,
                'tax_ids': [(6, 0, service.tax_ids.ids)],
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': self.invoice_date,
            'invoice_line_ids': invoice_lines,
        })
        self.write({'invoice_id': invoice.id, 'state': 'invoiced'})
        self.message_post(body=_("Invoice created: %s", invoice.name))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        """Cancel the billing record."""
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Billing record cancelled."))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        """Validate billing period dates."""
        for record in self:
            if record.period_start and record.period_end:
                if record.period_start > record.period_end:
                    raise ValidationError(_("Billing period start date cannot be after end date."))

    @api.constrains('due_date', 'invoice_date')
    def _check_due_date(self):
        """Validate due date is not before invoice date."""
        for record in self:
            if record.due_date and record.invoice_date:
                if record.due_date < record.invoice_date:
                    raise ValidationError(_("Due date cannot be before invoice date."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Assign a sequence number on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.billing') or _('New')
        return super().create(vals_list)
