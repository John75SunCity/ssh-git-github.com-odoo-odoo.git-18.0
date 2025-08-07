# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RevenueForecaster(models.Model):
    _name = "revenue.forecaster"
    _description = "Revenue Forecaster"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"

    name = fields.Char(string="Name", required=True, tracking=True),
    description = fields.Text(string="Description")

    # Forecast Configuration
    forecast_period = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ]),
        string="Forecast Period",
        default="monthly",
        required=True,
    )

    )

    start_date = fields.Date(string="Start Date", required=True),
    end_date = fields.Date(string="End Date", required=True)

    # Revenue Calculations
    projected_revenue = fields.Monetary(
        string="Projected Revenue", currency_field="currency_id", tracking=True
    ),
    actual_revenue = fields.Monetary(
        string="Actual Revenue", currency_field="currency_id")
    variance = fields.Monetary(
        string="Variance",
        compute="_compute_variance",
        currency_field="currency_id",
        store=True,
    ),
    variance_percent = fields.Float(
        string="Variance %", compute="_compute_variance", store=True
    )

    # Customer and Department
    customer_id = fields.Many2one("res.partner", string="Customer"),
    department_id = fields.Many2one("records.department", string="Department")

    # Control fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,)
    user_id = fields.Many2one(
        "res.users", string="Responsible", default=lambda self: self.env.user
    )
    )
    active = fields.Boolean(string="Active", default=True)

    # State management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ]),
        string="Status",
        default="draft",
    )

    # === MISSING FIELDS FROM VIEWS ===
    )
    custom_end_date = fields.Date(
        string="Custom End Date", help="Custom end date when forecast period is custom"
    ),
    custom_start_date = fields.Date(
        string="Custom Start Date",
        help="Custom start date when forecast period is custom",
    )
    customer_impact_count = fields.Integer(
        string="Customer Impact Count",
        help="Number of customers affected by this forecast",)
    customer_retention_rate = fields.Float(
        string="Customer Retention Rate %",
        default=95.0,
        help="Expected customer retention rate",
    ),
    customer_segment = fields.Selection(
        [
            ("all", "All Customers"),
            ("enterprise", "Enterprise"),
            ("mid_market", "Mid Market"),
            ("small_business", "Small Business"),
            ("specific_customers", "Specific Customers"),
        ]),
        string="Customer Segment",
        default="all",
    )

    specific_customer_ids = fields.Many2many(
        "res.partner",
        string="Specific Customers",
        help="Specific customers when segment is specific_customers",
    )

    )

    risk_assessment = fields.Selection(
        [
            ("low", "Low Risk"),
            ("medium", "Medium Risk"),
            ("high", "High Risk"),
            ("very_high", "Very High Risk"),
        ]),
        string="Risk Assessment",
        default="medium",
    )

    scenario_type = fields.Selection(
        [
            ("baseline", "Baseline Scenario"),
            ("optimistic", "Optimistic Scenario"),
            ("pessimistic", "Pessimistic Scenario"),
            ("global_increase", "Global Rate Increase"),
            ("global_decrease", "Global Rate Decrease"),
            ("category_specific", "Category Specific Change"),
        ]),
        string="Scenario Type",
        default="baseline",
    )

    )

    global_adjustment_type = fields.Selection(
        [("percentage", "Percentage"), ("fixed_amount", "Fixed Amount")],
        string="Global Adjustment Type",
        default="percentage",
    )

    global_adjustment_value = fields.Float(
        string="Global Adjustment Value",
        help="Adjustment value (percentage or fixed amount)",
    )

    )

    service_category = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("scanning", "Scanning"),
        ]),
        string="Service Category",
    )

    category_adjustment_value = fields.Float(
        string="Category Adjustment Value %",
        help="Adjustment value for specific category",
    )

    )

    market_growth_rate = fields.Float(
        string="Market Growth Rate %", default=3.0, help="Expected market growth rate"
    ),
    inflation_rate = fields.Float(
        string="Inflation Rate %", default=2.5, help="Expected inflation rate"
    )

    )

    competitor_rate_factor = fields.Float(
        string="Competitor Rate Factor",
        default=1.0,
        help="Competitive rate adjustment factor",
    ),
    analysis_complete = fields.Boolean(
        string="Analysis Complete",
        default=False,
        help="Whether the forecast analysis is complete",
    )

    )

    forecast_line_ids = fields.One2many(
        "revenue.forecast.line", "forecast_id", string="Forecast Lines"
    )

    # === BUSINESS CRITICAL FIELDS ===        "mail.followers", "res_id", string="Followers"
    )
    sequence = fields.Integer(string="Sequence", default=10),
    notes = fields.Text(string="Notes")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now),
    updated_date = fields.Datetime(string="Updated Date")
    # Revenue Forecasting Fields
    annual_revenue_impact = fields.Monetary(
        "Annual Revenue Impact", currency_field="currency_id"
    ),
    category_adjustment_value = fields.Float("Category Adjustment Value %", default=0.0)
    competitor_rate_factor = fields.Float("Competitor Rate Factor", default=1.0),
    container_count = fields.Integer("Container Count", default=0)
    current_monthly_revenue = fields.Monetary(
        "Current Monthly Revenue", currency_field="currency_id"
    ),
    customer_churn_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], default="low"
    )
    customer_growth_potential = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium"
    )
    )
    demand_seasonality_factor = fields.Float("Demand Seasonality Factor", default=1.0),
    economic_indicator_impact = fields.Float("Economic Indicator Impact %", default=0.0)
    forecast_accuracy_percentage = fields.Float("Forecast Accuracy %", default=0.0),
    forecast_confidence_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium"
    )
    )
    forecast_horizon_months = fields.Integer("Forecast Horizon (Months)", default=12)
    forecast_methodology = fields.Selection(
        [
            ("linear", "Linear"),
            ("exponential", "Exponential"),
            ("ai_model", "AI Model"),
        ]),
        default="linear",
    )
    market_penetration_rate = fields.Float("Market Penetration Rate %", default=0.0),
    market_size_estimate = fields.Monetary(
        "Market Size Estimate", currency_field="currency_id"
    )
    new_customer_acquisition_rate = fields.Float(
        "New Customer Acquisition Rate %", default=0.0
    ),
    predicted_quarterly_revenue = fields.Monetary(
        "Predicted Quarterly Revenue", currency_field="currency_id"
    )
    pricing_elasticity_factor = fields.Float("Pricing Elasticity Factor", default=1.0),
    revenue_growth_target = fields.Float("Revenue Growth Target %", default=0.0)
    revenue_variance_analysis = fields.Text("Revenue Variance Analysis"),
    risk_adjustment_factor = fields.Float("Risk Adjustment Factor", default=1.0)
    scenario_analysis_enabled = fields.Boolean(
        "Scenario Analysis Enabled", default=False
    )
    )
    service_mix_optimization = fields.Text("Service Mix Optimization"),
    trend_analysis_period = fields.Integer("Trend Analysis Period (Months)", default=6)
    volume_price_correlation = fields.Float("Volume-Price Correlation", default=0.0)

    @api.depends("projected_revenue", "actual_revenue")
    def _compute_variance(self):
        for record in self:
            record.variance = record.actual_revenue - record.projected_revenue
            if record.projected_revenue:
                record.variance_percent = (
                    record.variance / record.projected_revenue
                ) * 100
            else:
                record.variance_percent = 0.0

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})

