# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class PortalRequest(models.Model):
    _name = "portal.request"
    _description = "Portal Customer Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, create_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Request #", required=True, tracking=True, index=True)
    reference = fields.Char(string="Reference", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # Framework Required Fields
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

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & REQUEST DETAILS
    # ============================================================================

    # Customer Information
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)
    customer_name = fields.Char(string="Customer Name", related="partner_id.name", store=True)
    contact_person = fields.Many2one("res.partner", string="Contact Person")
    contact_email = fields.Char(string="Contact Email")
    contact_phone = fields.Char(string="Contact Phone")

    # Request Classification
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

    category = fields.Selection(
        [
            ("urgent", "Urgent"),
            ("standard", "Standard"),
            ("bulk", "Bulk Operation"),
            ("scheduled", "Scheduled"),
        ],
        string="Category",
        default="standard",
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="medium",
        tracking=True,
    )

    # ============================================================================
    # REQUEST CONTENT & DETAILS
    # ============================================================================

    # Request Details
    request_details = fields.Text(string="Request Details", required=True)
    special_instructions = fields.Text(string="Special Instructions")
    internal_notes = fields.Text(string="Internal Notes")
    resolution_notes = fields.Text(string="Resolution Notes")

    # Document Management
    document_description = fields.Text(string="Document Description")
    document_location = fields.Char(string="Document Location")
    document_count = fields.Integer(string="Document Count", default=0)
    
    # Service Details
    service_location = fields.Text(string="Service Location")
    estimated_volume = fields.Float(string="Estimated Volume", digits=(8, 2))
    
    # Missing fields from gap analysis
    to_person = fields.Char(string="To Person")
    upload_date = fields.Datetime(string="Upload Date")
    uploaded_by = fields.Many2one("res.users", string="Uploaded By")
    variance = fields.Float(string="Variance", digits=(5, 2))

    # ============================================================================
    # DATES & SCHEDULING
    # ============================================================================

    # Request Dates
    request_date = fields.Datetime(
        string="Request Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )
    
    due_date = fields.Datetime(string="Due Date", tracking=True)
    scheduled_date = fields.Datetime(string="Scheduled Date", tracking=True)
    completion_date = fields.Datetime(string="Completion Date", tracking=True)

    # SLA Management
    sla_deadline = fields.Datetime(
        string="SLA Deadline",
        compute="_compute_sla_metrics",
        store=True,
    )
    
    sla_status = fields.Selection(
        [
            ("on_time", "On Time"),
            ("at_risk", "At Risk"),
            ("overdue", "Overdue"),
        ],
        string="SLA Status",
        compute="_compute_sla_metrics",
        store=True,
    )

    # Time Tracking
    processing_time = fields.Float(
        string="Processing Time (Hours)",
        compute="_compute_time_metrics",
        store=True,
    )
    
    response_time = fields.Float(
        string="Response Time (Hours)",
        compute="_compute_time_metrics",
        store=True,
    )

    # ============================================================================
    # APPROVAL & WORKFLOW
    # ============================================================================

    # Approval Process
    requires_approval = fields.Boolean(string="Requires Approval", default=False)
    approved = fields.Boolean(string="Approved", default=False, tracking=True)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Datetime(string="Approval Date")
    rejection_reason = fields.Text(string="Rejection Reason")

    # E-Signature Integration
    signature_required = fields.Boolean(string="Signature Required", default=False)
    signature_completed = fields.Boolean(string="Signature Completed", default=False)
    signed_document_id = fields.Many2one("signed.document", string="Signed Document")

    # Workflow Automation
    auto_assign = fields.Boolean(string="Auto Assign", default=True)
    auto_notify = fields.Boolean(string="Auto Notify", default=True)

    # ============================================================================
    # COSTS & BILLING
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Cost Information
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
    )
    
    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
    )
    
    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        compute="_compute_total_amount",
        store=True,
    )

    # Billing Status
    is_billable = fields.Boolean(string="Billable", default=True)
    invoiced = fields.Boolean(string="Invoiced", default=False)
    invoice_id = fields.Many2one("account.move", string="Invoice")

    # ============================================================================
    # ATTACHMENTS & DOCUMENTATION
    # ============================================================================

    # File Attachments
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")
    attachment_count = fields.Integer(
        string="Attachment Count",
        compute="_compute_attachment_count",
    )

    # Documentation
    supporting_documents = fields.Text(string="Supporting Documents")
    reference_documents = fields.Text(string="Reference Documents")

    # ============================================================================
    # COMMUNICATION & NOTIFICATIONS
    # ============================================================================

    # Communication Tracking
    communication_method = fields.Selection(
        [
            ("portal", "Customer Portal"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("in_person", "In Person"),
        ],
        string="Communication Method",
        default="portal",
    )

    # Notification Settings
    notify_customer = fields.Boolean(string="Notify Customer", default=True)
    customer_notified = fields.Boolean(string="Customer Notified", default=False)
    notification_sent_date = fields.Datetime(string="Notification Sent Date")

    # Follow-up
    requires_followup = fields.Boolean(string="Requires Follow-up", default=False)
    followup_date = fields.Date(string="Follow-up Date")
    followup_completed = fields.Boolean(string="Follow-up Completed", default=False)

    # ============================================================================
    # QUALITY & SATISFACTION
    # ============================================================================

    # Quality Control
    quality_check_required = fields.Boolean(string="Quality Check Required", default=False)
    quality_approved = fields.Boolean(string="Quality Approved", default=False)
    quality_notes = fields.Text(string="Quality Notes")

    # Customer Satisfaction
    customer_rating = fields.Selection(
        [
            ("1", "1 - Very Poor"),
            ("2", "2 - Poor"),
            ("3", "3 - Average"),
            ("4", "4 - Good"),
            ("5", "5 - Excellent"),
        ],
        string="Customer Rating",
    )
    
    customer_feedback = fields.Text(string="Customer Feedback")
    satisfaction_survey_sent = fields.Boolean(string="Survey Sent", default=False)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Records
    portal_feedback_id = fields.Many2one("portal.feedback", string="Related Feedback")
    work_order_id = fields.Many2one("work.order", string="Work Order")
    pickup_request_id = fields.Many2one("pickup.request", string="Pickup Request")
    project_task_id = fields.Many2one("project.task", string="Related Task")

    # Document References
    document_ids = fields.Many2many(
        "records.document",
        string="Related Documents",
    )
    
    box_ids = fields.Many2many(
        "records.box",
        string="Related Boxes",
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        """Compute number of attachments"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.depends("request_type", "priority", "request_date")
    def _compute_sla_metrics(self):
        """Compute SLA deadline and status"""
        for record in self:
            if not record.request_date:
                record.sla_deadline = False
                record.sla_status = "on_time"
                continue

            # Set SLA based on request type and priority
            hours = 24  # Default 24 hours
            if record.priority == "urgent":
                hours = 4
            elif record.priority == "high":
                hours = 8
            elif record.request_type in ["document_retrieval", "pickup_request"]:
                hours = 48

            record.sla_deadline = record.request_date + timedelta(hours=hours)

            # Determine SLA status
            now = fields.Datetime.now()
            if record.completion_date:
                # Request completed
                if record.completion_date <= record.sla_deadline:
                    record.sla_status = "on_time"
                else:
                    record.sla_status = "overdue"
            else:
                # Request in progress
                time_remaining = (record.sla_deadline - now).total_seconds() / 3600
                if time_remaining > 2:  # More than 2 hours remaining
                    record.sla_status = "on_time"
                elif time_remaining > 0:  # Less than 2 hours but not overdue
                    record.sla_status = "at_risk"
                else:  # Past deadline
                    record.sla_status = "overdue"

    @api.depends("request_date", "completion_date", "state")
    def _compute_time_metrics(self):
        """Compute processing and response time metrics"""
        for record in self:
            if record.request_date:
                now = fields.Datetime.now()
                end_time = record.completion_date or now

                # Processing time (total time from request to completion)
                delta = end_time - record.request_date
                record.processing_time = delta.total_seconds() / 3600

                # Response time (time to first response/action)
                if record.state in ["under_review", "approved", "in_progress", "completed"]:
                    # Estimate first response as state change (simplified)
                    record.response_time = 2.0  # Default 2 hours response time
                else:
                    record.response_time = 0.0
            else:
                record.processing_time = 0.0
                record.response_time = 0.0

    @api.depends("estimated_cost", "actual_cost")
    def _compute_total_amount(self):
        """Compute total amount for billing"""
        for record in self:
            record.total_amount = record.actual_cost or record.estimated_cost or 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_submit_request(self):
        """Submit the request for processing"""
        self.ensure_one()
        if not self.request_details:
            raise UserError(_("Please provide request details before submitting."))
        
        self.write({
            "state": "submitted",
            "request_date": fields.Datetime.now(),
        })
        
        # Auto-assign if enabled
        if self.auto_assign:
            self._auto_assign_request()
        
        # Send notifications
        if self.auto_notify:
            self._send_submission_notification()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Request Submitted"),
                "message": _("Your request has been submitted successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_approve_request(self):
        """Approve the request"""
        self.ensure_one()
        self.write({
            "state": "approved",
            "approved": True,
            "approved_by": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        })
        
        # Notify customer of approval
        self._send_approval_notification()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Request Approved"),
                "message": _("Request has been approved successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_reject_request(self):
        """Reject the request with reason"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Request"),
            "res_model": "portal.request.rejection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_request_id": self.id},
        }

    def action_start_processing(self):
        """Start processing the request"""
        self.ensure_one()
        self.write({"state": "in_progress"})
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Processing Started"),
                "message": _("Request processing has been initiated."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_complete_request(self):
        """Complete the request"""
        self.ensure_one()
        if not self.resolution_notes:
            raise UserError(_("Please enter resolution notes before completing."))
        
        self.write({
            "state": "completed",
            "completion_date": fields.Datetime.now(),
        })
        
        # Send completion notification
        self._send_completion_notification()
        
        # Send satisfaction survey
        if not self.satisfaction_survey_sent:
            self._send_satisfaction_survey()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Request Completed"),
                "message": _("Request has been completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_create_work_order(self):
        """Create work order from request"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Work Order"),
            "res_model": "work.order",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"Work Order - {self.name}",
                "default_partner_id": self.partner_id.id,
                "default_request_id": self.id,
                "default_description": self.request_details,
            },
        }

    def action_view_attachments(self):
        """View request attachments"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
        }

    def action_create_invoice(self):
        """Create invoice for billable request"""
        self.ensure_one()
        if not self.is_billable:
            raise UserError(_("This request is not billable."))
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_move_type": "out_invoice",
                "default_ref": self.name,
            },
        }

    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================

    def _auto_assign_request(self):
        """Auto-assign request based on type and priority"""
        for record in self:
            if record.request_type == "billing_inquiry":
                # Assign to billing team
                billing_user = self.env.ref("records_management.user_billing", False)
                if billing_user:
                    record.user_id = billing_user
            elif record.priority == "urgent":
                # Assign to manager
                manager = self.env.ref("records_management.user_manager", False)
                if manager:
                    record.user_id = manager

    def _send_submission_notification(self):
        """Send notification when request is submitted"""
        for record in self:
            template = self.env.ref("records_management.mail_template_request_submission", False)
            if template and record.partner_id.email:
                template.send_mail(record.id, force_send=True)

    def _send_approval_notification(self):
        """Send notification when request is approved"""
        for record in self:
            template = self.env.ref("records_management.mail_template_request_approval", False)
            if template and record.partner_id.email:
                template.send_mail(record.id, force_send=True)

    def _send_completion_notification(self):
        """Send notification when request is completed"""
        for record in self:
            template = self.env.ref("records_management.mail_template_request_completion", False)
            if template and record.partner_id.email:
                template.send_mail(record.id, force_send=True)
                record.customer_notified = True
                record.notification_sent_date = fields.Datetime.now()

    def _send_satisfaction_survey(self):
        """Send customer satisfaction survey"""
        for record in self:
            survey_template = self.env.ref("records_management.mail_template_satisfaction_survey", False)
            if survey_template and record.partner_id.email:
                survey_template.send_mail(record.id, force_send=True)
                record.satisfaction_survey_sent = True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("request_date", "due_date", "completion_date")
    def _check_date_sequence(self):
        """Ensure dates are in logical sequence"""
        for record in self:
            if record.request_date and record.due_date:
                if record.due_date < record.request_date:
                    raise ValidationError(_("Due date cannot be before request date."))
            
            if record.request_date and record.completion_date:
                if record.completion_date < record.request_date:
                    raise ValidationError(_("Completion date cannot be before request date."))

    @api.constrains("estimated_cost", "actual_cost")
    def _check_positive_costs(self):
        """Ensure costs are positive"""
        for record in self:
            if record.estimated_cost and record.estimated_cost < 0:
                raise ValidationError(_("Estimated cost must be positive."))
            if record.actual_cost and record.actual_cost < 0:
                raise ValidationError(_("Actual cost must be positive."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals):
        """Override create to set defaults and generate sequence"""
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("portal.request") or _("New")
        
        # Set contact information from partner if not provided
        if vals.get("partner_id") and not vals.get("contact_email"):
            partner = self.env["res.partner"].browse(vals["partner_id"])
            vals["contact_email"] = partner.email
            vals["contact_phone"] = partner.phone
        
        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Request status changed from %s to %s") % (old_state, new_state)
                )
        
        return super().write(vals)
