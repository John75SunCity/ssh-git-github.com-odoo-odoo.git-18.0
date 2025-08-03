# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PortalRequest(models.Model):
    _name = "portal.request"
    _description = "Portal Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # Essential Portal Request Fields (from view analysis)
    request_type = fields.Selection(
        [
            ("document_retrieval", "Document Retrieval"),
            ("document_storage", "Document Storage"),
            ("document_destruction", "Document Destruction"),
            ("document_scanning", "Document Scanning"),
            ("pickup_request", "Pickup Request"),
            ("service_request", "Service Request"),
            ("billing_inquiry", "Billing Inquiry"),
            ("access_request", "Access Request"),
            ("complaint", "Complaint"),
            ("other", "Other"),
        ],
        string="Request Type",
        required=True,
        tracking=True,
    )

    request_status = fields.Selection(
        [
            ("submitted", "Submitted"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        string="Request Status",
        default="submitted",
        tracking=True,
    )

    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        string="Priority",
        default="1",
        tracking=True,
    )

    # Date Management
    submission_date = fields.Datetime(
        string="Submission Date", default=fields.Datetime.now, required=True
    )
    target_completion_date = fields.Date(string="Target Completion Date")
    actual_completion_date = fields.Datetime(string="Actual Completion Date")

    # Request Details
    requested_service = fields.Text(string="Requested Service")
    urgency_reason = fields.Text(string="Urgency Reason")
    special_instructions = fields.Text(string="Special Instructions")

    # Financial Information
    estimated_cost = fields.Monetary(
        string="Estimated Cost", currency_field="currency_id"
    )
    actual_cost = fields.Monetary(string="Actual Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Approval Workflow
    approval_required = fields.Boolean(string="Approval Required", default=True)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Datetime(string="Approval Date")
    approval_notes = fields.Text(string="Approval Notes")

    # Assignment and Processing
    assigned_to = fields.Many2one("res.users", string="Assigned To")
    department_id = fields.Many2one("hr.department", string="Department")
    processing_notes = fields.Text(string="Processing Notes")

    # Communication
    contact_method = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone"),
            ("portal", "Portal Message"),
            ("in_person", "In Person"),
        ],
        string="Preferred Contact Method",
        default="email",
    )

    # Related Documents
    document_ids = fields.Many2many("documents.document", string="Related Documents")
    attachment_count = fields.Integer(
        string="Attachment Count", compute="_compute_attachment_count"
    )

    # Service Level Agreement
    sla_deadline = fields.Datetime(
        string="SLA Deadline", compute="_compute_sla_deadline"
    )
    sla_status = fields.Selection(
        [("on_time", "On Time"), ("at_risk", "At Risk"), ("overdue", "Overdue")],
        string="SLA Status",
        compute="_compute_sla_status",
    )

    # Quality and Feedback
    customer_satisfaction = fields.Selection(
        [
            ("1", "Very Dissatisfied"),
            ("2", "Dissatisfied"),
            ("3", "Neutral"),
            ("4", "Satisfied"),
            ("5", "Very Satisfied"),
        ],
        string="Customer Satisfaction",
    )

    feedback_received = fields.Boolean(string="Feedback Received", default=False)
    quality_score = fields.Float(string="Quality Score", digits=(3, 1))

    # Compliance and Audit
    compliance_required = fields.Boolean(string="Compliance Required", default=False)
    audit_trail_ids = fields.One2many("audit.trail", "request_id", string="Audit Trail")
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=False
    )

    @api.depends("document_ids")
    def _compute_attachment_count(self):
        """Compute number of attachments"""
        for record in self:
            record.attachment_count = len(record.document_ids)

    @api.depends("submission_date", "request_type", "priority")
    def _compute_sla_deadline(self):
        """Compute SLA deadline based on request type and priority"""
        for record in self:
            if record.submission_date:
                # Base SLA hours by request type
                sla_hours = {
                    "document_retrieval": 24,
                    "document_storage": 48,
                    "document_destruction": 72,
                    "document_scanning": 48,
                    "pickup_request": 24,
                    "service_request": 48,
                    "billing_inquiry": 24,
                    "access_request": 12,
                    "complaint": 8,
                    "other": 48,
                }.get(record.request_type, 48)

                # Adjust for priority
                priority_multiplier = {"3": 0.5, "2": 0.75, "1": 1.0, "0": 1.5}.get(
                    record.priority, 1.0
                )
                adjusted_hours = sla_hours * priority_multiplier

                record.sla_deadline = record.submission_date + fields.timedelta(
                    hours=adjusted_hours
                )
            else:
                record.sla_deadline = False

    @api.depends("sla_deadline", "request_status")
    def _compute_sla_status(self):
        """Compute SLA status"""
        for record in self:
            if record.request_status in ["completed", "cancelled"]:
                record.sla_status = (
                    "on_time"  # Completed requests are considered on time
                )
            elif record.sla_deadline:
                now = fields.Datetime.now()
                hours_remaining = (record.sla_deadline - now).total_seconds() / 3600

                if hours_remaining < 0:
                    record.sla_status = "overdue"
                elif hours_remaining < 8:  # Less than 8 hours remaining
                    record.sla_status = "at_risk"
                else:
                    record.sla_status = "on_time"
            else:
                record.sla_status = "on_time"

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    rating = fields.Selection(
        [
            ("1", "Poor"),
            ("2", "Fair"),
            ("3", "Good"),
            ("4", "Very Good"),
            ("5", "Excellent"),
        ],
        string="Rating",
    )
    feedback_text = fields.Text(string="Feedback")
    response_date = fields.Datetime(string="Response Date")
    resolved = fields.Boolean(string="Resolved", default=False)
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # === COMPREHENSIVE MISSING FIELDS ===
    request_type_id = fields.Many2one("portal.request.type", string="Request Type")
    urgency_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Urgency",
        default="medium",
    )
    category_id = fields.Many2one("portal.request.category", string="Category")
    subcategory_id = fields.Many2one("portal.request.subcategory", string="Subcategory")
    customer_reference = fields.Char(string="Customer Reference")
    customer_po_number = fields.Char(string="Customer PO Number")
    delivery_address_id = fields.Many2one("res.partner", string="Delivery Address")
    billing_address_id = fields.Many2one("res.partner", string="Billing Address")
    assigned_department_id = fields.Many2one(
        "hr.department", string="Assigned Department"
    )
    processor_id = fields.Many2one("res.users", string="Request Processor")
    approved_by_id = fields.Many2one("res.users", string="Approved By")
    signed_document_ids = fields.One2many(
        "signed.document", "request_id", string="Signed Documents"
    )
    certificate_required = fields.Boolean(string="Certificate Required")
    certificate_id = fields.Many2one("certificate", "request_id", string="Certificate")
    tracking_number = fields.Char(string="Tracking Number")
    communication_log_ids = fields.One2many(
        "communication.log", "request_id", string="Communication Log"
    )
    customer_notification_sent = fields.Boolean(string="Customer Notified")
    internal_notes = fields.Text(string="Internal Notes")
    completion_percentage = fields.Float(string="Completion %", digits=(5, 2))
    delivery_method = fields.Selection(
        [
            ("pickup", "Customer Pickup"),
            ("delivery", "Delivery"),
            ("email", "Email"),
            ("portal", "Portal"),
        ],
        string="Delivery Method",
    )
    delivery_date = fields.Date(string="Delivery Date")
    delivery_confirmation = fields.Boolean(string="Delivery Confirmed")

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()

    # Portal Request Management Fields
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "portal_request_attachment_rel",
        "request_id",
        "attachment_id",
        "Attachments",
    )
    access_restrictions = fields.Text("Access Restrictions")
    actual_date = fields.Date("Actual Date")
    approval_action = fields.Selection(
        [("approve", "Approve"), ("reject", "Reject"), ("defer", "Defer")],
        "Approval Action",
    )
    approval_deadline = fields.Date("Approval Deadline")
    approval_history_ids = fields.One2many(
        "approval.history", "request_id", "Approval History"
    )
    approval_level_required = fields.Selection(
        [("basic", "Basic"), ("advanced", "Advanced"), ("executive", "Executive")],
        default="basic",
    )
    auto_approval_eligible = fields.Boolean("Auto Approval Eligible", default=False)
    billing_impact_assessment = fields.Text("Billing Impact Assessment")
    business_justification = fields.Text("Business Justification")
    compliance_approval_required = fields.Boolean(
        "Compliance Approval Required", default=False
    )
    compliance_verification_notes = fields.Text("Compliance Verification Notes")
    cost_center_id = fields.Many2one("account.analytic.account", "Cost Center")
    cost_impact_amount = fields.Monetary("Cost Impact", currency_field="currency_id")
    customer_confirmation_required = fields.Boolean(
        "Customer Confirmation Required", default=True
    )
    customer_contact_method = fields.Selection(
        [("email", "Email"), ("phone", "Phone"), ("portal", "Portal")], default="email"
    )
    customer_notification_sent = fields.Boolean(
        "Customer Notification Sent", default=False
    )
    department_approval_required = fields.Boolean(
        "Department Approval Required", default=False
    )
    document_verification_required = fields.Boolean(
        "Document Verification Required", default=False
    )
    escalation_level = fields.Selection(
        [
            ("none", "None"),
            ("supervisor", "Supervisor"),
            ("manager", "Manager"),
            ("director", "Director"),
        ],
        default="none",
    )
    estimated_completion_time = fields.Float("Estimated Completion Time (Hours)")
    external_reference = fields.Char("External Reference")
    follow_up_action_required = fields.Boolean(
        "Follow-up Action Required", default=False
    )
    impact_assessment = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], default="low"
    )
    internal_notes = fields.Text("Internal Notes")
    legal_review_required = fields.Boolean("Legal Review Required", default=False)
    manager_approval_required = fields.Boolean(
        "Manager Approval Required", default=False
    )
    notification_preferences = fields.Text("Notification Preferences")
    portal_visibility = fields.Selection(
        [
            ("customer", "Customer Only"),
            ("department", "Department"),
            ("public", "Public"),
        ],
        default="customer",
    )
    processing_notes = fields.Text("Processing Notes")
    quality_assurance_required = fields.Boolean(
        "Quality Assurance Required", default=False
    )
    request_category_id = fields.Many2one("request.category", "Request Category")
    request_complexity = fields.Selection(
        [("simple", "Simple"), ("moderate", "Moderate"), ("complex", "Complex")],
        default="simple",
    )
    request_source = fields.Selection(
        [
            ("portal", "Customer Portal"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("api", "API"),
        ],
        default="portal",
    )
    request_subcategory_id = fields.Many2one(
        "request.subcategory", "Request Subcategory"
    )
    resource_allocation_notes = fields.Text("Resource Allocation Notes")
    risk_assessment_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], default="low"
    )
    security_clearance_required = fields.Boolean(
        "Security Clearance Required", default=False
    )
    service_level_agreement = fields.Selection(
        [
            ("standard", "Standard"),
            ("expedited", "Expedited"),
            ("priority", "Priority"),
        ],
        default="standard",
    )
    stakeholder_notification_list = fields.Text("Stakeholder Notification List")
    status_change_log = fields.Text("Status Change Log")
    third_party_approval_required = fields.Boolean(
        "Third Party Approval Required", default=False
    )

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    # =============================================================================
    # PORTAL REQUEST ACTION METHODS
    # =============================================================================

    def action_approve_request(self):
        """Approve the portal request."""
        self.ensure_one()
        if self.state == "draft":
            self.write({"state": "active"})
            self.message_post(body=_("Request approved and activated."))
        return True

    def action_complete_request(self):
        """Mark request as complete."""
        self.ensure_one()
        self.write({"state": "inactive"})
        self.message_post(body=_("Request marked as complete."))
        return True

    def action_contact_customer(self):
        """Contact customer about this request."""
        self.ensure_one()
        # Return action to open compose message wizard
        return {
            "type": "ir.actions.act_window",
            "name": _("Contact Customer"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "portal.request",
                "default_res_id": self.id,
                "default_use_template": False,
                "default_composition_mode": "comment",
            },
        }

    def action_customer_history(self):
        """View customer history for this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer History"),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("user_id", "=", self.user_id.id)],
            "context": {"search_default_user_id": self.user_id.id},
        }

    def action_download(self):
        """Download request data."""
        self.ensure_one()
        # Return action to download as PDF or export
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.portal_request_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_escalate(self):
        """Escalate the request to management."""
        self.ensure_one()
        # Create activity for manager
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Escalated Request: %s") % self.name,
            note=_(
                "This request has been escalated and requires management attention."
            ),
            user_id=(
                self.env.ref("base.group_system").users[0].id
                if self.env.ref("base.group_system").users
                else self.env.user.id
            ),
        )
        self.message_post(body=_("Request escalated to management."))
        return True

    def action_process_request(self):
        """Process the request."""
        self.ensure_one()
        if self.state == "draft":
            self.write({"state": "active"})
        self.message_post(body=_("Request processing started."))
        return True

    def action_send_notification(self):
        """Send notification about request status."""
        self.ensure_one()
        # Send email notification
        template = self.env.ref(
            "records_management.portal_request_notification_template",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)
        self.message_post(body=_("Notification sent to stakeholders."))
        return True

    def action_view_attachments(self):
        """View attachments for this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "tree,form",
            "domain": [("res_model", "=", "portal.request"), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": "portal.request",
                "default_res_id": self.id,
            },
        }

    def action_view_communications(self):
        """View all communications for this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Communications"),
            "res_model": "mail.message",
            "view_mode": "tree,form",
            "domain": [("model", "=", "portal.request"), ("res_id", "=", self.id)],
            "context": {"search_default_model": "portal.request"},
        }

    def action_view_details(self):
        """View detailed information about this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Details"),
            "res_model": "portal.request",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_related_requests(self):
        """View related requests from same user."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Requests"),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("user_id", "=", self.user_id.id), ("id", "!=", self.id)],
            "context": {"search_default_user_id": self.user_id.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)
