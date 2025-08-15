# -*- coding: utf-8 -*-
"""
Payment Split Line Model

Individual line items for split payments across multiple services or billing periods.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentSplitLine(models.Model):
    """Payment Split Line"""

    _name = "payment.allocation.line"
    _description = "Payment Allocation Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "payment_id, allocation_order, service_type"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Split Description",
        required=True,
        tracking=True,
        help="Description of this payment split"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        help="Display name for the split line"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company", 
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(
        string="Active",
        default=True
    )

    allocation_order = fields.Integer(
        string="Allocation Order",
        default=10,
        help="Order for payment allocation"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    payment_id = fields.Many2one(
        "records.payment",
        string="Payment",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent payment record"
    )

    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        domain="[('move_type', '=', 'out_invoice')]",
        help="Invoice this split applies to"
    )

    service_id = fields.Many2one(
        "shredding.service",
        string="Service",
        help="Service this split applies to"
    )

    # ============================================================================
    # FINANCIAL DETAILS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True
    )

    allocated_amount = fields.Monetary(
        string="Allocated Amount",
        currency_field="currency_id",
        required=True,
        help="Amount allocated to this split"
    )

    allocation_percentage = fields.Float(
        string="Allocation %",
        compute='_compute_allocation_percentage',
        store=True,
        help="Percentage of total payment"
    )

    # ============================================================================
    # SERVICE CATEGORIZATION
    # ============================================================================
    service_type = fields.Selection([
        ('storage', 'Storage Services'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'Document Destruction'),
        ('scanning', 'Document Scanning'),
        ('transport', 'Transportation'),
        ('consultation', 'Consultation'),
        ('setup', 'Setup/Installation'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other Services')
    ], string='Service Type', required=True)

    billing_period = fields.Selection([
        ('current', 'Current Period'),
        ('previous', 'Previous Period'),
        ('advance', 'Advance Payment'),
        ('credit', 'Credit Application')
    ], string='Billing Period', default='current')

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'service_type', 'allocated_amount')
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            service_dict = dict(record._fields['service_type'].selection)
            service_label = service_dict.get(record.service_type, record.service_type)
            
            record.display_name = f"{service_label}: {record.allocated_amount}"

    @api.depends('allocated_amount', 'payment_id.total_amount')
    def _compute_allocation_percentage(self):
        """Calculate allocation percentage"""
        for record in self:
            if record.payment_id and record.payment_id.total_amount:
                record.allocation_percentage = (record.allocated_amount / record.payment_id.total_amount) * 100
            else:
                record.allocation_percentage = 0.0

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('allocated_amount')
    def _check_allocated_amount(self):
        """Validate allocated amount"""
        for record in self:
            if record.allocated_amount <= 0:
                raise ValidationError(_('Allocated amount must be greater than 0'))
