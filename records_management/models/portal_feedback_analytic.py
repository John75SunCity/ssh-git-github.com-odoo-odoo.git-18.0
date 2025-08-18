import calendar
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PortalFeedbackAnalytic(models.Model):
    _name = 'portal.feedback.analytic'
    _description = 'Portal Feedback Analytics'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_end desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Period Name', required=True, readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    period_start = fields.Date(string='Period Start Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    period_end = fields.Date(string='Period End Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], string='Status', default='draft', readonly=True, copy=False)

    # --- METRIC FIELDS ---
    total_feedback_count = fields.Integer(string='Total Feedback', readonly=True)
    positive_feedback_count = fields.Integer(string='Positive Feedback', readonly=True)
    neutral_feedback_count = fields.Integer(string='Neutral Feedback', readonly=True)
    negative_feedback_count = fields.Integer(string='Negative Feedback', readonly=True)
    
    average_rating = fields.Float(string='Average Rating (1-5)', readonly=True, digits=(3, 2))
    customer_satisfaction_index = fields.Float(string='CSI (%)', readonly=True, digits=(5, 2), help="Customer Satisfaction Index")
    nps_score = fields.Float(string='NPS', readonly=True, help="Net Promoter Score")
    
    average_response_time = fields.Float(string='Avg. Response Time (Hours)', readonly=True, digits=(16, 2))
    average_resolution_time = fields.Float(string='Avg. Resolution Time (Hours)', readonly=True, digits=(16, 2))
    
    sla_compliance_rate = fields.Float(string='SLA Compliance (%)', readonly=True, digits=(5, 2))
    escalation_rate = fields.Float(string='Escalation Rate (%)', readonly=True, digits=(5, 2))
    first_contact_resolution_rate = fields.Float(string='FCR (%)', readonly=True, digits=(5, 2), help="First Contact Resolution Rate")
    
    improvement_trend = fields.Selection([
        ('improving', 'Improving'),
        ('declining', 'Declining'),
        ('stable', 'Stable'),
        ('insufficient_data', 'Insufficient Data')
    ], string='Trend vs Previous Period', readonly=True, default='insufficient_data')
    trend_percentage = fields.Float(string='Trend Change (%)', readonly=True, digits=(5, 2))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        for record in self:
            if record.period_start and record.period_end and record.period_start >= record.period_end:
                raise ValidationError(_("Period start date must be before the end date."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_generate_analytics(self):
        for record in self:
            record.write({'state': 'generating'})
            record.message_post(body=_("Analytics generation started..."))
            try:
                record._compute_analytics()
                record.write({'state': 'done'})
                record.message_post(body=_("Analytics generated successfully."))
            except Exception as e:
                record.write({'state': 'error'})
                record.message_post(body=_("Failed to generate analytics: %s", e))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    def _compute_analytics(self):
        self.ensure_one()
        
        domain = [
            ("create_date", ">=", self.period_start),
            ("create_date", "<=", self.period_end),
            ("company_id", "=", self.company_id.id),
        ]
        feedback_records = self.env["portal.feedback"].search(domain)

        if not feedback_records:
            self._reset_analytics()
            return

        vals = {}
        # Volume metrics
        vals['total_feedback_count'] = len(feedback_records)
        vals['positive_feedback_count'] = len(feedback_records.filtered(lambda f: f.sentiment_category == "positive"))
        vals['neutral_feedback_count'] = len(feedback_records.filtered(lambda f: f.sentiment_category == "neutral"))
        vals['negative_feedback_count'] = len(feedback_records.filtered(lambda f: f.sentiment_category == "negative"))

        # Rating metrics
        self._compute_rating_metrics(feedback_records, vals)
        
        # Time metrics
        self._compute_time_metrics(feedback_records, vals)

        # SLA metrics
        self._compute_sla_metrics(feedback_records, vals)
        
        self.write(vals)

    def _compute_rating_metrics(self, feedback_records, vals):
        rated_feedback = feedback_records.filtered(lambda f: f.rating and f.rating != '0')
        if not rated_feedback:
            vals.update({'average_rating': 0.0, 'nps_score': 0.0, 'customer_satisfaction_index': 0.0})
            return

        ratings = [int(f.rating) for f in rated_feedback if f.rating.isdigit()]
        vals['average_rating'] = sum(ratings) / len(ratings) if ratings else 0.0
        
        # NPS Score
        promoters = len([r for r in ratings if r >= 9])
        detractors = len([r for r in ratings if r <= 6])
        vals['nps_score'] = ((promoters - detractors) / len(ratings) * 100) if ratings else 0.0
        
        # CSI
        satisfaction_ratio = (vals['positive_feedback_count'] + (vals['neutral_feedback_count'] * 0.5)) / vals['total_feedback_count']
        vals['customer_satisfaction_index'] = satisfaction_ratio * 100

    def _compute_time_metrics(self, feedback_records, vals):
        # Response Times
        responded_feedback = feedback_records.filtered(lambda f: f.first_response_date and f.create_date)
        response_times = [(f.first_response_date - f.create_date).total_seconds() / 3600 for f in responded_feedback]
        vals['average_response_time'] = sum(response_times) / len(response_times) if response_times else 0.0

        # Resolution Times
        resolved_feedback = feedback_records.filtered(lambda f: f.resolution_date and f.create_date)
        resolution_times = [(f.resolution_date - f.create_date).total_seconds() / 3600 for f in resolved_feedback]
        vals['average_resolution_time'] = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0

    def _compute_sla_metrics(self, feedback_records, vals):
        total_count = vals['total_feedback_count']
        if not total_count:
            vals.update({'sla_compliance_rate': 0.0, 'escalation_rate': 0.0, 'first_contact_resolution_rate': 0.0})
            return

        # SLA compliance (assuming 24 hour response SLA)
        sla_compliant = feedback_records.filtered(lambda f: f.first_response_date and (f.first_response_date - f.create_date).total_seconds() <= 86400)
        vals['sla_compliance_rate'] = (len(sla_compliant) / total_count * 100)

        # Escalation rate
        escalated = feedback_records.filtered(lambda f: f.priority in ['3', '4']) # high, urgent
        vals['escalation_rate'] = (len(escalated) / total_count * 100)

        # First contact resolution
        fcr = feedback_records.filtered(lambda f: f.state == 'resolved' and f.interaction_count <= 1)
        vals['first_contact_resolution_rate'] = (len(fcr) / total_count * 100)

    def _reset_analytics(self):
        self.write({
            "total_feedback_count": 0,
            "positive_feedback_count": 0,
            "neutral_feedback_count": 0,
            "negative_feedback_count": 0,
            "average_rating": 0.0,
            "customer_satisfaction_index": 0.0,
            "nps_score": 0.0,
            "average_response_time": 0.0,
            "average_resolution_time": 0.0,
            "sla_compliance_rate": 0.0,
            "escalation_rate": 0.0,
            "first_contact_resolution_rate": 0.0,
            "improvement_trend": 'insufficient_data',
            "trend_percentage": 0.0,
        })

