# -*- coding: utf-8 -*-
"""
Portal Feedback Support Models Module

Supporting models for the comprehensive portal feedback system within the Records Management System.
These models provide resolution tracking, escalation management, action item tracking, communication logging,
and analytics capabilities for customer feedback management.

Key Features:
- Resolution tracking with satisfaction measurement
- Multi-level escalation management
- Action item assignment and tracking
- Communication audit trail
- Comprehensive analytics and reporting

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PortalFeedbackResolution(models.Model):
    _name = "portal.feedback.resolution"
    _description = "Portal Feedback Resolution"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "feedback_id, resolution_date desc"
    _rec_name = "feedback_id"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # RESOLUTION TRACKING
    # ============================================================================
    feedback_id = fields.Many2one(
        "portal.feedback",
        string="Feedback",
        required=True,
        ondelete="cascade",
        index=True,
    )
    resolution_date = fields.Datetime(
        string="Resolution Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    resolved_by = fields.Many2one(
        "res.users",
        string="Resolved By",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    resolution_type = fields.Selection(
        [
            ("immediate", "Immediate Resolution"),
            ("process_change", "Process Change Required"),
            ("escalation", "Escalated to Higher Level"),
            ("training", "Training Required"),
            ("system_fix", "System Fix Required"),
            ("no_action", "No Action Required"),
        ],
        string="Resolution Type",
        required=True,
        tracking=True,
    )
    resolution_description = fields.Text(string="Resolution Description", required=True)
    customer_notified = fields.Boolean(
        string="Customer Notified", default=False, tracking=True
    )

    # ============================================================================
    # SATISFACTION TRACKING
    # ============================================================================
    satisfaction_after_resolution = fields.Selection(
        [
            ("1", "Very Dissatisfied"),
            ("2", "Dissatisfied"),
            ("3", "Neutral"),
            ("4", "Satisfied"),
            ("5", "Very Satisfied"),
        ],
        string="Satisfaction After Resolution",
        tracking=True,
    )

    # ============================================================================
    # FINANCIAL TRACKING
    # ============================================================================
    cost_of_resolution = fields.Monetary(
        string="Cost of Resolution", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_notify_customer(self):
        """Notify customer about the resolution"""
        self.ensure_one()
        if not self.feedback_id.customer_id:
            raise UserError(_("No customer found for this feedback."))

        self.write({"customer_notified": True})
        self.message_post(
            body=_("Customer has been notified about the resolution."),
            message_type="notification",
        )

    def action_update_satisfaction(self):
        """Open wizard to update customer satisfaction"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Update Satisfaction"),
            "res_model": "satisfaction.update.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_resolution_id": self.id},
        }


class PortalFeedbackEscalation(models.Model):
    _name = "portal.feedback.escalation"
    _description = "Portal Feedback Escalation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "feedback_id, escalation_date desc"
    _rec_name = "feedback_id"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ESCALATION TRACKING
    # ============================================================================
    feedback_id = fields.Many2one(
        "portal.feedback",
        string="Feedback",
        required=True,
        ondelete="cascade",
        index=True,
    )
    escalation_date = fields.Datetime(
        string="Escalation Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    escalated_by = fields.Many2one(
        "res.users",
        string="Escalated By",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    escalated_to = fields.Many2one(
        "res.users", string="Escalated To", required=True, tracking=True
    )
    escalation_reason = fields.Text(string="Escalation Reason", required=True)
    escalation_level = fields.Selection(
        [
            ("level_1", "Level 1 - Supervisor"),
            ("level_2", "Level 2 - Manager"),
            ("level_3", "Level 3 - Director"),
            ("level_4", "Level 4 - Executive"),
        ],
        string="Escalation Level",
        required=True,
        tracking=True,
    )
    urgency = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Urgency",
        default="medium",
        tracking=True,
    )
    deadline = fields.Datetime(string="Response Deadline")
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("acknowledged", "Acknowledged"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
        ],
        string="Status",
        default="pending",
        tracking=True,
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_acknowledge(self):
        """Acknowledge the escalation"""
        self.ensure_one()
        if self.status != "pending":
            raise UserError(_("Only pending escalations can be acknowledged."))

        self.write({"status": "acknowledged"})
        self.message_post(
            body=_("Escalation has been acknowledged."), message_type="notification"
        )

    def action_start_progress(self):
        """Start working on the escalation"""
        self.ensure_one()
        if self.status not in ["pending", "acknowledged"]:
            raise UserError(
                _("Can only start progress on pending or acknowledged escalations.")
            )

        self.write({"status": "in_progress"})
        self.message_post(
            body=_("Work has started on this escalation."), message_type="notification"
        )

    def action_resolve(self):
        """Mark escalation as resolved"""
        self.ensure_one()
        self.write({"status": "resolved"})
        self.message_post(
            body=_("Escalation has been resolved."), message_type="notification"
        )


