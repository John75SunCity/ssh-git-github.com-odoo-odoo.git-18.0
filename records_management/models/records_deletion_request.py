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
    Records Deletion Request Module
    This module manages deletion requests for the Records Management System,:
    pass
providing comprehensive tracking of document and container deletion workflows
with full NAID AAA compliance and audit trails.
    Key Features
- Complete deletion request lifecycle management
- NAID compliance audit trails
- Integration with chain of custody tracking
- Customer portal integration for request submissions:
- Automated approval workflows with notifications
- Legal compliance documentation
    Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    class RecordsDeletionRequest(models.Model):

        Records Deletion Request

    Manages comprehensive deletion request workflows for documents and containers""":"
        with complete NAID compliance tracking and audit trail management.""
    ""
    _name = "records.deletion.request"
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "records.deletion.request"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.deletion.request"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Records Deletion Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, name"
    _rec_name = "name"
""
        # ============================================================================ """"
    # CORE IDENTIFICATION FIELDS"""""
        # ============================================================================ """"
    name = fields.Char("""""
        string="Request Reference",
        required=True,""
        tracking=True,""
        index=True,""
        help="Unique identifier for this deletion request":
    ""
""
    company_id = fields.Many2one(""
        "res.company",
        string="Company",
        default=lambda self: self.env.company,""
        required=True""
    ""
""
    user_id = fields.Many2one(""
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,""
        tracking=True,""
        help="User who created this deletion request"
    ""
""
    active = fields.Boolean(""
        string="Active",
        default=True,""
        help="Whether this deletion request is active"
    ""
""
        # ============================================================================ """"
    # REQUEST DETAILS"""""
        # ============================================================================ """"
    partner_id = fields.Many2one("""""
        "res.partner",
        string="Customer",
        required=True,""
        tracking=True,""
        help="Customer requesting the deletion"
    ""
""
    request_date = fields.Date(""
        string="Request Date",
        required=True,""
        default=fields.Date.today,""
        tracking=True,""
        index=True,""
        help="Date when the deletion was requested"
    ""
""
    scheduled_deletion_date = fields.Date(""
        string="Scheduled Deletion Date",
        tracking=True,""
        help="Planned date for executing the deletion":
    ""
""
    actual_deletion_date = fields.Date(""
        string="Actual Deletion Date",
        tracking=True,""
        help="Date when deletion was actually completed"
    ""
""
    ,""
    deletion_type = fields.Selection([))""
        ("document", "Document Deletion"),
        ("container", "Container Deletion"),
        ("bulk", "Bulk Deletion"),
        ("emergency", "Emergency Deletion"),
    ""
        required=True,""
        default="document",
        tracking=True,""
        help="Type of deletion being requested"
""
    priority = fields.Selection([))""
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ""
        default="normal",
        tracking=True,""
        help="Priority level of the deletion request"
""
    # ============================================================================ """"
        # DOCUMENTATION FIELDS"""""
    # ============================================================================ """"
    description = fields.Text("""""
        string="Description",
        required=True,""
        tracking=True,""
        help="Detailed description of items to be deleted"
    ""
""
    reason = fields.Text(""
        string="Deletion Reason",
        required=True,""
        tracking=True,""
        help="Business reason for the deletion request":
    ""
""
    notes = fields.Text(""
        string="Internal Notes",
        help="Internal notes and comments about the deletion"
    ""
""
    special_instructions = fields.Text(""
        string="Special Instructions",
        help="Any special handling instructions for the deletion":
    ""
""
        # ============================================================================ """"
    # WORKFLOW STATE MANAGEMENT"""""
        # ============================================================================ """"
    ,"""""
    state = fields.Selection([))""
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ""
        default="draft",
        tracking=True,""
        required=True,""
        index=True,""
        help="Current status of the deletion request"
""
    # ============================================================================ """"
        # APPROVAL WORKFLOW FIELDS"""""
    # ============================================================================ """"
    approved_by_id = fields.Many2one("""""
        "res.users",
        string="Approved By",
        tracking=True,""
        help="User who approved this deletion request"
    ""
""
    approval_date = fields.Datetime(""
        string="Approval Date",
        tracking=True,""
        help="Date and time when request was approved"
    ""
""
    rejection_reason = fields.Text(""
        string="Rejection Reason",
        help="Reason why the request was rejected"
    ""
""
        # ============================================================================ """"
    # ITEM RELATIONSHIPS"""""
        # ============================================================================ """"
    document_ids = fields.Many2many("""""
        "records.document",
        string="Documents to Delete",
        help="Specific documents to be deleted"
    ""
""
    container_ids = fields.Many2many(""
        "records.container",
        string="Containers to Delete", 
        help="Specific containers to be deleted"
    ""
""
        # ============================================================================ """"
    # LEGAL AND COMPLIANCE FIELDS"""""
        # ============================================================================ """"
    legal_hold_check = fields.Boolean("""""
        string="Legal Hold Check Complete",
        help="Confirms legal hold status has been verified"
    ""
""
    retention_policy_verified = fields.Boolean(""
        string="Retention Policy Verified",
        help="Confirms retention policies have been checked"
    ""
""
    customer_authorization = fields.Boolean(""
        string="Customer Authorization Received",
        tracking=True,""
        help="Customer has provided proper authorization"
    ""
""
    compliance_approved = fields.Boolean(""
        string="Compliance Approved",
        tracking=True,""
        help="Compliance team has approved the deletion"
    ""
""
        # ============================================================================ """"
    # NAID COMPLIANCE TRACKING"""""
        # ============================================================================ """"
    naid_compliant = fields.Boolean("""""
        string="NAID Compliant",
        default=True,""
        help="Whether this deletion follows NAID standards"
    ""
""
    chain_of_custody_id = fields.Many2one(""
        "records.chain.of.custody",
        string="Chain of Custody",
        help="Associated chain of custody record"
    ""
""
    certificate_of_deletion_id = fields.Many2one(""
        "certificate.of.deletion",
        string="Certificate of Deletion",
        help="Generated certificate of deletion"
    ""
""
        # ============================================================================ """"
    # FINANCIAL TRACKING"""""
        # ============================================================================ """"
    estimated_cost = fields.Monetary("""""
        string="Estimated Cost",
        currency_field="currency_id",
        help="Estimated cost for the deletion service":
    ""
""
    actual_cost = fields.Monetary(""
        string="Actual Cost",
        currency_field="currency_id",
        help="Actual cost incurred for the deletion":
    ""
""
    currency_id = fields.Many2one(""
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,""
        required=True""
    ""
""
    billable = fields.Boolean(""
        string="Billable",
        default=True,""
        help="Whether this deletion service is billable to customer"
    ""
""
        # ============================================================================ """"
    # COMPUTED FIELDS"""""
        # ============================================================================ """"
    display_name = fields.Char("""""
        string="Display Name",
        compute="_compute_display_name",
        store=True,""
        help="Formatted display name with date and status"
    ""
""
    total_items_count = fields.Integer(""
        string="Total Items",
        compute="_compute_total_items",
        store=True,""
        help="Total number of items to be deleted"
    ""
""
    days_since_request = fields.Integer(""
        string="Days Since Request",
        compute="_compute_days_since_request",
        help="Number of days since the request was created"
    ""
""
    can_approve = fields.Boolean(""
        string="Can Approve",
        compute="_compute_can_approve",
        help="Whether current user can approve this request"
    ""
""
        # ============================================================================ """"
    # PORTAL AND COMMUNICATION FIELDS"""""
        # ============================================================================ """"
    portal_request_id = fields.Many2one("""""
        "portal.request",
        string="Portal Request",
        help="Related portal request if submitted through customer portal":
    ""
""
    customer_notified = fields.Boolean(""
        string="Customer Notified",
        help="Whether customer has been notified of completion"
    ""
""
        # ============================================================================ """"
    # MAIL THREAD FRAMEWORK FIELDS"""""
        # ============================================================================ """"
    activity_ids = fields.One2many("""""
        "mail.activity",
        "res_id",
        string="Activities",
        ,""
    domain=lambda self: [("res_model", "= """", self._name))"
    ""
""
    message_follower_ids = fields.One2many(""
        """"mail.followers",
        "res_id",
        string="Followers",
        ,""
    domain=lambda self: [("res_model", "= """", self._name))"
    ""
""
    message_ids = fields.One2many(""
        """"mail.message",
        "res_id",
        string="Messages",
        ,""
    domain=lambda self: [("model", "= """", self._name))"
    ""
""
        # ============================================================================""
    # COMPUTED METHODS""
        # ============================================================================""
    @api.depends(""""name", "request_date", "state")
    def _compute_display_name(self):""
        """Compute display name with date and state info"""
"""                record.display_name = _("%(name)s (%(state)s) - %(date)s", {)}"
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
""""
                    'date': record.request_date.strftime("%Y-%m-%d")
                ""
            else:""
                record.display_name = _("%(name)s - %(state)s", {)}
                    'name': record.name,""
                    'state': dict(record._fields['state'].selection).get(record.state, record.state)""
                ""
""
    @api.depends("document_ids", "container_ids")
    def _compute_total_items(self):""
        """Compute total number of items to be deleted"""
    """    @api.depends("request_date")"
    def _compute_days_since_request(self):""
        """Compute days since request was created"""
""""
""""
    """    def _compute_can_approve(self):"
        """Check if current user can approve this request"""
""""
""""
        """Override create to generate sequence and validate"""
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code()
                    "records.deletion.request"
                ) or _("New"
        ""
        records = super().create(vals_list)""
        ""
        for record in records:""
            record._create_naid_audit_log()""
        ""
        return records""
""
    def write(self, vals):""
        """Override write to track important changes"""
""""
""""
"""        if "state" in vals:"
"""
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
                record.message_post()""
                    body=_("Deletion request status changed to %s", vals("state")
                ""
        ""
        return result""
""
    # ============================================================================""
        # ACTION METHODS""
    # ============================================================================""
    def action_submit(self):""
        """Submit deletion request for approval"""
        if self.state != "draft":
            raise UserError(_("Only draft requests can be submitted"))
""
        # Validation before submission""
        self._validate_for_submission()""
""
        self.write({"state": "submitted"})
        self._notify_approvers()""
        self.message_post()""
            body=_("Deletion request submitted for approval"):
        ""
""
    def action_approve(self):""
        """Approve the deletion request"""
"""            raise UserError(_("You don't have permission to approve deletion requests"))'
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
""""
        if self.state not in ["submitted", "under_review"]:
            raise UserError(_("Only submitted or under review requests can be approved"))
""
        self.write({)}""
            "state": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        ""
""
        self.message_post()""
            body=_("Deletion request approved by %s", self.env.user.name)
        ""
        self._notify_requestor_approved()""
""
    def action_reject(self):""
        """Reject the deletion request"""
"""            raise UserError(_("You don't have permission to reject deletion requests"))'"
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
""""
        if self.state not in ["submitted", "under_review"]:
            raise UserError(_("Only submitted or under review requests can be rejected"))
""
        return {}""
            "type": "ir.actions.act_window",
            "name": _("Rejection Reason"),
            "res_model": "deletion.rejection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {}
                "default_request_id": self.id,
            ""
        ""
""
    def action_schedule(self):""
        """Schedule the approved deletion"""
        if self.state != "approved":
            raise UserError(_("Only approved requests can be scheduled"))
""
        if not self.scheduled_deletion_date:""
            raise UserError(_("Please set a scheduled deletion date"))
""
        self.write({"state": "scheduled"})
        self._create_work_orders()""
        self.message_post()""
            body=_("Deletion scheduled for %s", self.scheduled_deletion_date):
        ""
""
    def action_start_deletion(self):""
        """Start the deletion process"""
        if self.state != "scheduled":
            raise UserError(_("Only scheduled requests can be started"))
""
        self.write({"state": "in_progress"})
        self._create_chain_of_custody()""
        self.message_post()""
            body=_("Deletion process started")
        ""
""
    def action_complete_deletion(self):""
        """Complete the deletion process"""
        if self.state != "in_progress":
            raise UserError(_("Only in-progress requests can be completed"))
""
        self.write({)}""
            "state": "completed",
            "actual_deletion_date": fields.Date.today(),
        ""
""
        self._generate_certificate_of_deletion()""
        self._update_chain_of_custody()""
        self._notify_customer_completion()""
""
        self.message_post()""
            body=_("Deletion process completed successfully")
        ""
""
    def action_cancel(self):""
        """Cancel the deletion request"""
        if self.state in ["completed"]:
            raise UserError(_("Cannot cancel completed deletions"))
""
        self.write({"state": "cancelled"})
        self.message_post()""
            body=_("Deletion request cancelled")
        ""
""
    def action_reset_to_draft(self):""
        """Reset request to draft status"""
        if self.state in ["completed", "in_progress"]:
            raise UserError(_("Cannot reset completed or in-progress requests"))
""
        self.write({)}""
            "state": "draft",
            "approved_by_id": False,
            "approval_date": False,
        ""
""
        self.message_post()""
            body=_("Deletion request reset to draft")
        ""
""
    # ============================================================================""
        # BUSINESS METHODS""
    # ============================================================================""
    def get_deletion_summary(self):""
        """Get deletion request summary for reporting"""
"""
""""
    """
        """Validate request before submission"""
            raise ValidationError(_("Please provide a description of items to be deleted"))
""
        if not self.reason:""
            raise ValidationError(_("Please provide a reason for the deletion")):
        if not self.document_ids and not self.container_ids:""
            raise ValidationError(_("Please specify documents or containers to be deleted"))
""
        if not self.customer_authorization:""
            raise ValidationError(_("Customer authorization is required"))
""
    def _notify_approvers(self):""
        """Notify approvers of pending request"""
""""
"""
    """    def _notify_requestor_approved(self):"
        """Notify requestor of approval"""
"""
""""
    """
        """Create work orders for the deletion"""
""""
    """    def _create_chain_of_custody(self):"
        """Create chain of custody record"""
""""
"""
    """"
        """Update chain of custody with completion"""
"""
""""
    """    def _generate_certificate_of_deletion(self):"
        """Generate certificate of deletion"""
""""
"""
    """"
        """Notify customer of completion"""
"""
""""
    """    def _create_naid_audit_log(self):"
        """Create NAID audit log entry"""
""""
"""
"""                'description': _("Deletion request created: %s", self.name),"
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
            self.message_post()""
                body=_("Warning: Could not create NAID audit log: %s", str(e)),
                message_type='comment'""
            ""
""
    # ============================================================================""
        # VALIDATION METHODS""
    # ============================================================================""
    @api.constrains("request_date", "scheduled_deletion_date")
    def _check_dates(self):""
        """Validate date consistency"""
"""                raise ValidationError(_("Request date cannot be in the future"))"
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
""""
                    raise ValidationError(_("Scheduled deletion date cannot be before request date"))
""
    @api.constrains("estimated_cost", "actual_cost")
    def _check_costs(self):""
        """Validate cost amounts"""
"""                raise ValidationError(_("Estimated cost cannot be negative"))
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
""""
                raise ValidationError(_("Actual cost cannot be negative"))
""
    @api.constrains("document_ids", "container_ids")
    def _check_items_to_delete(self):""
        """Validate items to be deleted"""
"""                raise ValidationError(_("Please specify documents or containers to be deleted"))"
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
""""
        """Custom name display using computed display_name"""
    """
"""    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):"
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
""""
        """Enhanced search by name, customer, or description"""
""""
""""
"""                "|", "|", "|","
"""
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
                ("name", operator, name),
                ("partner_id.name", operator, name),
                ("description", operator, name),
                ("reason", operator, name),
            ""
        ""
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)""
""
    # ============================================================================""
        # REPORTING METHODS""
    # ============================================================================""
    @api.model""
    def get_deletion_dashboard_data(self):""
        """Get dashboard data for deletion requests"""
"""                ('actual_deletion_date', '>= """
            '"""by_type': self.read_group()"
                [('state', '!=', 'cancelled'),"
                ['deletion_type'],"
                ['deletion_type']"
            ""
        ""
""
    @api.model""
""""
        """Generate comprehensive deletion report"""
"""            domain.append(('request_date', '>= """', date_from))""
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
""""
            domain.append(('"""request_date', '<= """
"""            '"""
""""
"""            'requests': [req.get_deletion_summary() for req in requests],:"
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
    ""
    """"
"""
""""