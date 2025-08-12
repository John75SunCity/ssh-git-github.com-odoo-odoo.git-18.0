# -*- coding: utf-8 -*-
"""
Portal Feedback Communication Model
"""
from odoo import _, api, fields, models


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
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="feedback_id.partner_id",
        store=True,
        help="Associated partner for this record",
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
    sender_id = fields.Many2one("res.users", string="Sender")
    recipient_id = fields.Many2one("res.partner", string="Recipient")
    channel = fields.Char(string="Communication Channel")

    # ============================================================================
    # RESPONSE TRACKING
    # ============================================================================
    response_required = fields.Boolean(
        string="Response Required", default=False, tracking=True
    )
    response_deadline = fields.Datetime(string="Response Deadline")

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
