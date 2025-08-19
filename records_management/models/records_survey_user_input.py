from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsSurveyUserInput(models.Model):
    _name = 'records.survey.user.input'
    _description = 'Records Management Survey Response'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Response ID", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Submitted By", default=lambda self: self.env.user, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('follow_up', 'Follow-up Required'),
        ('resolved', 'Resolved'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # SURVEY & RESPONSE DETAILS
    # ============================================================================
    survey_title = fields.Char(string="Survey Title", required=True)
    response_date = fields.Datetime(string="Response Date", default=fields.Datetime.now, required=True, readonly=True)
    records_partner_id = fields.Many2one('res.partner', string="Customer", tracking=True)
    records_service_type = fields.Selection([
        ('general', 'General'),
        ('pickup', 'Pickup'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('consulting', 'Consulting'),
    ], string="Service Type", tracking=True)
    related_container_id = fields.Many2one('records.container', string="Related Container")
    related_pickup_request_id = fields.Many2one('portal.request', string="Related Pickup Request")
    related_destruction_id = fields.Many2one('records.destruction', string="Related Destruction Order")

    # ============================================================================
    # AI-DRIVEN ANALYTICS (COMPUTED)
    # ============================================================================
    sentiment_score = fields.Float(string="Sentiment Score", compute='_compute_analytics', store=True, group_operator="avg")
    sentiment_category = fields.Selection([
        ('very_negative', 'Very Negative'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('positive', 'Positive'),
        ('very_positive', 'Very Positive'),
    ], string="Sentiment", compute='_compute_analytics', store=True)
    feedback_priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string="Priority", compute='_compute_analytics', store=True)
    requires_followup = fields.Boolean(string="Requires Follow-up", compute='_compute_analytics', store=True)

    # ============================================================================
    # FOLLOW-UP MANAGEMENT
    # ============================================================================
    followup_assigned_to_id = fields.Many2one('res.users', string="Follow-up Assigned To", tracking=True)
    followup_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('escalated', 'Escalated'),
        ('resolved', 'Resolved'),
    ], string="Follow-up Status", tracking=True)

    # ============================================================================
    # RAW RESPONSE DATA
    # ============================================================================
    overall_satisfaction = fields.Float(string="Overall Satisfaction (1-5)", compute='_compute_analytics', store=True)
    service_quality_rating = fields.Float(string="Service Quality (1-5)", compute='_compute_analytics', store=True)
    timeliness_rating = fields.Float(string="Timeliness (1-5)", compute='_compute_analytics', store=True)
    communication_rating = fields.Float(string="Communication (1-5)", compute='_compute_analytics', store=True)
    nps_score = fields.Integer(string="NPS Score (-100 to 100)")
    text_responses = fields.Text(string="Text Feedback")
    rating_responses = fields.Char(string="Raw Ratings", help="Comma-separated numerical ratings, e.g., '4,5,3'")
    compliance_feedback = fields.Text(string="Compliance Feedback")
    security_concerns = fields.Boolean(string="Security Concerns Reported")
    audit_trail_complete = fields.Boolean(string="Audit Trail Complete")

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('text_responses', 'rating_responses', 'security_concerns')
    def _compute_analytics(self):
        """
        Compute sentiment, priority, and other metrics from survey responses.
        This is an AI-ready implementation with keyword analysis and rating consideration.
        """
        positive_keywords = [
            "excellent", "great", "good", "satisfied", "happy", "pleased",
            "professional", "efficient", "helpful", "timely", "secure",
        ]
        negative_keywords = [
            "poor", "bad", "terrible", "unsatisfied", "disappointed",
            "slow", "unprofessional", "careless", "late", "insecure", "damaged",
        ]

        for record in self:
            # 1. Extract Numerical Ratings
            numerical_ratings = record._extract_numerical_ratings()
            
            # 2. Calculate Satisfaction Metrics
            if numerical_ratings:
                avg_rating = sum(numerical_ratings) / len(numerical_ratings)
                record.overall_satisfaction = avg_rating
                # In a real scenario, these would come from specific questions
                record.service_quality_rating = avg_rating
                record.timeliness_rating = avg_rating
                record.communication_rating = avg_rating
            else:
                record.overall_satisfaction = 0.0
                record.service_quality_rating = 0.0
                record.timeliness_rating = 0.0
                record.communication_rating = 0.0

            # 3. Calculate Sentiment Score
            rating_sentiment = record._calculate_rating_sentiment(numerical_ratings)
            keyword_sentiment = record._calculate_keyword_sentiment(positive_keywords, negative_keywords)
            sentiment_score = (rating_sentiment * 0.7) + (keyword_sentiment * 0.3)
            record.sentiment_score = sentiment_score
            record.sentiment_category = record._categorize_sentiment(sentiment_score)

            # 4. Determine Priority
            priority = 'low'
            if record.sentiment_category in ['negative', 'very_negative']:
                priority = 'high'
            elif record.sentiment_category == 'neutral' and record.overall_satisfaction < 3.0:
                priority = 'medium'
            if record.security_concerns or record.sentiment_category == 'very_negative':
                priority = 'urgent'
            record.feedback_priority = priority

            # 5. Determine if Follow-up is needed
            record.requires_followup = record.feedback_priority in ['high', 'urgent']

    def _extract_numerical_ratings(self):
        """Extract numerical ratings from survey responses."""
        self.ensure_one()
        numerical_ratings = []
        if self.rating_responses:
            try:
                ratings = self.rating_responses.split(",")
                for rating in ratings:
                    rating_val = float(rating.strip())
                    if 1 <= rating_val <= 5:
                        numerical_ratings.append(rating_val)
            except (ValueError, TypeError):
                pass
        return numerical_ratings

    def _calculate_rating_sentiment(self, numerical_ratings):
        """Calculate sentiment from numerical ratings."""
        if numerical_ratings:
            avg_rating = sum(numerical_ratings) / len(numerical_ratings)
            return (avg_rating - 3) / 2  # Convert 1-5 rating to -1 to 1 sentiment score
        return 0

    def _calculate_keyword_sentiment(self, positive_keywords, negative_keywords):
        """Calculate sentiment from keyword analysis."""
        self.ensure_one()
        if not self.text_responses:
            return 0
        text_lower = self.text_responses.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        if positive_count + negative_count > 0:
            return (positive_count - negative_count) / (positive_count + negative_count)
        return 0

    def _categorize_sentiment(self, sentiment_score):
        """Categorize sentiment score into categories."""
        if sentiment_score <= -0.6: return "very_negative"
        elif sentiment_score <= -0.2: return "negative"
        elif sentiment_score <= 0.2: return "neutral"
        elif sentiment_score <= 0.6: return "positive"
        else: return "very_positive"

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("records.survey.user.input") or _("New")
        records = super().create(vals_list)
        for record in records:
            record.write({'state': 'completed'})
        return records

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_require_followup(self):
        for record in self:
            if not record.requires_followup:
                raise UserError(_("This feedback does not require follow-up based on current analytics."))
            
            assignee = record._get_followup_assignee()
            record.write({
                'state': 'follow_up',
                'followup_status': 'pending',
                'followup_assigned_to_id': assignee.id if assignee else False,
            })
            if assignee:
                record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Customer Feedback Follow-up Required'),
                    note=_('Priority: %s\nSentiment: %s\nService: %s',
                           record.feedback_priority, record.sentiment_category, record.records_service_type or "General"),
                    user_id=assignee.id
                )
                record.message_post(body=_("Follow-up assigned to %s.", assignee.name))

    def action_resolve_followup(self):
        self.write({"state": "resolved", "followup_status": "resolved"})
        self.message_post(body=_("Customer feedback follow-up resolved."))

    def action_create_customer_feedback_record(self):
        self.ensure_one()
        if not self.records_partner_id:
            raise UserError(_("Customer must be specified to create a feedback record."))

        feedback_vals = {
            "name": _("Survey Feedback: %s", self.survey_title or "N/A"),
            "partner_id": self.records_partner_id.id,
            "feedback_type": "survey",
            "service_type": self.records_service_type or "general",
            "rating": str(int(self.overall_satisfaction)) if self.overall_satisfaction else "3",
            "comments": self.text_responses or "",
            "sentiment_category": self.sentiment_category,
            "sentiment_score": self.sentiment_score,
            "priority": self.feedback_priority,
            "survey_response_id": self.id,
            "related_container_id": self.related_container_id.id,
            "related_pickup_request_id": self.related_pickup_request_id.id,
        }
        feedback = self.env["customer.feedback"].create(feedback_vals)
        self.message_post(
            body=_("Customer feedback record created: <a href='#' data-oe-model='customer.feedback' data-oe-id='%s'>%s</a>") % (feedback.id, feedback.name),
            message_type="notification")

        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Feedback"),
            "res_model": "customer.feedback",
            "res_id": feedback.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _get_followup_assignee(self):
        """Get appropriate user for follow-up assignment."""
        self.ensure_one()
        # This logic can be expanded with more complex rules
        manager_group = self.env.ref("records_management.group_records_manager", raise_if_not_found=False)
        if manager_group and self.feedback_priority == 'urgent':
            return manager_group.users[:1]
        
        user_group = self.env.ref("records_management.group_records_user", raise_if_not_found=False)
        if user_group:
            return user_group.users[:1]
            
        return self.env['res.users']