class RevenueForecastLine(models.Model):
    """Revenue Forecast Line for detailed customer impact analysis"""

    _name = "revenue.forecast.line"
    _description = "Revenue Forecast Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Forecast Line", compute="_compute_name", store=True, index=True
    ),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    ),
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # FORECAST DETAILS
    # ============================================================================
    forecast_id = fields.Many2one(
        "revenue.forecaster", string="Forecast", required=True, ondelete="cascade"
    ),
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    customer_segment = fields.Selection(
        [
            ("enterprise", "Enterprise"),
            ("mid_market", "Mid Market"),
            ("small_business", "Small Business"),
        ]),
        string="Customer Segment",
    )

    )

    container_count = fields.Integer(
        string="Container Count", help="Number of containers for this customer"
    ),
    current_monthly_revenue = fields.Monetary(
        string="Current Monthly Revenue", currency_field="currency_id"
    )
    projected_monthly_revenue = fields.Monetary(
        string="Projected Monthly Revenue", currency_field="currency_id")
    revenue_change = fields.Monetary(
        string="Revenue Change",
        compute="_compute_revenue_change",
        currency_field="currency_id",
        store=True,
    ),
    revenue_change_percentage = fields.Float(
        string="Revenue Change %", compute="_compute_revenue_change", store=True)
    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Risk Level",
        default="medium",
    )

    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

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
                line.name = f"{line.partner_id.name} - {line.forecast_id.name}"
            elif line.partner_id:
                line.name = f"{line.partner_id.name} - Forecast Line"
            else:
                line.name = f"Forecast Line {line.id or 'New'}")
