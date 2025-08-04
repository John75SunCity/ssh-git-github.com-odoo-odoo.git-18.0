# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import re


class PortalFeedback(models.Model):
    _name = "portal.feedback"
    _description = "Portal Customer Feedback"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Feedback Reference", required=True, tracking=True, index=True)
    subject = fields.Char(string="Subject", required=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # Framework Required Fields
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

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & FEEDBACK DETAILS
    # ============================================================================

    # Customer Information
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)
    customer_name = fields.Char(string="Customer Name", related="partner_id.name", store=True)
    customer_email = fields.Char(string="Customer Email", related="partner_id.email", store=True)
    customer_phone = fields.Char(string="Customer Phone", related="partner_id.phone", store=True)

    # Feedback Classification
    feedback_type = fields.Selection(
        [
            ("complaint", "Complaint"),
            ("compliment", "Compliment"),
            ("suggestion", "Suggestion"),
            ("inquiry", "Inquiry"),
            ("request", "Service Request"),
        ],
        string="Feedback Type",
        required=True,
        tracking=True,
    )

    category = fields.Selection(
        [
            ("service_quality", "Service Quality"),
            ("billing", "Billing"),
            ("delivery", "Delivery"),
            ("communication", "Communication"),
            ("staff", "Staff"),
            ("product", "Product"),
            ("other", "Other"),
        ],
        string="Category",
        tracking=True,
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="medium",
        tracking=True,
    )

    # ============================================================================
    # FEEDBACK CONTENT & ANALYSIS
    # ============================================================================

    # Feedback Content
    comments = fields.Text(string="Comments", required=True)
    internal_notes = fields.Text(string="Internal Notes")
    resolution_notes = fields.Text(string="Resolution Notes")
    follow_up_notes = fields.Text(string="Follow-up Notes")

    # Rating System
    rating = fields.Selection(
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
    
    service_rating = fields.Integer(
        string="Service Rating (1-10)",
        help="Service quality rating from 1 to 10"
    )

    # AI-Ready Sentiment Analysis
    sentiment_category = fields.Selection(
        [
            ("positive", "Positive"),
            ("neutral", "Neutral"),
            ("negative", "Negative"),
        ],
        string="Sentiment",
        compute="_compute_sentiment_analysis",
        store=True,
    )

    sentiment_score = fields.Float(
        string="Sentiment Score",
        digits=(3, 2),
        compute="_compute_sentiment_analysis",
        store=True,
        help="Sentiment score from -1 (negative) to 1 (positive)",
    )

    # ============================================================================
    # DATES & SCHEDULING
    # ============================================================================

    feedback_date = fields.Datetime(
        string="Feedback Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )
    
    response_date = fields.Datetime(string="Response Date", tracking=True)
    resolution_date = fields.Datetime(string="Resolution Date", tracking=True)
    follow_up_date = fields.Date(string="Follow-up Date", tracking=True)
    escalation_date = fields.Datetime(string="Escalation Date")

    # Computed Time Metrics
    response_time_hours = fields.Float(
        string="Response Time (Hours)",
        compute="_compute_response_metrics",
        store=True,
    )
    
    resolution_time_hours = fields.Float(
        string="Resolution Time (Hours)",
        compute="_compute_response_metrics",
        store=True,
    )

    # ============================================================================
    # COMMUNICATION & FOLLOW-UP
    # ============================================================================

    # Communication Tracking
    contact_method = fields.Selection(
        [
            ("portal", "Customer Portal"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("in_person", "In Person"),
            ("mail", "Mail"),
        ],
        string="Contact Method",
        default="portal",
    )

    communication_language = fields.Selection(
        [
            ("en", "English"),
            ("es", "Spanish"),
            ("fr", "French"),
        ],
        string="Communication Language",
        default="en",
    )

    requires_follow_up = fields.Boolean(string="Requires Follow-up", default=False)
    follow_up_completed = fields.Boolean(string="Follow-up Completed", default=False)
    customer_satisfied = fields.Boolean(string="Customer Satisfied")

    # ============================================================================
    # ESCALATION & MANAGEMENT
    # ============================================================================

    # Escalation Management
    is_escalated = fields.Boolean(string="Escalated", default=False, tracking=True)
    escalated_to = fields.Many2one("res.users", string="Escalated To")
    escalation_reason = fields.Text(string="Escalation Reason")

    # Management Review
    requires_management_review = fields.Boolean(string="Requires Management Review")
    management_reviewed = fields.Boolean(string="Management Reviewed")
    reviewed_by = fields.Many2one("res.users", string="Reviewed By")
    review_date = fields.Datetime(string="Review Date")

    # ============================================================================
    # ATTACHMENTS & DOCUMENTATION
    # ============================================================================

    # File Attachments
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")
    attachment_count = fields.Integer(
        string="Attachment Count",
        compute="_compute_attachment_count",
    )

    # Documentation
    reference_documents = fields.Text(string="Reference Documents")
    related_tickets = fields.Text(string="Related Tickets")
    
    # Binary Fields
    mimetype = fields.Char(string="MIME Type")

    # ============================================================================
    # PERFORMANCE & ANALYTICS
    # ============================================================================

    # Performance Metrics
    impact_level = fields.Selection(
        [
            ("low", "Low Impact"),
            ("medium", "Medium Impact"),
            ("high", "High Impact"),
            ("critical", "Critical Impact"),
        ],
        string="Impact Level",
        default="low",
    )

    business_impact = fields.Text(string="Business Impact Description")
    cost_impact = fields.Monetary(
        string="Cost Impact",
        currency_field="currency_id",
        help="Estimated cost impact of the feedback",
    )

    # Analytics Tags
    tag_ids = fields.Many2many("portal.feedback.tag", string="Tags")
    
    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Records
    portal_request_id = fields.Many2one("portal.request", string="Related Portal Request")
    project_task_id = fields.Many2one("project.task", string="Related Task")
    sale_order_id = fields.Many2one("sale.order", string="Related Sale Order")

    # Child/Parent Relationships
    parent_feedback_id = fields.Many2one("portal.feedback", string="Parent Feedback")
    child_feedback_ids = fields.One2many(
        "portal.feedback", "parent_feedback_id", string="Related Feedback"
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("comments", "rating", "feedback_type")
    def _compute_sentiment_analysis(self):
        """AI-ready sentiment analysis with extensible ML integration"""
        for record in self:
            if not record.comments:
                record.sentiment_category = "neutral"
                record.sentiment_score = 0.0
                continue

            # Simple keyword-based sentiment analysis (can be replaced with ML)
            positive_keywords = [
                "excellent", "great", "good", "amazing", "satisfied", "happy",
                "perfect", "outstanding", "wonderful", "fantastic", "pleased"
            ]
            negative_keywords = [
                "terrible", "bad", "awful", "disappointed", "angry", "frustrated",
                "horrible", "unsatisfied", "poor", "worst", "hate", "complaint"
            ]

            text_lower = record.comments.lower()
            positive_count = sum(1 for word in positive_keywords if word in text_lower)
            negative_count = sum(1 for word in negative_keywords if word in text_lower)

            # Factor in rating if available
            rating_score = 0
            if record.rating:
                rating_num = int(record.rating)
                if rating_num >= 4:
                    rating_score = 0.3
                elif rating_num <= 2:
                    rating_score = -0.3

            # Calculate sentiment score (-1 to 1)
            base_score = (positive_count - negative_count) * 0.2
            final_score = max(-1, min(1, base_score + rating_score))

            record.sentiment_score = final_score

            # Determine category
            if final_score > 0.2:
                record.sentiment_category = "positive"
            elif final_score < -0.2:
                record.sentiment_category = "negative"
            else:
                record.sentiment_category = "neutral"

    @api.depends("feedback_date", "response_date", "resolution_date")
    def _compute_response_metrics(self):
        """Compute response and resolution time metrics"""
        for record in self:
            if record.feedback_date and record.response_date:
                delta = record.response_date - record.feedback_date
                record.response_time_hours = delta.total_seconds() / 3600
            else:
                record.response_time_hours = 0.0

            if record.feedback_date and record.resolution_date:
                delta = record.resolution_date - record.feedback_date
                record.resolution_time_hours = delta.total_seconds() / 3600
            else:
                record.resolution_time_hours = 0.0

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        """Compute number of attachments"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_submit_feedback(self):
        """Submit feedback for processing"""
        self.ensure_one()
        self.write({
            "state": "submitted",
            "feedback_date": fields.Datetime.now(),
        })
        
        # Auto-assign based on category and priority
        self._auto_assign_feedback()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Feedback Submitted"),
                "message": _("Your feedback has been submitted successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_start_processing(self):
        """Start processing the feedback"""
        self.ensure_one()
        self.write({
            "state": "in_progress",
            "response_date": fields.Datetime.now(),
        })
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Processing Started"),
                "message": _("Feedback processing has been initiated."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_resolve_feedback(self):
        """Mark feedback as resolved"""
        self.ensure_one()
        if not self.resolution_notes:
            raise UserError(_("Please enter resolution notes before resolving."))
        
        self.write({
            "state": "resolved",
            "resolution_date": fields.Datetime.now(),
        })
        
        # Send resolution notification to customer
        self._send_resolution_notification()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Feedback Resolved"),
                "message": _("Feedback has been marked as resolved."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_escalate(self):
        """Escalate feedback to management"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Escalate Feedback"),
            "res_model": "feedback.escalation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_feedback_id": self.id,
                "default_escalation_reason": "Priority escalation required",
            },
        }

    def action_view_attachments(self):
        """View feedback attachments"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
        }

    def action_create_task(self):
        """Create project task from feedback"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Task"),
            "res_model": "project.task",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"Feedback: {self.subject}",
                "default_description": self.comments,
                "default_user_ids": [(6, 0, [self.user_id.id])],
                "default_partner_id": self.partner_id.id,
            },
        }

    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================

    def _auto_assign_feedback(self):
        """Auto-assign feedback based on category and priority"""
        for record in self:
            if record.category == "billing":
                # Assign to billing team
                billing_user = self.env.ref("records_management.user_billing", False)
                if billing_user:
                    record.user_id = billing_user
            elif record.priority == "urgent":
                # Assign to management
                manager = self.env.ref("records_management.user_manager", False)
                if manager:
                    record.user_id = manager

    def _send_resolution_notification(self):
        """Send resolution notification to customer"""
        for record in self:
            if record.partner_id.email:
                template = self.env.ref("records_management.mail_template_feedback_resolution", False)
                if template:
                    template.send_mail(record.id, force_send=True)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("service_rating")
    def _check_service_rating(self):
        """Ensure service rating is between 1 and 10"""
        for record in self:
            if record.service_rating and (record.service_rating < 1 or record.service_rating > 10):
                raise ValidationError(_("Service rating must be between 1 and 10."))

    @api.constrains("sentiment_score")
    def _check_sentiment_score(self):
        """Ensure sentiment score is between -1 and 1"""
        for record in self:
            if record.sentiment_score and (record.sentiment_score < -1 or record.sentiment_score > 1):
                raise ValidationError(_("Sentiment score must be between -1 and 1."))

    @api.constrains("feedback_date", "response_date", "resolution_date")
    def _check_date_sequence(self):
        """Ensure dates are in logical sequence"""
        for record in self:
            if record.feedback_date and record.response_date:
                if record.response_date < record.feedback_date:
                    raise ValidationError(_("Response date cannot be before feedback date."))
            
            if record.response_date and record.resolution_date:
                if record.resolution_date < record.response_date:
                    raise ValidationError(_("Resolution date cannot be before response date."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals):
        """Override create to set defaults and generate sequence"""
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("portal.feedback") or _("New")
        
        # Auto-set priority based on sentiment
        if vals.get("comments") and not vals.get("priority"):
            # Simple keyword-based priority detection
            urgent_keywords = ["urgent", "immediate", "emergency", "critical"]
            if any(keyword in vals["comments"].lower() for keyword in urgent_keywords):
                vals["priority"] = "urgent"
        
        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Feedback status changed from %s to %s") % (old_state, new_state)
                )
        
        return super().write(vals)


class PortalFeedbackTag(models.Model):
    """Tags for categorizing feedback"""
    _name = "portal.feedback.tag"
    _description = "Portal Feedback Tag"
    _order = "name"

    name = fields.Char(string="Tag Name", required=True)
    color = fields.Integer(string="Color Index", default=0)
    active = fields.Boolean(string="Active", default=True)
    description = fields.Text(string="Description")
