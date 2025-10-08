# -*- coding: utf-8 -*-
"""
Customer Feedback Module

Manages customer feedback, including complaints, suggestions, and compliments,
with AI-ready sentiment analysis and a structured resolution workflow.

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class CustomerFeedback(models.Model):
    _name = 'customer.feedback'
    _description = 'Customer Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # CORE & WORKFLOW (added escalation_date + communication_count)
    # ============================================================================
    name = fields.Char(string='Subject', required=True, tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned To', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], string='Status', default='new', required=True, tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)
    description = fields.Text(string='Description', help="Detailed description used in extended views and reports")

    # Escalation & Ownership (added to match view usage)
    escalation_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Escalation Level', tracking=True, index=True)
    escalated_to_id = fields.Many2one(comodel_name='res.users', string='Escalated To', tracking=True)
    escalated_by_id = fields.Many2one(comodel_name='res.users', string='Escalated By', tracking=True, default=lambda self: self.env.user, readonly=True)

    # Timeline / dates
    acknowledged_date = fields.Datetime(string='Acknowledged On', readonly=True)
    resolution_date = fields.Datetime(string='Resolved On', readonly=True)
    last_response_date = fields.Datetime(string='Last Response On')
    expected_resolution_date = fields.Date(string='Expected Resolution Date')
    follow_up_required = fields.Boolean(string='Follow-up Required')
    follow_up_date = fields.Date(string='Follow-up Date')
    escalation_date = fields.Datetime(string='Escalated On', readonly=True)

    # Durations (hours) – simplistic compute placeholders
    response_time = fields.Float(string='First Response Time (h)', readonly=True, compute='_compute_times', store=False)
    resolution_time = fields.Float(string='Resolution Time (h)', readonly=True, compute='_compute_times', store=False)
    escalation_time = fields.Float(string='Escalation Time (h)', readonly=True, compute='_compute_times', store=False)
    communication_count = fields.Integer(string='Message Count', compute='_compute_communication_count')

    # ============================================================================
    # RELATIONSHIPS & CONTEXT
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    contact_id = fields.Many2one(comodel_name='res.partner', string='Contact')
    team_id = fields.Many2one(comodel_name='crm.team', string='Sales Team', tracking=True)
    shredding_team_id = fields.Many2one(comodel_name='shredding.team', string="Shredding Team")
    # Primary classification (single theme) to satisfy inverse used by survey.feedback.theme.feedback_ids
    theme_id = fields.Many2one(
        'survey.feedback.theme',
        string='Primary Theme',
        help='Main theme classification (used for reporting & survey theme linkage).'
    )
    theme_ids = fields.Many2many(
        comodel_name='customer.feedback.theme',
        relation='customer_feedback_theme_rel',
        column1='feedback_id',
        column2='theme_id',
        string='Themes',
    )
    tags = fields.Char(string='Tags')  # widget=char_tags

    # ============================================================================
    # FEEDBACK DETAILS
    # ============================================================================
    feedback_type = fields.Selection(
        selection=[
            ('general', 'General'),
            ('suggestion', 'Suggestion'),
            ('bug_report', 'Bug Report'),
            ('feature_request', 'Feature Request'),
            ('compliment', 'Compliment'),
            ('complaint', 'Complaint'),
            ('security_concern', 'Security Concern'),
        ],
        string='Feedback Type',
        default='general',
        index=True,
        tracking=True,
        help='Categorizes the type of feedback for routing, analytics, and SLA prioritization.'
    )
    comments = fields.Text(string='Customer Comments')
    internal_notes = fields.Text(string='Internal Notes')
    resolution_type = fields.Selection(
        selection=[
            ('fixed', 'Fixed'),
            ('workaround', 'Workaround'),
            ('wont_fix', "Won't Fix"),
            ('duplicate', 'Duplicate'),
            ('invalid', 'Invalid'),
            ('info_provided', 'Information Provided'),
            ('other', 'Other'),
        ],
        string='Resolution Type',
    )
    resolution_notes = fields.Text(string='Resolution Notes')
    customer_response = fields.Text(string='Customer Response')

    # ============================================================================
    # SENTIMENT & RATING
    # ============================================================================
    rating = fields.Integer(string='Rating')  # 1–5 star widget
    satisfaction_score = fields.Integer(string='Satisfaction Score')
    sentiment_score = fields.Float(string='Sentiment Score', digits=(6, 3))
    sentiment_category = fields.Selection(
        selection=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')],
        string='Sentiment',
        default='neutral',
        tracking=True,
    )

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('acknowledged_date', 'create_date', 'resolution_date', 'escalated_by_id')
    def _compute_times(self):
        """Simple delta computations (in hours). TODO: refine with SLA logic."""
        for rec in self:
            rec.response_time = 0.0
            rec.resolution_time = 0.0
            rec.escalation_time = 0.0
            if rec.create_date and rec.acknowledged_date:
                rec.response_time = (rec.acknowledged_date - rec.create_date).total_seconds() / 3600.0
            if rec.create_date and rec.resolution_date:
                rec.resolution_time = (rec.resolution_date - rec.create_date).total_seconds() / 3600.0
            if rec.create_date and rec.escalated_by_id and rec.acknowledged_date:
                # Placeholder; real logic would use escalation timestamp field if separate
                rec.escalation_time = (rec.acknowledged_date - rec.create_date).total_seconds() / 3600.0

    # ============================================================================
    # ACTION METHODS (clean, single implementations)
    # ============================================================================
    def action_acknowledge(self):
        self.ensure_one()
        if self.state != 'new':
            raise UserError(_("Only new feedback can be acknowledged."))
        self.write({
            'state': 'acknowledged',
            'acknowledged_date': fields.Datetime.now(),
            'user_id': self.user_id.id or self.env.user.id,
        })
        self.message_post(body=_('Feedback acknowledged'))

    def action_start_progress(self):
        self.ensure_one()
        if self.state not in ('new', 'acknowledged'):
            raise UserError(_("Only new or acknowledged feedback can be started."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_('Feedback in progress'))

    def action_resolve(self):
        self.ensure_one()
        if self.state not in ('acknowledged', 'in_progress'):
            raise UserError(_("Only acknowledged or in-progress feedback can be resolved."))
        self.write({
            'state': 'resolved',
            'resolution_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Feedback resolved'))

    def action_close(self):
        self.ensure_one()
        if self.state != 'resolved':
            raise UserError(_("Only resolved feedback can be closed."))
        self.write({'state': 'closed'})
        self.message_post(body=_('Feedback closed'))

    def action_escalate(self):
        self.ensure_one()
        if self.state in ('resolved', 'closed'):
            raise UserError(_("Cannot escalate resolved or closed feedback."))
        level_order = ['low', 'medium', 'high', 'critical']
        current = self.escalation_level or 'low'
        if current == 'critical':
            return
        next_level = level_order[level_order.index(current) + 1] if current in level_order else 'medium'
        self.write({
            'escalation_level': next_level,
            'escalated_by_id': self.env.user.id,
            'escalated_to_id': self.escalated_to_id.id or self.env.user.id,
            'escalation_date': self.escalation_date or fields.Datetime.now(),
        })
        if self.state == 'new':
            self.action_acknowledge()
        self.message_post(body=_('Feedback escalated'))

    # --- Sentiment placeholder (extendable) ---
    @api.onchange('comments', 'rating')
    def _onchange_sentiment_stub(self):
        """Light heuristic placeholder. TODO: replace with real analyzer."""
        for rec in self:
            txt = (rec.comments or '').lower()
            score = 0
            if any(k in txt for k in ['great', 'excellent', 'love', 'good']):
                score += 0.5
            if any(k in txt for k in ['bad', 'poor', 'angry', 'terrible']):
                score -= 0.5
            if rec.rating:
                score += (rec.rating - 3) * 0.1
            rec.sentiment_score = max(-1, min(1, score))
            if rec.sentiment_score > 0.15:
                rec.sentiment_category = 'positive'
            elif rec.sentiment_score < -0.15:
                rec.sentiment_category = 'negative'
            else:
                rec.sentiment_category = 'neutral'

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("customer.feedback") or _("New")
        return super().create(vals_list)

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

    # Removed action_link_latest_survey_response (referenced undefined survey fields); re-add when fields exist.

    # ============================================================================
    # COMPUTE HELPERS (retain single valid implementation)
    # ============================================================================
    @api.depends('message_ids')
    def _compute_communication_count(self):
        for record in self:
            record.communication_count = len(record.message_ids)

    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        """If a contact with a parent is selected and no customer set yet, set partner_id."""
        for rec in self:
            if rec.contact_id and rec.contact_id.parent_id and not rec.partner_id:
                rec.partner_id = rec.contact_id.parent_id
