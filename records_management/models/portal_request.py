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
            ("sms", "SMS"),
            ("portal", "Portal"),
        ],
        string="Contact Method",
        default="portal",
    )

    # === CRITICAL MISSING FIELDS (from portal_request_views.xml analysis) ===

    # SLA and Performance Fields
    sla_status = fields.Selection(
        [("on_track", "On Track"), ("at_risk", "At Risk"), ("breached", "Breached")],
        string="SLA Status",
        compute="_compute_sla_status",
    )
    sla_deadline = fields.Datetime(
        string="SLA Deadline", compute="_compute_sla_deadline"
    )

    # Assignment Fields
    department = fields.Many2one("hr.department", string="Department")
    supervisor = fields.Many2one("res.users", string="Supervisor")
    escalation_contact = fields.Many2one("res.users", string="Escalation Contact")

    # Status Tracking Fields
    completion_percentage = fields.Float(
        string="Completion Percentage (%)", digits=(5, 2)
    )
    customer_satisfaction = fields.Float(string="Customer Satisfaction", digits=(3, 1))
    billing_required = fields.Boolean(string="Billing Required", default=False)

    # Service Details
    service_category = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("scanning", "Scanning"),
            ("transport", "Transport"),
        ],
        string="Service Category",
    )
    estimated_hours = fields.Float(string="Estimated Hours", digits=(8, 2))
    materials_required = fields.Text(string="Materials Required")

    # ============================================================================
    # MISSING FIELDS FROM SMART GAP ANALYSIS - PORTAL REQUEST ENHANCEMENT
    # ============================================================================

    # Communication & Approval Fields
    communication_date = fields.Datetime(
        string="Communication Date",
        help="Date of last communication regarding this request",
    )
    communication_type = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone Call"),
            ("portal", "Portal Message"),
            ("meeting", "Meeting"),
            ("sms", "SMS"),
        ],
        string="Communication Type",
        help="Type of communication used",
    )

    # Simplified Approval Fields (to match view references)
    approver = fields.Many2one(
        "res.users", string="Approver", help="Primary approver for this request"
    )
    approval_level = fields.Selection(
        [
            ("none", "No Approval Required"),
            ("basic", "Basic Approval"),
            ("advanced", "Advanced Approval"),
            ("management", "Management Approval"),
            ("executive", "Executive Approval"),
        ],
        string="Approval Level",
        help="Level of approval required",
    )

    # Comments and Notes
    comments = fields.Text(
        string="Comments", help="Additional comments and notes about the request"
    )

    # Security and Compliance
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Confidentiality Level",
        default="internal",
    )
    naid_compliance_required = fields.Boolean(
        string="NAID Compliance Required", default=False
    )
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=False
    )
    access_restrictions = fields.Text(string="Access Restrictions")

    # Approval Workflow Fields
    requires_approval = fields.Boolean(string="Requires Approval", default=True)
    approval_level_required = fields.Selection(
        [("1", "Level 1"), ("2", "Level 2"), ("3", "Level 3")],
        string="Approval Level Required",
        default="1",
    )
    auto_approve_threshold = fields.Monetary(
        string="Auto Approve Threshold", currency_field="currency_id"
    )
    approval_deadline = fields.Datetime(string="Approval Deadline")
    primary_approver = fields.Many2one("res.users", string="Primary Approver")
    secondary_approver = fields.Many2one("res.users", string="Secondary Approver")
    final_approver = fields.Many2one("res.users", string="Final Approver")
    escalation_approver = fields.Many2one("res.users", string="Escalation Approver")

    # Billing Fields
    billing_method = fields.Selection(
        [
            ("fixed", "Fixed Price"),
            ("hourly", "Hourly Rate"),
            ("material", "Material Based"),
        ],
        string="Billing Method",
        default="fixed",
    )
    hourly_rate = fields.Monetary(string="Hourly Rate", currency_field="currency_id")
    billable_hours = fields.Float(string="Billable Hours", digits=(8, 2))
    material_costs = fields.Monetary(
        string="Material Costs", currency_field="currency_id"
    )
    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        compute="_compute_total_amount",
    )
    invoice_generated = fields.Boolean(string="Invoice Generated", default=False)

    # SLA Metrics
    sla_target_hours = fields.Integer(string="SLA Target Hours", default=24)
    time_elapsed = fields.Float(
        string="Time Elapsed (Hours)", compute="_compute_time_metrics"
    )
    time_remaining = fields.Float(
        string="Time Remaining (Hours)", compute="_compute_time_metrics"
    )
    sla_breach_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="SLA Breach Risk",
        compute="_compute_sla_risk",
    )

    # Performance Metrics
    response_time = fields.Float(
        string="Response Time (Hours)", compute="_compute_response_time"
    )
    resolution_time = fields.Float(
        string="Resolution Time (Hours)", compute="_compute_resolution_time"
    )
    customer_rating = fields.Float(string="Customer Rating", digits=(3, 1))
    quality_score = fields.Float(string="Quality Score", digits=(5, 2))

    # Analytics Fields
    processing_time = fields.Float(
        string="Processing Time (Hours)", compute="_compute_processing_time"
    )
    customer_wait_time = fields.Float(
        string="Customer Wait Time (Hours)", compute="_compute_wait_time"
    )
    first_response_time = fields.Float(
        string="First Response Time (Hours)", compute="_compute_first_response_time"
    )
    resolution_efficiency = fields.Float(
        string="Resolution Efficiency (%)", compute="_compute_efficiency"
    )
    rework_required = fields.Boolean(string="Rework Required", default=False)
    customer_complaints = fields.Integer(string="Customer Complaints", default=0)
    compliance_score = fields.Float(string="Compliance Score (%)", digits=(5, 2))
    overall_satisfaction = fields.Float(string="Overall Satisfaction", digits=(3, 1))

    # One2many Relationship Fields
    attachment_ids = fields.One2many(
        "portal.request.attachment", "request_id", string="Attachments"
    )
    communication_log_ids = fields.One2many(
        "portal.communication.log", "request_id", string="Communication Log"
    )
    approval_history_ids = fields.One2many(
        "approval.history", "request_id", string="Approval History"
    )
    sla_milestone_ids = fields.One2many(
        "portal.sla.milestone", "request_id", string="SLA Milestones"
    )

    # System Fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

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

    # === MISSING FIELDS FOR PORTAL.REQUEST ===

    # Document and File Management
    # ============================================================================
    # MISSING FIELDS FROM SMART GAP ANALYSIS - PORTAL REQUEST ENHANCEMENT  
    # ============================================================================

    # Request Processing Status
    response_required = fields.Boolean(
        string="Response Required",
        default=True,
        help="Indicates if a response is required for this request"
    )
    
    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold')
    ], string="Status", default='new', tracking=True)
    
    # Request Details
    subject = fields.Char(
        string="Subject",
        required=True,
        help="Brief description or subject of the request"
    )
    
    target_date = fields.Date(
        string="Target Date",
        help="Target completion date for this request"
    )
    
    # Time Tracking
    time_taken = fields.Float(
        string="Time Taken (Hours)", 
        digits=(8, 2),
        help="Total time taken to process this request"
    )
    
    # Framework Integration Fields (required by mail.thread)
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities"
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers", 
        "res_id",
        string="Followers"
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id", 
        string="Messages"
    )
    
    # Additional Business Fields
    request_category = fields.Selection([
        ('standard', 'Standard Request'),
        ('expedited', 'Expedited Request'),
        ('emergency', 'Emergency Request'),
        ('batch', 'Batch Request')
    ], string="Request Category", default='standard')
    
    completion_notes = fields.Text(
        string="Completion Notes",
        help="Notes about the completion of this request"
    )
    confidential = fields.Boolean(
        string="Confidential",
        default=False,
        tracking=True,
        help="Mark request as confidential",
    )

    file_size = fields.Float(
        string="File Size (MB)", digits=(10, 2), help="Total size of attached files"
    )

    file_type = fields.Selection(
        [
            ("pdf", "PDF"),
            ("doc", "Document"),
            ("image", "Image"),
            ("archive", "Archive"),
            ("other", "Other"),
        ],
        string="File Type",
        help="Primary file type in request",
    )

    # Communication Fields
    from_person = fields.Char(
        string="From Person", help="Person who submitted the request"
    )

    milestone_name = fields.Char(
        string="Milestone Name", help="Project milestone associated with request"
    )

    # Process Enhancement Fields
    request_source = fields.Selection(
        [
            ("portal", "Customer Portal"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("mobile", "Mobile App"),
            ("internal", "Internal System"),
        ],
        string="Request Source",
        default="portal",
        tracking=True,
    )

    estimated_completion_date = fields.Datetime(
        string="Estimated Completion",
        tracking=True,
        help="Estimated completion date and time",
    )

    actual_completion_date = fields.Datetime(
        string="Actual Completion",
        tracking=True,
        help="Actual completion date and time",
    )

    # Cost and Billing
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="company_currency_id",
        help="Estimated cost for fulfilling the request",
    )

    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="company_currency_id",
        help="Actual cost incurred",
    )

    # Reference and External
    external_reference = fields.Char(
        string="External Reference", help="External system reference number"
    )

    customer_reference = fields.Char(
        string="Customer Reference", help="Customer provided reference number"
    )

    # Performance Metrics
    processing_time = fields.Float(
        string="Processing Time (Hours)",
        compute="_compute_processing_time",
        store=True,
        digits=(8, 2),
        help="Time taken to process the request",
    )

    response_time = fields.Float(
        string="Response Time (Hours)",
        compute="_compute_response_time",
        store=True,
        digits=(8, 2),
        help="Time taken to first respond to request",
    )

    completion_rate = fields.Float(
        string="Completion Rate (%)",
        compute="_compute_completion_rate",
        store=True,
        digits=(5, 2),
        help="Percentage of request completed",
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
                    "on_track"  # Completed requests are considered on track
                )
            elif record.sla_deadline:
                now = fields.Datetime.now()
                hours_remaining = (record.sla_deadline - now).total_seconds() / 3600

                if hours_remaining < 0:
                    record.sla_status = "breached"
                elif hours_remaining < 4:  # Less than 4 hours remaining
                    record.sla_status = "at_risk"
                else:
                    record.sla_status = "on_track"
            else:
                record.sla_status = "on_track"

    @api.depends("estimated_cost", "billable_hours", "hourly_rate", "material_costs")
    def _compute_total_amount(self):
        """Compute total amount"""
        for record in self:
            total = record.estimated_cost or 0
            if record.billable_hours and record.hourly_rate:
                total += record.billable_hours * record.hourly_rate
            if record.material_costs:
                total += record.material_costs
            record.total_amount = total

    @api.depends("submission_date", "actual_completion_date")
    def _compute_processing_time(self):
        """Compute processing time in hours"""
        for record in self:
            if record.submission_date and record.actual_completion_date:
                delta = record.actual_completion_date - record.submission_date
                record.processing_time = delta.total_seconds() / 3600.0
            else:
                record.processing_time = 0.0

    @api.depends("submission_date", "first_response_date")
    def _compute_response_time(self):
        """Compute response time in hours"""
        for record in self:
            if (
                record.submission_date
                and hasattr(record, "first_response_date")
                and record.first_response_date
            ):
                delta = record.first_response_date - record.submission_date
                record.response_time = delta.total_seconds() / 3600.0
            else:
                record.response_time = 0.0

    @api.depends("request_status", "progress_percentage")
    def _compute_completion_rate(self):
        """Compute completion rate percentage"""
        for record in self:
            if record.request_status == "completed":
                record.completion_rate = 100.0
            elif record.request_status == "cancelled":
                record.completion_rate = 0.0
            elif hasattr(record, "progress_percentage") and record.progress_percentage:
                record.completion_rate = record.progress_percentage
            else:
                # Estimate based on status
                status_completion = {
                    "submitted": 10.0,
                    "under_review": 25.0,
                    "approved": 40.0,
                    "in_progress": 60.0,
                    "rejected": 0.0,
                }
                record.completion_rate = status_completion.get(
                    record.request_status, 0.0
                )

    @api.depends("submission_date")
    def _compute_time_metrics(self):
        """Compute time elapsed and remaining"""
        for record in self:
            if record.submission_date:
                now = fields.Datetime.now()
                elapsed = (now - record.submission_date).total_seconds() / 3600
                record.time_elapsed = elapsed

                if record.sla_deadline:
                    remaining = (record.sla_deadline - now).total_seconds() / 3600
                    record.time_remaining = max(0, remaining)
                else:
                    record.time_remaining = 0
            else:
                record.time_elapsed = 0
                record.time_remaining = 0

    @api.depends("time_remaining", "sla_target_hours")
    def _compute_sla_risk(self):
        """Compute SLA breach risk"""
        for record in self:
            if record.sla_target_hours and record.time_remaining:
                risk_ratio = record.time_remaining / record.sla_target_hours
                if risk_ratio < 0.25:
                    record.sla_breach_risk = "high"
                elif risk_ratio < 0.5:
                    record.sla_breach_risk = "medium"
                else:
                    record.sla_breach_risk = "low"
            else:
                record.sla_breach_risk = "low"

    @api.depends("submission_date", "assigned_to")
    def _compute_response_time(self):
        """Compute response time"""
        for record in self:
            if record.submission_date and record.assigned_to:
                # For now, assume assignment is the response
                record.response_time = 2.0  # Default 2 hours
            else:
                record.response_time = 0.0

    @api.depends("submission_date", "actual_completion_date")
    def _compute_resolution_time(self):
        """Compute resolution time"""
        for record in self:
            if record.submission_date and record.actual_completion_date:
                delta = record.actual_completion_date - record.submission_date
                record.resolution_time = delta.total_seconds() / 3600
            else:
                record.resolution_time = 0.0

    @api.depends("submission_date", "assigned_to")
    def _compute_processing_time(self):
        """Compute processing time"""
        for record in self:
            if record.submission_date:
                now = fields.Datetime.now()
                delta = now - record.submission_date
                record.processing_time = delta.total_seconds() / 3600
            else:
                record.processing_time = 0.0

    @api.depends("submission_date", "assigned_to")
    def _compute_wait_time(self):
        """Compute customer wait time"""
        for record in self:
            record.customer_wait_time = record.processing_time

    @api.depends("submission_date")
    def _compute_first_response_time(self):
        """Compute first response time"""
        for record in self:
            record.first_response_time = 1.5  # Default 1.5 hours

    @api.depends("resolution_time", "sla_target_hours")
    def _compute_efficiency(self):
        """Compute resolution efficiency"""
        for record in self:
            if record.sla_target_hours and record.resolution_time:
                record.resolution_efficiency = min(
                    100, (record.sla_target_hours / record.resolution_time) * 100
                )
            else:
                record.resolution_efficiency = 100.0

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
    certificate_id = fields.Many2one("naid.certificate", string="Certificate")
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
        "approval.history", "request_id", string="Approval History"
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
