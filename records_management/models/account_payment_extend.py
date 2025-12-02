# -*- coding: utf-8 -*-
"""
Account Payment Extension for Records Management

Extends account.payment to add payment proof attachments for field
technicians collecting payments (photos of checks, cash, receipts).

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _


class AccountPaymentExtend(models.Model):
    """
    Extends account.payment to add payment proof fields.
    
    Allows technicians to attach photos of checks, cash, or receipts
    when collecting payments in the field.
    """
    _inherit = 'account.payment'

    # ============================================================================
    # PAYMENT PROOF FIELDS
    # ============================================================================
    payment_proof = fields.Binary(
        string='Payment Proof',
        attachment=True,
        help='Photo of check, cash, or receipt for payment verification'
    )
    payment_proof_filename = fields.Char(string='Payment Proof Filename')

    payment_proof_type = fields.Selection([
        ('check', 'Check Photo'),
        ('cash', 'Cash Photo'),
        ('receipt', 'Receipt'),
        ('card_slip', 'Credit Card Slip'),
        ('other', 'Other'),
    ], string='Proof Type', help='Type of payment proof attached')

    check_number = fields.Char(
        string='Check Number',
        help='Check number for reference (if paying by check)'
    )

    collected_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Collected By',
        default=lambda self: self.env.user,
        help='Technician who collected the payment'
    )

    collection_location = fields.Char(
        string='Collection Location',
        help='Where the payment was collected (customer site, office, etc.)'
    )

    collection_notes = fields.Text(
        string='Collection Notes',
        help='Any notes about the payment collection'
    )

    # Work order reference (if payment collected during service call)
    work_order_reference = fields.Char(
        string='Work Order Reference',
        help='Work order during which this payment was collected'
    )

    # Field collection flag
    is_field_collection = fields.Boolean(
        string='Field Collection',
        default=False,
        help='Payment was collected in the field by a technician'
    )

    @api.model
    def create_field_payment(self, partner_id, amount, journal_id, payment_proof=None,
                             payment_proof_type=None, check_number=None, work_order_ref=None,
                             collection_notes=None):
        """
        Create a payment collected in the field by a technician.
        
        :param partner_id: Customer ID
        :param amount: Payment amount
        :param journal_id: Payment journal (bank/cash)
        :param payment_proof: Base64 encoded image of payment proof
        :param payment_proof_type: Type of proof (check, cash, receipt, etc.)
        :param check_number: Check number if applicable
        :param work_order_ref: Work order reference
        :param collection_notes: Notes about the collection
        :return: Created payment record
        """
        vals = {
            'partner_id': partner_id,
            'amount': amount,
            'journal_id': journal_id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'is_field_collection': True,
            'collected_by_id': self.env.user.id,
            'work_order_reference': work_order_ref,
        }

        if payment_proof:
            vals['payment_proof'] = payment_proof
            vals['payment_proof_filename'] = f'payment_proof_{fields.Date.today()}.jpg'

        if payment_proof_type:
            vals['payment_proof_type'] = payment_proof_type

        if check_number:
            vals['check_number'] = check_number

        if collection_notes:
            vals['collection_notes'] = collection_notes

        payment = self.create(vals)
        return payment