class PortalFeedbackAction(models.Model):
    _name = "portal.feedback.action"
    _description = "Portal Feedback Action"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "feedback_id, priority desc, due_date"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Action Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ACTION TRACKING
    # ============================================================================
    feedback_id = fields.Many2one(
        "portal.feedback",
        string="Feedback",
        required=True,
        ondelete="cascade",
        index=True,
    )
    description = fields.Text(string="Action Description")
    action_type = fields.Selection(
        [
            ("training", "Training"),
            ("process_improvement", "Process Improvement"),
            ("system_enhancement", "System Enhancement"),
            ("policy_update", "Policy Update"),
            ("communication", "Communication"),
            ("follow_up", "Follow-up"),
        ],
        string="Action Type",
        required=True,
        tracking=True,
    )
    assigned_to = fields.Many2one(
        "res.users", string="Assigned To", required=True, tracking=True
    )
    due_date = fields.Date(string="Due Date", required=True, tracking=True)
    priority = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="medium",
        tracking=True,
    )
    status = fields.Selection(
        [
            ("not_started", "Not Started"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="not_started",
        tracking=True,
    )
    completion_date = fields.Date(string="Completion Date", tracking=True)
    completion_notes = fields.Text(string="Completion Notes")

    # ============================================================================
    # TIME TRACKING
    # ============================================================================
    estimated_hours = fields.Float(string="Estimated Hours", digits=(8, 2))
    actual_hours = fields.Float(string="Actual Hours", digits=(8, 2))

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    is_overdue = fields.Boolean(
        string="Is Overdue",
        compute="_compute_is_overdue",
        help="True if action is past due date and not completed",
    )
    days_remaining = fields.Integer(
        string="Days Remaining",
        compute="_compute_days_remaining",
        help="Days remaining until due date",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("due_date", "status")
    def _compute_is_overdue(self):
        """Check if action is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                record.due_date
                and record.due_date < today
                and record.status not in ["completed", "cancelled"]
            )

    @api.depends("due_date")
    def _compute_days_remaining(self):
        """Calculate days remaining until due date"""
        today = fields.Date.today()
        for record in self:
            if record.due_date:
                delta = record.due_date - today
                record.days_remaining = delta.days
            else:
                record.days_remaining = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start(self):
        """Start working on the action"""
        self.ensure_one()
        if self.status != "not_started":
            raise UserError(_("Can only start actions that haven't been started yet."))

        self.write({"status": "in_progress"})
        self.message_post(
            body=_("Action has been started."), message_type="notification"
        )

    def action_complete(self):
        """Mark action as completed"""
        self.ensure_one()
        if self.status == "completed":
            raise UserError(_("Action is already completed."))

        self.write({"status": "completed", "completion_date": fields.Date.today()})
        self.message_post(
            body=_("Action has been completed."), message_type="notification"
        )

    def action_cancel(self):
        """Cancel the action"""
        self.ensure_one()
        if self.status == "completed":
            raise UserError(_("Cannot cancel a completed action."))

        self.write({"status": "cancelled"})
        self.message_post(
            body=_("Action has been cancelled."), message_type="notification"
        )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("estimated_hours", "actual_hours")
    def _check_hours(self):
        """Validate hour fields"""
        for record in self:
            if record.estimated_hours < 0:
                raise ValidationError(_("Estimated hours cannot be negative."))
            if record.actual_hours < 0:
                raise ValidationError(_("Actual hours cannot be negative."))

    @api.constrains("due_date")
    def _check_due_date(self):
        """Validate due date is not in the past for new actions"""
        for record in self:
            if (
                record.due_date
                and record.due_date < fields.Date.today()
                and record.status == "not_started"
            ):
                raise ValidationError(
                    _("Due date cannot be in the past for new actions.")
                )


class PortalFeedbackCommunication(models.Model):
    _name = "portal.feedback.communication"
    _description = "Portal Feedback Communication"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "feedback_id, communication_date desc"
    _rec_name = "subject"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    subject = fields.Char(string="Subject", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # COMMUNICATION TRACKING
    # ============================================================================
    feedback_id = fields.Many2one(
        "portal.feedback",
        string="Feedback",
        required=True,
        ondelete="cascade",
        index=True,
    )
    communication_date = fields.Datetime(
        string="Communication Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    communication_type = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone Call"),
            ("portal_message", "Portal Message"),
            ("in_person", "In Person"),
            ("video_call", "Video Call"),
            ("chat", "Live Chat"),
        ],
        string="Communication Type",
        required=True,
        tracking=True,
    )
    direction = fields.Selection(
        [
            ("inbound", "Inbound (from Customer)"),
            ("outbound", "Outbound (to Customer)"),
        ],
        string="Direction",
        required=True,
        tracking=True,
    )
    message = fields.Text(string="Message Content", required=True)
    sender = fields.Many2one("res.users", string="Sender")
    recipient = fields.Many2one("res.partner", string="Recipient")
    channel = fields.Char(string="Communication Channel")

    # ============================================================================
    # RESPONSE TRACKING
    # ============================================================================
    response_required = fields.Boolean(
        string="Response Required", default=False, tracking=True
    )
    response_deadline = fields.Datetime(string="Response Deadline")

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_responded(self):
        """Mark communication as responded"""
        self.ensure_one()
        self.write({"response_required": False})
        self.message_post(
            body=_("Communication has been responded to."), message_type="notification"
        )

    def action_send_followup(self):
        """Send a follow-up communication"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Send Follow-up"),
            "res_model": "communication.followup.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_original_communication_id": self.id},
        }


