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
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
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
    
    # Attachment and file management
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        string='Attachments',
        help='Documents or files attached to this feedback'
    )
    file_size = fields.Float(
        string='Total File Size (MB)',
        compute='_compute_file_size',
        help='Total size of all attached files'
    )
    mimetype = fields.Char(
        string='Primary MIME Type',
        compute='_compute_mimetype',
        help='MIME type of the primary attachment'
    )
    
    # Activity tracking
    activity_date = fields.Datetime(
        string='Last Activity Date',
        compute='_compute_activity_date',
        help='Date of the most recent activity'
    )
    activity_type = fields.Selection([
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('todo', 'To Do'),
        ('upload', 'Upload')
    ], string='Last Activity Type', compute='_compute_activity_type')
    followup_activity_ids = fields.Many2many('mail.activity', relation='followup_activity_ids_rel', string='Follow-up Activities',
        domain=[('res_model', '=', 'portal.feedback')  # Fixed: was One2many with missing inverse field],
        help='Scheduled follow-up activities for this feedback'
    )
    
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

    # Compute methods for the fields above
    @api.depends()
    def _compute_response_time(self):
        """Compute response time in hours"""
        for record in self:
            if record.create_date and record.response_date:
                delta = record.response_date - record.create_date
                record.response_time_hours = delta.total_seconds() / 3600
            else:
                record.response_time_hours = 0.0

    @api.depends()
    def _compute_resolution_time(self):
        """Compute resolution time in hours"""
        for record in self:
            if record.create_date and record.resolution_date:
                delta = record.resolution_date - record.create_date
                record.resolution_time_hours = delta.total_seconds() / 3600
            else:
                record.resolution_time_hours = 0.0

    @api.depends('feedback_description', 'overall_rating', 'satisfaction_level')
    def _compute_sentiment_analysis(self):
        """Compute sentiment analysis based on feedback description and ratings"""
        for record in self:
            if not record.feedback_description and not record.overall_rating:
                record.sentiment_analysis = 'neutral'
                continue
                
            # Simple sentiment analysis based on rating and keywords
            if record.overall_rating:
                rating_num = int(record.overall_rating) if record.overall_rating.isdigit() else 3
                if rating_num >= 4:
                    record.sentiment_analysis = 'positive'
                elif rating_num <= 2:
                    record.sentiment_analysis = 'negative'
                else:
                    record.sentiment_analysis = 'neutral'
            else:
                # Check satisfaction level as fallback
                if record.satisfaction_level in ['satisfied', 'very_satisfied']:
                    record.sentiment_analysis = 'positive'
                elif record.satisfaction_level in ['dissatisfied', 'very_dissatisfied']:
                    record.sentiment_analysis = 'negative'
                else:
                    record.sentiment_analysis = 'neutral'

    @api.depends('sentiment_analysis', 'overall_rating', 'urgency_level', 'priority')
    def _compute_retention_risk(self):
        """Compute customer retention risk based on sentiment and other factors"""
        for record in self:
            # Simple risk assessment logic
            risk_factors = 0
            
            # Check sentiment
            if record.sentiment_analysis == 'negative':
                risk_factors += 2
            elif record.sentiment_analysis == 'positive':
                risk_factors -= 1
                
            # Check rating
            if record.overall_rating:
                rating_num = int(record.overall_rating) if record.overall_rating.isdigit() else 3
                if rating_num <= 2:
                    risk_factors += 2
                elif rating_num >= 4:
                    risk_factors -= 1
                    
            # Check urgency and priority
            if record.urgency_level == 'critical' or record.priority == 'urgent':
                risk_factors += 1
                
            # Determine risk level
            if risk_factors >= 3:
                record.retention_risk = 'critical'
            elif risk_factors >= 2:
                record.retention_risk = 'high'
            elif risk_factors >= 1:
                record.retention_risk = 'medium'
            else:
                record.retention_risk = 'low'

    @api.depends()
    def _compute_feedback_count(self):
        """Compute customer feedback count"""
        for record in self:
            # This would typically count related feedback records
            record.customer_feedback_count = 1  # Simplified

    @api.depends()
    def _compute_improvement_count(self):
        """Compute improvement action count"""
        for record in self:
            # This would typically count related improvement actions
            record.improvement_action_count = 0  # Simplified

    @api.depends()
    def _compute_related_count(self):
        """Compute related ticket count"""
        for record in self:
            # This would typically count related tickets/issues
            record.related_ticket_count = 0  # Simplified
    
    @api.depends('attachment_ids')
    def _compute_file_size(self):
        """Compute total file size of all attachments."""
        for record in self:
            total_size = 0
            for attachment in record.attachment_ids:
                if attachment.file_size:
                    total_size += attachment.file_size
            record.file_size = total_size / (1024 * 1024)  # Convert to MB
    
    @api.depends('attachment_ids')
    def _compute_mimetype(self):
        """Compute the MIME type of the primary attachment."""
        for record in self:
            if record.attachment_ids:
                record.mimetype = record.attachment_ids[0].mimetype
            else:
                record.mimetype = False
    
    @api.depends('activity_ids')
    def _compute_activity_date(self):
        """Compute the date of the most recent activity."""
        for record in self:
            if record.activity_ids:
                record.activity_date = max(record.activity_ids.mapped('date_deadline'))
            else:
                record.activity_date = False
    
    @api.depends('activity_ids')
    def _compute_activity_type(self):
        """Compute the type of the most recent activity."""
        for record in self:
            if record.activity_ids:
                latest_activity = record.activity_ids.sorted('date_deadline', reverse=True)[0]
                record.activity_type = latest_activity.activity_type_id.category or 'todo'
            else:
                record.activity_type = False