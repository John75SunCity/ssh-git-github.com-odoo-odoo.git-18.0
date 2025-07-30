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
    resolution_time_hours = fields.Float(string='Resolution Time (Hours)')

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
