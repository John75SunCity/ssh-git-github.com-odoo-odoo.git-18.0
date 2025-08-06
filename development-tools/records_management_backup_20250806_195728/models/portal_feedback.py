# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


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

    assigned_to = fields.Many2one("res.users", string="Assigned To", tracking=True)
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
    # RELATIONSHIP FIELDS
    # ============================================================================
    improvement_areas = fields.Many2many(
        "feedback.improvement.area", string="Improvement Areas"
    )
    related_service_ids = fields.Many2many(
        "portal.request", string="Related Service Requests"
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends(
        "overall_rating",
        "service_quality_rating",
        "response_time_rating",
        "staff_friendliness_rating",
    )
    def _compute_satisfaction_level(self):
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
            elif record.sentiment_score < -0.2:
                record.sentiment_category = "negative"
            else:
                record.sentiment_category = "neutral"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_reviewed(self):
        """Mark feedback as reviewed"""
        self.ensure_one()
        if self.status != "new":
            raise UserError(_("Can only mark new feedback as reviewed"))
        self.write({"status": "reviewed", "assigned_to": self.env.user.id})

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
            "view_mode": "list,form",
            "domain": [("customer_id", "=", self.customer_id.id)],
            "context": {"default_customer_id": self.customer_id.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("follow_up_date")
    def _check_follow_up_date(self):
        for record in self:
            if (
                record.follow_up_required
                and record.follow_up_date
                and record.follow_up_date <= fields.Date.today()
            ):
                raise ValidationError(_("Follow-up date must be in the future"))

    @api.constrains("sentiment_score")
    def _check_sentiment_score(self):
        for record in self:
            if not (-1 <= record.sentiment_score <= 1):
                raise ValidationError(_("Sentiment score must be between -1 and 1"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate reference number"""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("portal.feedback") or "FB-NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Track status changes"""
        if "status" in vals:
            for record in self:
                if vals["status"] == "closed" and not vals.get("closure_date"):
                    vals["closure_date"] = fields.Datetime.now()
                elif vals["status"] == "responded" and not vals.get("response_date"):
                    vals["response_date"] = fields.Datetime.now()
        return super().write(vals)


class FeedbackImprovementArea(models.Model):
    _name = "feedback.improvement.area"
    _description = "Feedback Improvement Areas"
    _order = "name"

    name = fields.Char(string="Area", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
    color = fields.Integer(string="Color")
