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
    active = fields.Boolean(string='Active', default=True)
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

    # Escalation & Ownership (added to match view usage)
    escalation_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Escalation Level', tracking=True, index=True)
    escalated_to_id = fields.Many2one('res.users', string='Escalated To', tracking=True)
    escalated_by_id = fields.Many2one('res.users', string='Escalated By', tracking=True, default=lambda self: self.env.user, readonly=True)
    escalation_time = fields.Float(string='Escalation Time (hrs)', help='Time in hours from creation until escalation.', compute='_compute_escalation_time', store=True)
    escalation_date = fields.Datetime(string='Escalation Date', readonly=True)

    # Computed metrics referenced by analytics pages (placeholders if not already implemented elsewhere)
    response_time = fields.Float(string='Response Time (hrs)', readonly=True, help='Time in hours from creation until first response.')
    resolution_time = fields.Float(string='Resolution Time (hrs)', readonly=True, help='Time in hours from creation until resolution.')
    communication_count = fields.Integer(string='Communications', compute='_compute_communication_count', store=False, help='Number of chatter messages linked to this feedback.')


    # ============================================================================
    # RELATIONSHIPS & CONTEXT
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    contact_person_id = fields.Many2one('res.partner', string='Contact Person', domain="[('parent_id', '=', partner_id)]")
    team_id = fields.Many2one('crm.team', string='Sales Team', tracking=True)
    shredding_team_id = fields.Many2one('shredding.team', string="Shredding Team")
    theme_id = fields.Many2one('survey.feedback.theme', string="Feedback Theme")
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        domain="[('parent_id', '=', partner_id)]",
        help="Specific contact person (child of the Customer) related to this feedback."
    )

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
    # Added to satisfy view reference and provide numeric value of rating
    satisfaction_score = fields.Float(string='Satisfaction Score', compute='_compute_satisfaction_score', store=True, help='Numeric representation of rating (1-5), 0 when not set.', aggregator='avg')
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

    # --- Survey Integration (optional linkage, not structural inheritance) ---
    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string='Survey Template',
        help='Optional survey used to collect this feedback.'
    )
    survey_user_input_id = fields.Many2one(
        comodel_name='survey.user_input',
        string='Survey Response',
        domain="[('survey_id', '=', survey_id)]",
        help='Specific submitted survey response linked to this feedback.'
    )
    survey_answer_count = fields.Integer(
        string='Answers',
        compute='_compute_survey_answer_count',
        help='Number of answer lines in the linked survey response.'
    )

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('rating')
    def _compute_satisfaction_score(self):
        for record in self:
            record.satisfaction_score = float(record.rating) if record.rating else 0.0

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

    @api.depends('survey_user_input_id')
    def _compute_survey_answer_count(self):
        for rec in self:
            rec.survey_answer_count = len(rec.survey_user_input_id.user_input_line_ids) if rec.survey_user_input_id else 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_acknowledge(self):
        self.ensure_one()
        if self.state != "new":
            raise UserError(_("Only new feedback can be acknowledged."))
        self.write({"state": "acknowledged"})
        # Log acknowledgement with actor name
        self.message_post(body=_("Feedback acknowledged by %s") % self.env.user.name)

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

    def action_escalate(self):
        """Escalate feedback to higher priority."""
        self.ensure_one()
        if self.state in ["resolved", "closed"]:
            raise UserError(_("Cannot escalate resolved or closed feedback."))

        # Increase priority automatically when escalating
        if self.priority == "0":
            self.priority = "1"
        elif self.priority == "1":
            self.priority = "2"

        # Set escalation metadata
        if not self.escalation_date:
            self.escalation_date = fields.Datetime.now()
        if not self.escalated_by_id:
            self.escalated_by_id = self.env.user

        # Auto-assign escalation level if none chosen
        if not self.escalation_level:
            self.escalation_level = 'moderate' if self.priority == '1' else 'high' if self.priority == '2' else 'low'
        # Log escalation action (include user performing escalation)
        self.message_post(body=_("Feedback escalated by %s") % self.env.user.name)
        return True

    def action_link_latest_survey_response(self):
        """Convenience: link the most recent completed survey.user_input for the same partner & survey."""
        self.ensure_one()
        if not self.partner_id or not self.survey_id:
            raise UserError(_("Partner and Survey must be set before linking a survey response."))
        latest = self.env['survey.user_input'].search([
            ('partner_id', '=', self.partner_id.id),
            ('survey_id', '=', self.survey_id.id),
            ('state', '=', 'done'),
        ], order='create_date desc', limit=1)
        if not latest:
            raise UserError(_("No completed survey response found for this customer and survey."))
        self.survey_user_input_id = latest
        # Optional: derive rating from a question tagged 'rating'
        rating_line = latest.user_input_line_ids.filtered(lambda l: l.question_id.question_type in ('simple_choice', 'matrix') and 'rating' in (l.question_id.tags or '').lower())[:1]
        if rating_line and not self.rating:
            # Assuming answer scoring 1..5 stored in numerical_value / value_suggested
            score = getattr(rating_line, 'numerical_value', False) or getattr(rating_line, 'value_suggested', False)
            if score and str(int(score)) in {'1', '2', '3', '4', '5'}:
                self.rating = str(int(score))
        self.message_post(body=_("Linked survey response %s") % latest.display_name)
        return True

    # ==========================================================================
    # COMPUTE METHODS (Metrics)
    # ==========================================================================
    @api.depends('create_date', 'escalation_date')
    def _compute_escalation_time(self):
        for record in self:
            if record.create_date and record.escalation_date:
                delta = fields.Datetime.from_string(record.escalation_date) - fields.Datetime.from_string(record.create_date)
                record.escalation_time = round(delta.total_seconds() / 3600.0, 2)
            else:
                record.escalation_time = 0.0

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

    # ============================================================================
    # COMPUTE HELPERS
    # ============================================================================
    @api.depends('message_ids')
    def _compute_communication_count(self):
        # Use sudo=False context to respect access rules; count messages excluding system notifications if desired
        for record in self:
            # Exclude internal notifications if needed: record.message_ids.filtered(lambda m: m.message_type != 'notification')
            record.communication_count = len(record.message_ids)

    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        """If a contact with a parent is selected and no customer set yet, set partner_id."""
        for rec in self:
            if rec.contact_id and rec.contact_id.parent_id and not rec.partner_id:
                rec.partner_id = rec.contact_id.parent_id
