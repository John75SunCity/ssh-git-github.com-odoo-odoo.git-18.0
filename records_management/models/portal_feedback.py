# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PortalFeedback(models.Model):
    _name = 'portal.feedback'
    _description = 'Portal Customer Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'feedback_subject'

    # Core feedback fields
    feedback_subject = fields.Char(string='Subject', required=True, tracking=True)
    feedback_description = fields.Text(string='Description', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    customer_email = fields.Char(related='customer_id.email', string='Customer Email', readonly=True)
    customer_phone = fields.Char(related='customer_id.phone', string='Customer Phone', readonly=True)
    
    # Feedback categorization
    feedback_type = fields.Selection([
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('compliment', 'Compliment'),
        ('inquiry', 'Inquiry'),
        ('technical', 'Technical Issue')
    ], string='Feedback Type', required=True, tracking=True)
    
    feedback_category = fields.Selection([
        ('service_quality', 'Service Quality'),
        ('communication', 'Communication'),
        ('billing', 'Billing'),
        ('website', 'Website'),
        ('delivery', 'Delivery'),
        ('staff', 'Staff'),
        ('other', 'Other')
    ], string='Category', tracking=True)
    
    # Status and priority
    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated')
    ], string='Status', default='new', required=True, tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium', tracking=True)
    
    urgency_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Urgency Level', tracking=True)
    
    # Assignment and responsibility
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    account_manager = fields.Many2one('res.users', string='Account Manager', tracking=True)
    
    # Dates and timing
    submission_date = fields.Datetime(string='Submission Date', default=fields.Datetime.now, readonly=True)
    response_date = fields.Datetime(string='Response Date', tracking=True)
    resolution_date = fields.Datetime(string='Resolution Date', tracking=True)
    completion_date = fields.Datetime(string='Completion Date', tracking=True)
    
    # Response time tracking
    response_time_hours = fields.Float(string='Response Time (Hours)', compute='_compute_response_time')
    resolution_time_hours = fields.Float(string='Resolution Time (Hours)', compute='_compute_resolution_time')
    
    # Escalation
    escalated = fields.Boolean(string='Escalated', tracking=True)
    escalated_to = fields.Many2one('res.users', string='Escalated To', tracking=True)
    escalation_date = fields.Datetime(string='Escalation Date', tracking=True)
    escalation_reason = fields.Text(string='Escalation Reason')
    
    # Response and resolution
    response_description = fields.Text(string='Response Description', tracking=True)
    responded_by = fields.Many2one('res.users', string='Responded By', tracking=True)
    resolved_by = fields.Many2one('res.users', string='Resolved By', tracking=True)
    response_method = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('portal', 'Portal'),
        ('in_person', 'In Person')
    ], string='Response Method', tracking=True)
    
    # Satisfaction ratings
    overall_rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Overall Rating')
    
    satisfaction_level = fields.Selection([
        ('very_dissatisfied', 'Very Dissatisfied'),
        ('dissatisfied', 'Dissatisfied'),
        ('neutral', 'Neutral'),
        ('satisfied', 'Satisfied'),
        ('very_satisfied', 'Very Satisfied')
    ], string='Satisfaction Level')
    
    # NPS and specific ratings
    nps_score = fields.Integer(string='NPS Score (0-10)', help='Net Promoter Score')
    likelihood_to_recommend = fields.Integer(string='Likelihood to Recommend (1-10)')
    likelihood_to_return = fields.Integer(string='Likelihood to Return (1-10)')
    
    service_quality_rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Service Quality Rating')
    
    communication_rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Communication Rating')
    
    response_time_rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Response Time Rating')
    
    staff_professionalism_rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Staff Professionalism Rating')
    
    value_for_money_rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Value for Money Rating')
    
    # CES and CSAT scores
    ces_score = fields.Integer(string='Customer Effort Score (1-7)', help='How easy was it to resolve your issue?')
    csat_score = fields.Integer(string='Customer Satisfaction Score (1-5)')
    
    # Customer insights
    positive_aspects = fields.Text(string='What did we do well?')
    negative_aspects = fields.Text(string='What could we improve?')
    improvement_suggestions = fields.Text(string='Improvement Suggestions')
    improvement_opportunity = fields.Text(string='Improvement Opportunity')
    
    # Analysis and categorization
    sentiment_analysis = fields.Selection([
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ], string='Sentiment Analysis', compute='_compute_sentiment_analysis')
    
    keyword_tags = fields.Char(string='Keyword Tags')
    trend_analysis = fields.Text(string='Trend Analysis')
    competitive_mention = fields.Boolean(string='Competitive Mention')
    
    # Revenue and business impact
    revenue_impact = fields.Monetary(string='Revenue Impact', currency_field='currency_id')
    customer_tier = fields.Selection([
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ], string='Customer Tier')
    
    customer_segment = fields.Selection([
        ('small', 'Small Business'),
        ('medium', 'Medium Business'),
        ('enterprise', 'Enterprise'),
        ('government', 'Government')
    ], string='Customer Segment')
    
    retention_risk = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], string='Retention Risk', compute='_compute_retention_risk')
    
    # Related records
    service_request_id = fields.Many2one('records.service.request', string='Related Service Request')
    product_id = fields.Many2one('product.product', string='Related Product')
    
    # Follow-up and actions
    followup_required = fields.Boolean(string='Follow-up Required', tracking=True)
    followup_date = fields.Date(string='Follow-up Date', tracking=True)
    followup_assigned_to = fields.Many2one('res.users', string='Follow-up Assigned To', tracking=True)
    followup_method = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('survey', 'Survey')
    ], string='Follow-up Method')
    
    # Actions and resolutions
    internal_actions = fields.Text(string='Internal Actions Taken')
    resolution_category = fields.Selection([
        ('policy_change', 'Policy Change'),
        ('training', 'Training'),
        ('process_improvement', 'Process Improvement'),
        ('compensation', 'Compensation'),
        ('explanation', 'Explanation'),
        ('no_action', 'No Action Required')
    ], string='Resolution Category')
    
    root_cause_category = fields.Selection([
        ('communication', 'Communication'),
        ('process', 'Process'),
        ('system', 'System'),
        ('training', 'Training'),
        ('policy', 'Policy'),
        ('external', 'External Factor')
    ], string='Root Cause Category')
    
    impact_assessment = fields.Text(string='Impact Assessment')
    
    # Completion and status
    completed = fields.Boolean(string='Completed', tracking=True)
    
    # Counters and related records
    customer_feedback_count = fields.Integer(string='Customer Feedback Count', compute='_compute_feedback_count')
    improvement_action_count = fields.Integer(string='Improvement Action Count', compute='_compute_improvement_count')
    related_ticket_count = fields.Integer(string='Related Ticket Count', compute='_compute_related_count')
    
    # One2many relationships
    followup_activity_ids = fields.One2many('mail.activity', compute='_compute_followup_activities', string='Follow-up Activities')
    attachment_ids = fields.One2many('ir.attachment', compute='_compute_attachments', string='Attachments')
    
    # File information
    file_size = fields.Integer(string='File Size')
    mimetype = fields.Char(string='MIME Type')
    
    # Technical fields for view compatibility  
    arch = fields.Text(string='View Architecture')
    model = fields.Char(string='Model Name', default='portal.feedback')
    res_model = fields.Char(string='Resource Model', default='portal.feedback')
    context = fields.Text(string='Context')
    help = fields.Text(string='Help Text')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    view_mode = fields.Char(string='View Mode', default='tree,form')
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    description = fields.Text(string='Description', related='feedback_description')
    
    # Activity and message fields
    activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids', string='Activities')
    activity_state = fields.Selection(selection=[
        ('overdue', 'Overdue'),
        ('today', 'Today'),
        ('planned', 'Planned')
    ], string='Activity State')
    activity_type = fields.Many2one('mail.activity.type', string='Activity Type')
    activity_date = fields.Date(string='Activity Date')
    activity_exception_decoration = fields.Selection([
        ('warning', 'Alert'),
        ('danger', 'Error')
    ], string='Activity Exception Decoration')
    
    message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers', string='Followers')
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Messages')
    
    # Additional fields
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('feedback_subject', 'feedback_type')
    def _compute_name(self):
        for record in self:
            if record.feedback_subject:
                record.name = f"[{record.feedback_type or 'Feedback'}] {record.feedback_subject}"
            else:
                record.name = record.feedback_type or 'Feedback'

    @api.depends('submission_date', 'response_date')
    def _compute_response_time(self):
        for record in self:
            if record.submission_date and record.response_date:
                delta = record.response_date - record.submission_date
                record.response_time_hours = delta.total_seconds() / 3600
            else:
                record.response_time_hours = 0.0

    @api.depends('submission_date', 'resolution_date')
    def _compute_resolution_time(self):
        for record in self:
            if record.submission_date and record.resolution_date:
                delta = record.resolution_date - record.submission_date
                record.resolution_time_hours = delta.total_seconds() / 3600
            else:
                record.resolution_time_hours = 0.0

    @api.depends('feedback_description', 'positive_aspects', 'negative_aspects')
    def _compute_sentiment_analysis(self):
        for record in self:
            # Simple sentiment analysis based on keywords
            text = f"{record.feedback_description or ''} {record.positive_aspects or ''} {record.negative_aspects or ''}".lower()
            positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'love', 'amazing', 'perfect']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'disappointed', 'poor', 'worst', 'horrible']
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                record.sentiment_analysis = 'positive'
            elif negative_count > positive_count:
                record.sentiment_analysis = 'negative'
            else:
                record.sentiment_analysis = 'neutral'

    @api.depends('overall_rating', 'satisfaction_level', 'nps_score')
    def _compute_retention_risk(self):
        for record in self:
            if record.nps_score and record.nps_score <= 3:
                record.retention_risk = 'critical'
            elif record.overall_rating in ['1', '2'] or record.satisfaction_level in ['very_dissatisfied', 'dissatisfied']:
                record.retention_risk = 'high'
            elif record.overall_rating == '3' or record.satisfaction_level == 'neutral':
                record.retention_risk = 'medium'
            else:
                record.retention_risk = 'low'

    @api.depends('customer_id')
    def _compute_feedback_count(self):
        for record in self:
            if record.customer_id:
                record.customer_feedback_count = self.search_count([('customer_id', '=', record.customer_id.id)])
            else:
                record.customer_feedback_count = 0

    def _compute_improvement_count(self):
        for record in self:
            # Count related improvement actions
            record.improvement_action_count = 0  # Placeholder

    def _compute_related_count(self):
        for record in self:
            # Count related tickets/service requests
            record.related_ticket_count = 0  # Placeholder

    def action_respond(self):
        """Open response wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Respond to Feedback'),
            'res_model': 'portal.feedback.response.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_feedback_id': self.id}
        }

    def action_escalate(self):
        """Escalate feedback to supervisor"""
        self.ensure_one()
        self.write({
            'escalated': True,
            'escalation_date': fields.Datetime.now(),
            'status': 'escalated'
        })
        return True

    def action_resolve(self):
        """Mark feedback as resolved"""
        self.ensure_one()
        self.write({
            'status': 'resolved',
            'resolution_date': fields.Datetime.now(),
            'resolved_by': self.env.user.id
        })
        return True

    # Compute methods for One2many fields
    def _compute_followup_activities(self):
        """Compute follow-up activities for this feedback"""
        for feedback in self:
            feedback.followup_activity_ids = self.env['mail.activity'].search([
                ('res_model', '=', 'portal.feedback'),
                ('res_id', '=', feedback.id),
                ('activity_type_id.category', '=', 'meeting')  # Follow-up specific activities
            ])

    def _compute_attachments(self):
        """Compute attachments for this feedback"""
        for feedback in self:
            feedback.attachment_ids = self.env['ir.attachment'].search([
                ('res_model', '=', 'portal.feedback'),
                ('res_id', '=', feedback.id)
            ])

    def _compute_activity_ids(self):
        """Compute activities for this feedback"""
        for feedback in self:
            feedback.activity_ids = self.env['mail.activity'].search([
                ('res_model', '=', 'portal.feedback'),
                ('res_id', '=', feedback.id)
            ])

    def _compute_message_followers(self):
        """Compute message followers for this record"""
        for record in self:
            record.message_follower_ids = self.env["mail.followers"].search([
                ("res_model", "=", "portal.feedback"),
                ("res_id", "=", record.id)
            ])

    def _compute_message_ids(self):
        """Compute messages for this record"""
        for record in self:
            record.message_ids = self.env["mail.message"].search([
                ("res_model", "=", "portal.feedback"),
                ("res_id", "=", record.id)
            ])
