# -*- coding: utf-8 -*-
"""
Approval History Module

This module manages the complete approval workflow history for the Records
Management System, providing comprehensive tracking of budget, expense,
invoice, and payment approvals with detailed audit trails and performance metrics.

Key Features:
- Complete approval workflow management with state tracking
- Performance analytics with response time calculations
- Multi-type approval support (budget, expense, invoice, payment)
- Integration with Records Department Billing Contacts
- Automated notification system with mail thread integration
- Comprehensive audit trails with user tracking

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _

from odoo.exceptions import UserError




class ApprovalHistory(models.Model):
    """
    Approval History Model

    Manages comprehensive approval workflow history for the Records Management System
    with detailed tracking of approval types, status, performance metrics, and audit trails.
    """

    _name = "approval.history"
    _description = "Approval History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "approval_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for approval history record",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        help="Company context for approval",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who requested the approval",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this approval history record is active"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    contact_id = fields.Many2one(
        "records.department.billing.contact",
        string="Billing Contact",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="Associated billing contact for this approval"
    )

    # ============================================================================
    # APPROVAL WORKFLOW FIELDS
    # ============================================================================
    approval_date = fields.Datetime(
        string="Approval Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time when approval was processed"
    )

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
        help="Type of approval being requested"
    )

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
        help="Current status of the approval request"
    )

    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True,
        help="User who processed the approval"
    )

    # ============================================================================
    # FINANCIAL FIELDS
    # ============================================================================
    approval_amount = fields.Monetary(
        string="Approval Amount",
        currency_field="currency_id",
        tracking=True,
        help="Monetary amount requiring approval"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
        help="Currency for the approval amount"
    )

    # ============================================================================
    # PERFORMANCE TRACKING FIELDS
    # ============================================================================
    response_time_hours = fields.Float(
        string="Response Time (Hours)",
        compute="_compute_response_time",
        store=True,
        help="Time taken to respond to the approval request"
    )

    request_date = fields.Datetime(
        string="Request Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time when approval was requested"
    )

    completed_date = fields.Datetime(
        string="Completed Date",
        tracking=True,
        help="Date and time when approval was completed"
    )

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    description = fields.Text(
        string="Description",
        tracking=True,
        help="Detailed description of the approval request",
    )
    approval_notes = fields.Text(
        string="Approval Notes",
        tracking=True,
        help="Additional notes from the approver",
    )
    reference_document = fields.Char(
        string="Reference Document",
        tracking=True,
        help="Reference to related document or transaction",
    )
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
        help="Priority level of the approval request"
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[("res_model", "=", "approval.history")],
        help="Related activities for this approval",
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=[("res_model", "=", "approval.history")],
        help="Users following this approval",
    )
    message_ids = fields.One2many(

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        "mail.message",
        "res_id",
        string="Messages",
        domain=[("model", "=", "approval.history")],
        help="Communication history for this approval",
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends("request_date", "completed_date")
    def _compute_response_time(self):
        """Compute response time in hours"""
        for record in self:
            if record.request_date and record.completed_date:
                delta = record.completed_date - record.request_date
                record.response_time_hours = delta.total_seconds() / 3600
            else:
                record.response_time_hours = 0.0

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name"""
        for vals in vals_list:
            if not vals.get("name"):
                approval_type = vals.get("approval_type", "other")
                sequence = self.env["ir.sequence"].next_by_code("approval.history")
                if not sequence:
                    # Raise error or provide a descriptive fallback
                    raise ValueError(
                        "Sequence code 'approval.history' does not exist. Please configure the sequence in Odoo."
                    )
                vals["name"] = "%s-%s" % (approval_type.upper(), sequence)
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve(self):
        """Approve the request"""

        self.ensure_one()
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be approved."))

        self.write(
            {
                "approval_status": "approved",
                "approved_by_id": self.env.user.id,
                "completed_date": fields.Datetime.now(),
            }
        )
        self.message_post(
            body=_("Approval request approved by %s", self.env.user.name),
            message_type="notification",
        )

    def action_reject(self):
        """Reject the request"""

        self.ensure_one()
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be rejected."))

        self.write(
            {
                "approval_status": "rejected",
                "approved_by_id": self.env.user.id,
                "completed_date": fields.Datetime.now(),
            }
        )
        self.message_post(
            body=_("Approval request rejected by %s", self.env.user.name),
            message_type="notification",
        )

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
        )

        self.message_post(
            body=_("Approval request cancelled by %s", self.env.user.name),
            message_type="notification",
        )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name_parts = [record.name]
            if record.approval_type:
                type_label = dict(record._fields["approval_type"].selection).get(
                    record.approval_type, record.approval_type
                )
                name_parts.append("(%s)" % type_label)
            if record.approval_amount:
                name_parts.append("- %s%s" % (
                    record.currency_id.symbol,
                    "{:.2f}".format(record.approval_amount)
                ))

            result.append((record.id, " ".join(name_parts)))
        return result

    def get_approval_statistics(self):
        """Get approval statistics for dashboard"""
        stats = {}
        for status in ["pending", "approved", "rejected", "cancelled"]:
            stats[status] = self.search_count([("approval_status", "=", status)])

        # Average response time for completed approvals
        completed_approvals = self.search([
            ("approval_status", "in", ["approved", "rejected"]),
            ("response_time_hours", ">", 0)
        ])

        if completed_approvals:
            avg_response_time = sum(completed_approvals.mapped("response_time_hours")) / len(completed_approvals)
            stats["avg_response_time_hours"] = round(avg_response_time, 2)
        else:
            stats["avg_response_time_hours"] = 0.0

        return stats
