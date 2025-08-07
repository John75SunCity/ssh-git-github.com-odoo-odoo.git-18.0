# -*- coding: utf-8 -*-
# Supporting Models for Portal Feedback System

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PortalFeedbackResolution(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    """Resolution tracking for portal feedback"""

    _name = "portal.feedback.resolution"
    _description = "Portal Feedback Resolution"
    _order = "feedback_id, resolution_date desc"
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    ),
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True),
    feedback_id = fields.Many2one(
        "portal.feedback", string="Feedback", required=True, ondelete="cascade"
    )
    resolution_date = fields.Datetime(
        string="Resolution Date", required=True, default=fields.Datetime.now
    ),
    resolved_by = fields.Many2one(
        "res.users",
        string="Resolved By",
        required=True,
        default=lambda self: self.env.user,
    )
    resolution_type = fields.Selection(
        [
            ("immediate", "Immediate Resolution"),
            ("process_change", "Process Change Required"),
            ("escalation", "Escalated to Higher Level"),
            ("training", "Training Required"),
            ("system_fix", "System Fix Required"),
            ("no_action", "No Action Required"),
        ]),
        string="Resolution Type",
        required=True,
    resolution_description = fields.Text(string="Resolution Description", required=True),
    customer_notified = fields.Boolean(string="Customer Notified", default=False)
    satisfaction_after_resolution = fields.Selection(
        [
            ("1", "Very Dissatisfied"),
            ("2", "Dissatisfied"),
            ("3", "Neutral"),
            ("4", "Satisfied"),
            ("5", "Very Satisfied"),
        ]),
        string="Satisfaction After Resolution",
    )
    cost_of_resolution = fields.Monetary(
        string="Cost of Resolution", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

class PortalFeedbackEscalation(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    """Escalation tracking for portal feedback"""

    _name = "portal.feedback.escalation"
    _description = "Portal Feedback Escalation"
    _order = "feedback_id, escalation_date desc"

    )

    feedback_id = fields.Many2one(
        "portal.feedback", string="Feedback", required=True, ondelete="cascade")
    escalation_date = fields.Datetime(
        string="Escalation Date", required=True, default=fields.Datetime.now
    )
    )
    escalated_by = fields.Many2one(
        "res.users",
        string="Escalated By",
        required=True,
        default=lambda self: self.env.user,)
    escalated_to = fields.Many2one("res.users", string="Escalated To", required=True),
    escalation_reason = fields.Text(string="Escalation Reason", required=True)
    escalation_level = fields.Selection(
        [
            ("level_1", "Level 1 - Supervisor"),
            ("level_2", "Level 2 - Manager"),
            ("level_3", "Level 3 - Director"),
            ("level_4", "Level 4 - Executive"),
        ]),
        string="Escalation Level",
        required=True,
    )
    urgency = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ]),
        string="Urgency",
        default="medium",
    deadline = fields.Datetime(string="Response Deadline"),
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("acknowledged", "Acknowledged"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
        ]),
        string="Status",
        default="pending",
    )

class PortalFeedbackAction(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    """Action items generated from portal feedback"""

    _name = "portal.feedback.action"
    _description = "Portal Feedback Action"
    _order = "feedback_id, priority desc, due_date"

    )

    feedback_id = fields.Many2one(
        "portal.feedback", string="Feedback", required=True, ondelete="cascade")
    name = fields.Char(string="Action Name", required=True),
    description = fields.Text(string="Action Description")
    action_type = fields.Selection(
        [
            ("training", "Training"),
            ("process_improvement", "Process Improvement"),
            ("system_enhancement", "System Enhancement"),
            ("policy_update", "Policy Update"),
            ("communication", "Communication"),
            ("follow_up", "Follow-up"),
        ]),
        string="Action Type",
        required=True,
    )
    assigned_to = fields.Many2one("res.users", string="Assigned To", required=True),
    due_date = fields.Date(string="Due Date", required=True)
    priority = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="medium",
    )
    status = fields.Selection(
        [
            ("not_started", "Not Started"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ]),
        string="Status",
        default="not_started",
    completion_date = fields.Date(string="Completion Date"),
    completion_notes = fields.Text(string="Completion Notes")
    estimated_hours = fields.Float(string="Estimated Hours", digits=(8, 2)
    actual_hours = fields.Float(string="Actual Hours", digits=(8, 2)
class PortalFeedbackCommunication(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    """Communication log for portal feedback"""

    _name = "portal.feedback.communication"
    _description = "Portal Feedback Communication"
    _order = "feedback_id, communication_date desc"
)
    feedback_id = fields.Many2one(
        "portal.feedback", string="Feedback", required=True, ondelete="cascade"
    ),
    communication_date = fields.Datetime(
        string="Communication Date", required=True, default=fields.Datetime.now
    )
    communication_type = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone Call"),
            ("portal_message", "Portal Message"),
            ("in_person", "In Person"),
            ("video_call", "Video Call"),
            ("chat", "Live Chat"),
        ]),
        string="Communication Type",
        required=True,
    )
    direction = fields.Selection(
        [
            ("inbound", "Inbound (from Customer)"),
            ("outbound", "Outbound (to Customer)"),
        ]),
        string="Direction",
        required=True,
    subject = fields.Char(string="Subject"),
    message = fields.Text(string="Message Content", required=True)
    sender = fields.Many2one("res.users", string="Sender"),
    recipient = fields.Many2one("res.partner", string="Recipient")
    channel = fields.Char(string="Communication Channel"),
    response_required = fields.Boolean(string="Response Required", default=False)
    response_deadline = fields.Datetime(string="Response Deadline")

