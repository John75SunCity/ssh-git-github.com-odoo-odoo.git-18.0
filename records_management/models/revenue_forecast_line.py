from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RevenueForecastLine(models.Model):
    _name = 'revenue.forecast.line'
    _description = 'Revenue Forecast Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'forecast_id, customer_id, service_type'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Description", compute='_compute_name', store=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(related='forecast_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='forecast_id.currency_id', store=True, readonly=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    forecast_id = fields.Many2one('revenue.forecast', string="Forecast", required=True, ondelete='cascade')
    customer_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)

    # ============================================================================
    # FORECAST DETAILS
    # ============================================================================
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('pickup', 'Pickup'),
        ('destruction', 'Destruction'),
        ('other', 'Other'),
    ], string="Service Type", required=True, tracking=True)
    period_type = fields.Selection(related='forecast_id.period_type', string="Period Type", store=True, readonly=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('achieved', 'Achieved'),
        ('missed', 'Missed'),
    ], string="Status", default='draft', required=True, tracking=True)
    confidence_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Confidence Level", default='medium', tracking=True)
    probability_percentage = fields.Float(string="Probability (%)", default=75.0, help="Confidence percentage for achieving this forecast.")

    # ============================================================================
    # FINANCIAL & VOLUME METRICS
    # ============================================================================
    forecasted_amount = fields.Monetary(string="Forecasted Amount", currency_field='currency_id', tracking=True)
    actual_amount = fields.Monetary(string="Actual Amount", currency_field='currency_id', tracking=True)
    variance_amount = fields.Monetary(string="Variance", compute='_compute_variance', store=True)
    variance_percentage = fields.Float(string="Variance (%)", compute='_compute_variance', store=True, aggregator="avg")

    forecasted_volume = fields.Float(string="Forecasted Volume", help="e.g., number of boxes, weight in kg")
    actual_volume = fields.Float(string="Actual Volume")
    forecasted_containers = fields.Integer(string="Forecasted Containers")
    actual_containers = fields.Integer(string="Actual Containers")

    notes = fields.Text(string='Notes')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('forecasted_amount', 'actual_amount', 'forecasted_volume', 'actual_volume', 'forecasted_containers', 'actual_containers')
    def _check_non_negative_values(self):
        for record in self:
            if record.forecasted_amount < 0: raise ValidationError(_('Forecasted amount cannot be negative.'))
            if record.actual_amount < 0: raise ValidationError(_('Actual amount cannot be negative.'))
            if record.forecasted_volume < 0: raise ValidationError(_('Forecasted volume cannot be negative.'))
            if record.actual_volume < 0: raise ValidationError(_('Actual volume cannot be negative.'))
            if record.forecasted_containers < 0: raise ValidationError(_('Forecasted containers cannot be negative.'))
            if record.actual_containers < 0: raise ValidationError(_('Actual containers cannot be negative.'))

    @api.constrains('probability_percentage')
    def _check_probability(self):
        for record in self:
            if not (0 <= record.probability_percentage <= 100):
                raise ValidationError(_('Probability percentage must be between 0 and 100.'))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('customer_id', 'service_type', 'period_type')
    def _compute_name(self):
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
            record.name = " - ".join(parts) if parts else _("New Forecast Line")

    @api.depends('name', 'forecasted_amount', 'currency_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.forecasted_amount:
                amount_str = f"{record.currency_id.name} {record.forecasted_amount:,.2f}"
                record.display_name = f"{record.name} ({amount_str})"
            else:
                record.display_name = record.name or _("New Forecast Line")

    @api.depends('actual_amount', 'forecasted_amount')
    def _compute_variance(self):
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
        self.ensure_one()
        if self.status != 'draft':
            raise UserError(_('Can only confirm draft forecast lines.'))
        self.write({'status': 'confirmed'})
        self.message_post(body=_('Forecast line confirmed.'))

    def action_start_tracking(self):
        self.ensure_one()
        if self.status != 'confirmed':
            raise UserError(_('Can only start tracking confirmed forecasts.'))
        self.write({'status': 'in_progress'})
        self.message_post(body=_('Forecast tracking started.'))

    def action_mark_achieved(self):
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_('Can only mark in-progress forecasts as achieved.'))
        self.write({'status': 'achieved'})
        self.message_post(body=_('Forecast achieved.'))

    def action_mark_missed(self):
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_('Can only mark in-progress forecasts as missed.'))
        self.write({'status': 'missed'})
        self.message_post(body=_('Forecast missed.'))
