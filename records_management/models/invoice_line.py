# -*- coding: utf-8 -*-
"""
Invoice Line Model Extension

Extended invoice line for Records Management billing.
"""

from odoo import models, fields, api, _


class InvoiceLine(models.Model):
    """Invoice Line Extension"""

    _name = "invoice.line"
    _description = "Invoice Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "sequence, id"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Description",
        required=True,
        tracking=True,
        help="Line item description"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this line"
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for line ordering"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        ondelete="cascade",
        help="Parent invoice"
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        help="Product for this line"
    )

    # ============================================================================
    # PRICING FIELDS
    # ============================================================================
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True,
        help="Quantity of items"
    )

    unit_price = fields.Float(
        string="Unit Price",
        required=True,
        help="Price per unit"
    )

    subtotal = fields.Float(
        string="Subtotal",
        compute='_compute_subtotal',
        help="Line subtotal"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        """Calculate line subtotal"""
        for record in self:
            record.subtotal = record.quantity * record.unit_price
