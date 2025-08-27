# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class RetrievalMetric(models.Model):
    _name = 'retrieval.metric'
    _description = 'Retrieval Performance Metric'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'metric_date desc, metric_type'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Metric Reference", compute='_compute_display_name', store=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Metric Recorder', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    # Polymorphic relation to link to any type of retrieval item
    retrieval_item_id = fields.Reference(
        selection=[
            ('file.retrieval.item', 'File Retrieval'),
            ('container.retrieval.item', 'Container Retrieval'),
            ('scan.retrieval.item', 'Scan Retrieval')
        ],
        string="Retrieval Item",
        required=True
    )

    team_id = fields.Many2one('maintenance.team', string='Team')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    partner_id = fields.Many2one('res.partner', string='Customer')

    metric_type = fields.Selection([
        ('search_time', 'Search Time'),
        ('retrieval_time', 'Retrieval Time'),
        ('accuracy_rate', 'Accuracy Rate'),
        ('quality_score', 'Quality Score'),
        ('error_count', 'Error Count'),
    ], string='Metric Type', required=True)

    metric_value = fields.Float(string='Metric Value')
    metric_unit = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('percentage', '%'),
        ('units', 'Units'),
        ('score', 'Score'),
    ], string='Unit')

    metric_date = fields.Date(string='Metric Date', default=fields.Date.context_today)
    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)

    target_value = fields.Float(string='Target Value')
    variance = fields.Float(string='Variance', compute='_compute_variance', store=True)
    variance_percentage = fields.Float(string='Variance (%)', compute='_compute_variance_percentage', store=True)

    performance_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('acceptable', 'Acceptable'),
        ('poor', 'Poor'),
        ('unacceptable', 'Unacceptable'),
    ], string='Performance Rating', compute='_compute_performance_rating', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('recorded', 'Recorded'),
        ('validated', 'Validated'),
        ('analyzed', 'Analyzed'),
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Notes')
    improvement_suggestions = fields.Text(string='Improvement Suggestions')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('metric_value')
    def _check_metric_value(self):
        for record in self:
            if record.metric_unit == 'percentage' and not 0 <= record.metric_value <= 100:
                raise ValidationError(_('Percentage values must be between 0 and 100.'))
            if record.metric_value < 0:
                raise ValidationError(_('Metric value cannot be negative.'))

    @api.constrains('start_time', 'end_time')
    def _check_time_sequence(self):
        for record in self:
            if record.start_time and record.end_time and record.start_time > record.end_time:
                raise ValidationError(_('Start time must be before end time.'))

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('metric_type', 'metric_value', 'metric_unit')
    def _compute_display_name(self):
        for record in self:
            metric_label = dict(record._fields['metric_type'].selection).get(record.metric_type, '')
            unit_label = dict(record._fields['metric_unit'].selection).get(record.metric_unit, '')
            record.display_name = _('%s: %.2f %s') % (metric_label, record.metric_value, unit_label)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds() / 3600
            else:
                record.duration = 0.0

    @api.depends('metric_value', 'target_value')
    def _compute_variance(self):
        for record in self:
            if record.target_value:
                record.variance = record.metric_value - record.target_value
            else:
                record.variance = 0.0

    @api.depends('variance', 'target_value')
    def _compute_variance_percentage(self):
        for record in self:
            if record.target_value:
                record.variance_percentage = (record.variance / record.target_value) * 100 if record.target_value else 0.0
            else:
                record.variance_percentage = 0.0

    @api.depends('metric_value', 'target_value', 'metric_type')
    def _compute_performance_rating(self):
        for record in self:
            if not record.target_value:
                record.performance_rating = 'acceptable'
                continue

            # For time-based metrics, lower is better
            if record.metric_type in ['search_time', 'retrieval_time']:
                ratio = record.target_value / record.metric_value if record.metric_value else 0
            else:  # For rate/count metrics, higher is better
                ratio = record.metric_value / record.target_value if record.target_value else 0

            if ratio >= 1.2:
                record.performance_rating = 'excellent'
            elif ratio >= 1.0:
                record.performance_rating = 'good'
            elif ratio >= 0.8:
                record.performance_rating = 'acceptable'
            elif ratio >= 0.6:
                record.performance_rating = 'poor'
            else:
                record.performance_rating = 'unacceptable'

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_record_metric(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Can only record draft metrics.'))
        self.write({'state': 'recorded'})

    def action_validate_metric(self):
        self.ensure_one()
        if self.state != 'recorded':
            raise UserError(_('Can only validate recorded metrics.'))
        self.write({'state': 'validated'})

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        # Override create to set default name if not provided
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            for record in self:
                state_label = dict(record._fields['state'].selection).get(record.state)
                if state_label:
                    record.message_post(body=_('State changed to %s') % state_label)
        return res

