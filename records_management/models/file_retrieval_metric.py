# -*- coding: utf-8 -*-
"""
File Retrieval Metrics Model

Metrics and performance tracking for file retrieval operations.
Provides comprehensive analytics for retrieval efficiency, accuracy rates,
and team performance optimization within Records Management system.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FileRetrievalMetric(models.Model):
    """
    File Retrieval Performance Metrics

    Tracks and analyzes performance metrics for file retrieval operations
    including search times, accuracy rates, and team performance measurements
    for continuous improvement and NAID compliance reporting.
    """

    _name = "file.retrieval.metric"
    _description = "File Retrieval Performance Metric"
from odoo.exceptions import ValidationError


class DocumentRetrievalMetric(models.Model):
    """
    Document Retrieval Performance Metrics

    Tracks and analyzes performance metrics for document retrieval operations
    including search times, accuracy rates, and team efficiency measurements
    for continuous improvement and NAID compliance reporting.
    """

    _name = "file.retrieval.metric"
    _description = "Document Retrieval Performance Metric"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "retrieval_date desc, metric_type"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Metric Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the performance metric"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="Display name for the metric"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    user_id = fields.Many2one(
        "res.users",
        string="Recorded By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who recorded this metric"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this metric"
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Display sequence for ordering"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    work_order_id = fields.Many2one(
        "file.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete="cascade",
        index=True,
        help="Related work order"
    )

    team_id = fields.Many2one(
        "file.retrieval.team",
        string="Retrieval Team",
        help="Team responsible for this retrieval metric"
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        help="Employee who performed the retrieval"
    )

    container_id = fields.Many2one(
        "records.container",
        string="Container",
        help="Container being processed"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="work_order_id.partner_id",
        readonly=True,
        store=True,
        help="Customer for this retrieval operation"
    )

    # ============================================================================
    # METRIC DETAILS
    # ============================================================================
    metric_type = fields.Selection([
        ('file_search_time', 'File Search Time'),
        ('file_retrieval_time', 'Physical File Retrieval Time'),
        ('file_scanning_time', 'File Scanning Duration'),
        ('file_accuracy_rate', 'File Retrieval Accuracy'),
        ('container_access_time', 'Container Access Time'),
        ('container_retrieval_time', 'Container Retrieval Time'),
        ('container_movement_time', 'Container Movement Time'),
        ('scan_processing_time', 'Scan Processing Time'),
        ('scan_quality_check_time', 'Scan Quality Check Duration'),
        ('success_rate', 'Success Rate'),
        ('files_found', 'Files Found Count'),
        ('files_requested', 'Files Requested Count'),
        ('containers_accessed', 'Containers Accessed Count'),
        ('pages_scanned', 'Pages Scanned Count'),
        ('travel_time', 'Travel Time'),
        ('processing_time', 'Total Processing Time'),
        ('packaging_time', 'Packaging Time')
    ], string='Metric Type', required=True, tracking=True, index=True)

    metric_value = fields.Float(
        string="Metric Value",
        required=True,
        digits=(12, 2),
        help="Numerical value of the metric"
    )

    metric_unit = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('seconds', 'Seconds'),
        ('percentage', 'Percentage'),
        ('count', 'Count'),
        ('files', 'Files'),
        ('containers', 'Containers'),
        ('pages', 'Pages'),
        ('folders', 'Folders'),
        ('items', 'Items')
    ], string='Unit', default='minutes', required=True)

    # ============================================================================
    # DATE AND TIME TRACKING
    # ============================================================================
    retrieval_date = fields.Date(
        string="Retrieval Date",
        required=True,
        default=fields.Date.today,
        index=True,
        help="Date when retrieval was performed"
    )

    start_time = fields.Datetime(
        string="Start Time",
        help="When the measured activity started"
    )

    end_time = fields.Datetime(
        string="End Time",
        help="When the measured activity ended"
    )

    duration = fields.Float(
        string="Duration",
        compute='_compute_duration',
        store=True,
        help="Calculated duration in hours"
    )

    # ============================================================================
    # PERFORMANCE ANALYSIS
    # ============================================================================
    target_value = fields.Float(
        string="Target Value",
        digits=(12, 2),
        help="Target or expected value for this metric"
    )

    variance = fields.Float(
        string="Variance",
        compute='_compute_variance',
        store=True,
        digits=(12, 2),
        help="Difference from target value"
    )

    variance_percentage = fields.Float(
        string="Variance %",
        compute='_compute_variance_percentage',
        store=True,
        digits=(5, 2),
        help="Variance as percentage of target"
    )

    performance_rating = fields.Selection([
        ('excellent', 'Excellent (>120% of target)'),
        ('good', 'Good (100-120% of target)'),
        ('acceptable', 'Acceptable (80-100% of target)'),
        ('poor', 'Poor (60-80% of target)'),
        ('unacceptable', 'Unacceptable (<60% of target)')
    ], string='Performance Rating', compute='_compute_performance_rating', store=True)

    # ============================================================================
    # QUALITY METRICS
    # ============================================================================
    accuracy_percentage = fields.Float(
        string="Accuracy %",
        default=100.0,
        digits=(5, 2),
        help="Accuracy percentage for retrieval"
    )

    quality_score = fields.Float(
        string="Quality Score",
        compute='_compute_quality_score',
        store=True,
        digits=(5, 2),
        help="Overall quality score"
    )

    error_count = fields.Integer(
        string="Error Count",
        default=0,
        help="Number of errors during retrieval"
    )

    rework_required = fields.Boolean(
        string="Rework Required",
        default=False,
        tracking=True,
        help="Whether rework was required"
    )

    # ============================================================================
    # CONTEXTUAL INFORMATION
    # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Storage Location",
        help="Location where retrieval occurred"
    )

    complexity_level = fields.Selection([
        ('simple', 'Simple'),
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
        ('very_complex', 'Very Complex')
    ], string='Complexity Level', default='moderate', tracking=True)

    difficulty_factors = fields.Text(
        string="Difficulty Factors",
        help="Factors that affected retrieval difficulty"
    )

    # ============================================================================
    # PROCESS STATE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('recorded', 'Recorded'),
        ('validated', 'Validated'),
        ('analyzed', 'Analyzed')
    ], string='Status', default='draft', tracking=True)

    # ============================================================================
    # NOTES AND OBSERVATIONS
    # ============================================================================
    notes = fields.Text(
        string="Performance Notes",
        help="Additional notes about the performance"
    )

    improvement_suggestions = fields.Text(
        string="Improvement Suggestions",
        help="Suggestions for performance improvement"
    )

    lessons_learned = fields.Text(
        string="Lessons Learned",
        help="Key lessons learned from this retrieval"
    )

    # ============================================================================
    # BENCHMARKING DATA
    # ============================================================================
    benchmark_value = fields.Float(
        string="Benchmark Value",
        digits=(12, 2),
        help="Industry or internal benchmark value"
    )

    benchmark_comparison = fields.Selection([
        ('above', 'Above Benchmark'),
        ('at', 'At Benchmark'),
        ('below', 'Below Benchmark'),
        ('no_data', 'No Benchmark Data')
    ], string='Benchmark Comparison', compute='_compute_benchmark_comparison', store=True)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'metric_type', 'metric_value', 'metric_unit')
    def _compute_display_name(self):
        """Compute display name with proper translation"""
        for record in self:
            metric_dict = dict(record._fields['metric_type'].selection)
            metric_label = metric_dict.get(record.metric_type, record.metric_type)
            unit_dict = dict(record._fields['metric_unit'].selection)
            unit_label = unit_dict.get(record.metric_unit, record.metric_unit)

            record.display_name = _("%s: %s %s", metric_label, record.metric_value, unit_label)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Calculate duration between start and end time"""
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds() / 3600  # Convert to hours
            else:
                record.duration = 0.0

    @api.depends('metric_value', 'target_value')
    def _compute_variance(self):
        """Calculate variance from target"""
        for record in self:
            if record.target_value:
                record.variance = record.metric_value - record.target_value
            else:
                record.variance = 0.0

    @api.depends('variance', 'target_value')
    def _compute_variance_percentage(self):
        """Calculate variance percentage"""
        for record in self:
            if record.target_value and record.target_value != 0:
                record.variance_percentage = (record.variance / record.target_value) * 100
            else:
                record.variance_percentage = 0.0

    @api.depends('metric_value', 'target_value', 'metric_type')
    def _compute_performance_rating(self):
        """Compute performance rating based on target achievement"""
        for record in self:
            if not record.target_value or record.target_value == 0:
                record.performance_rating = 'acceptable'
                continue

            # For time-based metrics, lower is better
            if record.metric_type in ['file_search_time', 'file_retrieval_time', 'file_scanning_time',
                                    'container_access_time', 'container_retrieval_time', 'container_movement_time',
                                    'scan_processing_time', 'scan_quality_check_time', 'travel_time', 'processing_time']:
                ratio = record.target_value / record.metric_value if record.metric_value != 0 else 0
            else:
                # For rate/count metrics, higher is better
                ratio = record.metric_value / record.target_value

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

    @api.depends('accuracy_percentage', 'performance_rating', 'error_count')
    def _compute_quality_score(self):
        """Calculate overall quality score"""
        for record in self:
            base_score = record.accuracy_percentage

            # Adjust based on performance rating
            rating_multiplier = {
                'excellent': 1.2,
                'good': 1.1,
                'acceptable': 1.0,
                'poor': 0.9,
                'unacceptable': 0.8
            }

            multiplier = rating_multiplier.get(record.performance_rating, 1.0)

            # Factor in error count
            error_penalty = record.error_count * 2  # 2 points per error

            quality_score = (base_score * multiplier) - error_penalty
            record.quality_score = max(min(quality_score, 100.0), 0.0)

    @api.depends('metric_value', 'benchmark_value')
    def _compute_benchmark_comparison(self):
        """Compare metric value to benchmark"""
        for record in self:
            if not record.benchmark_value or record.benchmark_value == 0:
                record.benchmark_comparison = 'no_data'
            elif record.metric_value > record.benchmark_value * 1.05:  # 5% tolerance
                record.benchmark_comparison = 'above'
            elif record.metric_value < record.benchmark_value * 0.95:  # 5% tolerance
                record.benchmark_comparison = 'below'
            else:
                record.benchmark_comparison = 'at'

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('metric_value')
    def _check_metric_value(self):
        """Validate metric value based on type"""
        for record in self:
            if record.metric_type in ['file_accuracy_rate', 'success_rate'] and record.metric_unit == 'percentage':
                if not 0 <= record.metric_value <= 100:
                    raise ValidationError(_('Percentage values must be between 0 and 100'))

            if record.metric_value < 0:
                raise ValidationError(_('Metric value cannot be negative'))

    @api.constrains('accuracy_percentage')
    def _check_accuracy_percentage(self):
        """Validate accuracy percentage"""
        for record in self:
            if not 0 <= record.accuracy_percentage <= 100:
                raise ValidationError(_('Accuracy percentage must be between 0 and 100'))

    @api.constrains('start_time', 'end_time')
    def _check_time_sequence(self):
        """Validate time sequence"""
        for record in self:
            if record.start_time and record.end_time:
                if record.start_time > record.end_time:
                    raise ValidationError(_('Start time must be before end time'))

    @api.constrains('target_value', 'benchmark_value')
    def _check_positive_values(self):
        """Ensure target and benchmark values are positive"""
        for record in self:
            if record.target_value and record.target_value < 0:
                raise ValidationError(_('Target value cannot be negative'))
            if record.benchmark_value and record.benchmark_value < 0:
                raise ValidationError(_('Benchmark value cannot be negative'))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_record_metric(self):
        """Record the metric"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Can only record draft metrics'))

        self.write({'state': 'recorded'})
        self.message_post(body=_('Metric recorded: %s', self.display_name))

    def action_validate_metric(self):
        """Validate the metric"""
        self.ensure_one()
        if self.state != 'recorded':
            raise ValidationError(_('Can only validate recorded metrics'))

        self.write({'state': 'validated'})
        self.message_post(body=_('Metric validated: %s', self.display_name))

    def action_analyze_metric(self):
        """Analyze the metric for insights"""
        self.ensure_one()
        if self.state != 'validated':
            raise ValidationError(_('Can only analyze validated metrics'))

        self.write({'state': 'analyzed'})
        self._generate_insights()
        self.message_post(body=_('Metric analyzed: %s', self.display_name))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _generate_insights(self):
        """Generate performance insights"""
        self.ensure_one()

        insights = []

        # Performance analysis
        if self.performance_rating == 'excellent':
            insights.append(_('Exceptional performance - consider using as benchmark'))
        elif self.performance_rating == 'unacceptable':
            insights.append(_('Performance needs immediate attention'))

        # Quality analysis
        if self.quality_score < 70:
            insights.append(_('Quality score below acceptable threshold'))

        # Time efficiency analysis
        if self.metric_type.endswith('_time') and self.variance_percentage > 20:
            insights.append(_('Time variance significantly above target'))

        if insights:
            current_suggestions = self.improvement_suggestions or ''
            new_suggestions = '\n'.join(insights)
            self.improvement_suggestions = _('%s\n\nGenerated Insights:\n%s', current_suggestions, new_suggestions).strip()

    @api.model
    def get_performance_dashboard_data(self, date_from=None, date_to=None):
        """Get performance dashboard data"""
        domain = []
        if date_from:
            domain.append(('retrieval_date', '>=', date_from))
        if date_to:
            domain.append(('retrieval_date', '<=', date_to))

        metrics = self.search(domain)

        # Calculate averages by metric type
        dashboard_data = {}
        for metric_type in ['file_search_time', 'file_retrieval_time', 'file_accuracy_rate', 'container_access_time']:
            type_metrics = metrics.filtered(lambda m: m.metric_type == metric_type)
            if type_metrics:
                dashboard_data[metric_type] = {
                    'average': sum(type_metrics.mapped('metric_value')) / len(type_metrics),
                    'count': len(type_metrics),
                    'best': min(type_metrics.mapped('metric_value')),
                    'worst': max(type_metrics.mapped('metric_value'))
                }

        return dashboard_data

    def get_trend_data(self, days=30):
        """Get trend data for this metric type"""
        self.ensure_one()

        from_date = fields.Date.subtract(fields.Date.today(), days=days)

        similar_metrics = self.search([
            ('metric_type', '=', self.metric_type),
            ('retrieval_date', '>=', from_date),
            ('state', '!=', 'draft')
        ], order='retrieval_date')

        trend_data = []
        for metric in similar_metrics:
            trend_data.append({
                'date': metric.retrieval_date,
                'value': metric.metric_value,
                'quality_score': metric.quality_score
            })

        return trend_data

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name"""
        for vals in vals_list:
            if not vals.get('name'):
                metric_type = vals.get('metric_type', 'unknown')
                vals['name'] = _('Metric: %s', metric_type.replace('_', ' ').title())

        return super().create(vals_list)

    def write(self, vals):
        """Override write for modification tracking"""
        result = super().write(vals)

        if 'state' in vals:
            for record in self:
                state_label = dict(record._fields['state'].selection)[record.state]
                record.message_post(body=_('State changed to %s', state_label))

        return result

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.display_name or record.name
            if record.state != 'draft':
                state_label = dict(record._fields['state'].selection)[record.state]
                name = _('%s [%s]', name, state_label)
            result.append((record.id, name))
        return result

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================
    @api.model
    def get_metric_summary(self, metric_type=None, team_id=None, date_from=None, date_to=None):
        """Get metric summary for reporting"""
        domain = [('state', '!=', 'draft')]

        if metric_type:
            domain.append(('metric_type', '=', metric_type))
        if team_id:
            domain.append(('team_id', '=', team_id))
        if date_from:
            domain.append(('retrieval_date', '>=', date_from))
        if date_to:
            domain.append(('retrieval_date', '<=', date_to))

        metrics = self.search(domain)

        summary = {
            'total_metrics': len(metrics),
            'average_quality_score': sum(metrics.mapped('quality_score')) / len(metrics) if metrics else 0,
            'performance_distribution': {},
            'metric_type_breakdown': {}
        }

        # Performance rating distribution
        for rating in ['excellent', 'good', 'acceptable', 'poor', 'unacceptable']:
            rating_count = len(metrics.filtered(lambda m: m.performance_rating == rating))
            summary['performance_distribution'][rating] = rating_count

        # Metric type breakdown
        for metric in metrics:
            if metric.metric_type not in summary['metric_type_breakdown']:
                summary['metric_type_breakdown'][metric.metric_type] = {
                    'count': 0,
                    'average_value': 0,
                    'total_value': 0
                }

            breakdown = summary['metric_type_breakdown'][metric.metric_type]
            breakdown['count'] += 1
            breakdown['total_value'] += metric.metric_value
            breakdown['average_value'] = breakdown['total_value'] / breakdown['count']

        return summary
