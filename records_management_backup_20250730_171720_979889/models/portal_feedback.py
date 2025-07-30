# -*- coding: utf-8 -*-
"""
Portal Customer Feedback
"""

from odoo import models, fields, api, _


class PortalFeedback(models.Model):
    """
    Portal Customer Feedback
    """

    _name = "portal.feedback"
    _description = "Portal Customer Feedback"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    # Customer Information
    customer_segment = fields.Selection([('basic', 'Basic'), ('premium', 'Premium'), ('enterprise', 'Enterprise')], string='Customer Segment')
    customer_tier = fields.Selection([('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], string='Customer Tier')
    
    # Feedback Classification
    feedback_category = fields.Selection([('service', 'Service'), ('product', 'Product'), ('billing', 'Billing'), ('support', 'Support')], string='Category')
    feedback_type = fields.Selection([('complaint', 'Complaint'), ('suggestion', 'Suggestion'), ('compliment', 'Compliment'), ('inquiry', 'Inquiry')], string='Type')
    sentiment_analysis = fields.Selection([('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')], string='Sentiment')
    priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], string='Priority')
    urgency_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Urgency')
    
    # Escalation Management
    escalated = fields.Boolean(string='Escalated', default=False)
    escalation_date = fields.Datetime(string='Escalation Date')
    escalation_reason = fields.Text(string='Escalation Reason')
    escalated_to = fields.Many2one('res.users', string='Escalated To')
    
    # Assignment and Response
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    responded_by = fields.Many2one('res.users', string='Responded By')
    response_date = fields.Datetime(string='Response Date')
    response_method = fields.Selection([('email', 'Email'), ('phone', 'Phone'), ('meeting', 'Meeting'), ('chat', 'Chat')], string='Response Method')
    
    # Resolution
    resolution_category = fields.Selection([('resolved', 'Resolved'), ('duplicate', 'Duplicate'), ('wont_fix', 'Won\'t Fix'), ('deferred', 'Deferred')], string='Resolution Category')
    resolution_date = fields.Datetime(string='Resolution Date')
    resolved_by = fields.Many2one('res.users', string='Resolved By')
    
    # Satisfaction Metrics
    satisfaction_level = fields.Selection([('very_unsatisfied', 'Very Unsatisfied'), ('unsatisfied', 'Unsatisfied'), ('neutral', 'Neutral'), ('satisfied', 'Satisfied'), ('very_satisfied', 'Very Satisfied')], string='Satisfaction Level')
    likelihood_to_recommend = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], string='Likelihood to Recommend')
    likelihood_to_return = fields.Selection([('very_unlikely', 'Very Unlikely'), ('unlikely', 'Unlikely'), ('neutral', 'Neutral'), ('likely', 'Likely'), ('very_likely', 'Very Likely')], string='Likelihood to Return')
    
    # Survey Scores
    nps_score = fields.Integer(string='NPS Score')
    csat_score = fields.Float(string='CSAT Score')
    ces_score = fields.Float(string='CES Score')
    
    # Detailed Ratings
    overall_rating = fields.Float(string='Overall Rating')
    service_quality_rating = fields.Float(string='Service Quality Rating')
    response_time_rating = fields.Float(string='Response Time Rating')
    communication_rating = fields.Float(string='Communication Rating')
    value_for_money_rating = fields.Float(string='Value for Money Rating')
    staff_professionalism_rating = fields.Float(string='Staff Professionalism Rating')
    
    # Qualitative Feedback
    positive_aspects = fields.Text(string='Positive Aspects')
    negative_aspects = fields.Text(string='Negative Aspects')
    improvement_suggestions = fields.Text(string='Improvement Suggestions')
    competitive_mention = fields.Text(string='Competitive Mention')
    
    # Business Impact
    retention_risk = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Retention Risk')
    revenue_impact = fields.Float(string='Revenue Impact')
    trend_analysis = fields.Text(string='Trend Analysis')
    keyword_tags = fields.Char(string='Keyword Tags')
    
    # Follow-up
    followup_required = fields.Boolean(string='Follow-up Required', default=False)
    followup_date = fields.Date(string='Follow-up Date')
    followup_method = fields.Selection([('email', 'Email'), ('phone', 'Phone'), ('meeting', 'Meeting')], string='Follow-up Method')
    followup_assigned_to = fields.Many2one('res.users', string='Follow-up Assigned To')
    
    # Improvement Tracking
    improvement_opportunity = fields.Boolean(string='Improvement Opportunity', default=False)
    improvement_action_count = fields.Integer(string='Improvement Action Count', default=0)
    related_ticket_count = fields.Integer(string='Related Ticket Count', default=0)
    customer_feedback_count = fields.Integer(string='Customer Feedback Count', default=0)
    
    # Analysis
    impact_assessment = fields.Text(string='Impact Assessment')
    root_cause_category = fields.Selection([('process', 'Process'), ('system', 'System'), ('training', 'Training'), ('resource', 'Resource')], string='Root Cause Category')
    internal_actions = fields.Text(string='Internal Actions')
    
    # Time Tracking
    response_time_hours = fields.Float(string='Response Time (Hours)')
    resolution_time_hours = fields.Float(string='Resolution Time (Hours)
    account_manager = fields.Char(string='Account Manager')
    action_close = fields.Char(string='Action Close')
    action_escalate = fields.Char(string='Action Escalate')
    action_mark_reviewed = fields.Char(string='Action Mark Reviewed')
    action_reopen = fields.Char(string='Action Reopen')
    action_respond = fields.Char(string='Action Respond')
    action_view_customer_history = fields.Char(string='Action View Customer History')
    action_view_improvement_actions = fields.Char(string='Action View Improvement Actions')
    action_view_related_tickets = fields.Char(string='Action View Related Tickets')
    activity_date = fields.Date(string='Activity Date')
    activity_exception_decoration = fields.Char(string='Activity Exception Decoration')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    activity_state = fields.Selection([], string='Activity State')  # TODO: Define selection options
    activity_type = fields.Selection([], string='Activity Type')  # TODO: Define selection options
    analysis = fields.Char(string='Analysis')
    attachment_ids = fields.One2many('attachment', 'portal_feedback_id', string='Attachment Ids')
    attachments = fields.Char(string='Attachments')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    closed = fields.Char(string='Closed')
    complaints = fields.Char(string='Complaints')
    completed = fields.Boolean(string='Completed', default=False)
    completion_date = fields.Date(string='Completion Date')
    compliments = fields.Char(string='Compliments')
    context = fields.Char(string='Context')
    customer_email = fields.Char(string='Customer Email')
    customer_id = fields.Many2one('res.partner', string='Customer Id', domain=[('is_company', '=', True)])
    customer_info = fields.Char(string='Customer Info')
    customer_phone = fields.Char(string='Customer Phone')
    escalated_cases = fields.Char(string='Escalated Cases')
    feedback_content = fields.Char(string='Feedback Content')
    feedback_description = fields.Char(string='Feedback Description')
    feedback_details = fields.Char(string='Feedback Details')
    feedback_subject = fields.Char(string='Feedback Subject')
    file_size = fields.Char(string='File Size')
    followup = fields.Char(string='Followup')
    followup_activity_ids = fields.One2many('followup.activity', 'portal_feedback_id', string='Followup Activity Ids')
    group_assigned = fields.Char(string='Group Assigned')
    group_customer = fields.Char(string='Group Customer')
    group_date = fields.Date(string='Group Date')
    group_priority = fields.Selection([], string='Group Priority')  # TODO: Define selection options
    group_satisfaction = fields.Char(string='Group Satisfaction')
    group_status = fields.Selection([], string='Group Status')  # TODO: Define selection options
    group_type = fields.Selection([], string='Group Type')  # TODO: Define selection options
    help = fields.Char(string='Help')
    high_priority = fields.Selection([], string='High Priority')  # TODO: Define selection options
    high_ratings = fields.Char(string='High Ratings')
    low_satisfaction = fields.Char(string='Low Satisfaction')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    metrics = fields.Char(string='Metrics')
    mimetype = fields.Selection([], string='Mimetype')  # TODO: Define selection options
    my_feedback = fields.Char(string='My Feedback')
    new = fields.Char(string='New')
    overdue_response = fields.Char(string='Overdue Response')
    product_id = fields.Many2one('product', string='Product Id')
    ratings = fields.Char(string='Ratings')
    res_model = fields.Char(string='Res Model')
    responded = fields.Char(string='Responded')
    response_actions = fields.Char(string='Response Actions')
    response_description = fields.Char(string='Response Description')
    reviewed = fields.Char(string='Reviewed')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    service_request_id = fields.Many2one('service.request', string='Service Request Id')
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed')], string='Status', default='new')
    submission_date = fields.Date(string='Submission Date')
    today = fields.Char(string='Today')
    view_mode = fields.Char(string='View Mode')
    week = fields.Char(string='Week')')

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
