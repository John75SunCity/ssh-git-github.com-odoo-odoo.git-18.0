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
    ], string='Status', default='draft', required=True, tracking=True, readonly=True)

    # ============================================================================
    # BILLING DETAILS & DATES
    # ============================================================================
    invoice_date = fields.Date(
        string='Invoice Date',
        default=lambda self: fields.Date.context_today(self),
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    due_date = fields.Date(string='Due Date', readonly=True, states={'draft': [('readonly', False)]})
    period_start = fields.Date(string='Billing Period Start', readonly=True, states={'draft': [('readonly', False)]})
    period_end = fields.Date(string='Billing Period End', readonly=True, states={'draft': [('readonly', False)]})
    billing_type = fields.Selection([
        ('storage', 'Storage'),
        ('service', 'Service Request'),
        ('destruction', 'Destruction'),
        ('one_time', 'One-Time Fee')
    ], string='Billing Type', required=True, default='storage', readonly=True, states={'draft': [('readonly', False)]})

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
        store=True,
        readonly=True
    )
    tax_amount = fields.Monetary(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True,
        readonly=True
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
        readonly=True
    )
    paid_amount = fields.Monetary(
        string='Paid Amount',
        compute='_compute_payment_status',
        store=True,
        readonly=True
    )
    balance_due = fields.Monetary(
        string='Balance Due',
        compute='_compute_payment_status',
        store=True,
        readonly=True
    )
    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid')
    ], string='Payment Status', compute='_compute_payment_status', store=True, readonly=True)

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
        string='Billed Services',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    notes = fields.Text(string='Notes', readonly=True, states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]})
    internal_notes = fields.Text(string='Internal Notes')

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

    @api.depends('invoice_id.payment_state', 'total_amount', 'state')
    def _compute_payment_status(self):
        """Compute payment status and amounts based on the related invoice."""
        for record in self:
            if record.state != 'invoiced' or not record.invoice_id:
                record.paid_amount = 0.0
                record.balance_due = record.total_amount
                record.payment_status = 'not_paid'
                continue

            invoice = record.invoice_id
            paid_amount = invoice.amount_total - invoice.amount_residual
            record.paid_amount = paid_amount
            record.balance_due = invoice.amount_residual

            if invoice.payment_state == 'paid':
                record.payment_status = 'paid'
                if record.state == 'invoiced':
                    record.action_mark_as_paid()
            elif invoice.payment_state in ('partial', 'in_payment') and paid_amount > 0:
                record.payment_status = 'partial'
            else:
                record.payment_status = 'not_paid'

    @api.onchange('partner_id', 'invoice_date')
    def _onchange_partner_id(self):
        """Set due date based on partner payment terms."""
        if self.partner_id and self.invoice_date:
            payment_term = self.partner_id.property_payment_term_id or self.env['account.payment.term']
            self.due_date = payment_term._get_due_date(self.invoice_date)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the billing record."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft records can be confirmed."))
        if not self.service_ids:
            raise UserError(
                _("You cannot confirm a billing record with no service lines.")
            )
        self.write({"state": "confirmed"})
        self.message_post(body=_("Billing record confirmed."))

    def _prepare_invoice_lines(self):
        """Prepare invoice line values from service lines."""
        self.ensure_one()
        invoice_lines = []
        for service in self.service_ids:
            invoice_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": service.product_id.id,
                        "name": service.description,
                        "quantity": service.quantity,
                        "price_unit": service.price_unit,
                        "tax_ids": [(6, 0, service.tax_ids.ids)],
                        "analytic_distribution": {
                            self.department_id.analytic_account_id.id: 100
                        }
                        if self.department_id.analytic_account_id
                        else {},
                    },
                )
            )
        return invoice_lines

    def action_create_invoice(self):
        """Create a customer invoice from the billing record."""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed billing records can be invoiced."))

        invoice_lines = self._prepare_invoice_lines()
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "invoice_date": self.invoice_date,
            "currency_id": self.currency_id.id,
            "invoice_payment_term_id": self.partner_id.property_payment_term_id.id,
            "invoice_line_ids": invoice_lines,
            "narration": self.notes,
            "ref": self.name,
        }
        invoice = self.env["account.move"].create(invoice_vals)
        self.write({"invoice_id": invoice.id, "state": "invoiced"})
        self.message_post(body=_("Invoice created."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
        }

    def action_view_invoice(self):
        """View the related invoice."""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No invoice associated with this billing record."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Invoice"),
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
        }

    def action_cancel(self):
        """Cancel the billing record."""
        self.ensure_one()
        if self.state in ("invoiced", "paid"):
            raise UserError(
                _(
                    "Cannot cancel an invoiced or paid billing record. Cancel the related invoice first."
                )
            )
        if self.invoice_id and self.invoice_id.state != "cancel":
            raise UserError(
                _(
                    "The related invoice must be cancelled before cancelling this billing record."
                )
            )
        self.write({"state": "cancelled"})
        self.message_post(body=_("Billing record cancelled."))

    def action_reset_to_draft(self):
        """Reset the billing record to draft state."""
        self.ensure_one()
        if self.state not in ("confirmed", "cancelled"):
            raise UserError(_("Only confirmed or cancelled records can be reset to draft."))
        self.write({"state": "draft"})
        self.message_post(body=_("Billing record reset to draft."))

    def action_mark_as_paid(self):
        """Mark the record as paid. Called from payment status compute."""
        self.ensure_one()
        if self.state == 'invoiced':
            self.write({'state': 'paid'})
            self.message_post(body=_("Billing record marked as paid."))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        """Validate billing period dates."""
        for record in self:
            if record.period_start and record.period_end and record.period_start > record.period_end:
                raise ValidationError(_("Billing period start date cannot be after end date."))

    @api.constrains('due_date', 'invoice_date')
    def _check_due_date(self):
        """Validate due date is not before invoice date."""
        for record in self:
            if record.due_date and record.invoice_date and record.due_date < record.invoice_date:
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

    def unlink(self):
        """Prevent deletion of non-draft/cancelled records."""
        for record in self:
            if record.state not in ('draft', 'cancelled'):
                raise UserError(_("You can only delete billing records that are in draft or cancelled state."))
        return super().unlink()
