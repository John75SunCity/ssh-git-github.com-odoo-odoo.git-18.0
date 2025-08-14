# -*- coding: utf-8 -*-
# Records Billing Line Model

from odoo import fields, models, api


class RecordsBillingLine(models.Model):
    """Billing line items for detailed billing tracking"""

    """
    Represents a single billing line item for detailed billing tracking.
    Each line item records the quantity, unit price, total amount, and associated department contact for a specific billing configuration and date.
    Used to track billable services or products provided to departments, enabling granular invoice generation and financial analysis.
    """
    _name = "records.billing.line"
    _description = "Records Billing Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True,
        default=lambda self: _('New'),
        help='Unique identifier for this record'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide this record'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.billing.line') or _('New')
        return super().create(vals_list)
    _order = "config_id, date desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )

    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Config",
        required=True,
        ondelete="cascade",
    )
    billing_id = fields.Many2one(
        "advanced.billing",
        string="Advanced Billing",
        help="Reference to advanced billing record",
    )
    contact_id = fields.Many2one(
        "records.department.billing.contact",
        string="Department Contact",
        help="Department contact associated with this billing line",
    )
    date = fields.Date(string="Billing Date", required=True, default=fields.Date.today)
    quantity = fields.Float(string="Quantity", digits=(10, 2), default=1.0)
    unit_price = fields.Monetary(
        string="Unit Price", currency_field="currency_id", required=True
    )
    amount = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        compute="_compute_amount",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    billable = fields.Boolean(string="Billable", default=True)

    @api.depends("quantity", "unit_price")
    def _compute_amount(self):
        for record in self:
            record.amount = record.quantity * record.unit_price
