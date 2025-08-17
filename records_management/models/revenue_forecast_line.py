from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RevenueForecastLine(models.Model):
    _name = 'revenue.forecast.line'
    _description = 'Revenue Forecast Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'forecast_id, customer_id, service_type'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    forecast_id = fields.Many2one()
    customer_id = fields.Many2one()
    service_type = fields.Selection()
    period_type = fields.Selection()
    currency_id = fields.Many2one()
    forecasted_amount = fields.Monetary()
    actual_amount = fields.Monetary()
    variance_amount = fields.Monetary()
    variance_percentage = fields.Float()
    forecasted_volume = fields.Float()
    actual_volume = fields.Float()
    forecasted_containers = fields.Integer()
    actual_containers = fields.Integer()
    confidence_level = fields.Selection()
    probability_percentage = fields.Float()
    status = fields.Selection()
    notes = fields.Text()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    achieved = fields.Char(string='Achieved')
    action_confirm_forecast = fields.Char(string='Action Confirm Forecast')
    action_mark_achieved = fields.Char(string='Action Mark Achieved')
    action_mark_missed = fields.Char(string='Action Mark Missed')
    action_start_tracking = fields.Char(string='Action Start Tracking')
    confidence = fields.Char(string='Confidence')
    confirmed = fields.Boolean(string='Confirmed')
    context = fields.Char(string='Context')
    destruction = fields.Char(string='Destruction')
    draft = fields.Char(string='Draft')
    financial = fields.Char(string='Financial')
    group_confidence = fields.Char(string='Group Confidence')
    group_customer = fields.Char(string='Group Customer')
    group_service = fields.Char(string='Group Service')
    group_status = fields.Selection(string='Group Status')
    help = fields.Char(string='Help')
    high_confidence = fields.Char(string='High Confidence')
    in_progress = fields.Char(string='In Progress')
    main_info = fields.Char(string='Main Info')
    missed = fields.Char(string='Missed')
    res_model = fields.Char(string='Res Model')
    storage = fields.Char(string='Storage')
    view_mode = fields.Char(string='View Mode')
    volume_metrics = fields.Char(string='Volume Metrics')

    # ============================================================================
    # METHODS
    # ============================================================================
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

                record.name = " - ".join(parts) if parts else "New Forecast Line":

    def _compute_display_name(self):
            """Compute display name"""
            for record in self:
                if record.forecasted_amount:
                    record.display_name = f"{record.name} ({record.forecasted_amount:,.2f})"
                else:
                    record.display_name = record.name or "New Forecast Line"


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

    def _check_amounts(self):
            """Validate amounts are not negative"""
            for record in self:
                if record.forecasted_amount < 0:
                    raise ValidationError(_('Forecasted amount cannot be negative'))
                if record.actual_amount < 0:
                    raise ValidationError(_('Actual amount cannot be negative'))


    def _check_probability(self):
            """Validate probability percentage is between 0 and 100"""
            for record in self:
                if not (0 <= record.probability_percentage <= 100):
                    raise ValidationError(_('Probability percentage must be between 0 and 100'))


    def _check_volumes(self):
            """Validate volumes are not negative"""
            for record in self:
                if record.forecasted_volume < 0:
                    raise ValidationError(_('Forecasted volume cannot be negative'))
                if record.actual_volume < 0:
                    raise ValidationError(_('Actual volume cannot be negative'))


    def _check_containers(self):
            """Validate container counts are not negative"""
            for record in self:
                if record.forecasted_containers < 0:
                    raise ValidationError(_('Forecasted containers cannot be negative'))
                if record.actual_containers < 0:
                    raise ValidationError(_('Actual containers cannot be negative'))
