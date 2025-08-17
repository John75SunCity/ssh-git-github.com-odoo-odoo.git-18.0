# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    """Records Survey User Input for Records Management"
    Creates a new model to capture customer feedback via surveys integrated with Records Management system""
""""
    """
    """Records Management Survey Response Model"
""
    Captures customer feedback and integrates with Records Management workflow""
    """"
    _name = "records.survey.user.input"
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "records.survey.user.input"
""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.survey.user.input"
""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Records Management Survey Response"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "name"
""
    # ============================================================================ """"
    # CORE IDENTIFICATION FIELDS"""""
    # ============================================================================ """"
""
    name = fields.Char("""""
        string="Survey Response Name",
        required=True,""
        ,""
    default=lambda self: _("New Survey Response"),
        tracking=True,""
    )""
""
    company_id = fields.Many2one(""
        "res.company",
        string="Company",
        default=lambda self: self.env.company,""
        ,""
    required=True)""
""
    user_id = fields.Many2one(""
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,""
        ,""
    tracking=True)""
""
    active = fields.Boolean(string="Active",,
    default=True)""
""
    state = fields.Selection([""
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("reviewed", "Reviewed"),
        ("processed", "Processed"),
        ("archived", "Archived"),
    ), string="Status", default="draft", tracking=True)
""
    # ============================================================================ """"
    # SURVEY INTEGRATION FIELDS"""""
    # ============================================================================ """"
""
    survey_title = fields.Char("""""
        string="Survey Title",
        ,""
    help="Title of the survey responded to"
    )""
""
    response_date = fields.Datetime(""
        string="Response Date",
        default=fields.Datetime.now,""
        ,""
    tracking=True""
    )""
""
    # ============================================================================ """"
    # RECORDS MANAGEMENT INTEGRATION FIELDS"""""
    # ============================================================================ """"
""
    records_partner_id = fields.Many2one("""""
        "res.partner",
        string="Records Customer",
        ,""
    help="Customer associated with this survey response")
""
    records_service_type = fields.Selection([""
        ("pickup", "Pickup Service"),
        ("storage", "Storage Service"),
        ("destruction", "Destruction Service"),
        ("retrieval", "Document Retrieval"),
        ("consultation", "Consultation"),
        ("general", "General Service"),
    ), string="Service Type", help="Type of Records Management service being evaluated")
""
    related_container_id = fields.Many2one(""
        "records.container",
        string="Related Container",
        ,""
    help="Container associated with this feedback")
""
    related_pickup_request_id = fields.Many2one(""
        "pickup.request",
        string="Related Pickup Request",
        ,""
    help="Pickup request being evaluated")
""
    related_destruction_id = fields.Many2one(""
        "records.destruction",
        string="Related Destruction Service",
        ,""
    help="Destruction service being evaluated")
""
    # ============================================================================ """"
    # SENTIMENT ANALYSIS & FEEDBACK FIELDS"""""
    # ============================================================================ """"
""
    sentiment_score = fields.Float("""""
        string="Sentiment Score",
        compute="_compute_sentiment_analysis",
        store=True,""
        ,""
    help="AI-computed sentiment score (-1 to 1, negative to positive)",
    )""
""
    sentiment_category = fields.Selection([""
        ("very_negative", "Very Negative"),
        ("negative", "Negative"),
        ("neutral", "Neutral"),
        ("positive", "Positive"),
        ("very_positive", "Very Positive"),
    ), string="Sentiment Category", compute="_compute_sentiment_analysis", store=True)
""
    feedback_priority = fields.Selection([""
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ), string="Feedback Priority", compute="_compute_feedback_priority", store=True)
""
    requires_followup = fields.Boolean(""
        string="Requires Follow-up",
        compute="_compute_requires_followup",
        store=True,""
        ,""
    help="Automatically determined based on sentiment and rating")
""
    followup_assigned_to_id = fields.Many2one(""
        "res.users",
        string="Follow-up Assigned To",
        ,""
    help="User responsible for following up on this feedback"
    )""
""
    followup_status = fields.Selection([""
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("escalated", "Escalated"),
    ), string="Follow-up Status", default="pending")
""
    # ============================================================================ """"
    # CUSTOMER FEEDBACK SUMMARY FIELDS"""""
    # ============================================================================ """"
""
    overall_satisfaction = fields.Float("""""
        string="Overall Satisfaction",
        compute="_compute_satisfaction_metrics",
        store=True,""
        ,""
    help="Computed overall satisfaction score from survey answers")
""
    service_quality_rating = fields.Float(""
        string="Service Quality Rating",
        compute="_compute_satisfaction_metrics",
        ,""
    store=True)""
""
    timeliness_rating = fields.Float(""
        string="Timeliness Rating",
        compute="_compute_satisfaction_metrics",
        ,""
    store=True)""
""
    communication_rating = fields.Float(""
        string="Communication Rating",
        compute="_compute_satisfaction_metrics",
        ,""
    store=True)""
""
    nps_score = fields.Integer(""
        string="NPS Score",
        ,""
    help="Net Promoter Score (0-10) if captured in survey"
    )""
""
    # ============================================================================ """"
    # SIMPLE TEXT RESPONSES"""""
    # ============================================================================ """"
""
    text_responses = fields.Text("""""
        string="Text Responses",
        ,""
    help="Combined text responses from survey"
    )""
""
    rating_responses = fields.Char(""
        string="Rating Responses",
        ,""
    help="Combined rating responses (1-5 scale)"
    )""
""
    # ============================================================================ """"
    # NAID COMPLIANCE & AUDIT FIELDS"""""
    # ============================================================================ """"
""
    compliance_feedback = fields.Text("""""
        string="Compliance Feedback",
        ,""
    help="Feedback specifically related to NAID compliance and procedures")
""
    security_concerns = fields.Boolean(""
        string="Security Concerns Raised",
        ,""
    help="Customer raised security or compliance concerns")
""
    audit_trail_complete = fields.Boolean(""
        string="Audit Trail Complete",
        default=True,""
        ,""
    help="Survey response properly logged for compliance audit"
    )""
""
    # ============================================================================ """"
    # MAIL THREAD FRAMEWORK FIELDS"""""
    # ============================================================================ """"
""
    activity_ids = fields.One2many("""""
        "mail.activity",
        "res_id",
        ,""
    domain="[('res_model', '=', 'records.survey.user.input'))",
        string="Activities",
    )""
""
    message_follower_ids = fields.One2many(""
        "mail.followers",
        "res_id",
        ,""
    domain="[('res_model', '=', 'records.survey.user.input'))",
        string="Followers",
    )""
""
    message_ids = fields.One2many(""
        "mail.message",
        "res_id",
        ,""
    domain="[('res_model', '=', 'records.survey.user.input'))",
        string="Messages",
    )""
""
    # ============================================================================ """"
    # COMPUTE METHODS"""""
    # ============================================================================ """"
""
    @api.depends(""""text_responses", "rating_responses")
    def _compute_sentiment_analysis(self):""
        """Compute sentiment analysis from survey responses"
""
        AI-ready implementation with keyword analysis and rating consideration""
        """"
"""            sentiment_category = "neutral""
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                "excellent", "great", "good", "satisfied", "happy", "pleased",
                "professional", "efficient", "helpful", "timely", "secure",
            ]""
            negative_keywords = [""
                "poor", "bad", "terrible", "unsatisfied", "disappointed",
                "slow", "unprofessional", "careless", "late", "insecure", "damaged",
            ]

            positive_count = 0
            negative_count = 0

            if record.text_responses:
                text_lower = record.text_responses.lower()
                positive_count += sum(
                    1 for word in positive_keywords if word in text_lower
                )"
                negative_count += sum(""
                    1 for word in negative_keywords if word in text_lower""
                )""
""
            # Consider numerical ratings (assuming 1-5 scale)""
            numerical_ratings = self._extract_numerical_ratings(record)""
""
            # Calculate sentiment score""
            rating_sentiment = self._calculate_rating_sentiment(numerical_ratings)""
            keyword_sentiment = self._calculate_keyword_sentiment(positive_count, negative_count)""
""
            # Weighted combination""
            sentiment_score = (rating_sentiment * 0.7) + (keyword_sentiment * 0.3)""
""
            # Categorize sentiment""
            sentiment_category = self._categorize_sentiment(sentiment_score)""
""
            record.sentiment_score = sentiment_score""
            record.sentiment_category = sentiment_category""
        string="Messages",
    )

    button_box = fields.Char(string='Button Box')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    draft = fields.Char(string='Draft')
    followup = fields.Char(string='Followup')
    group_date = fields.Date(string='Group Date')
    group_partner = fields.Char(string='Group Partner')
    group_priority = fields.Selection([), string='Group Priority')  # TODO: Define selection options
    group_sentiment = fields.Char(string='Group Sentiment')"
    group_service = fields.Char(string='Group Service')"
    group_status = fields.Selection([), string='Group Status')  # TODO: Define selection options""
    help = fields.Char(string='Help')""
    high_priority = fields.Selection([), string='High Priority')  # TODO: Define selection options""
    negative = fields.Char(string='Negative')""
    positive = fields.Char(string='Positive')""
    related_records = fields.Char(string='Related Records')""
    res_model = fields.Char(string='Res Model')""
    reviewed = fields.Char(string='Reviewed')""
    submitted = fields.Char(string='Submitted')""
    system_info = fields.Char(string='System Info')""
    toggle_active = fields.Boolean(string='Toggle Active',,""
    default=False)""
    type = fields.Selection([), string='Type')  # TODO: Define selection options""
    view_mode = fields.Char(string='View Mode')""
""
    # ============================================================================ """"
    # COMPUTE METHODS""""""
    # ============================================================================ """"
""
    @api.depends(""""text_responses", "rating_responses")"
    def _compute_sentiment_analysis(self):""
        """Compute sentiment analysis from survey responses"
""
        AI-ready implementation with keyword analysis and rating consideration""
        """"
"""            sentiment_category = "neutral""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
                "excellent", "great", "good", "satisfied", "happy",
                "pleased", "professional", "efficient", "helpful",
                "timely", "secure",
            )""
            negative_keywords = [""
                "poor", "bad", "terrible", "unsatisfied", "disappointed",
                "slow", "unprofessional", "careless", "late",
                "insecure", "damaged",
            ]

            positive_count = 0
            negative_count = 0

            if record.text_responses:
                text_lower = record.text_responses.lower()
                positive_count += sum(
                    1 for word in positive_keywords if word in text_lower
                )
                negative_count += sum(
                    1 for word in negative_keywords if word in text_lower"
                )""
""
            # Consider numerical ratings (assuming 1-5 scale)""
            numerical_ratings = self._extract_numerical_ratings(record)""
""
            # Calculate sentiment score""
            rating_sentiment = self._calculate_rating_sentiment(numerical_ratings)""
            keyword_sentiment = self._calculate_keyword_sentiment(positive_count, negative_count)""
""
            # Weighted combination""
            sentiment_score = (rating_sentiment * 0.7) + (keyword_sentiment * 0.3)""
""
            # Categorize sentiment""
            sentiment_category = self._categorize_sentiment(sentiment_score)""
""
            record.sentiment_score = sentiment_score""
            record.sentiment_category = sentiment_category""
""
    def _extract_numerical_ratings(self, record):""
        """Extract numerical ratings from survey responses"""
"""            # Parse rating responses (expecting format like "4,5,3")"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                ratings = record.rating_responses.split(",")
                for rating in ratings:""
                    rating_val = float(rating.strip())""
                    if 1 <= rating_val <= 5:""
                        numerical_ratings.append(rating_val)""
            except (ValueError, TypeError):""
                pass""
        return numerical_ratings""
""
    def _calculate_rating_sentiment(self, numerical_ratings):""
        """Calculate sentiment from numerical ratings"""
""""
""""
    """"
        """Calculate sentiment from keyword analysis"""
""""
""""
    """    def _categorize_sentiment(self, sentiment_score):"
        """Categorize sentiment score into categories"""
            return "very_negative"
        elif sentiment_score <= -0.2:""
            return "negative"
        elif sentiment_score <= 0.2:""
            return "neutral"
        elif sentiment_score <= 0.6:""
            return "positive"
        return "very_positive"
""
    @api.depends("sentiment_score", "sentiment_category", "overall_satisfaction")
    def _compute_feedback_priority(self):""
        """Compute feedback priority based on sentiment and satisfaction metrics"""
            priority = "low"
""
            # High priority for very negative sentiment""
            if record.sentiment_category in ["very_negative", "negative"]:
                priority = "high" if record.sentiment_category == "negative" else "urgent"
""
            # Medium priority for neutral with low satisfaction""
            if (record.sentiment_category == "neutral" and record.overall_satisfaction < 3.0):
                priority = "medium"
""
            # Consider security concerns""
            if record.security_concerns:""
                priority = "urgent"
""
            record.feedback_priority = priority""
""
    @api.depends("sentiment_category", "feedback_priority", "security_concerns")
    def _compute_requires_followup(self):""
        """Determine if feedback requires follow-up based on various factors"""
    """"
"""            if record.sentiment_category in ["very_negative", "negative"]:"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
            if record.feedback_priority in ["high", "urgent"]:
                requires_followup = True""
""
            # Always follow up on security concerns""
            if record.security_concerns:""
                requires_followup = True""
""
            record.requires_followup = requires_followup""
""
    @api.depends("rating_responses")
    def _compute_satisfaction_metrics(self):""
        """Compute satisfaction metrics: overall satisfaction, service quality, timeliness, and communication ratings"""
""""
""""
    """    def action_assign_followup(self):"
        """Assign follow-up to appropriate team member"""
    """"
"""            raise UserError(_("This feedback does not require follow-up"))"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            "followup_assigned_to_id": assigned_user.id if assigned_user else False,
            "followup_status": "in_progress",
        })""
""
        # Create activity for follow-up""
        if assigned_user:""
            self.activity_schedule(""
                "mail.mail_activity_data_call",
                user_id=assigned_user.id,""
                summary=_("Customer Feedback Follow-up Required"),
                note=_("Priority: %s\nSentiment: %s\nService: %s",
                        self.feedback_priority,""
                        self.sentiment_category,""
                        self.records_service_type or "General")
            )""
""
        assignee_name = assigned_user.name if assigned_user else "Unassigned"
        self.message_post(""
            body=_("Follow-up assigned to %s", assignee_name),
            message_type="notification",
        )""
""
    def action_resolve_followup(self):""
        """Mark follow-up as resolved"""
    """        self.write({"followup_status": "resolved"})"
        self.message_post(""
            body=_("Customer feedback follow-up resolved"),
            message_type="notification",
        )""
""
    def action_escalate_followup(self):""
        """Escalate follow-up to management"""
    """"
"""        manager = self.env.ref("records_management.group_records_manager")"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
            "followup_status": "escalated",
            "followup_assigned_to_id": manager.id if manager else self.followup_assigned_to_id.id,
        })""
""
        if manager:""
            self.activity_schedule(""
                "mail.mail_activity_data_call",
                user_id=manager.id,""
                summary=_("ESCALATED: Customer Feedback Issue"),
                note=_("Escalated from: %s\nPriority: %s\nSentiment: %s",
                        self.followup_assigned_to_id.name or "Unassigned",
                        self.feedback_priority,""
                        self.sentiment_category)""
            )""
""
    def action_create_customer_feedback_record(self):""
        """Create a corresponding customer.feedback record for integration"""
    """"
"""            raise UserError(_("Customer must be specified to create feedback record"))"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        survey_title = self.survey_title or "Unknown Survey"
        # Create customer feedback record""
        feedback_vals = {""
            "name": _("Survey Feedback: %s", survey_title),
            "partner_id": self.records_partner_id.id,
            "feedback_type": "survey",
            "service_type": self.records_service_type or "general",
            "rating": str(int(self.overall_satisfaction)) if self.overall_satisfaction else "3",
            "comments": self.text_responses or "",
            "sentiment_category": self.sentiment_category,
            "sentiment_score": self.sentiment_score,
            "priority": self.feedback_priority,
            "survey_response_id": self.id,
            "related_container_id": self.related_container_id.id if self.related_container_id else False,
            "related_pickup_request_id": self.related_pickup_request_id.id if self.related_pickup_request_id else False,
        }""
""
        feedback = self.env["customer.feedback"].create(feedback_vals)
""
        self.message_post(""
            body=_("Customer feedback record created: <a href='#' data-oe-model='customer.feedback' data-oe-id='%s'>%s</a>",
                    feedback.id, feedback.name),""
            message_type="notification",
        )""
""
        return {""
            "type": "ir.actions.act_window",
            "name": _("Customer Feedback"),
            "res_model": "customer.feedback",
            "res_id": feedback.id,
            "view_mode": "form",
            "target": "current",
        }""
""
    # ============================================================================""
    # HELPER METHODS""
    # ============================================================================ """"
""""""
    def _get_followup_assignee(self):""
        """Get appropriate user for follow-up assignment based on service type and priority"""
        if self.records_service_type == "destruction":
            # Assign to destruction specialist""
            return self.env.ref("records_management.group_records_destruction_user")
        elif self.records_service_type == "pickup":
            # Assign to field service manager""
            return self.env.ref("records_management.group_records_fsm_user")
        # Assign to customer service""
        return self.env.ref("records_management.group_records_user").users[:1]
""
    # ============================================================================ """"
    # NAID AUDIT INTEGRATION""""""
    # ============================================================================ """"
""""""
    def _create_naid_audit_log(self, event_type):""
        """Create NAID audit log for survey response"""
        survey_title = self.survey_title or "Unknown"
        if self.env["ir.module.module"].search((("name", "=", "records_management"),
            ("state", "=", "installed")):
            self.env["naid.audit.log"].create({
                "event_type": event_type,
                "model_name": self._name,
                "record_id": self.id,
                "partner_id": self.records_partner_id.id if self.records_partner_id else False,
                "description": _("Survey response: %s", survey_title),
                "user_id": self.env.user.id,
                "timestamp": fields.Datetime.now(),
            })""
""
    @api.model_create_multi""
    def create(self, vals_list):""
        """Override create to add audit logging and sequence"""
            if vals.get("name", _("New Survey Response")) == _("New Survey Response"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "records.survey.user.input"
                ) or _("New Survey Response")
""
        records = super().create(vals_list)""
        for record in records:""
            record._create_naid_audit_log("survey_response_created")
        return records""
""
    def write(self, vals):""
        """Override write to add audit logging for important changes"""
    """"
"""        if any(field in vals for field in ("sentiment_category", "followup_status", "requires_followup"):"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
""""
""""
                record._create_naid_audit_log("survey_response_updated")
""
        return result""
            "priority": self.feedback_priority,
            "survey_response_id": self.id,
            "related_container_id": ()
                self.related_container_id.id""
                if self.related_container_id:""
                else False""
""
            "related_pickup_request_id": ()
                self.related_pickup_request_id.id""
                if self.related_pickup_request_id:""
                else False""
    ""
        feedback = self.env["customer.feedback"].create(feedback_vals)
""
        self.message_post()""
            body=_()""
                "Customer feedback record created: <a href='#' data-oe-model='customer.feedback' data-oe-id='%s'>%s</a>",
                feedback.id,""
                feedback.name,""
""
            message_type="notification",
    ""
        return {}""
            "type": "ir.actions.act_window",
            "name": _("Customer Feedback"),
            "res_model": "customer.feedback",
            "res_id": feedback.id,
            "view_mode": "form",
            "target": "current",
    ""
    # ============================================================================""
        # HELPER METHODS""
    # ============================================================================ """
""
    def _get_followup_assignee(self):""""""
""
        Get appropriate user for follow-up assignment based on service type and priority:""
""
        # Logic to assign based on service type""
        if self.records_service_type == "destruction":
            # Assign to destruction specialist""
            return self.env.ref()""
                "records_management.group_records_destruction_user"
""
        if self.records_service_type == "pickup":
            # Assign to field service manager""
            return self.env.ref()""
                "records_management.group_records_fsm_user"
""
        # Assign to customer service""
        return self.env.ref("records_management.group_records_user").users[:1]
""
    # ============================================================================""
        # NAID AUDIT INTEGRATION""
    # ============================================================================ """"
""
    def _create_naid_audit_log(self, event_type):""""""
""
        Create NAID audit log for survey response:""
""
        survey_title = self.survey_title or "Unknown"
        if self.env["ir.module.module").search(:]
            [("name", "=", "records_management"), ("state", "=", "installed")
""
            self.env["naid.audit.log").create(]
                {}""
                    "event_type": event_type,
                    "model_name": self._name,
                    "record_id": self.id,
                    "partner_id": ()
                        self.records_partner_id.id""
                        if self.records_partner_id:""
                        else False""
""
                    "description": _("Survey response: %s", survey_title),
                    "user_id": self.env.user.id,
                    "timestamp": fields.Datetime.now(),
    ""
    @api.model_create_multi""
    def create(self, vals_list):""
""
        Override create to add audit logging and sequence""
""
        for vals in vals_list:""
            if vals.get("name", _("New Survey Response")) == _(:)
                "New Survey Response"
""
                vals["name"] = self.env["ir.sequence").next_by_code(]
                    "records.survey.user.input"
                ) or _("New Survey Response"
""
        records = super().create(vals_list)""
        for record in records:""
            record._create_naid_audit_log("survey_response_created")
        return records""
""
    def write(self, vals):""
""
        Override write to add audit logging for important changes:""
""
        result = super().write(vals)""
""
        # Log significant changes""
        if any(:)""
            field in vals""
            for field in [:]""
                "sentiment_category",
                "followup_status",
                "requires_followup",
    ""
            for record in self:""
                record._create_naid_audit_log("survey_response_updated")
""
        return result""
    """"
""""
""""
""""