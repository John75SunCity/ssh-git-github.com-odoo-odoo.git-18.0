# -*- coding: utf-8 -*-
"""
Revenue Forecaster - Financial Planning and Rate Analysis
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class RevenueForecaster(models.Model):
    """
    Revenue Forecaster Model
    Handles financial planning, rate analysis, and revenue projections
    """

    _name = 'revenue.forecaster'
    _description = 'Revenue Forecaster'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string='Forecast Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Created By', 
                            default=lambda self: self.env.user, tracking=True)

    # ==========================================
    # FORECAST CONFIGURATION
    # ==========================================
    scenario_type = fields.Selection([
        ('global_increase', 'Global Rate Increase'),
        ('category_specific', 'Category-Specific Changes'),
        ('customer_specific', 'Customer-Specific Adjustments'),
        ('market_analysis', 'Market Analysis'),
        ('seasonal_adjustment', 'Seasonal Adjustments')
    ], string='Scenario Type', required=True, default='global_increase', tracking=True)

    forecast_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('multi_year', 'Multi-Year')
    ], string='Forecast Period', default='annual', required=True)

    start_date = fields.Date(string='Forecast Start Date', required=True, 
                           default=fields.Date.today, tracking=True)
    end_date = fields.Date(string='Forecast End Date', required=True, tracking=True)

    # ==========================================
    # GLOBAL ADJUSTMENT SETTINGS
    # ==========================================
    global_adjustment_type = fields.Selection([
        ('percentage', 'Percentage Increase'),
        ('fixed_amount', 'Fixed Amount Increase')
    ], string='Global Adjustment Type', default='percentage')

    global_adjustment_value = fields.Float(string='Adjustment Value', 
                                         help="Enter percentage (e.g., 5 for 5%) or fixed amount")

    # ==========================================
    # CATEGORY-SPECIFIC SETTINGS  
    # ==========================================
    service_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'Secure Destruction'),
        ('scanning', 'Document Scanning'),
        ('transport', 'Transportation'),
        ('consulting', 'Consulting Services')
    ], string='Service Category')

    category_adjustment_value = fields.Float(string='Category Adjustment (%)', 
                                           help="Percentage adjustment for this category")

    # ==========================================
    # CUSTOMER-SPECIFIC SETTINGS
    # ==========================================
    specific_customer_ids = fields.Many2many('res.partner', 
                                            string='Target Customers',
                                            domain=[('is_company', '=', True)])

    customer_adjustment_type = fields.Selection([
        ('volume_based', 'Volume-Based Pricing'),
        ('contract_renegotiation', 'Contract Renegotiation'),
        ('loyalty_discount', 'Loyalty Discount'),
        ('premium_service', 'Premium Service Pricing')
    ], string='Customer Adjustment Type')

    # ==========================================
    # FINANCIAL PROJECTIONS
    # ==========================================
    current_revenue = fields.Float(string='Current Annual Revenue', digits=(12, 2))
    projected_revenue = fields.Float(string='Projected Revenue', 
                                   compute='_compute_projected_revenue', 
                                   store=True, digits=(12, 2))
    revenue_increase = fields.Float(string='Revenue Increase', 
                                  compute='_compute_revenue_increase', 
                                  store=True, digits=(12, 2))
    revenue_increase_percentage = fields.Float(string='Revenue Increase %', 
                                             compute='_compute_revenue_increase_percentage', 
                                             store=True, digits=(12, 2))

    # ==========================================
    # MARKET ANALYSIS
    # ==========================================
    market_growth_rate = fields.Float(string='Market Growth Rate (%)', digits=(12, 2))
    competitor_analysis = fields.Text(string='Competitor Analysis')
    market_position = fields.Selection([
        ('premium', 'Premium Pricing'),
        ('competitive', 'Competitive Pricing'),
        ('value', 'Value Pricing'),
        ('penetration', 'Market Penetration')
    ], string='Market Position', default='competitive')

    # ==========================================
    # RISK ASSESSMENT
    # ==========================================
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk')
    ], string='Risk Level', compute='_compute_risk_level', store=True)

    customer_retention_risk = fields.Float(string='Customer Retention Risk (%)', 
                                         digits=(12, 2), default=5.0)
    competitive_response_risk = fields.Float(string='Competitive Response Risk (%)', 
                                           digits=(12, 2), default=10.0)

    # ==========================================
    # IMPLEMENTATION TRACKING
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('analysis', 'Under Analysis'),
        ('review', 'Management Review'),
        ('approved', 'Approved'),
        ('implemented', 'Implemented'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    implementation_date = fields.Date(string='Implementation Date', tracking=True)
    actual_revenue_impact = fields.Float(string='Actual Revenue Impact', digits=(12, 2))

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    rate_change_wizard_ids = fields.One2many('rate.change.confirmation.wizard', 
                                            'forecast_id', 
                                            string='Rate Change Wizards')

    # ==========================================
    # COMPUTE METHODS
    # ==========================================
    @api.depends('current_revenue', 'global_adjustment_value', 'global_adjustment_type', 'scenario_type')
    def _compute_projected_revenue(self):
        for record in self:
            if record.scenario_type == 'global_increase':
                if record.global_adjustment_type == 'percentage':
                    record.projected_revenue = record.current_revenue * (1 + record.global_adjustment_value / 100)
                else:
                    record.projected_revenue = record.current_revenue + record.global_adjustment_value
            elif record.scenario_type == 'category_specific':
                # Simplified calculation - could be more sophisticated
                category_impact = record.current_revenue * 0.3 * (record.category_adjustment_value / 100)
                record.projected_revenue = record.current_revenue + category_impact
            else:
                record.projected_revenue = record.current_revenue

    @api.depends('current_revenue', 'projected_revenue')
    def _compute_revenue_increase(self):
        for record in self:
            record.revenue_increase = record.projected_revenue - record.current_revenue

    @api.depends('current_revenue', 'revenue_increase')
    def _compute_revenue_increase_percentage(self):
        for record in self:
            if record.current_revenue:
                record.revenue_increase_percentage = (record.revenue_increase / record.current_revenue) * 100
            else:
                record.revenue_increase_percentage = 0

    @api.depends('global_adjustment_value', 'customer_retention_risk', 'competitive_response_risk')
    def _compute_risk_level(self):
        for record in self:
            total_risk = record.customer_retention_risk + record.competitive_response_risk
            if record.global_adjustment_value > 10 or total_risk > 20:
                record.risk_level = 'high'
            elif record.global_adjustment_value > 5 or total_risk > 10:
                record.risk_level = 'medium'
            else:
                record.risk_level = 'low'

    # ==========================================
    # BUSINESS METHODS
    # ==========================================
    def _get_target_customers(self):
        """Get customers affected by this forecast"""
        if self.scenario_type == 'customer_specific':
            return self.specific_customer_ids
        elif self.scenario_type == 'category_specific':
            # Return customers who use the specific service category
            return self.env['res.partner'].search([
                ('is_company', '=', True),
                # Add domain to filter by service category usage
            ])
        else:
            # Global changes affect all customers
            return self.env['res.partner'].search([('is_company', '=', True)])

    def action_start_analysis(self):
        """Start the forecast analysis"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft forecasts can be analyzed'))
        
        self.write({'state': 'analysis'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Forecast analysis started'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_submit_for_review(self):
        """Submit forecast for management review"""
        self.ensure_one()
        if self.state != 'analysis':
            raise UserError(_('Forecast must be analyzed before review'))
            
        self.write({'state': 'review'})
        
        # Create activity for management review
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_('Review Revenue Forecast: %s') % self.name,
            user_id=self.env.ref('records_management.group_records_manager').users[0].id if self.env.ref('records_management.group_records_manager').users else self.env.user.id
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Forecast submitted for management review'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_approve(self):
        """Approve the forecast"""
        self.ensure_one()
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_('Only managers can approve forecasts'))
            
        if self.state != 'review':
            raise UserError(_('Forecast must be in review state to approve'))
            
        self.write({'state': 'approved'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Forecast approved successfully'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_implement(self):
        """Mark forecast as implemented"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved forecasts can be implemented'))
            
        self.write({
            'state': 'implemented',
            'implementation_date': fields.Date.today()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Forecast marked as implemented'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_cancel(self):
        """Cancel the forecast"""
        self.ensure_one()
        if self.state == 'implemented':
            raise UserError(_('Cannot cancel implemented forecasts'))
            
        self.write({'state': 'cancelled'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Forecast cancelled'),
                'type': 'warning',
                'sticky': False,
            },
        }

    def action_create_rate_change_wizard(self):
        """Create rate change confirmation wizard"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Forecast must be approved before creating rate change wizard'))
            
        wizard = self.env['rate.change.confirmation.wizard'].create({
            'forecast_id': self.id,
            'revenue_impact': self.revenue_increase,
            'customer_count': len(self._get_target_customers()),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rate Change Confirmation'),
            'res_model': 'rate.change.confirmation.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate forecast dates"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date >= record.end_date:
                    raise ValidationError(_('Start date must be before end date'))
