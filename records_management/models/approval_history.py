# -*- coding: utf-8 -*-
"""
Approval History
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ApprovalHistory(models.Model):
    """
    Approval History Model
    """

    _name = "approval.history"
    _description = "Approval History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "approval_date desc"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Relationship field
    contact_id = fields.Many2one(
        "records.department.billing.contact",
        string="Billing Contact",
        required=True,
        ondelete="cascade",
        tracking=True,
    

    # Approval Details
    approval_date = fields.Datetime(
        string="Approval Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    
    approval_type = fields.Selection(
        [
            ("budget", "Budget Approval"),
            ("expense", "Expense Approval"),
            ("invoice", "Invoice Approval"),
            ("payment", "Payment Approval"),
            ("other", "Other"),
        ],
        string="Approval Type",
        required=True,
        default="expense",
        tracking=True,
    
    approval_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="pending",
        tracking=True,
    
    approved_by = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True,
    
    approval_amount = fields.Monetary(
        string="Approval Amount",
        currency_field="currency_id",
        tracking=True,
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    

    # Performance Tracking
    response_time_hours = fields.Float(
        string="Response Time (Hours)",
        compute="_compute_response_time",
        store=True,
        help="Time taken to respond to the approval request",
    
    request_date = fields.Datetime(
        string="Request Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    
    completed_date = fields.Datetime(
        string="Completed Date",
        tracking=True,
    

    # Additional Information
    description = fields.Text(string="Description", tracking=True)
    approval_notes = fields.Text(string="Approval Notes", tracking=True)
    reference_document = fields.Char(string="Reference Document", tracking=True)
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="normal",
        tracking=True,
    

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    @api.depends("request_date", "completed_date")
    def _compute_response_time(self):
        """Compute response time in hours"""
        for record in self:
            if record.request_date and record.completed_date:
                delta = record.completed_date - record.request_date
                record.response_time_hours = delta.total_seconds() / 3600
            else:
                pass
            pass
                record.response_time_hours = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name"""
        for vals in vals_list:
            if not vals.get("name"):
                approval_type = vals.get("approval_type", "other")
                sequence = (
                    self.env["ir.sequence"].next_by_code("approval.history") or "/"
                
                vals["name"] = _("%s-%s"
        return super().create(vals_list)

    def action_approve(self):
        """Approve the request"""
        self.ensure_one()
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be approved."))

        self.write(
            {
                "approval_status": "approved",
                "approved_by": self.env.user.id,
                "completed_date": fields.Datetime.now(),
            }
        

        self.message_post(body=_("Action completed"))
            body=_("Approval request approved by %s", self.env.user.name),
            message_type="notification",
        

    def action_reject(self):
        """Reject the request"""
        self.ensure_one()
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be rejected."))

        self.write(
            {
                "approval_status": "rejected",
                "approved_by": self.env.user.id,
                "completed_date": fields.Datetime.now(),
            }
        

        self.message_post(body=_("Action completed"))
            body=_("Approval request rejected by %s", self.env.user.name),
            message_type="notification",
        

    def action_cancel(self):
        """Cancel the request"""
        self.ensure_one()
        if self.approval_status in ["approved", "rejected"]:
            raise UserError(_("Cannot cancel completed approvals."))

        self.write(
            {
                "approval_status": "cancelled",
                "completed_date": fields.Datetime.now(),
            }
        

        self.message_post(body=_("Action completed"))
            body=_("Approval request cancelled"),
            message_type="notification",
        
