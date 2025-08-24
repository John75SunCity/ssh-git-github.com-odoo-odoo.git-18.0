# -*- coding: utf-8 -*-
"""
Records Billing Service Line Module

Manages individual service lines within billing records. Each line represents
a specific service, product, or fee that will be included in the customer invoice.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBillingService(models.Model):
    _name = 'records.billing.service'
    _description = 'Records Billing Service Line'
    _order = 'billing_id, sequence, id'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    billing_id = fields.Many2one(
        'records.billing',
        string='Billing Record',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Sequence', default=10)
    product_id = fields.Many2one(
        'product.product',
        string='Service/Product',
        required=True,
        domain=[('sale_ok', '=', True)]
    )
    name = fields.Char(string='Label', required=True)
    description = fields.Text(string='Description', required=True)

    # ============================================================================
    # QUANTITY & PRICING
    # ============================================================================
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        digits='Product Unit of Measure',
        required=True
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        readonly=True
    )
    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price',
        required=True
    )
    discount = fields.Float(
        string='Discount (%)',
        digits='Discount',
        default=0.0
    )

    # ============================================================================
    # TAX & CURRENCY
    # ============================================================================
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain=['|', ('active', '=', False), ('active', '=', True)]
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='billing_id.currency_id',
        store=True,
        readonly=True
    )

    # ============================================================================
    # COMPUTED AMOUNTS
    # ============================================================================
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amount',
        store=True
    )
    price_tax = fields.Monetary(
        string='Total Tax',
        compute='_compute_amount',
        store=True
    )
    price_total = fields.Monetary(
        string='Total',
        compute='_compute_amount',
        store=True
    )

    # ============================================================================
    # BUSINESS RELATIONSHIPS
    # ============================================================================
    container_id = fields.Many2one(
        'records.container',
        string='Related Container',
        help="Container associated with this billing line"
    )
    service_request_id = fields.Many2one(
        'portal.request',
        string='Service Request',
        help="Service request that generated this billing line"
    )
    destruction_service_id = fields.Many2one(
        'shredding.service',
        string='Destruction Service',
        help="Destruction service associated with this billing line"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('quantity', 'price_unit', 'discount', 'tax_ids')
    def _compute_amount(self):
        """Compute the amounts of the line with discount applied."""
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids.compute_all(
                price,
                line.currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.billing_id.partner_id
            )
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update line details when product changes."""
        if self.product_id:
            self.name = self.product_id.name
            self.description = self.product_id.get_product_multiline_description_sale()
            self.price_unit = self.product_id.list_price

            # Set taxes based on product and customer
            if self.billing_id.partner_id:
                taxes = self.product_id.taxes_id.filtered(
                    lambda t: t.company_id == self.billing_id.company_id
                )
                self.tax_ids = taxes
            else:
                self.tax_ids = self.product_id.taxes_id

    @api.onchange('quantity', 'price_unit', 'discount')
    def _onchange_pricing(self):
        """Recalculate amounts when pricing fields change."""
        # Trigger compute method
        self._compute_amount()

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive."""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Quantity must be positive."))

    @api.constrains('discount')
    def _check_discount(self):
        """Validate discount percentage."""
        for line in self:
            if not 0 <= line.discount <= 100:
                raise ValidationError(_("Discount must be between 0%% and 100%%."))

    @api.constrains('price_unit')
    def _check_price_unit(self):
        """Validate unit price is not negative."""
        for line in self:
            if line.price_unit < 0:
                raise ValidationError(_("Unit price cannot be negative."))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_billing_line_description(self):
        """Get formatted description for billing purposes."""
        self.ensure_one()
        description_parts = [self.description]

        if self.container_id:
            description_parts.append(_("Container: %s", self.container_id.name))

        if self.service_request_id:
            description_parts.append(_("Request: %s", self.service_request_id.name))

        return "\n".join(description_parts)

    def update_from_container_specs(self):
        """Update pricing based on container specifications if applicable."""
        if self.container_id and self.product_id:
            # Container-specific pricing logic
            container_type = self.container_id.container_type
            if container_type and hasattr(self.product_id, 'container_pricing_ids'):
                pricing = self.product_id.container_pricing_ids.filtered(
                    lambda p: p.container_type == container_type
                )
                if pricing:
                    self.price_unit = pricing[0].unit_price
