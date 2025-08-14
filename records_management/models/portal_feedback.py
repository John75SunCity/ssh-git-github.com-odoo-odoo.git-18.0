# -*- coding: utf-8 -*-
"""
Portal Feedback Management Module

Comprehensive customer feedback system within the Records Management System.
This module provides AI-ready sentiment analysis, multi-dimensional rating systems,
workflow management, and integration with customer portal for enterprise-grade
feedback collection and response management.

Key Features:
- AI-ready sentiment analysis with extensible ML integration
- Multi-dimensional rating system (overall, service quality, response time, staff)
- Comprehensive workflow management with escalation capabilities
- Integration with customer portal and service request systems
- Advanced analytics and reporting capabilities

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError




class PortalFeedback(models.Model):
    _name = "portal.feedback"
    _description = "Portal Customer Feedback"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Feedback Reference", required=True, tracking=True, index=True
    )
    subject = fields.Char(string="Subject", required=True, tracking=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & FEEDBACK DETAILS
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True, index=True
    )
    feedback_type = fields.Selection(
        [
            ("general", "General Feedback"),
            ("complaint", "Complaint"),
            ("suggestion", "Suggestion"),
            ("compliment", "Compliment"),
            ("service_request", "Service Request"),
        ],
        string="Feedback Type",
        required=True,
        default="general",
        tracking=True,
    )

    # ============================================================================
    # RATINGS & SATISFACTION
    # ============================================================================
    overall_rating = fields.Selection(
        [
            ("1", "1 - Very Poor"),
            ("2", "2 - Poor"),
            ("3", "3 - Average"),
            ("4", "4 - Good"),
            ("5", "5 - Excellent"),
        ],
        string="Overall Rating",
        tracking=True,
    )

    service_quality_rating = fields.Selection(
        [
            ("1", "1 - Very Poor"),
            ("2", "2 - Poor"),
            ("3", "3 - Average"),
            ("4", "4 - Good"),
            ("5", "5 - Excellent"),
        ],
        string="Service Quality",
        tracking=True,
    )

    response_time_rating = fields.Selection(
        [
            ("1", "1 - Very Poor"),
            ("2", "2 - Poor"),
            ("3", "3 - Average"),
            ("4", "4 - Good"),
            ("5", "5 - Excellent"),
        ],
        string="Response Time",
        tracking=True,
    )

    staff_friendliness_rating = fields.Selection(
        [
            ("1", "1 - Very Poor"),
            ("2", "2 - Poor"),
            ("3", "3 - Average"),
            ("4", "4 - Good"),
            ("5", "5 - Excellent"),
        ],
        string="Staff Friendliness",
        tracking=True,
    )

    satisfaction_level = fields.Selection(
        [
            ("very_satisfied", "Very Satisfied"),
            ("satisfied", "Satisfied"),
            ("neutral", "Neutral"),
            ("dissatisfied", "Dissatisfied"),
            ("very_dissatisfied", "Very Dissatisfied"),
        ],
        string="Satisfaction Level",
        compute="_compute_satisfaction_level",
        store=True,
        tracking=True,
    )

    # ============================================================================
    # WORKFLOW & STATUS
    # ============================================================================
    status = fields.Selection(
        [
            ("new", "New"),
            ("reviewed", "Under Review"),
            ("responded", "Responded"),
            ("escalated", "Escalated"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="new",
        required=True,
        tracking=True,
    )

    priority = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="medium",
        tracking=True,
    )

    assigned_to_id = fields.Many2one(
        "res.users", string="Assigned To", tracking=True
    )
    submission_date = fields.Datetime(
        string="Submission Date", default=fields.Datetime.now, required=True
    )
    response_date = fields.Datetime(string="Response Date", tracking=True)
    closure_date = fields.Datetime(string="Closure Date", tracking=True)

    # ============================================================================
    # CONTENT & COMMUNICATION
    # ============================================================================
    comments = fields.Text(string="Customer Comments", required=True)
    internal_notes = fields.Text(string="Internal Notes", groups="base.group_user")
    response_text = fields.Html(string="Response to Customer")
    resolution_notes = fields.Text(string="Resolution Notes")

    follow_up_required = fields.Boolean(string="Follow-up Required", default=False)
    follow_up_date = fields.Date(string="Follow-up Date")
    escalation_reason = fields.Text(string="Escalation Reason")

    # ============================================================================
    # AI SENTIMENT ANALYSIS
    # ============================================================================
    sentiment_score = fields.Float(
        string="Sentiment Score",
        compute="_compute_sentiment_analysis",
        store=True,
        help="AI sentiment score from -1 (negative) to 1 (positive)",
    )
    sentiment_category = fields.Selection(
        [("positive", "Positive"), ("neutral", "Neutral"), ("negative", "Negative")],
        string="Sentiment Category",
        compute="_compute_sentiment_analysis",
        store=True,
    )

    # ============================================================================
    # ENTERPRISE WORKFLOW FIELDS
    # ============================================================================
    escalated = fields.Boolean(
        string="Escalated",
        compute="_compute_escalated",
        store=True,
        help="True if feedback has been escalated",
    )

    # NPS Fields for Analytics Integration
    nps_score = fields.Integer(
        string="NPS Score",
        compute="_compute_nps_score",
        store=True,
        help="Net Promoter Score (0-10)",
    )
    nps_category = fields.Selection(
        [
            ("detractor", "Detractor (0-6)"),
            ("passive", "Passive (7-8)"),
            ("promoter", "Promoter (9-10)"),
        ],
        string="NPS Category",
        compute="_compute_nps_score",
        store=True,
    )

    # Response Time Fields for SLA Tracking
    response_time_hours = fields.Float(
        string="Response Time (Hours)", compute="_compute_response_time", store=True
    )
    resolution_time_hours = fields.Float(
        string="Resolution Time (Hours)", compute="_compute_resolution_time", store=True
    )

    # SLA Fields
    sla_deadline = fields.Datetime(string="SLA Deadline", tracking=True)
    sla_met = fields.Boolean(
        string="SLA Met", compute="_compute_sla_compliance", store=True
    )

    # Date Created Field (required for analytics)
    date_created = fields.Datetime(
        string="Date Created", default=fields.Datetime.now, required=True, index=True
    )

    # Sentiment Analysis (simplified for existing code compatibility)
    sentiment = fields.Selection(
        [
            ("very_positive", "Very Positive"),
            ("positive", "Positive"),
            ("neutral", "Neutral"),
            ("negative", "Negative"),
            ("very_negative", "Very Negative"),
        ],
        string="Sentiment",
        compute="_compute_sentiment_analysis",
        store=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    improvement_area_ids = fields.Many2many(
        "feedback.improvement.area", string="Improvement Areas"
    )
    related_service_ids = fields.Many2many(
        "portal.request", string="Related Service Requests"
    )

    # Resolution and Escalation Tracking
    resolution_ids = fields.One2many(
        "portal.feedback.resolution", "feedback_id", string="Resolutions"
    )
    escalation_ids = fields.One2many(
        "portal.feedback.escalation", "feedback_id", string="Escalations"
    )
    action_ids = fields.One2many(
        "portal.feedback.action", "feedback_id", string="Actions"
    )
    communication_ids = fields.One2many(
        "portal.feedback.communication", "feedback_id", string="Communications"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends(
        "overall_rating",
        "service_quality_rating",
        "response_time_rating",
        "staff_friendliness_rating",
    )
    def _compute_satisfaction_level(self):
        """Compute overall satisfaction based on individual ratings"""
        for record in self:
            ratings = [
                int(record.overall_rating or 0),
                int(record.service_quality_rating or 0),
                int(record.response_time_rating or 0),
                int(record.staff_friendliness_rating or 0),
            ]
            valid_ratings = [r for r in ratings if r > 0]
            if valid_ratings:
                avg_rating = sum(valid_ratings) / len(valid_ratings)
                if avg_rating >= 4.5:
                    record.satisfaction_level = "very_satisfied"
                elif avg_rating >= 3.5:
                    record.satisfaction_level = "satisfied"
                elif avg_rating >= 2.5:
                    record.satisfaction_level = "neutral"
                elif avg_rating >= 1.5:
                    record.satisfaction_level = "dissatisfied"
                else:
                    record.satisfaction_level = "very_dissatisfied"
            else:
                record.satisfaction_level = "neutral"

    @api.depends("comments", "overall_rating", "satisfaction_level")
    def _compute_sentiment_analysis(self):
        """AI-Ready Sentiment Analysis with keyword matching and rating consideration"""
        for record in self:
            score = 0
            text = (record.comments or "").lower()

            # Keyword-based sentiment analysis (extensible for ML integration)
            positive_keywords = [
                "excellent",
                "great",
                "good",
                "satisfied",
                "happy",
                "pleased",
                "recommend",
                "professional",
                "helpful",
                "amazing",
                "outstanding",
            ]
            negative_keywords = [
                "poor",
                "bad",
                "terrible",
                "awful",
                "disappointed",
                "frustrated",
                "angry",
                "complaint",
                "problem",
                "horrible",
                "unacceptable",
            ]

            positive_count = sum(1 for word in positive_keywords if word in text)
            negative_count = sum(1 for word in negative_keywords if word in text)

            # Base sentiment from keywords
            if positive_count > negative_count:
                score += 0.3
            elif negative_count > positive_count:
                score -= 0.3

            # Rating influence
            if record.overall_rating:
                rating_score = (
                    int(record.overall_rating) - 3
                ) / 2  # Scale 1-5 to -1 to 1
                score += rating_score * 0.7

            # Normalize score
            record.sentiment_score = max(-1, min(1, score))

            # Categorize sentiment
            if record.sentiment_score > 0.2:
                record.sentiment_category = "positive"
                record.sentiment = "positive"
            elif record.sentiment_score < -0.2:
                record.sentiment_category = "negative"
                record.sentiment = "negative"
            else:
                record.sentiment_category = "neutral"
                record.sentiment = "neutral"

    @api.depends("status")
    def _compute_escalated(self):
        """Check if feedback has been escalated"""
        for record in self:
            record.escalated = record.status == "escalated"

    @api.depends("overall_rating")
    def _compute_nps_score(self):
        """Compute NPS score and category"""
        for record in self:
            if record.overall_rating:
                # Convert 1-5 rating to 0-10 NPS scale
                nps_value = (int(record.overall_rating) - 1) * 2.5
                record.nps_score = int(nps_value)

                if record.nps_score <= 6:
                    record.nps_category = "detractor"
                elif record.nps_score <= 8:
                    record.nps_category = "passive"
                else:
                    record.nps_category = "promoter"
            else:
                record.nps_score = 0
                record.nps_category = False

    @api.depends("submission_date", "response_date")
    def _compute_response_time(self):
        """Calculate response time in hours"""
        for record in self:
            if record.response_date and record.submission_date:
                delta = record.response_date - record.submission_date
                record.response_time_hours = delta.total_seconds() / 3600
            else:
                record.response_time_hours = 0

    @api.depends("submission_date", "closure_date")
    def _compute_resolution_time(self):
        """Calculate resolution time in hours"""
        for record in self:
            if record.closure_date and record.submission_date:
                delta = record.closure_date - record.submission_date
                record.resolution_time_hours = delta.total_seconds() / 3600
            else:
                record.resolution_time_hours = 0

    @api.depends("response_date", "sla_deadline")
    def _compute_sla_compliance(self):
        """Check if SLA was met"""
        for record in self:
            if record.sla_deadline and record.response_date:
                record.sla_met = record.response_date <= record.sla_deadline
            else:
                record.sla_met = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_reviewed(self):
        """Mark feedback as reviewed"""

        self.ensure_one()
        if self.status != "new":
            raise UserError(_("Can only mark new feedback as reviewed"))
        self.write({"status": "reviewed", "assigned_to": self.env.user.id})

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner", 
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility"
    )

    def action_respond(self):
        """Mark feedback as responded"""

        self.ensure_one()
        if self.status not in ["new", "reviewed"]:
            raise UserError(_("Can only respond to new or reviewed feedback"))
        self.write(
            {
                "status": "responded",
                "response_date": fields.Datetime.now(),
                "assigned_to": self.env.user.id,
            }
        )

    def action_escalate(self):
        """Escalate feedback to higher priority"""

        self.ensure_one()
        if self.status in ["closed"]:
            raise UserError(_("Cannot escalate closed feedback"))
        self.write({"status": "escalated", "priority": "high"})

    def action_close(self):
        """Close feedback"""

        self.ensure_one()
        if self.status not in ["responded", "escalated"]:
            raise UserError(_("Can only close responded or escalated feedback"))
        self.write({"status": "closed", "closure_date": fields.Datetime.now()})

    def action_reopen(self):
        """Reopen closed feedback"""

        self.ensure_one()
        if self.status != "closed":
            raise UserError(_("Can only reopen closed feedback"))
        self.write({"status": "reviewed", "closure_date": False})

    def action_view_related_records(self):
        """View related service requests and records"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Records"),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("customer_id", "=", self.customer_id.id)],
            "context": {"default_customer_id": self.customer_id.id},
        }

    def action_create_improvement_action(self):
        """Create improvement action based on feedback"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Improvement Action"),
            "res_model": "improvement.action.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_feedback_id": self.id,
                "default_customer_id": self.customer_id.id,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("follow_up_date")
    def _check_follow_up_date(self):
        """Validate follow-up date logic"""
        for record in self:
            if record.follow_up_required and record.follow_up_date:
                if record.follow_up_date <= fields.Date.today():
                    raise ValidationError(_("Follow-up date must be in the future"))
            if not record.follow_up_required and record.follow_up_date:
                raise ValidationError(
                    _("Follow-up date should not be set if follow-up is not required")
                )

    @api.constrains("sentiment_score")
    def _check_sentiment_score(self):
        """Validate sentiment score range"""
        for record in self:
            if not (-1 <= record.sentiment_score <= 1):
                raise ValidationError(_("Sentiment score must be between -1 and 1"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate reference number and set SLA deadline"""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "portal.feedback"
                ) or _("New")

            # Set SLA deadline (24 hours for urgent, 48 hours for high, 72 hours for others)
            if not vals.get("sla_deadline"):
                priority = vals.get("priority", "medium")
                hours_map = {"urgent": 24, "high": 48, "medium": 72, "low": 96}
                hours = hours_map.get(priority, 72)
                vals["sla_deadline"] = fields.Datetime.now() + fields.timedelta(
                    hours=hours
                )

        return super(PortalFeedback, self).create(vals_list)

    def write(self, vals):
        """Track status changes and update timestamps"""
        if "status" in vals:
            for record in self:
                if vals["status"] == "closed" and not vals.get("closure_date"):
                    vals["closure_date"] = fields.Datetime.now()
                elif vals["status"] == "responded" and not vals.get("response_date"):
                    vals["response_date"] = fields.Datetime.now()
        return super(PortalFeedback, self).write(vals)

    def get_priority_color(self):
        """Get color code for priority display"""
        self.ensure_one()
        color_map = {
            "low": "success",
            "medium": "info",
            "high": "warning",
            "urgent": "danger",
        }
        return color_map.get(self.priority, "secondary")

    def get_sentiment_color(self):
        """Get color code for sentiment display"""
        self.ensure_one()
        color_map = {
            "positive": "success",
            "neutral": "secondary",
            "negative": "danger",
        }
        return color_map.get(self.sentiment_category, "secondary")


class FeedbackImprovementArea(models.Model):
    """
    Model representing areas for improvement identified from customer feedback.
    """

    _name = "feedback.improvement.area"
    _description = "Feedback Improvement Areas"
    _order = "name"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string="Area", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
    color = fields.Integer(string="Color", default=1)

    # ============================================================================
    # ANALYTICS FIELDS
    # ============================================================================
    feedback_count = fields.Integer(

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        string="Feedback Count",
        compute="_compute_feedback_count",
        help="Number of feedback entries related to this area",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name")
    def _compute_feedback_count(self):
        """Compute number of related feedback entries"""
        for record in self:
            record.feedback_count = self.env["portal.feedback"].search_count(
                [("improvement_areas", "in", record.id)]
            )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_related_feedback(self):
        """View feedback related to this improvement area"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Feedback"),
            "res_model": "portal.feedback",
            "view_mode": "tree,form",
            "domain": [("improvement_areas", "in", self.id)],
            "context": {"default_improvement_areas": [(6, 0, [self.id])]},
        }
