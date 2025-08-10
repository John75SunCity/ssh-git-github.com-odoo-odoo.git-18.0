# -*- coding: utf-8 -*-
"""
Revenue Forecasting Management Module
This module provides comprehensive revenue forecasting and analysis capabilities
for the Records Management System. It implements advanced financial modeling,
scenario analysis, and predictive analytics for business planning and decision-making.
Key Features:
- Multi-scenario revenue forecasting (baseline, optimistic, pessimistic)
- Customer segment analysis with retention rate modeling
- Service category-specific forecasting and pricing optimization
- Global rate adjustment modeling with inflation and market factors
- Risk assessment integration with confidence level tracking
- Detailed variance analysis with actual vs projected comparisons
Business Processes:
1. Forecast Creation: Set up forecasting parameters and scenarios
2. Customer Segmentation: Analyze revenue by customer segments and specific customers
3. Service Analysis: Forecast revenue by service categories (storage, retrieval, destruction)
4. Risk Assessment: Evaluate forecast confidence and market risk factors
5. Variance Tracking: Monitor actual performance against projections
6. Strategic Planning: Use forecasts for pricing and capacity planning decisions
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RevenueForecaster(models.Model):
    _name = "revenue.forecaster"
    _description = "Revenue Forecaster"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Forecast Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the revenue forecast",
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of the forecast purpose and assumptions",
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Display order for forecasts"
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current forecast status",
    )

    # ============================================================================
    # REVENUE CALCULATIONS
    # ============================================================================
    projected_revenue = fields.Monetary(
        string="Projected Revenue",
        currency_field="currency_id",
        tracking=True,
        help="Total projected revenue for the forecast period",
    )
    actual_revenue = fields.Monetary(
        string="Actual Revenue",
        currency_field="currency_id",
        help="Actual revenue achieved",
    )
    current_monthly_revenue = fields.Monetary(
        string="Current Monthly Revenue",
        currency_field="currency_id",
        help="Current baseline monthly revenue",
    )
    predicted_quarterly_revenue = fields.Monetary(
        string="Predicted Quarterly Revenue",
        currency_field="currency_id",
        help="Projected quarterly revenue",
    )
    annual_revenue_impact = fields.Monetary(
        string="Annual Revenue Impact",
        currency_field="currency_id",
        help="Projected annual revenue impact",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    forecast_line_ids = fields.One2many(
        "revenue.forecast.line",
        "forecast_id",
        string="Forecast Lines",
        help="Detailed forecast lines by customer",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("forecast_line_ids.projected_monthly_revenue")
    def _compute_projected_revenue(self):
        """Compute total projected revenue from forecast lines"""
        for forecast in self:
            forecast.projected_revenue = sum(
                forecast.forecast_line_ids.mapped("projected_monthly_revenue")
            )

    @api.depends("forecast_line_ids.actual_revenue")
    def _compute_actual_revenue(self):
        """Compute total actual revenue from forecast lines"""
        for forecast in self:
            forecast.actual_revenue = sum(
                forecast.forecast_line_ids.mapped("actual_revenue")
            )

    @api.depends("forecast_line_ids.current_monthly_revenue")
    def _compute_current_monthly_revenue(self):
        """Compute current monthly revenue from forecast lines"""
        for forecast in self:
            forecast.current_monthly_revenue = sum(
                forecast.forecast_line_ids.mapped("current_monthly_revenue")
            )

    @api.depends("forecast_line_ids.predicted_quarterly_revenue")
    def _compute_predicted_quarterly_revenue(self):
        """Compute predicted quarterly revenue from forecast lines"""
        for forecast in self:
            forecast.predicted_quarterly_revenue = sum(
                forecast.forecast_line_ids.mapped("predicted_quarterly_revenue")
            )

    @api.depends("forecast_line_ids.annual_revenue_impact")
    def _compute_annual_revenue_impact(self):
        """Compute annual revenue impact from forecast lines"""
        for forecast in self:
            forecast.annual_revenue_impact = sum(
                forecast.forecast_line_ids.mapped("annual_revenue_impact")
            )


class RevenueForecastLine(models.Model):
    """Revenue Forecast Line for detailed customer impact analysis"""

    _name = "revenue.forecast.line"
    _description = "Revenue Forecast Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "forecast_id, partner_id"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Forecast Line", compute="_compute_name", store=True, index=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    # ============================================================================
    # FORECAST RELATIONSHIP
    # ============================================================================
    forecast_id = fields.Many2one(
        "revenue.forecaster", string="Forecast", required=True, ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)

    # ============================================================================
    # CUSTOMER DETAILS
    # ============================================================================
    customer_segment = fields.Selection(
        [
            ("enterprise", "Enterprise"),
            ("mid_market", "Mid Market"),
            ("small_business", "Small Business"),
        ],
        string="Customer Segment",
    )
    container_count = fields.Integer(
        string="Container Count", help="Number of containers for this customer"
    )
    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Risk Level",
        default="medium",
    )

    # ============================================================================
    # REVENUE CALCULATIONS
    # ============================================================================
    current_monthly_revenue = fields.Monetary(
        string="Current Monthly Revenue",
        currency_field="currency_id",
        help="Current baseline monthly revenue",
    )
    projected_monthly_revenue = fields.Monetary(
        string="Projected Monthly Revenue",
        currency_field="currency_id",
        help="Projected monthly revenue after adjustments",
    )
    revenue_change = fields.Monetary(
        string="Revenue Change",
        compute="_compute_revenue_change",
        currency_field="currency_id",
        store=True,
        help="Absolute change in revenue",
    )
    revenue_change_percentage = fields.Float(
        string="Revenue Change %",
        compute="_compute_revenue_change",
        store=True,
        digits=(5, 2),
        help="Percentage change in revenue",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("current_monthly_revenue", "projected_monthly_revenue")
    def _compute_revenue_change(self):
        """Compute revenue change amount and percentage"""
        for line in self:
            line.revenue_change = (line.projected_monthly_revenue or 0.0) - (
                line.current_monthly_revenue or 0.0
            )
            if line.current_monthly_revenue:
                line.revenue_change_percentage = (
                    line.revenue_change / line.current_monthly_revenue
                ) * 100
            else:
                line.revenue_change_percentage = 0.0

    @api.depends("partner_id", "forecast_id")
    def _compute_name(self):
        """Compute descriptive name for forecast line"""
        for line in self:
            if line.partner_id and line.forecast_id:
                line.name = _("%s - %s"
            elif line.partner_id:
                line.name = _("%s - Forecast Line"
            else:
                line.name = _("Forecast Line %s"
