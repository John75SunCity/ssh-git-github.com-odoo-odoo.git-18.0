# -*- coding: utf-8 -*-
"""
Revenue Forecaster Model

Provides revenue forecasting and analysis tools for rate changes and business scenarios.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json


class RevenueForecaster(models.TransientModel):
    """
    Revenue forecasting wizard for analyzing potential revenue impact of rate changes.
    """

    _name = 'revenue.forecaster'
    _description = 'Revenue Forecaster'

    # ============================================================================
    # CONFIGURATION FIELDS
    # ============================================================================
    name = fields.Char(string='Analysis Name', default='Revenue Forecast Analysis')

    forecast_period = fields.Selection([
        ('1_month', '1 Month'),
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('12_months', '12 Months'),
        ('custom', 'Custom Period')
    ], string='Forecast Period', default='12_months', required=True)

    scenario_type = fields.Selection([
        ('global_increase', 'Global Rate Increase'),
        ('global_decrease', 'Global Rate Decrease'),
        ('category_specific', 'Category-Specific Adjustment'),
        ('market_analysis', 'Market Analysis Only')
    ], string='Scenario Type', default='global_increase', required=True)

    customer_segment = fields.Selection([
        ('all_customers', 'All Customers'),
        ('base_rate_customers', 'Base Rate Customers Only'),
        ('negotiated_customers', 'Negotiated Rate Customers Only'),
        ('specific_customers', 'Specific Customers')
    ], string='Customer Segment', default='all_customers', required=True)

    # ============================================================================
    # ANALYSIS PARAMETERS
    # ============================================================================
    global_adjustment_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')
    ], string='Adjustment Type', default='percentage')

    global_adjustment_value = fields.Float(string='Adjustment Value (%)', default=5.0)

    service_category = fields.Selection([
        ('storage', 'Storage Rates'),
        ('pickup_delivery', 'Pickup & Delivery'),
        ('destruction', 'Destruction Services'),
        ('retrieval', 'Document Retrieval'),
        ('scanning', 'Scanning Services')
    ], string='Service Category')

    category_adjustment_value = fields.Float(string='Category Adjustment (%)', default=5.0)

    # ============================================================================
    # MARKET FACTORS
    # ============================================================================
    market_growth_rate = fields.Float(string='Market Growth Rate (%)', default=3.0)
    inflation_rate = fields.Float(string='Inflation Rate (%)', default=2.5)
    customer_retention_rate = fields.Float(string='Expected Retention Rate (%)', default=95.0)
    competitor_rate_factor = fields.Float(string='Competitor Rate Factor', default=1.0)

    # ============================================================================
    # CUSTOM PERIOD
    # ============================================================================
    custom_start_date = fields.Date(string='Start Date')
    custom_end_date = fields.Date(string='End Date')
    specific_customer_ids = fields.Many2many(
        'res.partner',
        string='Specific Customers'
    )

    # ============================================================================
    # RESULTS FIELDS
    # ============================================================================
    analysis_complete = fields.Boolean(string='Analysis Complete', default=False)

    current_monthly_revenue = fields.Monetary(string='Current Monthly Revenue', currency_field='currency_id')
    projected_monthly_revenue = fields.Monetary(string='Projected Monthly Revenue', currency_field='currency_id')
    revenue_difference = fields.Monetary(string='Monthly Revenue Change', currency_field='currency_id', compute='_compute_revenue_analysis', store=True)
    revenue_percentage_change = fields.Float(string='Revenue Change (%)', compute='_compute_revenue_analysis', store=True)
    annual_revenue_impact = fields.Monetary(string='Annual Revenue Impact', currency_field='currency_id', compute='_compute_revenue_analysis', store=True)

    customer_impact_count = fields.Integer(string='Customers Affected')
    risk_assessment = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk')
    ], string='Risk Assessment', compute='_compute_risk_assessment', store=True)

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================================
    # FORECAST LINES
    # ============================================================================
    forecast_line_ids = fields.One2many("revenue.forecaster.line", "forecaster_id", string="Forecast Lines")

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('current_monthly_revenue', 'projected_monthly_revenue')
    def _compute_revenue_analysis(self):
        """Compute revenue analysis metrics."""
        for record in self:
            record.revenue_difference = record.projected_monthly_revenue - record.current_monthly_revenue

            if record.current_monthly_revenue > 0:
                record.revenue_percentage_change = (record.revenue_difference / record.current_monthly_revenue) * 100
            else:
                record.revenue_percentage_change = 0.0

            record.annual_revenue_impact = record.revenue_difference * 12

    @api.depends('revenue_percentage_change', 'customer_retention_rate')
    def _compute_risk_assessment(self):
        """Assess risk level based on revenue change and retention."""
        for record in self:
            if abs(record.revenue_percentage_change) <= 5:
                record.risk_assessment = 'low'
            elif abs(record.revenue_percentage_change) <= 10:
                record.risk_assessment = 'medium'
            elif abs(record.revenue_percentage_change) <= 20:
                record.risk_assessment = 'high'
            else:
                record.risk_assessment = 'very_high'

            # Adjust for retention rate
            if record.customer_retention_rate < 90:
                if record.risk_assessment == 'low':
                    record.risk_assessment = 'medium'
                elif record.risk_assessment == 'medium':
                    record.risk_assessment = 'high'

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_run_forecast(self):
        """Run the revenue forecast analysis."""
        self.ensure_one()

        # Clear previous results
        self.forecast_line_ids.unlink()

        # Get affected customers
        customers = self._get_affected_customers()

        # Calculate current and projected revenue
        current_revenue = 0.0
        projected_revenue = 0.0
        forecast_lines = []

        for customer in customers:
            current_monthly = self._calculate_customer_monthly_revenue(customer)
            projected_monthly = self._calculate_projected_revenue(customer, current_monthly)

            current_revenue += current_monthly
            projected_revenue += projected_monthly

            # Create forecast line
            forecast_lines.append({
                'partner_id': customer.id,
                'customer_segment': self._get_customer_segment(customer),
                'container_count': self._get_customer_container_count(customer),
                'current_monthly_revenue': current_monthly,
                'projected_monthly_revenue': projected_monthly,
                'revenue_change': projected_monthly - current_monthly,
                'revenue_change_percentage': ((projected_monthly - current_monthly) / current_monthly * 100) if current_monthly > 0 else 0,
                'risk_level': self._assess_customer_risk(customer, projected_monthly - current_monthly),
                'forecaster_id': self.id,
            })

        # Create forecast lines
        self.env["revenue.forecaster.line"].create(forecast_lines)

        # Update results
        self.write({
            'current_monthly_revenue': current_revenue,
            'projected_monthly_revenue': projected_revenue,
            'customer_impact_count': len(customers),
            'analysis_complete': True,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Analysis Complete'),
                'message': _('Revenue forecast analysis completed successfully.'),
                'type': 'success'
            }
        }

    def action_export_forecast(self):
        """Export forecast results to Excel."""
        self.ensure_one()

        if not self.analysis_complete:
            raise UserError(_('Please run the forecast analysis first.'))

        # This would typically generate an Excel file
        # For now, return a notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Export Initiated'),
                'message': _('Forecast data export has been initiated.'),
                'type': 'info'
            }
        }

    def action_apply_scenario(self):
        """Apply the forecasted rate changes."""
        self.ensure_one()

        if not self.analysis_complete:
            raise UserError(_('Please run the forecast analysis first.'))

        # This would implement the rate changes
        # For now, return a confirmation dialog
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirm Rate Changes'),
            'res_model': 'rate.change.confirmation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_forecaster_id': self.id,
                'default_revenue_impact': self.revenue_difference,
                'default_customer_count': self.customer_impact_count,
            }
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _get_affected_customers(self):
        """Get customers affected by the rate change scenario."""
        domain = [('is_company', '=', True)]

        if self.customer_segment == 'base_rate_customers':
            # Customers without negotiated rates
            negotiated_partners = self.env['customer.negotiated.rate'].search([
                ('state', '=', 'active')
            ]).mapped('partner_id')
            domain.append(('id', 'not in', negotiated_partners.ids))

        elif self.customer_segment == 'negotiated_customers':
            # Customers with negotiated rates
            negotiated_partners = self.env['customer.negotiated.rate'].search([
                ('state', '=', 'active')
            ]).mapped('partner_id')
            domain.append(('id', 'in', negotiated_partners.ids))

        elif self.customer_segment == 'specific_customers':
            domain.append(('id', 'in', self.specific_customer_ids.ids))

        return self.env['res.partner'].search(domain)

    def _calculate_customer_monthly_revenue(self, customer):
        """Calculate current monthly revenue for a customer."""
        # This would typically query billing records
        # For now, return estimated based on container count
        container_count = self._get_customer_container_count(customer)
        base_rate = self.env['base.rate'].search([('active', '=', True)], limit=1)

        if base_rate and container_count > 0:
            return container_count * (base_rate.standard_box_rate or 25.0)

        return 0.0

    def _calculate_projected_revenue(self, customer, current_revenue):
        """Calculate projected revenue after rate changes."""
        if self.scenario_type == 'market_analysis':
            return current_revenue

        adjustment_factor = 1.0

        if self.scenario_type in ['global_increase', 'global_decrease']:
            if self.global_adjustment_type == 'percentage':
                adjustment_factor = 1 + (self.global_adjustment_value / 100)
                if self.scenario_type == 'global_decrease':
                    adjustment_factor = 1 - (self.global_adjustment_value / 100)

        elif self.scenario_type == 'category_specific':
            # Apply category-specific adjustments
            adjustment_factor = 1 + (self.category_adjustment_value / 100)

        # Apply market factors
        market_factor = 1 + (self.market_growth_rate / 100)
        retention_factor = self.customer_retention_rate / 100

        return current_revenue * adjustment_factor * market_factor * retention_factor

    def _get_customer_segment(self, customer):
        """Determine customer segment."""
        negotiated_rate = self.env['customer.negotiated.rate'].search([
            ('partner_id', '=', customer.id),
            ('state', '=', 'active')
        ], limit=1)

        if negotiated_rate:
            return 'negotiated'
        else:
            return 'base_rate'

    def _get_customer_container_count(self, customer):
        """Get container count for customer."""
        return self.env['records.container'].search_count([
            ('partner_id', '=', customer.id),
            ('active', '=', True)
        ])

    def _assess_customer_risk(self, customer, revenue_change):
        """Assess risk level for individual customer."""
        if abs(revenue_change) <= 100:
            return 'low'
        elif abs(revenue_change) <= 500:
            return 'medium'
        elif abs(revenue_change) <= 1000:
            return 'high'
        else:
            return 'very_high'


class RevenueForecasterLine(models.TransientModel):
    """
    Individual customer forecast line for detailed analysis.
    """

    _name = "revenue.forecaster.line"
    _description = "Revenue Forecaster Line"

    forecaster_id = fields.Many2one('revenue.forecaster', string='Forecaster', ondelete='cascade')

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    customer_segment = fields.Selection([
        ('base_rate', 'Base Rate'),
        ('negotiated', 'Negotiated Rate')
    ], string='Customer Segment')

    container_count = fields.Integer(string='Container Count')

    current_monthly_revenue = fields.Monetary(string='Current Monthly Revenue', currency_field='currency_id')
    projected_monthly_revenue = fields.Monetary(string='Projected Monthly Revenue', currency_field='currency_id')
    revenue_change = fields.Monetary(string='Revenue Change', currency_field='currency_id')
    revenue_change_percentage = fields.Float(string='Change (%)')

    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High')
    ], string='Risk Level')

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
