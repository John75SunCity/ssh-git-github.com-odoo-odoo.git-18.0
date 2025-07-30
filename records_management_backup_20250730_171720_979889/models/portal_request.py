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
        "shredding.service", string="Related Shredding Service", tracking=True
    )
    access_restrictions = fields.Char(string='Access Restrictions')
    action_approve_request = fields.Char(string='Action Approve Request')
    action_complete_request = fields.Char(string='Action Complete Request')
    action_contact_customer = fields.Char(string='Action Contact Customer')
    action_customer_history = fields.Char(string='Action Customer History')
    action_download = fields.Char(string='Action Download')
    action_escalate = fields.Char(string='Action Escalate')
    action_process_request = fields.Char(string='Action Process Request')
    action_send_notification = fields.Char(string='Action Send Notification')
    action_view_attachments = fields.Char(string='Action View Attachments')
    action_view_communications = fields.Char(string='Action View Communications')
    action_view_details = fields.Char(string='Action View Details')
    action_view_related_requests = fields.Char(string='Action View Related Requests')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    actual_cost = fields.Char(string='Actual Cost')
    actual_date = fields.Date(string='Actual Date')
    analytics = fields.Char(string='Analytics')
    approval = fields.Char(string='Approval')
    approval_action = fields.Char(string='Approval Action')
    approval_date = fields.Date(string='Approval Date')
    approval_deadline = fields.Char(string='Approval Deadline')
    approval_history_ids = fields.One2many('approval.history', 'portal_request_id', string='Approval History Ids')
    approval_level = fields.Char(string='Approval Level')
    approval_level_required = fields.Boolean(string='Approval Level Required', default=False)
    approver = fields.Char(string='Approver')
    assigned_to = fields.Char(string='Assigned To')
    attachment_ids = fields.One2many('attachment', 'portal_request_id', string='Attachment Ids')
    attachments = fields.Char(string='Attachments')
    auto_approve_threshold = fields.Char(string='Auto Approve Threshold')
    billable_hours = fields.Char(string='Billable Hours')
    billing = fields.Char(string='Billing')
    billing_method = fields.Char(string='Billing Method')
    billing_required = fields.Boolean(string='Billing Required', default=False)
    button_box = fields.Char(string='Button Box')
    cancelled = fields.Char(string='Cancelled')
    card = fields.Char(string='Card')
    chain_of_custody_required = fields.Boolean(string='Chain Of Custody Required', default=False)
    comments = fields.Char(string='Comments')
    communication_count = fields.Integer(string='Communication Count', compute='_compute_communication_count', store=True)
    communication_date = fields.Date(string='Communication Date')
    communication_log_ids = fields.One2many('communication.log', 'portal_request_id', string='Communication Log Ids')
    communication_type = fields.Selection([], string='Communication Type')  # TODO: Define selection options
    communications = fields.Char(string='Communications')
    completed = fields.Boolean(string='Completed', default=False)
    completion_percentage = fields.Char(string='Completion Percentage')
    compliance_score = fields.Char(string='Compliance Score')
    confidential = fields.Char(string='Confidential')
    confidentiality_level = fields.Char(string='Confidentiality Level')
    context = fields.Char(string='Context')
    customer_complaints = fields.Char(string='Customer Complaints')
    customer_rating = fields.Char(string='Customer Rating')
    customer_satisfaction = fields.Char(string='Customer Satisfaction')
    customer_wait_time = fields.Float(string='Customer Wait Time', digits=(12, 2))
    department = fields.Char(string='Department')
    details = fields.Char(string='Details')
    escalation_approver = fields.Char(string='Escalation Approver')
    escalation_contact = fields.Char(string='Escalation Contact')
    estimated_cost = fields.Char(string='Estimated Cost')
    estimated_hours = fields.Char(string='Estimated Hours')
    file_size = fields.Char(string='File Size')
    file_type = fields.Selection([], string='File Type')  # TODO: Define selection options
    final_approver = fields.Char(string='Final Approver')
    first_response_time = fields.Float(string='First Response Time', digits=(12, 2))
    from_person = fields.Char(string='From Person')
    group_by_assigned = fields.Char(string='Group By Assigned')
    group_by_customer = fields.Char(string='Group By Customer')
    group_by_date = fields.Date(string='Group By Date')
    group_by_priority = fields.Selection([], string='Group By Priority')  # TODO: Define selection options
    group_by_sla = fields.Char(string='Group By Sla')
    group_by_status = fields.Selection([], string='Group By Status')  # TODO: Define selection options
    group_by_type = fields.Selection([], string='Group By Type')  # TODO: Define selection options
    help = fields.Char(string='Help')
    high_priority = fields.Selection([], string='High Priority')  # TODO: Define selection options
    hourly_rate = fields.Float(string='Hourly Rate', digits=(12, 2))
    in_progress = fields.Char(string='In Progress')
    invoice_generated = fields.Char(string='Invoice Generated')
    low_priority = fields.Selection([], string='Low Priority')  # TODO: Define selection options
    material_costs = fields.Char(string='Material Costs')
    materials_required = fields.Boolean(string='Materials Required', default=False)
    medium_priority = fields.Selection([], string='Medium Priority')  # TODO: Define selection options
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    milestone_name = fields.Char(string='Milestone Name')
    naid_compliance_required = fields.Boolean(string='Naid Compliance Required', default=False)
    naid_required = fields.Boolean(string='Naid Required', default=False)
    notes = fields.Char(string='Notes')
    overall_satisfaction = fields.Char(string='Overall Satisfaction')
    pending_approval = fields.Char(string='Pending Approval')
    primary_approver = fields.Char(string='Primary Approver')
    processing_time = fields.Float(string='Processing Time', digits=(12, 2))
    quality_score = fields.Char(string='Quality Score')
    related_request_count = fields.Integer(string='Related Request Count', compute='_compute_related_request_count', store=True)
    request_status = fields.Selection([], string='Request Status')  # TODO: Define selection options
    requires_approval = fields.Char(string='Requires Approval')
    res_model = fields.Char(string='Res Model')
    resolution_efficiency = fields.Char(string='Resolution Efficiency')
    resolution_time = fields.Float(string='Resolution Time', digits=(12, 2))
    response_required = fields.Boolean(string='Response Required', default=False)
    response_time = fields.Float(string='Response Time', digits=(12, 2))
    rework_required = fields.Boolean(string='Rework Required', default=False)
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    secondary_approver = fields.Char(string='Secondary Approver')
    service_category = fields.Char(string='Service Category')
    sla = fields.Char(string='Sla')
    sla_at_risk = fields.Char(string='Sla At Risk')
    sla_breach_risk = fields.Char(string='Sla Breach Risk')
    sla_breached = fields.Char(string='Sla Breached')
    sla_deadline = fields.Char(string='Sla Deadline')
    sla_milestone_ids = fields.One2many('sla.milestone', 'portal_request_id', string='Sla Milestone Ids')
    sla_on_time = fields.Float(string='Sla On Time', digits=(12, 2))
    sla_status = fields.Selection([], string='Sla Status')  # TODO: Define selection options
    sla_target_hours = fields.Char(string='Sla Target Hours')
    special_instructions = fields.Char(string='Special Instructions')
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed')], string='Status', default='new')
    subject = fields.Char(string='Subject')
    submission_date = fields.Date(string='Submission Date')
    submitted = fields.Char(string='Submitted')
    supervisor = fields.Char(string='Supervisor')
    target_completion_date = fields.Date(string='Target Completion Date')
    target_date = fields.Date(string='Target Date')
    this_month = fields.Char(string='This Month')
    this_week = fields.Char(string='This Week')
    time_elapsed = fields.Char(string='Time Elapsed')
    time_remaining = fields.Char(string='Time Remaining')
    time_taken = fields.Char(string='Time Taken')
    to_person = fields.Char(string='To Person')
    today = fields.Char(string='Today')
    total_amount = fields.Float(string='Total Amount', digits=(12, 2))
    upload_date = fields.Date(string='Upload Date')
    uploaded_by = fields.Char(string='Uploaded By')
    variance = fields.Char(string='Variance')
    view_mode = fields.Char(string='View Mode')

    @api.depends('communication_ids')
    def _compute_communication_count(self):
        for record in self:
            record.communication_count = len(record.communication_ids)

    @api.depends('related_request_ids')
    def _compute_related_request_count(self):
        for record in self:
            record.related_request_count = len(record.related_request_ids)

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('amount'))

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
