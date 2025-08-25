# -*- coding: utf-8 -*-
"""
Advanced Billing Model

Manages complex billing scenarios for Records Management services, including
service-based, storage-based, and combined billing with prepaid options.
This model integrates with work orders and generates customer invoices.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AdvancedBilling(models.Model):
    """
    Advanced Billing Management

    Handles the creation, confirmation, and invoicing of complex billing
    records for various records management services.
    """
    _name = 'advanced.billing'
    _description = 'Advanced Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Billing Reference',
        required=True,
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: _('New')
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Set to false to archive this billing record."
    )

    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        index=True
    )
    billing_period_id = fields.Many2one(
        'billing.period',
        string='Billing Period',
        help="The billing period this record applies to."
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Generated Invoice',
        readonly=True,
        copy=False
    )

    payment_terms = fields.Selection([
        ('immediate', 'Immediate'),
        ('15_days', '15 Days'),
        ('30_days', '30 Days'),
        ('45_days', '45 Days'),
        ('60_days', '60 Days'),
    ], string='Payment Terms', default='30_days')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Line relationships
    line_ids = fields.One2many(
        'advanced.billing.line',
        'billing_id',
        string='Billing Lines'
    )
    service_line_ids = fields.One2many(
        'advanced.billing.service.line',
        'billing_id',
        string='Service Lines'
    )
    storage_line_ids = fields.One2many(
        'advanced.billing.storage.line',
        'billing_id',
        string='Storage Lines'
    )

    # Financial fields
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )
    service_amount = fields.Monetary(
        string='Service Amount',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )
    storage_amount = fields.Monetary(
        string='Storage Amount',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )

    # ============================================================================
    # BILLING CONFIGURATION FIELDS
    # ============================================================================
    billing_type = fields.Selection([
        ('service', 'Service Billing'),
        ('storage', 'Storage Billing'),
        ('combined', 'Combined Billing'),
    ], string='Billing Type', default='combined')

    billing_day = fields.Integer(
        string='Billing Day',
        default=1,
        help='Day of the month for recurring billing generation.'
    )

    # Dates
    invoice_date = fields.Date(string='Invoice Date')
    period_start_date = fields.Date(string='Period Start Date')
    period_end_date = fields.Date(string='Period End Date')

    # Contact information
    email = fields.Char(string='Email', related='partner_id.email', readonly=False)
    phone = fields.Char(string='Phone', related='partner_id.phone', readonly=False)
    primary_contact = fields.Char(string='Primary Contact')
    billing_profile_id = fields.Many2one('advanced.billing.profile', string='Billing Profile')

    # Prepaid configuration
    prepaid_enabled = fields.Boolean(string='Prepaid Enabled')
    prepaid_balance = fields.Monetary(string='Prepaid Balance', currency_field='currency_id')
    prepaid_discount_percent = fields.Float(string='Prepaid Discount %')
    prepaid_months = fields.Integer(string='Prepaid Months')

    # Automation settings
    auto_generate_service_invoices = fields.Boolean(string='Auto Generate Service Invoices')
    auto_generate_storage_invoices = fields.Boolean(string='Auto Generate Storage Invoices')
    auto_send_invoices = fields.Boolean(string='Auto Send Invoices')

    # Billing preferences
    receive_service_invoices = fields.Boolean(string='Receive Service Invoices', default=True)
    receive_statements = fields.Boolean(string='Receive Statements', default=True)
    receive_storage_invoices = fields.Boolean(string='Receive Storage Invoices', default=True)

    # Work order relationships
    retrieval_work_order_id = fields.Many2one(
        'document.retrieval.work.order',
        string='Retrieval Work Order'
    )
    shredding_work_order_id = fields.Many2one(
        'shredding.service',
        string='Shredding Work Order'
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('line_ids.price_total', 'service_line_ids.subtotal', 'storage_line_ids.subtotal')
    def _compute_amounts(self):
        """Calculate total, service, and storage amounts from all billing lines."""
        for record in self:
            service_total = sum(record.service_line_ids.mapped('subtotal'))
            storage_total = sum(record.storage_line_ids.mapped('subtotal'))
            # Assuming line_ids are generic and should be added to the service total
            line_total = sum(record.line_ids.mapped('price_total'))

            record.service_amount = service_total + line_total
            record.storage_amount = storage_total
            record.total_amount = record.service_amount + record.storage_amount

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the billing record, locking it for invoicing."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft billing records can be confirmed."))

        if not self.line_ids and not self.service_line_ids and not self.storage_line_ids:
            raise UserError(_("Cannot confirm a billing record without any lines."))

        self.write({'state': 'confirmed'})
        self.message_post(body=_("Advanced billing record confirmed."))

    def action_generate_invoice(self):
        """Generate a customer invoice from the billing lines."""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed billing records can be invoiced."))

        if not self.partner_id:
            raise UserError(_("A customer is required to generate an invoice."))

        invoice_lines = self._prepare_invoice_lines()

        if not invoice_lines:
            raise UserError(_("There are no lines to invoice."))

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'currency_id': self.currency_id.id,
            'invoice_date': self.invoice_date or fields.Date.today(),
            'invoice_line_ids': invoice_lines,
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            'state': 'invoiced',
            'invoice_id': invoice.id,
        })

        self.message_post(body=_("Invoice generated: %s", invoice.name))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_done(self):
        """Mark the billing record as done."""
        self.ensure_one()
        if self.state != 'invoiced':
            raise UserError(_("Only invoiced billing records can be marked as done."))

        self.write({'state': 'done'})
        self.message_post(body=_("Advanced billing record completed."))

    def action_cancel(self):
        """Cancel the billing record."""
        self.ensure_one()
        if self.state in ['invoiced', 'done']:
            raise UserError(_("Cannot cancel an invoiced or completed billing record."))

        self.write({'state': 'cancelled'})
        self.message_post(body=_("Advanced billing record cancelled."))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _prepare_invoice_lines(self):
        """Prepare invoice line values from all billing line types."""
        self.ensure_one()
        invoice_lines = []

        # Process generic lines
        for line in self.line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name or line.description,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, line.tax_ids.ids)] if line.tax_ids else False,
            }))

        # Process service lines
        for line in self.service_line_ids:
            invoice_lines.append((0, 0, {
                'name': _("Service: %s", line.name),
                'quantity': 1,
                'price_unit': line.subtotal,
            }))

        # Process storage lines
        for line in self.storage_line_ids:
            invoice_lines.append((0, 0, {
                'name': _("Storage: %s", line.name),
                'quantity': 1,
                'price_unit': line.subtotal,
            }))

        return invoice_lines

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Assign a sequence number on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('advanced.billing') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('total_amount')
    def _check_total_amount(self):
        """Validate that the total amount is not negative."""
        for record in self:
            if record.total_amount < 0:
                raise ValidationError(_("Total amount cannot be negative."))

    @api.constrains('period_start_date', 'period_end_date')
    def _check_period_dates(self):
        """Validate that the period dates are logical."""
        for record in self:
            if record.period_start_date and record.period_end_date:
                if record.period_end_date < record.period_start_date:
                    raise ValidationError(_("Period end date cannot be before the start date."))

    @api.constrains('billing_day')
    def _check_billing_day(self):
        """Validate that the billing day is within a valid range."""
        for record in self:
            if record.billing_day and not (1 <= record.billing_day <= 31):
                raise ValidationError(_("Billing day must be between 1 and 31."))

    @api.constrains('prepaid_discount_percent')
    def _check_prepaid_discount(self):
        """Validate that the prepaid discount percentage is valid."""
        for record in self:
            if record.prepaid_discount_percent and not (0 <= record.prepaid_discount_percent <= 100):
                raise ValidationError(_("Prepaid discount percentage must be between 0 and 100."))
