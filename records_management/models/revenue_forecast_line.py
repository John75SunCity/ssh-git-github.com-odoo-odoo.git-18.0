# -*- coding: utf-8 -*-
"""
Revenue Forecast Line Model

Individual line items for revenue forecasting with customer and service breakdowns.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RevenueForecastLine(models.Model):
    """Revenue Forecast Line"""

    _name = "revenue.forecast.line"
    _description = "Revenue Forecast Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "forecast_id, customer_id, service_type"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Line Description",
        compute='_compute_name',
        store=True,
        help="Computed name based on customer and service"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        help="Display name for the forecast line"
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
        help="Set to false to archive this forecast line"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    forecast_id = fields.Many2one(
        "revenue.forecaster",
        string="Revenue Forecast",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent revenue forecast"
    )

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain="[('is_company', '=', True)]",
        help="Customer for this forecast line"
    )

    # ============================================================================
    # FORECAST DETAILS
    # ============================================================================
    service_type = fields.Selection([
        ('storage', 'Document Storage'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'Document Destruction'),
        ('pickup', 'Pickup Services'),
        ('delivery', 'Delivery Services'),
        ('consulting', 'Consulting Services'),
        ('other', 'Other Services')
    ], string='Service Type', required=True, tracking=True)

    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual')
    ], string='Period Type', default='monthly', required=True)

    # ============================================================================
    # FINANCIAL FIELDS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True
    )

    forecasted_amount = fields.Monetary(
        string="Forecasted Amount",
        currency_field="currency_id",
        required=True,
        tracking=True,
        help="Predicted revenue amount"
    )

    actual_amount = fields.Monetary(
        string="Actual Amount",
        currency_field="currency_id",
        tracking=True,
        help="Actual revenue amount achieved"
    )

    variance_amount = fields.Monetary(
        string="Variance Amount",
        currency_field="currency_id",
        compute='_compute_variance',
        store=True,
        help="Difference between forecasted and actual"
    )

    variance_percentage = fields.Float(
        string="Variance %",
        compute='_compute_variance',
        store=True,
        help="Variance as percentage"
    )

    # ============================================================================
    # VOLUME METRICS
    # ============================================================================
    forecasted_volume = fields.Float(
        string="Forecasted Volume (CF)",
        help="Predicted volume in cubic feet"
    )

    actual_volume = fields.Float(
        string="Actual Volume (CF)",
        help="Actual volume achieved"
    )

    forecasted_containers = fields.Integer(
        string="Forecasted Containers",
        help="Predicted number of containers"
    )

    actual_containers = fields.Integer(
        string="Actual Containers",
        help="Actual number of containers"
    )

    # ============================================================================
    # PROBABILITY AND CONFIDENCE
    # ============================================================================
    confidence_level = fields.Selection([
        ('low', 'Low (0-30%)'),
        ('medium', 'Medium (30-70%)'),
        ('high', 'High (70-90%)'),
        ('very_high', 'Very High (90-100%)')
    ], string='Confidence Level', default='medium', required=True)

    probability_percentage = fields.Float(
        string="Probability %",
        default=50.0,
        help="Probability of achieving this forecast"
    )

    # ============================================================================
    # STATUS AND NOTES
    # ============================================================================
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('achieved', 'Achieved'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    notes = fields.Text(
        string="Notes",
        help="Additional notes and assumptions"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('customer_id', 'service_type', 'period_type')
    def _compute_name(self):
        """Compute line description"""
        for record in self:
            parts = []
            if record.customer_id:
                parts.append(record.customer_id.name)
            if record.service_type:
                service_dict = dict(record._fields['service_type'].selection)
                parts.append(service_dict.get(record.service_type, record.service_type))
            if record.period_type:
                period_dict = dict(record._fields['period_type'].selection)
                parts.append(period_dict.get(record.period_type, record.period_type))
            
            record.name = " - ".join(parts) if parts else "New Forecast Line"

    @api.depends('name', 'forecasted_amount')
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            if record.forecasted_amount:
                record.display_name = f"{record.name} ({record.forecasted_amount:,.2f})"
            else:
                record.display_name = record.name or "New Forecast Line"

    @api.depends('forecasted_amount', 'actual_amount')
    def _compute_variance(self):
        """Calculate variance between forecasted and actual amounts"""
        for record in self:
            record.variance_amount = record.actual_amount - record.forecasted_amount
            
            if record.forecasted_amount:
                record.variance_percentage = (record.variance_amount / record.forecasted_amount) * 100
            else:
                record.variance_percentage = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm_forecast(self):
        """Confirm the forecast line"""
        self.ensure_one()
        if self.status != 'draft':
            raise UserError(_('Can only confirm draft forecast lines'))
        
        self.write({'status': 'confirmed'})
        self.message_post(body=_('Forecast line confirmed'))

    def action_start_tracking(self):
        """Start tracking progress against forecast"""
        self.ensure_one()
        if self.status != 'confirmed':
            raise UserError(_('Can only start tracking confirmed forecasts'))
        
        self.write({'status': 'in_progress'})
        self.message_post(body=_('Forecast tracking started'))

    def action_mark_achieved(self):
        """Mark forecast as achieved"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_('Can only mark in-progress forecasts as achieved'))
        
        self.write({'status': 'achieved'})
        self.message_post(body=_('Forecast achieved'))

    def action_mark_missed(self):
        """Mark forecast as missed"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_('Can only mark in-progress forecasts as missed'))
        
        self.write({'status': 'missed'})
        self.message_post(body=_('Forecast missed'))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('forecasted_amount', 'actual_amount')
    def _check_amounts(self):
        """Validate amounts are not negative"""
        for record in self:
            if record.forecasted_amount < 0:
                raise ValidationError(_('Forecasted amount cannot be negative'))
            if record.actual_amount < 0:
                raise ValidationError(_('Actual amount cannot be negative'))

    @api.constrains('probability_percentage')
    def _check_probability(self):
        """Validate probability percentage is between 0 and 100"""
        for record in self:
            if not (0 <= record.probability_percentage <= 100):
                raise ValidationError(_('Probability percentage must be between 0 and 100'))

    @api.constrains('forecasted_volume', 'actual_volume')
    def _check_volumes(self):
        """Validate volumes are not negative"""
        for record in self:
            if record.forecasted_volume < 0:
                raise ValidationError(_('Forecasted volume cannot be negative'))
            if record.actual_volume < 0:
                raise ValidationError(_('Actual volume cannot be negative'))

    @api.constrains('forecasted_containers', 'actual_containers')
    def _check_containers(self):
        """Validate container counts are not negative"""
        for record in self:
            if record.forecasted_containers < 0:
                raise ValidationError(_('Forecasted containers cannot be negative'))
            if record.actual_containers < 0:
                raise ValidationError(_('Actual containers cannot be negative'))
