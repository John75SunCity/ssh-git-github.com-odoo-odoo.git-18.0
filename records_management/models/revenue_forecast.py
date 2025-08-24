from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class RevenueForecast(models.Model):
    _name = 'revenue.forecast'
    _description = 'Revenue Forecast'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Forecast Name", required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # PERIOD & TYPE
    # ============================================================================
    date_start = fields.Date(string="Start Date", required=True, tracking=True)
    date_end = fields.Date(string="End Date", required=True, tracking=True)
    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ], string="Period Type", required=True, default='quarterly', tracking=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    forecast_line_ids = fields.One2many('revenue.forecast.line', 'forecast_id', string="Forecast Lines")

    # ============================================================================
    # AGGREGATED FINANCIAL METRICS (COMPUTED)
    # ============================================================================
    total_forecasted_amount = fields.Monetary(string="Total Forecasted Revenue", compute='_compute_aggregated_amounts', store=True)
    total_actual_amount = fields.Monetary(string="Total Actual Revenue", compute='_compute_aggregated_amounts', store=True)
    total_variance_amount = fields.Monetary(string="Total Variance", compute='_compute_aggregated_amounts', store=True)
    achievement_percentage = fields.Float(string="Achievement (%)", compute='_compute_aggregated_amounts', store=True, aggregator="avg")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('forecast_line_ids.forecasted_amount', 'forecast_line_ids.actual_amount')
    def _compute_aggregated_amounts(self):
        """Compute total amounts from all forecast lines."""
        for forecast in self:
            total_forecasted = sum(forecast.forecast_line_ids.mapped('forecasted_amount'))
            total_actual = sum(forecast.forecast_line_ids.mapped('actual_amount'))

            forecast.total_forecasted_amount = total_forecasted
            forecast.total_actual_amount = total_actual
            forecast.total_variance_amount = total_actual - total_forecasted

            if total_forecasted > 0:
                forecast.achievement_percentage = (total_actual / total_forecasted) * 100
            else:
                forecast.achievement_percentage = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        if not self.forecast_line_ids:
            raise UserError(_("You cannot confirm a forecast with no lines."))
        self.write({'state': 'confirmed'})
        self.forecast_line_ids.write({'status': 'confirmed'})
        self.message_post(body=_("Forecast confirmed."))

    def action_start_tracking(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        self.forecast_line_ids.filtered(lambda l: l.status == 'confirmed').write({'status': 'in_progress'})
        self.message_post(body=_("Forecast tracking started."))

    def action_close(self):
        self.ensure_one()
        self.write({'state': 'closed'})
        self.message_post(body=_("Forecast closed."))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Forecast cancelled."))

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.forecast_line_ids.write({'status': 'draft'})
        self.message_post(body=_("Forecast reset to draft."))

    def action_generate_forecast_lines(self):
        """Generate forecast lines based on the period type."""
        self.ensure_one()
        if self.state not in ['draft', 'confirmed']:
            raise UserError(_("You can only generate lines for a forecast in draft or confirmed state."))

        # Clear existing lines to prevent duplicates
        self.forecast_line_ids.unlink()

        lines_to_create = []
        start_date = self.date_start
        end_date = self.date_end

        if self.period_type == 'monthly':
            current_date = start_date
            while current_date <= end_date:
                period_start = current_date
                period_end = current_date + relativedelta(months=1, days=-1)
                if period_end > end_date:
                    period_end = end_date

                lines_to_create.append({
                    'name': _("Forecast for %s") % period_start.strftime('%B %Y'),
                    'date_start': period_start,
                    'date_end': period_end,
                    'forecast_id': self.id,
                })
                current_date += relativedelta(months=1)

        elif self.period_type == 'quarterly':
            current_date = start_date
            quarter = (start_date.month - 1) // 3 + 1
            year = start_date.year
            while current_date <= end_date:
                period_start = current_date
                period_end = current_date + relativedelta(months=3, days=-1)
                if period_end > end_date:
                    period_end = end_date

                lines_to_create.append({
                    'name': _("Forecast for Q%s %s") % (quarter, year),
                    'date_start': period_start,
                    'date_end': period_end,
                    'forecast_id': self.id,
                })
                current_date += relativedelta(months=3)
                quarter = (current_date.month - 1) // 3 + 1
                year = current_date.year

        elif self.period_type == 'annual':
            lines_to_create.append({
                'name': _("Forecast for %s") % start_date.strftime('%Y'),
                'date_start': start_date,
                'date_end': end_date,
                'forecast_id': self.id,
            })

        if lines_to_create:
            self.env['revenue.forecast.line'].create(lines_to_create)
            self.message_post(body=_("%s forecast lines have been generated.") % len(lines_to_create))

        return True
