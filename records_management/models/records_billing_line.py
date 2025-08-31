# -*- coding: utf-8 -*-
"""
Records Billing Line Model

Billing line model for Records Management system that handles
individual billing line items and calculations.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsBillingLine(models.Model):
    """
    Records Billing Line Model

    Model for individual billing line items that are part of
    a billing record in the Records Management system.
    """

    _name = 'records.billing.line'
    _description = 'Records Billing Line'
    _order = 'sequence, id'

    # Basic Information
    sequence = fields.Integer(string='Sequence', default=10)

    billing_id = fields.Many2one(
        'records.billing',
        string='Billing',
        required=True,
        ondelete='cascade',
        index=True
    )

    name = fields.Char(
        string='Description',
        required=True
    )

    # Product/Service Information
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        ondelete='restrict'
    )

    # Quantity and Pricing
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True
    )

    price_unit = fields.Float(
        string='Unit Price',
        required=True
    )

    discount = fields.Float(
        string='Discount (%)',
        default=0.0
    )

    # Tax Information
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes'
    )

    # Computed Fields
    price_subtotal = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )

    price_tax = fields.Float(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True
    )

    price_total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='billing_id.currency_id',
        store=True
    )

    # Additional Information
    notes = fields.Text(string='Notes')

    @api.depends('quantity', 'price_unit', 'discount', 'tax_ids')
    def _compute_amounts(self):
        for line in self:
            # Calculate subtotal
            subtotal = line.quantity * line.price_unit
            if line.discount:
                subtotal *= (1 - line.discount / 100.0)
            line.price_subtotal = subtotal

            # Calculate tax
            taxes = line.tax_ids.compute_all(
                line.price_unit,
                line.currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.billing_id.partner_id
            )
            line.price_tax = taxes['total_included'] - taxes['total_excluded']
            line.price_total = taxes['total_included']
