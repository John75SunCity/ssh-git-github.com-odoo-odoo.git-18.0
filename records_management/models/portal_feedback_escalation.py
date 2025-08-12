# -*- coding: utf-8 -*-
"""
Portal Feedback Escalation Model
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="feedback_id.partner_id",
        store=True,
        help="Associated partner for this record",
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
    escalated_by_id = fields.Many2one(
        "res.users",
        string="Escalated By",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    escalated_to_id = fields.Many2one(
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
