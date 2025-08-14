# -*- coding: utf-8 -*-
# Revenue Analytic Model

from odoo import api, fields, models, _

class RevenueAnalytic(models.Model):
    """Revenue analytics for billing configurations"""

    _name = "revenue.analytic"
    _description = "Revenue Analytic"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "config_id, period_start desc"

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
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help='Company this record belongs to'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Config",
        required=True,
        ondelete="cascade",
    )
    period_start = fields.Date(string="Period Start", required=True)
    period_end = fields.Date(string="Period End", required=True)
    total_revenue = fields.Monetary(
        string="Total Revenue", currency_field="currency_id"
    )
    projected_revenue = fields.Monetary(
        string="Projected Revenue", currency_field="currency_id"
    )
    actual_costs = fields.Monetary(string="Actual Costs", currency_field="currency_id")
    profit_margin = fields.Float(
        string="Profit Margin %", digits=(5, 2), compute="_compute_profit_margin"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    customer_count = fields.Integer(string="Customer Count")
    average_revenue_per_customer = fields.Monetary(
        string="Avg Revenue/Customer",
        currency_field="currency_id",
        compute="_compute_average_revenue",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "revenue.analytic"
                ) or _("New")
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("total_revenue", "actual_costs")
    def _compute_profit_margin(self):
        for record in self:
            if record.total_revenue:
                record.profit_margin = (
                    (record.total_revenue - record.actual_costs) / record.total_revenue
                ) * 100
            else:
                record.profit_margin = 0.0

    @api.depends("total_revenue", "customer_count")
    def _compute_average_revenue(self):
        for record in self:
            if record.customer_count:
                record.average_revenue_per_customer = (
                    record.total_revenue / record.customer_count
                )
            else:
                record.average_revenue_per_customer = 0.0
