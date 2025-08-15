# -*- coding: utf-8 -*-
"""
Document Retrieval Metrics Model

Metrics and performance tracking for document retrieval operations.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DocumentRetrievalMetrics(models.Model):
    """Document Retrieval Metrics"""

    _name = "document.retrieval.metrics"
    _description = "Document Retrieval Performance Metrics"
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
        help="Name of the performance metric"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        help="Display name for the metric"
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
        help="Set to false to archive this metric"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    work_order_id = fields.Many2one(
        "document.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete="cascade",
        index=True,
        help="Related work order"
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

    # ============================================================================
    # METRIC DETAILS
    # ============================================================================
    metric_type = fields.Selection([
        ('search_time', 'Document Search Time'),
        ('retrieval_time', 'Physical Retrieval Time'),
        ('scanning_time', 'Scanning Duration'),
        ('accuracy_rate', 'Retrieval Accuracy'),
        ('success_rate', 'Success Rate'),
        ('documents_found', 'Documents Found Count'),
        ('documents_requested', 'Documents Requested Count'),
        ('container_access_time', 'Container Access Time'),
        ('travel_time', 'Travel Time'),
        ('processing_time', 'Processing Time')
    ], string='Metric Type', required=True, tracking=True)

    metric_value = fields.Float(
        string="Metric Value",
        required=True,
        help="Numerical value of the metric"
    )

    metric_unit = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('seconds', 'Seconds'),
        ('percentage', 'Percentage'),
        ('count', 'Count'),
        ('documents', 'Documents'),
        ('containers', 'Containers')
    ], string='Unit', default='minutes', required=True)

    # ============================================================================
    # DATE AND TIME TRACKING
    # ============================================================================
    retrieval_date = fields.Date(
        string="Retrieval Date",
        required=True,
        default=fields.Date.today,
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

    # ============================================================================
    # PERFORMANCE ANALYSIS
    # ============================================================================
    target_value = fields.Float(
        string="Target Value",
        help="Target or expected value for this metric"
    )

    variance = fields.Float(
        string="Variance",
        compute='_compute_variance',
        store=True,
        help="Difference from target value"
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
        help="Accuracy percentage for retrieval"
    )

    quality_score = fields.Float(
        string="Quality Score",
        compute='_compute_quality_score',
        store=True,
        help="Overall quality score"
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
    ], string='Complexity Level', default='moderate')

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

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'metric_type', 'metric_value', 'metric_unit')
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            metric_dict = dict(record._fields['metric_type'].selection)
            metric_label = metric_dict.get(record.metric_type, record.metric_type)
            unit_dict = dict(record._fields['metric_unit'].selection)
            unit_label = unit_dict.get(record.metric_unit, record.metric_unit)
            
            record.display_name = f"{metric_label}: {record.metric_value} {unit_label}"

    @api.depends('metric_value', 'target_value')
    def _compute_variance(self):
        """Calculate variance from target"""
        for record in self:
            if record.target_value:
                record.variance = record.metric_value - record.target_value
            else:
                record.variance = 0.0

    @api.depends('metric_value', 'target_value', 'metric_type')
    def _compute_performance_rating(self):
        """Compute performance rating based on target achievement"""
        for record in self:
            if not record.target_value or record.target_value == 0:
                record.performance_rating = 'acceptable'
                continue
            
            # For time-based metrics, lower is better
            if record.metric_type in ['search_time', 'retrieval_time', 'scanning_time', 'travel_time']:
                ratio = record.target_value / record.metric_value
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

    @api.depends('accuracy_percentage', 'performance_rating')
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
            record.quality_score = min(base_score * multiplier, 100.0)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('metric_value')
    def _check_metric_value(self):
        """Validate metric value based on type"""
        for record in self:
            if record.metric_type in ['accuracy_rate', 'success_rate'] and record.metric_unit == 'percentage':
                if not (0 <= record.metric_value <= 100):
                    raise ValidationError(_('Percentage values must be between 0 and 100'))
            
            if record.metric_value < 0:
                raise ValidationError(_('Metric value cannot be negative'))

    @api.constrains('accuracy_percentage')
    def _check_accuracy_percentage(self):
        """Validate accuracy percentage"""
        for record in self:
            if not (0 <= record.accuracy_percentage <= 100):
                raise ValidationError(_('Accuracy percentage must be between 0 and 100'))

    @api.constrains('start_time', 'end_time')
    def _check_time_sequence(self):
        """Validate time sequence"""
        for record in self:
            if record.start_time and record.end_time:
                if record.start_time > record.end_time:
                    raise ValidationError(_('Start time must be before end time'))
