# -*- coding: utf-8 -*-
"""
Work Order Field Payment Wizard

Wizard for technicians to collect payments in the field with
payment proof attachments (photos of checks, cash, receipts).

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class WorkOrderFieldPaymentWizard(models.TransientModel):
    """
    Wizard for collecting payments in the field with proof attachments.
    
    Allows technicians to:
    - Select payment method
    - Enter payment amount
    - Attach photo proof (check/cash/receipt)
    - Enter check number
    - Add collection notes
    """
    _name = 'work.order.field.payment.wizard'
    _description = 'Field Payment Collection Wizard'

    # ============================================================================
    # CUSTOMER & AMOUNT
    # ============================================================================
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        readonly=True,
    )
    
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    
    amount = fields.Monetary(
        string='Payment Amount',
        currency_field='currency_id',
        required=True,
    )
    
    outstanding_balance = fields.Monetary(
        string='Outstanding Balance',
        currency_field='currency_id',
        compute='_compute_outstanding_balance',
    )

    # ============================================================================
    # PAYMENT METHOD
    # ============================================================================
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Payment Method',
        domain=[('type', 'in', ['bank', 'cash'])],
        required=True,
    )
    
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('other', 'Other'),
    ], string='Payment Type', required=True, default='cash')

    # ============================================================================
    # PAYMENT PROOF
    # ============================================================================
    payment_proof = fields.Binary(
        string='Payment Proof Photo',
        help='Take a photo of check, cash, or receipt',
    )
    payment_proof_filename = fields.Char(string='Proof Filename')
    
    check_number = fields.Char(
        string='Check Number',
        help='Enter check number if paying by check',
    )
    
    card_last_four = fields.Char(
        string='Card Last 4 Digits',
        help='Last 4 digits of credit/debit card for reference',
    )

    # ============================================================================
    # WORK ORDER REFERENCE
    # ============================================================================
    work_order_reference = fields.Char(
        string='Work Order',
        readonly=True,
    )
    work_order_model = fields.Char(string='Work Order Model')
    work_order_id = fields.Integer(string='Work Order ID')

    # ============================================================================
    # COLLECTION DETAILS
    # ============================================================================
    collection_notes = fields.Text(
        string='Collection Notes',
        help='Any notes about the payment collection',
    )
    
    memo = fields.Char(
        string='Payment Memo',
        help='Reference to appear on payment',
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('partner_id')
    def _compute_outstanding_balance(self):
        """Compute total outstanding balance for customer"""
        for wizard in self:
            balance = 0.0
            if wizard.partner_id:
                unpaid_invoices = self.env['account.move'].sudo().search([
                    ('partner_id', '=', wizard.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                ])
                balance = sum(inv.amount_residual for inv in unpaid_invoices)
            wizard.outstanding_balance = balance

    @api.onchange('payment_method')
    def _onchange_payment_method(self):
        """Set appropriate journal based on payment method"""
        if self.payment_method == 'cash':
            cash_journal = self.env['account.journal'].search([
                ('type', '=', 'cash'),
                ('company_id', '=', self.env.company.id),
            ], limit=1)
            if cash_journal:
                self.journal_id = cash_journal
        elif self.payment_method in ['check', 'credit_card', 'debit_card']:
            bank_journal = self.env['account.journal'].search([
                ('type', '=', 'bank'),
                ('company_id', '=', self.env.company.id),
            ], limit=1)
            if bank_journal:
                self.journal_id = bank_journal

    # ============================================================================
    # VALIDATION
    # ============================================================================
    @api.constrains('amount')
    def _check_amount(self):
        for wizard in self:
            if wizard.amount <= 0:
                raise ValidationError(_("Payment amount must be greater than zero."))

    @api.constrains('check_number', 'payment_method')
    def _check_check_number(self):
        for wizard in self:
            if wizard.payment_method == 'check' and not wizard.check_number:
                raise ValidationError(_("Check number is required for check payments."))

    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_process_payment(self):
        """
        Process the field payment and create payment record.
        
        Creates an account.payment with field collection details
        and attaches the payment proof photo.
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("Customer is required."))
        
        if not self.amount or self.amount <= 0:
            raise UserError(_("Payment amount must be greater than zero."))
        
        if not self.journal_id:
            raise UserError(_("Please select a payment method."))
        
        # Get unpaid invoices to reconcile
        unpaid_invoices = self.env['account.move'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ], order='invoice_date_due asc')  # Pay oldest first
        
        # Map payment method to proof type
        proof_type_map = {
            'cash': 'cash',
            'check': 'check',
            'credit_card': 'card_slip',
            'debit_card': 'card_slip',
            'other': 'other',
        }
        
        # Create memo
        memo = self.memo or _('Field collection - %s') % self.work_order_reference
        
        # Create the payment
        payment_vals = {
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'journal_id': self.journal_id.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'ref': memo,
            # Field collection fields
            'is_field_collection': True,
            'collected_by_id': self.env.user.id,
            'work_order_reference': self.work_order_reference,
            'payment_proof_type': proof_type_map.get(self.payment_method, 'other'),
            'collection_notes': self.collection_notes,
        }
        
        # Add payment proof if provided
        if self.payment_proof:
            payment_vals['payment_proof'] = self.payment_proof
            ext = 'jpg'
            if self.payment_proof_filename:
                ext = self.payment_proof_filename.split('.')[-1] if '.' in self.payment_proof_filename else 'jpg'
            payment_vals['payment_proof_filename'] = f'payment_proof_{fields.Date.today()}.{ext}'
        
        # Add check number if applicable
        if self.payment_method == 'check' and self.check_number:
            payment_vals['check_number'] = self.check_number
        
        # Create payment
        payment = self.env['account.payment'].sudo().create(payment_vals)
        
        # Post the payment
        payment.action_post()
        
        # Post message to work order if we have reference
        if self.work_order_model and self.work_order_id:
            try:
                work_order = self.env[self.work_order_model].browse(self.work_order_id)
                if work_order.exists():
                    work_order.message_post(
                        body=_("Payment of %s %s collected by %s.<br/>Method: %s<br/>Reference: %s") % (
                            self.currency_id.symbol,
                            self.amount,
                            self.env.user.name,
                            dict(self._fields['payment_method'].selection).get(self.payment_method),
                            payment.name,
                        )
                    )
            except Exception:
                pass  # Don't fail if work order posting fails
        
        # Return success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Processed'),
                'message': _('Payment of %s %s has been recorded successfully.') % (
                    self.currency_id.symbol, self.amount
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_cancel(self):
        """Cancel and close the wizard"""
        return {'type': 'ir.actions.act_window_close'}
