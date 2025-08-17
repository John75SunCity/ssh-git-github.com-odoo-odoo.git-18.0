from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class FileRetrievalMetric(models.Model):
    _name = 'file.retrieval.metric'
    _description = 'File Retrieval Performance Metric'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'retrieval_date desc, metric_type'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    work_order_id = fields.Many2one()
    team_id = fields.Many2one()
    employee_id = fields.Many2one()
    container_id = fields.Many2one()
    partner_id = fields.Many2one()
    metric_type = fields.Selection()
    metric_value = fields.Float()
    metric_unit = fields.Selection()
    retrieval_date = fields.Date()
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    duration = fields.Float()
    target_value = fields.Float()
    variance = fields.Float()
    variance_percentage = fields.Float()
    performance_rating = fields.Selection()
    accuracy_percentage = fields.Float()
    quality_score = fields.Float()
    error_count = fields.Integer()
    rework_required = fields.Boolean()
    location_id = fields.Many2one()
    complexity_level = fields.Selection()
    difficulty_factors = fields.Text()
    state = fields.Selection()
    notes = fields.Text()
    improvement_suggestions = fields.Text()
    lessons_learned = fields.Text()
    benchmark_value = fields.Float()
    benchmark_comparison = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    from_date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name with proper translation"""
            for record in self:
                metric_dict = dict(record._fields['metric_type'].selection)
                metric_label = metric_dict.get(record.metric_type, record.metric_type)
                unit_dict = dict(record._fields['metric_unit'].selection)
                unit_label = unit_dict.get(record.metric_unit, record.metric_unit)

                record.display_name = _("%s: %s %s", metric_label, record.metric_value, unit_label)


    def _compute_duration(self):
            """Calculate duration between start and end time"""
            for record in self:
                if record.start_time and record.end_time:
                    delta = record.end_time - record.start_time
                    record.duration = delta.total_seconds() / 3600  # Convert to hours
                else:
                    record.duration = 0.0


    def _compute_variance(self):
            """Calculate variance from target"""
            for record in self:
                if record.target_value:
                    record.variance = record.metric_value - record.target_value
                else:
                    record.variance = 0.0


    def _compute_variance_percentage(self):
            """Calculate variance percentage"""
            for record in self:
                if record.target_value and record.target_value != 0:
                    record.variance_percentage = (record.variance / record.target_value) * 100
                else:
                    record.variance_percentage = 0.0


    def _compute_performance_rating(self):
            """Compute performance rating based on target achievement"""
            for record in self:
                if not record.target_value or record.target_value == 0:
                    record.performance_rating = 'acceptable'
                    continue

                # For time-based metrics, lower is better
                if record.metric_type in ['file_search_time', 'file_retrieval_time', 'file_scanning_time',:]
                                        'container_access_time', 'container_retrieval_time', 'container_movement_time',
                                        'scan_processing_time', 'scan_quality_check_time', 'travel_time', 'processing_time'
                    ratio = record.target_value / record.metric_value if record.metric_value != 0 else 0:
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


    def _compute_quality_score(self):
            """Calculate overall quality score"""
            for record in self:
                base_score = record.accuracy_percentage

                # Adjust based on performance rating
                rating_multiplier = {}
                    'excellent': 1.2,
                    'good': 1.1,
                    'acceptable': 1.0,
                    'poor': 0.9,
                    'unacceptable': 0.8


                multiplier = rating_multiplier.get(record.performance_rating, 1.0)

                # Factor in error count
                error_penalty = record.error_count * 2  # 2 points per error

                quality_score = (base_score * multiplier) - error_penalty
                record.quality_score = max(min(quality_score, 100.0), 0.0)


    def _compute_benchmark_comparison(self):
            """Compare metric value to benchmark"""
            for record in self:
                if not record.benchmark_value or record.benchmark_value == 0:
                    record.benchmark_comparison = 'no_data'
                elif record.metric_value > record.benchmark_value * 1.5:  # 5% tolerance
                    record.benchmark_comparison = 'above'
                elif record.metric_value < record.benchmark_value * 0.95:  # 5% tolerance
                    record.benchmark_comparison = 'below'
                else:
                    record.benchmark_comparison = 'at'

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_metric_value(self):
            """Validate metric value based on type"""
            for record in self:
                if record.metric_type in ['file_accuracy_rate', 'success_rate'] and record.metric_unit == 'percentage':
                    if not 0 <= record.metric_value <= 100:
                        raise ValidationError(_('Percentage values must be between 0 and 100'))

                if record.metric_value < 0:
                    raise ValidationError(_('Metric value cannot be negative'))


    def _check_accuracy_percentage(self):
            """Validate accuracy percentage"""
            for record in self:
                if not 0 <= record.accuracy_percentage <= 100:
                    raise ValidationError(_('Accuracy percentage must be between 0 and 100'))


    def _check_time_sequence(self):
            """Validate time sequence"""
            for record in self:
                if record.start_time and record.end_time:
                    if record.start_time > record.end_time:
                        raise ValidationError(_('Start time must be before end time'))


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
            """Analyze the metric for insights""":
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
                    dashboard_data[metric_type] = {}
                        'average': sum(type_metrics.mapped('metric_value')) / len(type_metrics),
                        'count': len(type_metrics),
                        'best': min(type_metrics.mapped('metric_value')),
                        'worst': max(type_metrics.mapped('metric_value'))


            return dashboard_data


    def get_trend_data(self, days=30):
            """Get trend data for this metric type""":
            self.ensure_one()


    def create(self, vals_list):
            """Override create to set default name"""
            for vals in vals_list:
                if not vals.get('name'):
                    metric_type_val = vals.get('metric_type', 'unknown')
                    vals['name'] = _('Metric: %s', metric_type_val.replace('_', ' ').title())

            return super().create(vals_list)


    def write(self, vals):
            """Override write for modification tracking""":
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

    def get_metric_summary(self, metric_type=None, team_id=None, date_from=None, date_to=None):
            """Get metric summary for reporting""":
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

            summary = {}
                'total_metrics': len(metrics),
                'average_quality_score': sum(metrics.mapped('quality_score')) / len(metrics) if metrics else 0,:
                'performance_distribution': {},
                'metric_type_breakdown': {}


            # Performance rating distribution
            for rating_key in ['excellent', 'good', 'acceptable', 'poor', 'unacceptable']:
                rating_count = len(metrics.filtered(lambda m: m.performance_rating == rating_key))
                summary['performance_distribution'][rating_key] = rating_count

            # Metric type breakdown
            for metric_record in metrics:
                if metric_record.metric_type not in summary['metric_type_breakdown']:
                    summary['metric_type_breakdown'][metric_record.metric_type] = {}
                        'count': 0,
                        'average_value': 0,
                        'total_value': 0


                breakdown = summary['metric_type_breakdown'][metric_record.metric_type]
                breakdown['count'] += 1
                breakdown['total_value'] += metric_record.metric_value
                breakdown['average_value'] = breakdown['total_value'] / breakdown['count']

            return summary

