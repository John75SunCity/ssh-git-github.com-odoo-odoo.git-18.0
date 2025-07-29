# -*- coding: utf-8 -*-
"""
Portal Request Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PortalRequest(models.Model):
    """
    Portal Request Management
    Customer requests submitted through the portal
    """

    _name = "portal.request"
    _description = "Portal Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(
        string="Request Number",
        required=True,
        tracking=True,
        default=lambda self: _("New"),
        copy=False,
    )
    description = fields.Text(string="Request Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
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

    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )
    contact_person = fields.Many2one(
        "res.partner",
        string="Requesting Contact",
        domain=[("is_company", "=", False)],
        tracking=True,
    )

    # ==========================================
    # REQUEST DETAILS
    # ==========================================
    request_date = fields.Date(
        string="Request Date", default=fields.Date.today, required=True, tracking=True
    )
    request_type = fields.Selection(
        [
            ("pickup", "Pickup Request"),
            ("destruction", "Destruction Request"),
            ("retrieval", "Document Retrieval"),
            ("new_service", "New Service Request"),
            ("billing_inquiry", "Billing Inquiry"),
            ("general", "General Request"),
        ],
        string="Request Type",
        required=True,
        tracking=True,
    )

    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="normal",
        tracking=True,
    )

    # ==========================================
    # STATUS AND WORKFLOW
    # ==========================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("acknowledged", "Acknowledged"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
    )

    # ==========================================
    # SERVICE DETAILS
    # ==========================================
    requested_service_date = fields.Date(string="Requested Service Date", tracking=True)
    estimated_completion_date = fields.Date(
        string="Estimated Completion", tracking=True
    )
    actual_completion_date = fields.Date(string="Actual Completion", tracking=True)

    # For destruction requests
    container_count = fields.Integer(string="Number of Containers", tracking=True)
    witness_required = fields.Boolean(string="Witness Required", tracking=True)

    # ==========================================
    # RESPONSE TRACKING
    # ==========================================
    acknowledged_date = fields.Date(string="Acknowledged Date", tracking=True)
    acknowledged_by = fields.Many2one(
        "res.users", string="Acknowledged By", tracking=True
    )

    response_notes = fields.Text(string="Response Notes", tracking=True)
    completion_notes = fields.Text(string="Completion Notes", tracking=True)

    # ==========================================
    # ATTACHMENTS AND DOCUMENTS
    # ==========================================
    attachment_count = fields.Integer(
        string="Attachments", compute="_compute_attachment_count"
    )

    # ==========================================
    # RELATED RECORDS
    # ==========================================
    container_id = fields.Many2one(
        "records.container", string="Related Records Container", tracking=True
    )
    shredding_service_id = fields.Many2one(
        "shred.svc", string="Related Shredding Service", tracking=True
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends()
    def _compute_attachment_count(self):
        """Count attachments"""
        for record in self:
            attachments = self.env["ir.attachment"].search(
                [("res_model", "=", self._name), ("res_id", "=", record.id)]
            )
            record.attachment_count = len(attachments)

    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_submit(self):
        """Submit the request"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft requests can be submitted"))

        self.write({"state": "submitted"})
        self.message_post(body=_("Request submitted"))

        # Create activity for staff to acknowledge
        self.activity_schedule(
            "mail.mail_activity_data_call",
            summary="New Portal Request",
            note=f"New {self.request_type} request from {self.customer_id.name}",
            user_id=self.user_id.id,
        )

    def action_acknowledge(self):
        """Acknowledge the request"""
        self.ensure_one()
        if self.state != "submitted":
            raise UserError(_("Only submitted requests can be acknowledged"))

        self.write(
            {
                "state": "acknowledged",
                "acknowledged_date": fields.Date.today(),
                "acknowledged_by": self.env.user.id,
            }
        )
        self.message_post(body=_("Request acknowledged"))

    def action_start_progress(self):
        """Start working on the request"""
        self.ensure_one()
        if self.state != "acknowledged":
            raise UserError(_("Only acknowledged requests can be started"))

        self.write({"state": "in_progress"})
        self.message_post(body=_("Started working on request"))

    def action_complete(self):
        """Complete the request"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress requests can be completed"))

        self.write(
            {"state": "completed", "actual_completion_date": fields.Date.today()}
        )
        self.message_post(body=_("Request completed"))

    def action_cancel(self):
        """Cancel the request"""
        self.ensure_one()
        if self.state in ["completed", "cancelled"]:
            raise UserError(_("Cannot cancel completed or already cancelled requests"))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Request cancelled"))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "portal.request"
                ) or _("New")
        return super().create(vals_list)
