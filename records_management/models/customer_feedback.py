# -*- coding: utf-8 -*-
"""
Customer Feedback Management Module

This module provides comprehensive customer feedback collection, analysis, and response management
for the Records Management System. It implements AI-ready sentiment analysis, automated priority
assignment, and complete feedback lifecycle management with customer portal integration.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerFeedback(models.Model):
    """
    Customer Feedback Management with AI-powered sentiment analysis
    """

    _name = "customer.feedback"
    _description = "Customer Feedback"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "feedback_date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Feedback Reference",
        required=True,
        tracking=True,
        default="New",
        copy=False,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # CUSTOMER INFORMATION FIELDS
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    contact_person_id = fields.Many2one(
        "res.partner", string="Contact Person", tracking=True
    )

    # ============================================================================
    # FEEDBACK DETAILS FIELDS
    # ============================================================================
    description = fields.Text(string="Feedback Details", tracking=True)
    feedback_date = fields.Date(
        string="Feedback Date", default=fields.Date.today, required=True, tracking=True
    )
    feedback_type = fields.Selection(
        [
            ("compliment", "Compliment"),
            ("complaint", "Complaint"),
            ("suggestion", "Suggestion"),
            ("question", "Question"),
            ("general", "General Feedback"),
        ],
        string="Feedback Type",
        required=True,
        tracking=True,
    )

    service_area = fields.Selection(
        [
            ("pickup", "Pickup Service"),
            ("storage", "Storage Service"),
            ("destruction", "Destruction Service"),
            ("customer_service", "Customer Service"),
            ("billing", "Billing"),
            ("general", "General"),
        ],
        string="Service Area",
        tracking=True,
    )

    # ============================================================================
    # RATING AND SATISFACTION FIELDS
    # ============================================================================
    rating = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Rating",
        tracking=True,
    )

    satisfaction_level = fields.Selection(
        [
            ("very_dissatisfied", "Very Dissatisfied"),
            ("dissatisfied", "Dissatisfied"),
            ("neutral", "Neutral"),
            ("satisfied", "Satisfied"),
            ("very_satisfied", "Very Satisfied"),
        ],
        string="Satisfaction Level",
        tracking=True,
    )

    # ============================================================================
    # AI SENTIMENT ANALYSIS FIELDS
    # ============================================================================
    sentiment_category = fields.Selection(
        [("positive", "Positive"), ("neutral", "Neutral"), ("negative", "Negative")],
        string="Sentiment Category",
        compute="_compute_sentiment_analysis",
        store=True,
    )

    sentiment_score = fields.Float(
        string="Sentiment Score",
        compute="_compute_sentiment_analysis",
        store=True,
        help="Sentiment score from -1 (negative) to 1 (positive)",
    )

    # ============================================================================
    # WORKFLOW STATE FIELDS
    # ============================================================================
    state = fields.Selection(
        [
            ("new", "New"),
            ("acknowledged", "Acknowledged"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="new",
        tracking=True,
        required=True,
    )

    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="normal",
        tracking=True,
        compute="_compute_priority",
        store=True,
    )

    # ============================================================================
    # RESPONSE TRACKING FIELDS
    # ============================================================================
    response_required = fields.Boolean(string="Response Required", default=True)
    response_date = fields.Date(string="Response Date", tracking=True)
    response_notes = fields.Text(string="Response Notes", tracking=True)
    resolution_notes = fields.Text(string="Resolution Notes", tracking=True)

    # ============================================================================
    # COMMUNICATION FIELDS
    # ============================================================================
    communication_method = fields.Selection(
        [
            ("portal", "Customer Portal"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("sms", "SMS"),
            ("in_person", "In Person"),
        ],
        string="Communication Method",
        default="portal",
    )

    follow_up_required = fields.Boolean(string="Follow-up Required", default=False)
    follow_up_date = fields.Date(string="Follow-up Date")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    attachment_ids = fields.Many2many(
        "ir.attachment", string="Attachments", help="Files attached to this feedback"
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
    @api.depends("description", "rating", "satisfaction_level")
    def _compute_sentiment_analysis(self):
        """AI-ready sentiment analysis with keyword matching and rating consideration"""
        for record in self:
            if not record.description:
                record.sentiment_category = "neutral"
                record.sentiment_score = 0.0
                continue

            # Simple keyword-based sentiment analysis (AI-ready for ML enhancement)
            description_lower = record.description.lower()

            # Positive keywords
            positive_words = [
                "excellent",
                "great",
                "amazing",
                "wonderful",
                "fantastic",
                "satisfied",
                "happy",
                "pleased",
                "good",
                "awesome",
                "perfect",
                "love",
                "thank",
            ]

            # Negative keywords
            negative_words = [
                "terrible",
                "awful",
                "horrible",
                "bad",
                "poor",
                "disappointed",
                "frustrated",
                "angry",
                "unsatisfied",
                "complaint",
                "problem",
                "issue",
                "wrong",
                "hate",
            ]

            positive_count = sum(
                1 for word in positive_words if word in description_lower
            )
            negative_count = sum(
                1 for word in negative_words if word in description_lower
            )

            # Calculate base sentiment score
            base_score = (positive_count - negative_count) / max(
                len(description_lower.split()), 1
            )

            # Adjust based on rating if available
            rating_adjustment = 0
            if record.rating:
                rating_num = int(record.rating)
                rating_adjustment = (rating_num - 3) / 5  # Normalize to -0.4 to 0.4

            # Adjust based on satisfaction level
            satisfaction_adjustment = 0
            if record.satisfaction_level:
                satisfaction_map = {
                    "very_dissatisfied": -0.4,
                    "dissatisfied": -0.2,
                    "neutral": 0,
                    "satisfied": 0.2,
                    "very_satisfied": 0.4,
                }
                satisfaction_adjustment = satisfaction_map.get(
                    record.satisfaction_level, 0
                )

            # Calculate final sentiment score
            final_score = base_score + rating_adjustment + satisfaction_adjustment
            final_score = max(-1.0, min(1.0, final_score))  # Clamp between -1 and 1

            record.sentiment_score = final_score

            # Determine category
            if final_score > 0.1:
                record.sentiment_category = "positive"
            elif final_score < -0.1:
                record.sentiment_category = "negative"
            else:
                record.sentiment_category = "neutral"

    @api.depends("sentiment_category", "feedback_type", "rating")
    def _compute_priority(self):
        """Compute priority based on sentiment analysis and feedback type"""
        for record in self:
            priority = "normal"  # default

            # Negative sentiment increases priority
            if record.sentiment_category == "negative":
                priority = "high"

            # Complaints get higher priority
            if record.feedback_type == "complaint":
                priority = "high"

            # Very poor ratings get urgent priority
            if record.rating == "1":
                priority = "urgent"

            # Very dissatisfied customers get urgent priority
            if record.satisfaction_level == "very_dissatisfied":
                priority = "urgent"

            record.priority = priority

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_acknowledge(self):
        """Acknowledge feedback and move to acknowledged state"""
        self.ensure_one()
        if self.state != "new":
            raise UserError(_("Only new feedback can be acknowledged"))
        self.write({"state": "acknowledged"})
        self.message_post(body=_("Feedback acknowledged by %s", self.env.user.name))

    def action_start_progress(self):
        """Start working on feedback"""
        self.ensure_one()
        if self.state not in ["new", "acknowledged"]:
            raise UserError(_("Only new or acknowledged feedback can be started"))
        self.write({"state": "in_progress"})
        self.message_post(body=_("Started working on feedback"))

    def action_resolve(self):
        """Mark feedback as resolved"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress feedback can be resolved"))
        self.write({"state": "resolved", "response_date": fields.Date.today()})
        self.message_post(body=_("Feedback resolved"))

    def action_close(self):
        """Close feedback after customer confirmation"""
        self.ensure_one()
        if self.state != "resolved":
            raise UserError(_("Only resolved feedback can be closed"))
        self.write({"state": "closed"})
        self.message_post(body=_("Feedback closed"))

    def action_reopen(self):
        """Reopen closed feedback if needed"""
        self.ensure_one()
        if self.state != "closed":
            raise UserError(_("Only closed feedback can be reopened"))
        self.write({"state": "in_progress"})
        self.message_post(body=_("Feedback reopened"))

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Create feedback records with auto-generated sequence numbers"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "customer.feedback"
                ) or _("New")
        return super().create(vals_list)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("rating")
    def _check_rating(self):
        """Validate rating value"""
        for record in self:
            if record.rating and record.rating not in ["1", "2", "3", "4", "5"]:
                raise ValidationError(_("Invalid rating value"))

    @api.constrains("sentiment_score")
    def _check_sentiment_score(self):
        """Validate sentiment score range"""
        for record in self:
            if record.sentiment_score and not (-1.0 <= record.sentiment_score <= 1.0):
                raise ValidationError(_("Sentiment score must be between -1 and 1"))

    @api.constrains("follow_up_date")
    def _check_follow_up_date(self):
        """Validate follow-up date is not in the past"""
        for record in self:
            if record.follow_up_date and record.follow_up_date < fields.Date.today():
                raise ValidationError(_("Follow-up date cannot be in the past"))