class PortalFeedbackAnalytics(models.Model):
    _name = "portal.feedback.analytics"
    _description = "Portal Feedback Analytics"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "period_start desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Analytics Period", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # PERIOD DEFINITION
    # ============================================================================
    period_start = fields.Date(string="Period Start", required=True)
    period_end = fields.Date(string="Period End", required=True)

    # ============================================================================
    # COMPUTED ANALYTICS FIELDS
    # ============================================================================
    total_feedback_count = fields.Integer(
        string="Total Feedback", compute="_compute_analytics", store=True
    )
    positive_feedback_count = fields.Integer(
        string="Positive Feedback", compute="_compute_analytics", store=True
    )
    negative_feedback_count = fields.Integer(
        string="Negative Feedback", compute="_compute_analytics", store=True
    )
    average_rating = fields.Float(
        string="Average Rating", digits=(3, 2), compute="_compute_analytics", store=True
    )
    average_response_time = fields.Float(
        string="Avg Response Time (Hours)",
        digits=(8, 2),
        compute="_compute_analytics",
        store=True,
    )
    average_resolution_time = fields.Float(
        string="Avg Resolution Time (Hours)",
        digits=(8, 2),
        compute="_compute_analytics",
        store=True,
    )
    sla_compliance_rate = fields.Float(
        string="SLA Compliance Rate (%)",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    nps_score = fields.Float(
        string="Net Promoter Score",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    customer_satisfaction_index = fields.Float(
        string="Customer Satisfaction Index",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    escalation_rate = fields.Float(
        string="Escalation Rate (%)",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    repeat_feedback_rate = fields.Float(
        string="Repeat Feedback Rate (%)",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
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
    @api.depends("period_start", "period_end")
    def _compute_analytics(self):
        """Compute analytics for the specified period"""
        for record in self:
            if not record.period_start or not record.period_end:
                record._reset_analytics()
                continue

            # Get feedback in the period
            domain = [
                ("date_created", ">=", record.period_start),
                ("date_created", "<=", record.period_end),
            ]
            feedback_records = self.env["portal.feedback"].search(domain)

            if feedback_records:
                record.total_feedback_count = len(feedback_records)

                # Sentiment analysis
                positive_feedback = feedback_records.filtered(
                    lambda f: f.sentiment in ["positive", "very_positive"]
                )
                negative_feedback = feedback_records.filtered(
                    lambda f: f.sentiment in ["negative", "very_negative"]
                )
                record.positive_feedback_count = len(positive_feedback)
                record.negative_feedback_count = len(negative_feedback)

                # Average rating
                rated_feedback = feedback_records.filtered(lambda f: f.overall_rating)
                if rated_feedback:
                    ratings = [int(f.overall_rating) for f in rated_feedback]
                    record.average_rating = sum(ratings) / len(ratings)
                else:
                    record.average_rating = 0.0

                # Response and resolution times
                responded_feedback = feedback_records.filtered(
                    lambda f: f.response_time_hours and f.response_time_hours > 0
                )
                if responded_feedback:
                    record.average_response_time = sum(
                        responded_feedback.mapped("response_time_hours")
                    ) / len(responded_feedback)
                else:
                    record.average_response_time = 0.0

                resolved_feedback = feedback_records.filtered(
                    lambda f: f.resolution_time_hours and f.resolution_time_hours > 0
                )
                if resolved_feedback:
                    record.average_resolution_time = sum(
                        resolved_feedback.mapped("resolution_time_hours")
                    ) / len(resolved_feedback)
                else:
                    record.average_resolution_time = 0.0

                # SLA compliance
                sla_applicable = feedback_records.filtered(lambda f: f.sla_deadline)
                if sla_applicable:
                    sla_met_count = len(sla_applicable.filtered(lambda f: f.sla_met))
                    record.sla_compliance_rate = (
                        sla_met_count / len(sla_applicable)
                    ) * 100
                else:
                    record.sla_compliance_rate = 0.0

                # NPS calculation
                nps_feedback = feedback_records.filtered(lambda f: f.nps_score)
                if nps_feedback:
                    promoters = len(
                        nps_feedback.filtered(lambda f: f.nps_category == "promoter")
                    )
                    detractors = len(
                        nps_feedback.filtered(lambda f: f.nps_category == "detractor")
                    )
                    record.nps_score = (
                        (promoters - detractors) / len(nps_feedback)
                    ) * 100
                else:
                    record.nps_score = 0.0

                # Customer Satisfaction Index (based on multiple factors)
                satisfaction_factors = []
                if record.average_rating > 0:
                    satisfaction_factors.append((record.average_rating / 5) * 100)
                if record.sla_compliance_rate > 0:
                    satisfaction_factors.append(record.sla_compliance_rate)
                if satisfaction_factors:
                    record.customer_satisfaction_index = sum(
                        satisfaction_factors
                    ) / len(satisfaction_factors)
                else:
                    record.customer_satisfaction_index = 0.0

                # Escalation rate
                escalated_feedback = feedback_records.filtered(lambda f: f.escalated)
                record.escalation_rate = (
                    len(escalated_feedback) / len(feedback_records)
                ) * 100

                # Repeat feedback rate (customers with multiple feedback)
                unique_customers = feedback_records.mapped("customer_id")
                if unique_customers:
                    repeat_customers = []
                    for customer in unique_customers:
                        customer_feedback_count = len(
                            feedback_records.filtered(
                                lambda f: f.customer_id == customer
                            )
                        )
                        if customer_feedback_count > 1:
                            repeat_customers.append(customer)

                    record.repeat_feedback_rate = (
                        len(repeat_customers) / len(unique_customers)
                    ) * 100
                else:
                    record.repeat_feedback_rate = 0.0
            else:
                record._reset_analytics()

    def _reset_analytics(self):
        """Reset all analytics metrics to zero"""
        self.total_feedback_count = 0
        self.positive_feedback_count = 0
        self.negative_feedback_count = 0
        self.average_rating = 0.0
        self.average_response_time = 0.0
        self.average_resolution_time = 0.0
        self.sla_compliance_rate = 0.0
        self.nps_score = 0.0
        self.customer_satisfaction_index = 0.0
        self.escalation_rate = 0.0
        self.repeat_feedback_rate = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_refresh_analytics(self):
        """Manually refresh analytics data"""
        self._compute_analytics()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _("Analytics refreshed successfully"),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_period_feedback(self):
        """View feedback records for this analytics period"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Period Feedback"),
            "res_model": "portal.feedback",
            "view_mode": "tree,form",
            "domain": [
                ("date_created", ">=", self.period_start),
                ("date_created", "<=", self.period_end),
            ],
            "target": "current",
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("period_start", "period_end")
    def _check_period_dates(self):
        """Validate period dates"""
        for record in self:
            if record.period_start and record.period_end:
                if record.period_start >= record.period_end:
                    raise ValidationError(
                        _("Period start date must be before end date.")
                    )
