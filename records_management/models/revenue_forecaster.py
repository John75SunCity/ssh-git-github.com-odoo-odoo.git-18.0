# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RevenueForecaster(models.Model):
    _name = "revenue.forecaster"
    _description = "Revenue Forecaster"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"

    name = fields.Char(string="Name", required=True, tracking=True)
    description = fields.Text(string="Description")

    # Forecast Configuration
    forecast_period = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ],
        string="Forecast Period",
        default="monthly",
        required=True,
    )

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    # Revenue Calculations
    projected_revenue = fields.Monetary(
        string="Projected Revenue", currency_field="currency_id", tracking=True
    )
    actual_revenue = fields.Monetary(
        string="Actual Revenue", currency_field="currency_id"
    )
    variance = fields.Monetary(
        string="Variance",
        compute="_compute_variance",
        currency_field="currency_id",
        store=True,
    )
    variance_percent = fields.Float(
        string="Variance %", compute="_compute_variance", store=True
    )

    # Customer and Department
    customer_id = fields.Many2one("res.partner", string="Customer")
    department_id = fields.Many2one("records.department", string="Department")

    # Control fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # State management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
    )

    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    sequence = fields.Integer(string="Sequence", default=10)
    notes = fields.Text(string="Notes")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # Revenue Forecasting Fields
    annual_revenue_impact = fields.Monetary('Annual Revenue Impact', currency_field='currency_id')
    category_adjustment_value = fields.Float('Category Adjustment Value %', default=0.0)
    competitor_rate_factor = fields.Float('Competitor Rate Factor', default=1.0)
    container_count = fields.Integer('Container Count', default=0)
    current_monthly_revenue = fields.Monetary('Current Monthly Revenue', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id)
    customer_churn_risk = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low')
    customer_growth_potential = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')
    demand_seasonality_factor = fields.Float('Demand Seasonality Factor', default=1.0)
    economic_indicator_impact = fields.Float('Economic Indicator Impact %', default=0.0)
    forecast_accuracy_percentage = fields.Float('Forecast Accuracy %', default=0.0)
    forecast_confidence_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')
    forecast_horizon_months = fields.Integer('Forecast Horizon (Months)', default=12)
    forecast_methodology = fields.Selection([('linear', 'Linear'), ('exponential', 'Exponential'), ('ai_model', 'AI Model')], default='linear')
    market_penetration_rate = fields.Float('Market Penetration Rate %', default=0.0)
    market_size_estimate = fields.Monetary('Market Size Estimate', currency_field='currency_id')
    new_customer_acquisition_rate = fields.Float('New Customer Acquisition Rate %', default=0.0)
    predicted_quarterly_revenue = fields.Monetary('Predicted Quarterly Revenue', currency_field='currency_id')
    pricing_elasticity_factor = fields.Float('Pricing Elasticity Factor', default=1.0)
    revenue_growth_target = fields.Float('Revenue Growth Target %', default=0.0)
    revenue_variance_analysis = fields.Text('Revenue Variance Analysis')
    risk_adjustment_factor = fields.Float('Risk Adjustment Factor', default=1.0)
    scenario_analysis_enabled = fields.Boolean('Scenario Analysis Enabled', default=False)
    service_mix_optimization = fields.Text('Service Mix Optimization')
    trend_analysis_period = fields.Integer('Trend Analysis Period (Months)', default=6)
    volume_price_correlation = fields.Float('Volume-Price Correlation', default=0.0)

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
