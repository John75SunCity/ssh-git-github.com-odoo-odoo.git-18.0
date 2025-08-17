# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    Approval History Module
    This module manages the complete approval workflow history for the Records:
    pass
Management System, providing comprehensive tracking of budget, expense,
invoice, and payment approvals with detailed audit trails and performance metrics.
    Key Features
- Complete approval workflow management with state tracking
- Performance analytics with response time calculations
- Multi-type approval support (budget, expense, invoice, payment)
- Integration with Records Department Billing Contacts
- Automated notification system with mail thread integration
- Comprehensive audit trails with user tracking
    Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
    from odoo import models, fields, api, _
from odoo.exceptions import UserError
    class ApprovalHistory(models.Model):

        Approval History Model

    Manages comprehensive approval workflow history for the Records Management System""":"
        with detailed tracking of approval types, status, performance metrics, and audit trails.""
    ""
    _name = "approval.history"
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "approval.history"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "approval.history"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Approval History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "approval_date desc"
    _rec_name = "name"
""
        # ============================================================================ """"
    # CORE IDENTIFICATION FIELDS"""""
        # ============================================================================ """"
    name = fields.Char("""""
        string="Name",
        required=True,""
        tracking=True,""
        index=True,""
        help="Unique identifier for approval history record":
    ""
    ""
    company_id = fields.Many2one(""
        "res.company",
        string="Company",
        default=lambda self: self.env.company,""
        required=True,""
        help="Company context for approval":
    ""
    ""
    user_id = fields.Many2one(""
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,""
        tracking=True,""
        help="User who requested the approval"
    ""
    ""
    active = fields.Boolean(""
        string="Active",
        default=True,""
        help="Whether this approval history record is active"
    ""
""
        # ============================================================================ """"
    # RELATIONSHIP FIELDS"""""
        # ============================================================================ """"
    contact_id = fields.Many2one("""""
        "records.department.billing.contact",
        string="Billing Contact",
        required=True,""
        ondelete="cascade",
        tracking=True,""
        help="Associated billing contact for this approval":
    ""
""
        # ============================================================================ """"
    # APPROVAL WORKFLOW FIELDS"""""
        # ============================================================================ """"
    approval_date = fields.Datetime("""""
        string="Approval Date",
        default=fields.Datetime.now,""
        required=True,""
        tracking=True,""
        help="Date and time when approval was processed"
    ""
""
    ,""
    approval_type = fields.Selection([))""
        ("budget", "Budget Approval"),
        ("expense", "Expense Approval"),
        ("invoice", "Invoice Approval"),
        ("payment", "Payment Approval"),
        ("other", "Other"),
    ""
        required=True,""
        default="expense",
        tracking=True,""
        help="Type of approval being requested"
""
    approval_status = fields.Selection([))""
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ""
        required=True,""
        default="pending",
        tracking=True,""
        help="Current status of the approval request"
""
    approved_by_id = fields.Many2one(""
        "res.users",
        string="Approved By",
        tracking=True,""
        help="User who processed the approval"
    ""
""
        # ============================================================================ """"
    # FINANCIAL FIELDS"""""
        # ============================================================================ """"
    approval_amount = fields.Monetary("""""
        string="Approval Amount",
        currency_field="currency_id",
        tracking=True,""
        help="Monetary amount requiring approval"
    ""
    ""
    currency_id = fields.Many2one(""
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,""
        required=True,""
        help="Currency for the approval amount":
    ""
""
        # ============================================================================ """"
    # PERFORMANCE TRACKING FIELDS"""""
        # ============================================================================ """"
    response_time_hours = fields.Float("""""
    string="Response Time (Hours)",
        compute="_compute_response_time",
        store=True,""
        help="Time taken to respond to the approval request"
    ""
""
    request_date = fields.Datetime(""
        string="Request Date",
        required=True,""
        default=fields.Datetime.now,""
        tracking=True,""
        help="Date and time when approval was requested"
    ""
""
    completed_date = fields.Datetime(""
        string="Completed Date",
        tracking=True,""
        help="Date and time when approval was completed"
    ""
""
        # ============================================================================ """"
    # DOCUMENTATION FIELDS"""""
        # ============================================================================ """"
    description = fields.Text("""""
        string="Description",
        tracking=True,""
        help="Detailed description of the approval request"
    ""
    ""
    approval_notes = fields.Text(""
        string="Approval Notes",
        tracking=True,""
        help="Additional notes from the approver"
    ""
    ""
    reference_document = fields.Char(""
        string="Reference Document",
        tracking=True,""
        help="Reference to related document or transaction"
    ""
    ""
    ,""
    priority = fields.Selection([))""
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ""
        default="normal",
        tracking=True,""
        help="Priority level of the approval request"
""
    # ============================================================================ """"
        # WORKFLOW STATE MANAGEMENT"""""
    # ============================================================================ """"
    state = fields.Selection([))"""""
        ('draft', 'Draft'),"
        ('active', 'Active'),"
        ('inactive', 'Inactive'),"
        ('archived', 'Archived'),"
    ""
        help='Current status of the record'"
""
    # ============================================================================ """"
        # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance):"""""
    # ============================================================================ """"
    activity_ids = fields.One2many("""""
        "mail.activity",
        "res_id",
        string="Activities",
        ,""
    domain=lambda self: [("res_model", "= """", self._name)),"
        help=""""Related activities for this approval":
    ""
    ""
    message_follower_ids = fields.One2many(""
        "mail.followers",
        "res_id",
        string="Followers",
        ,""
    domain=lambda self: [("res_model", "= """", self._name)),"
        help=""""Users following this approval"
    ""
    ""
    message_ids = fields.One2many(""
        "mail.message",
        "res_id",
        string="Messages",
        ,""
    domain=lambda self: [("model", "= """", self._name))"
    context = fields.Char(string='"""
"""        help="Communication history for this approval":"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        # ============================================================================""
    @api.depends("request_date", "completed_date")
    def _compute_response_time(self):""
        """Compute response time in hours"""
""""
""""
"""    def create(self, vals_list):"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
        """Override create to set default name"""
            if not vals.get("name"):
                approval_type = vals.get("approval_type", "other")
                sequence = self.env["ir.sequence").next_by_code("approval.history")
                if not sequence:""
                    # Provide a descriptive fallback""
                    sequence = "NEW"
                vals["name"] = _("%(type)s-%(seq)s", type=approval_type.upper(), seq=sequence)
        return super().create(vals_list)""
""
    def write(self, vals):""
        """Override write to track important changes"""
""""
"""
"""        if "approval_status" in vals:"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            for record in self:""
                status_display = dict(record._fields['approval_status'].selection).get(vals("approval_status")
                record.message_post()""
                    body=_("Approval status changed to %s", status_display)
                ""
        ""
        return result""
""
    # ============================================================================ """"
        # ACTION METHODS""""""
    # ============================================================================ """"
    def action_approve(self):""""""
        """Approve the request"""
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be approved"))
""
        self.write({)}""
            "approval_status": "approved",
            "approved_by_id": self.env.user.id,
            "completed_date": fields.Datetime.now(),
        ""
""
        self.message_post()""
            body=_("Approval request approved by %s", self.env.user.name),
            message_type="notification",
        ""
""
    def action_reject(self):""
        """Reject the request"""
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be rejected"))
""
        self.write({)}""
            "approval_status": "rejected",
            "approved_by_id": self.env.user.id,
            "completed_date": fields.Datetime.now(),
        ""
""
        self.message_post()""
            body=_("Approval request rejected by %s", self.env.user.name),
            message_type="notification",
        ""
""
    def action_cancel(self):""
        """Cancel the request"""
        if self.approval_status in ["approved", "rejected"]:
            raise UserError(_("Cannot cancel completed approvals"))
""
        self.write({)}""
            "approval_status": "cancelled",
            "completed_date": fields.Datetime.now(),
        ""
""
        self.message_post()""
            body=_("Approval request cancelled by %s", self.env.user.name),
            message_type="notification",
        ""
""
    def action_reset_to_pending(self):""
        """Reset approval to pending status"""
        if self.approval_status == "pending":
            raise UserError(_("Approval is already pending"))
""
        self.write({)}""
            "approval_status": "pending",
            "approved_by_id": False,
            "completed_date": False,
        ""
""
        self.message_post()""
            body=_("Approval reset to pending by %s", self.env.user.name),
            message_type="notification",
        ""
""
    def action_escalate(self):""
        """Escalate approval to higher authority"""
""""
""""
"""            body=_("Approval escalated to %s", manager.name),"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
            message_type="notification",
        ""
""
    # ============================================================================""
        # BUSINESS METHODS""
    # ============================================================================ """"
    def get_approval_summary(self):""""""
        """Get approval summary for reporting"""
    """"
""""
        """Get approval statistics for dashboard"""
""""
"""        for status in ["pending", "approved", "rejected", "cancelled"]:"
            stats[status] = self.search_count((("approval_status", "= """""
"""            (""""approval_status", "in", ("approved", "rejected"),""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            ("response_time_hours", ">", 0)
        ""
""
        if completed_approvals:""
            avg_response_time = sum(completed_approvals.mapped("response_time_hours")) / len(completed_approvals)
            stats["avg_response_time_hours"] = round(avg_response_time, 2)
        else:""
            stats["avg_response_time_hours"] = 0.0
""
        # Approval rate""
        total_completed = stats["approved"] + stats["rejected"]
        if total_completed > 0:""
            stats["approval_rate"] = round((stats["approved"] / total_completed) * 100, 2)
        else:""
            stats["approval_rate"] = 0.0
""
        return stats""
""
    @api.model""
    def get_performance_metrics(self, date_from=None, date_to=None):""
        """Get performance metrics for specified period"""
"""            domain.append(('request_date', '>= """
            domain.append(('"""request_date', '<= """
"""        completed = approvals.filtered(lambda r: r.approval_status in ('"""approved', 'rejected')""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
        return metrics""
    """"
        """Get statistics grouped by field"""
""""
""""
"""    def _send_approval_notification(self, notification_type):"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Send approval notification based on type"""
""""
""""
    """"
        """Notify users about pending approval"""
""""
""""
"""    def name_get(self):"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
        """Custom display name"""
""""
""""
"""                type_label = dict(record._fields["approval_type").selection).get(]"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                ""
                name_parts.append(_("(%s)", type_label))
            ""
            if record.approval_amount:""
                name_parts.append(_("- %s%s", 
                    record.currency_id.symbol or '',""
                    "{:.2f}".format(record.approval_amount)
                ""
""
            result.append((record.id, " ".join(name_parts)))
        return result""
""
    @api.model""
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Enhanced search by name, type, or reference"""
""""
""""
"""                "|", "|", "|","
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
                ("name", operator, name),
                ("approval_type", operator, name), 
                ("reference_document", operator, name),
                ("description", operator, name),
            ""
            args = domain + args""
        ""
        return super().name_search(name=name, args=args, operator=operator, limit=limit)""
""
    # ============================================================================""
        # VALIDATION METHODS""
    # ============================================================================""
    @api.constrains("request_date", "completed_date")
    def _check_dates(self):""
        """Validate date consistency"""
""""
""""
"""                    raise UserError(_("Completion date cannot be before request date"))"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""
    @api.constrains("approval_amount")
    def _check_approval_amount(self):""
        """Validate approval amount"""
"""                raise UserError(_("Approval amount cannot be negative"))"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
        """Generate comprehensive approval report"""
"""            domain.append(('request_date', '>= """
""""
            domain.append(('"""request_date', '<= """
            domain.append(('"""approval_type', 'in', approval_types))"
        ""
        approvals = self.search(domain, order='request_date desc')""
        ""
        return {}""
            'period': {'from': date_from, 'to': date_to},""
            'total_requests': len(approvals),""
            'summary': self.get_performance_metrics(date_from, date_to),""
            'approvals': [approval.get_approval_summary() for approval in approvals],:""
""""
    """"
""""
""""
"""
""""