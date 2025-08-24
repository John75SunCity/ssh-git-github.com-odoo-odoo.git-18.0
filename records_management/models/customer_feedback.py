# -*- coding: utf-8 -*-
"""
Customer Feedback Module

Manages customer feedback, including complaints, suggestions, and compliments,
with AI-ready sentiment analysis and a structured resolution workflow.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CustomerFeedback(models.Model):
    _name = 'customer.feedback'
    _description = 'Customer Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, feedback_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE & WORKFLOW
    # ============================================================================
    name = fields.Char(string='Feedback Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned To', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened')
    ], string='Status', default='new', required=True, tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent')
    ], string='Priority', compute='_compute_priority', store=True, default='0')

    # ============================================================================
    # RELATIONSHIPS & CONTEXT
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    contact_person_id = fields.Many2one('res.partner', string='Contact Person', domain="[('parent_id', '=', partner_id)]")
    team_id = fields.Many2one('crm.team', string='Sales Team', tracking=True)
    shredding_team_id = fields.Many2one('shredding.team', string="Shredding Team")
    theme_id = fields.Many2one('survey.feedback.theme', string="Feedback Theme")

    # ============================================================================
    # FEEDBACK DETAILS
    # ============================================================================
    description = fields.Text(string='Feedback Details', required=True)
    feedback_date = fields.Date(string='Feedback Date', default=fields.Date.context_today, required=True)
    feedback_type = fields.Selection([
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('compliment', 'Compliment'),
        ('question', 'Question')
    ], string='Feedback Type', default='complaint', required=True, tracking=True)
    service_area = fields.Selection([
        ('billing', 'Billing'),
        ('customer_service', 'Customer Service'),
        ('delivery', 'Delivery/Pickup'),
        ('portal', 'Customer Portal'),
        ('other', 'Other')
    ], string='Service Area', tracking=True)
    communication_method = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('portal', 'Portal'),
        ('in_person', 'In Person')
    ], string='Communication Method')

    # ============================================================================
    # SENTIMENT & RATING
    # ============================================================================
    rating = fields.Selection([
        ('1', '1 - Very Dissatisfied'),
        ('2', '2 - Dissatisfied'),
        ('3', '3 - Neutral'),
        ('4', '4 - Satisfied'),
        ('5', '5 - Very Satisfied')
    ], string='Rating', tracking=True)
    sentiment_category = fields.Selection([
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ], string='Sentiment Category', compute='_compute_sentiment_analysis', store=True)
    sentiment_score = fields.Float(string='Sentiment Score', compute='_compute_sentiment_analysis', store=True, aggregator='avg')

    # ============================================================================
    # RESOLUTION & FOLLOW-UP
    # ============================================================================
    response_required = fields.Boolean(string='Response Required', default=True)
    response_date = fields.Date(string='Response Date', readonly=True)
    response_notes = fields.Text(string='Internal Response Notes')
    resolution_notes = fields.Text(string='Resolution Notes')
    follow_up_required = fields.Boolean(string='Follow-up Required')
    follow_up_date = fields.Date(string='Follow-up Date')

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('description', 'rating', 'feedback_type')
    def _compute_sentiment_analysis(self):
        """AI-ready sentiment analysis with keyword matching and rating consideration."""
        positive_words = [
            "excellent", "great", "amazing", "wonderful", "fantastic",
            "satisfied", "happy", "pleased", "good", "awesome", "perfect", "love", "thank"
        ]
        negative_words = [
            "terrible", "awful", "horrible", "bad", "poor", "disappointed",
            "frustrated", "angry", "unsatisfied", "complaint", "problem", "issue", "wrong", "hate"
        ]
        for record in self:
            if not record.description:
                record.sentiment_category = "neutral"
                record.sentiment_score = 0.0
                continue

            description_lower = record.description.lower()
            positive_count = sum(1 for word in positive_words if word in description_lower)
            negative_count = sum(1 for word in negative_words if word in description_lower)

            base_score = (positive_count - negative_count) / max(len(description_lower.split()), 1)

            rating_adjustment = 0
            if record.rating:
                rating_adjustment = (int(record.rating) - 3) / 5.0

            final_score = max(-1.0, min(1.0, base_score + rating_adjustment))
            record.sentiment_score = final_score

            if final_score > 0.15:
                record.sentiment_category = "positive"
            elif final_score < -0.15:
                record.sentiment_category = "negative"
            else:
                record.sentiment_category = "neutral"

    @api.depends('sentiment_category', 'feedback_type', 'rating')
    def _compute_priority(self):
        """Compute priority based on sentiment analysis and feedback type."""
        for record in self:
            priority = '0'  # Normal
            if record.sentiment_category == "negative" or record.feedback_type == "complaint":
                priority = '1'  # High
            if record.rating == '1':
                priority = '2'  # Urgent
            record.priority = priority

    @api.constrains('sentiment_score')
    def _check_sentiment_score(self):
        for record in self:
            if record.sentiment_score and not (-1.0 <= record.sentiment_score <= 1.0):
                raise ValidationError(_("Sentiment score must be between -1 and 1."))

    @api.constrains('follow_up_date', 'feedback_date')
    def _check_follow_up_date(self):
        for record in self:
            if record.follow_up_date and record.feedback_date and record.follow_up_date < record.feedback_date:
                raise ValidationError(_("Follow-up date cannot be before the feedback date."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_acknowledge(self):
        self.ensure_one()
        if self.state != "new":
            raise UserError(_("Only new feedback can be acknowledged."))
        self.write({"state": "acknowledged"})
        self.message_post(body=_("Feedback acknowledged by %s.", self.env.user.name))

    def action_start_progress(self):
        self.ensure_one()
        if self.state not in ["new", "acknowledged"]:
            raise UserError(_("Only new or acknowledged feedback can be started."))
        self.write({"state": "in_progress"})
        self.message_post(body=_("Started working on feedback."))

    def action_resolve(self):
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress feedback can be resolved."))
        self.write({"state": "resolved", "response_date": fields.Date.today()})
        self.message_post(body=_("Feedback resolved."))

    def action_close(self):
        self.ensure_one()
        if self.state != "resolved":
            raise UserError(_("Only resolved feedback can be closed."))
        self.write({"state": "closed"})
        self.message_post(body=_("Feedback closed."))

    def action_reopen(self):
        self.ensure_one()
        if self.state != "closed":
            raise UserError(_("Only closed feedback can be reopened."))
        self.write({"state": "reopened"})
        self.message_post(body=_("Feedback reopened."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("customer.feedback") or _("New")
        return super().create(vals_list)

