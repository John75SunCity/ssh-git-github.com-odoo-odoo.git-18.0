from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PortalFeedback(models.Model):
    _name = 'portal.feedback'
    _description = 'Customer Portal Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    subject = fields.Char(string='Subject', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    submitted_by_id = fields.Many2one('res.users', string='Submitted By', default=lambda self: self.env.user, tracking=True)
    assigned_to_id = fields.Many2one('res.users', string='Assigned To', tracking=True)

    description = fields.Html(string='Feedback Details', required=True)

    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='new', readonly=True, tracking=True)

    # ============================================================================
    # CATEGORIZATION & RATING
    # ============================================================================
    feedback_type = fields.Selection([
        ('suggestion', 'Suggestion'),
        ('bug_report', 'Bug Report'),
        ('question', 'Question'),
        ('compliment', 'Compliment'),
        ('complaint', 'Complaint'),
    ], string='Feedback Type', default='suggestion', tracking=True)

    rating = fields.Selection([
        ('1', '1 - Very Poor'),
        ('2', '2 - Poor'),
        ('3', '3 - Neutral'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent'),
    ], string='Rating', tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', tracking=True)

    # ============================================================================
    # AI & SENTIMENT ANALYSIS
    # ============================================================================
    sentiment_score = fields.Float(string='Sentiment Score', compute='_compute_sentiment', store=True, readonly=True, help="Sentiment score from -1 (Negative) to 1 (Positive)")
    sentiment_category = fields.Selection([
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ], string='Sentiment', compute='_compute_sentiment', store=True, readonly=True)

    # ============================================================================
    # RESOLUTION & TRACKING
    # ============================================================================
    resolution_date = fields.Datetime(string='Resolution Date', readonly=True)
    first_response_date = fields.Datetime(string='First Response Date', readonly=True)
    interaction_count = fields.Integer(string='Interaction Count', default=0, readonly=True)

    # ============================================================================
    # RELATIONAL FIELDS
    # ============================================================================
    resolution_ids = fields.One2many('portal.feedback.resolution', 'feedback_id', string='Resolutions')
    communication_ids = fields.One2many('portal.feedback.communication', 'feedback_id', string='Communications')
    escalation_ids = fields.One2many('portal.feedback.escalation', 'feedback_id', string='Escalations')

    # ============================================================================
    # COMPUTE & ONCHANGE
    # ============================================================================
    @api.depends('description', 'rating')
    def _compute_sentiment(self):
        """
        Placeholder for AI-driven sentiment analysis.
        A real implementation would use a library like NLTK, TextBlob, or an external API.
        """
        for record in self:
            score = 0.0
            # Basic rating-based score
            if record.rating:
                score = (int(record.rating) - 3) / 2.0  # Scale 1-5 to -1 to 1

            # Basic keyword analysis (can be expanded)
            if record.description:
                lower_desc = record.description.lower()
                positive_keywords = ['excellent', 'great', 'love', 'amazing', 'good']
                negative_keywords = ['bad', 'poor', 'terrible', 'awful', 'disappointed']
                if any(kw in lower_desc for kw in positive_keywords):
                    score = max(score, 0.5)
                if any(kw in lower_desc for kw in negative_keywords):
                    score = min(score, -0.5)

            record.sentiment_score = score
            if score > 0.25:
                record.sentiment_category = 'positive'
            elif score < -0.25:
                record.sentiment_category = 'negative'
            else:
                record.sentiment_category = 'neutral'

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('portal.feedback') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_progress(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Feedback is now in progress."))

    def action_resolve(self):
        self.ensure_one()
        self.write({
            'state': 'resolved',
            'resolution_date': fields.Datetime.now()
        })
        self.message_post(body=_("Feedback has been marked as resolved."))

    def action_close(self):
        self.ensure_one()
        if self.state != 'resolved':
            raise UserError(_("Only resolved feedback can be closed."))
        self.write({'state': 'closed'})
        self.message_post(body=_("Feedback has been closed."))

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Feedback has been cancelled."))

    # Placeholder XML button
    def action_view_related_records(self):
        self.ensure_one()
        return False