class PortalFeedbackAnalytics(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    """Analytics data for portal feedback"""

    _name = "portal.feedback.analytics"
    _description = "Portal Feedback Analytics"
    _order = "period_start desc"

    name = fields.Char(string="Analytics Period", required=True),
    period_start = fields.Date(string="Period Start", required=True)
    period_end = fields.Date(string="Period End", required=True),
    total_feedback_count = fields.Integer(
        string="Total Feedback", compute="_compute_analytics"
    )
    positive_feedback_count = fields.Integer(
        string="Positive Feedback", compute="_compute_analytics")
    negative_feedback_count = fields.Integer(
        string="Negative Feedback", compute="_compute_analytics"
    ),
    average_rating = fields.Float(
        string="Average Rating", digits=(3, 2), compute="_compute_analytics")
    average_response_time = fields.Float(
        string="Avg Response Time (Hours)", digits=(8, 2), compute="_compute_analytics"
    )
    average_resolution_time = fields.Float(
        string="Avg Resolution Time (Hours)",
        digits=(8, 2),
        compute="_compute_analytics",)
    sla_compliance_rate = fields.Float(
        string="SLA Compliance Rate (%)", digits=(5, 2), compute="_compute_analytics"
    )
    nps_score = fields.Float(
        string="Net Promoter Score", digits=(5, 2), compute="_compute_analytics")
    customer_satisfaction_index = fields.Float(
        string="Customer Satisfaction Index",
        digits=(5, 2),
        compute="_compute_analytics",
    )
    escalation_rate = fields.Float(
        string="Escalation Rate (%)", digits=(5, 2), compute="_compute_analytics")
    repeat_feedback_rate = fields.Float(
        string="Repeat Feedback Rate (%)", digits=(5, 2), compute="_compute_analytics"
    )

    @api.depends("period_start", "period_end")
    def _compute_analytics(self):
        """Compute analytics for the specified period"""
        for record in self:
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
                    lambda f: f.response_time_hours > 0
                )
                if responded_feedback:
                    record.average_response_time = sum(
                        responded_feedback.mapped("response_time_hours")
                    ) / len(responded_feedback)
                else:
                    record.average_response_time = 0.0

                resolved_feedback = feedback_records.filtered(
                    lambda f: f.resolution_time_hours > 0
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
                    sla_met_count = len(sla_applicable.filtered(lambda f: f.sla_met)
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
                if len(satisfaction_factors) > 0:
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
                repeat_customers = []
                for customer in unique_customers:
                    customer_feedback_count = len(
                        feedback_records.filtered(lambda f: f.customer_id == customer)
                    )
                    if customer_feedback_count > 1:
                        repeat_customers.append(customer)

                record.repeat_feedback_rate = (
                    (len(repeat_customers) / len(unique_customers)) * 100
                    if unique_customers
                    else 0.0
                )
            else:
                # Reset all metrics if no feedback found
                record.total_feedback_count = 0
                record.positive_feedback_count = 0
                record.negative_feedback_count = 0
                record.average_rating = 0.0
                record.average_response_time = 0.0
                record.average_resolution_time = 0.0
                record.sla_compliance_rate = 0.0
                record.nps_score = 0.0
                record.customer_satisfaction_index = 0.0
                record.escalation_rate = 0.0
                record.repeat_feedback_rate = 0.0)
