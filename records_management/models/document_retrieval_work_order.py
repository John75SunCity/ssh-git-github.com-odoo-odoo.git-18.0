# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class DocumentRetrievalWorkOrder(models.Model):
    _name = "document.retrieval.work.order"
    _description = "Document Retrieval Work Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, create_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Work Order #", required=True, tracking=True, index=True)
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
        string="Assigned Technician",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
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
    customer_phone = fields.Char(string="Phone", related="partner_id.phone", store=True)
    customer_email = fields.Char(string="Email", related="partner_id.email", store=True)

    # Request Classification
    request_type = fields.Selection(
        [
            ("retrieval", "Document Retrieval"),
            ("inspection", "Document Inspection"),
            ("copy", "Document Copying"),
            ("scan", "Document Scanning"),
            ("urgent", "Urgent Retrieval"),
        ],
        string="Request Type",
        required=True,
        tracking=True,
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

    urgency_reason = fields.Text(string="Urgency Reason")

    # ============================================================================
    # DOCUMENT & LOCATION DETAILS
    # ============================================================================

    # Document Information
    document_id = fields.Many2one("records.document", string="Document", tracking=True)
    document_type = fields.Char(string="Document Type")
    document_description = fields.Text(string="Document Description")
    box_id = fields.Many2one("records.container", string="Storage Box", tracking=True)
    
    # Location Information
    location_id = fields.Many2one("records.location", string="Storage Location", tracking=True)
    current_location = fields.Char(string="Current Location")
    retrieval_location = fields.Char(string="Retrieval Location")
    
    # Item Details
    item_type = fields.Selection(
        [
            ("document", "Document"),
            ("file", "File"),
            ("box", "Box"),
            ("folder", "Folder"),
        ],
        string="Item Type",
        default="document",
    )
    
    item_count = fields.Integer(string="Item Count", default=1)
    estimated_volume = fields.Float(string="Estimated Volume (cubic ft)", digits=(8, 2))

    # ============================================================================
    # SCHEDULING & TIMING
    # ============================================================================

    # Scheduling
    requested_date = fields.Datetime(
        string="Requested Date",
        required=True,
        tracking=True,
    )
    scheduled_date = fields.Datetime(string="Scheduled Date", tracking=True)
    start_date = fields.Datetime(string="Start Date", tracking=True)
    completion_date = fields.Datetime(string="Completion Date", tracking=True)
    deadline = fields.Datetime(string="Deadline", tracking=True)

    # Time Tracking
    estimated_hours = fields.Float(string="Estimated Hours", digits=(5, 2))
    actual_hours = fields.Float(string="Actual Hours", digits=(5, 2))
    
    # Computed Time Metrics
    processing_time = fields.Float(
        string="Processing Time (Hours)",
        compute="_compute_processing_metrics",
        store=True,
    )
    
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_overdue_status",
        store=True,
    )

    # ============================================================================
    # WORK ORDER EXECUTION
    # ============================================================================

    # Work Instructions
    work_instructions = fields.Text(string="Work Instructions")
    special_requirements = fields.Text(string="Special Requirements")
    safety_notes = fields.Text(string="Safety Notes")
    
    # Execution Details
    technician_notes = fields.Text(string="Technician Notes")
    completion_notes = fields.Text(string="Completion Notes")
    quality_check_notes = fields.Text(string="Quality Check Notes")

    # Quality Control
    quality_approved = fields.Boolean(string="Quality Approved", default=False)
    quality_approved_by = fields.Many2one("res.users", string="Quality Approved By")
    quality_approval_date = fields.Datetime(string="Quality Approval Date")

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
    billable_amount = fields.Monetary(
        string="Billable Amount",
        currency_field="currency_id",
    )

    # Billing Status
    is_billable = fields.Boolean(string="Billable", default=True)
    invoiced = fields.Boolean(string="Invoiced", default=False)
    invoice_id = fields.Many2one("account.move", string="Invoice")

    # ============================================================================
    # EQUIPMENT & RESOURCES
    # ============================================================================

    # Equipment Requirements
    equipment_required = fields.Text(string="Equipment Required")
    vehicle_required = fields.Boolean(string="Vehicle Required", default=False)
    vehicle_id = fields.Many2one("records.vehicle", string="Assigned Vehicle")
    
    # Tools and Supplies
    tools_required = fields.Text(string="Tools Required")
    supplies_needed = fields.Text(string="Supplies Needed")

    # Team Assignment
    team_members = fields.Many2many(
        "res.users",
        "work_order_team_rel",
        "work_order_id",
        "user_id",
        string="Team Members",
    )

    # ============================================================================
    # CUSTOMER INTERACTION
    # ============================================================================

    # Communication
    customer_contacted = fields.Boolean(string="Customer Contacted", default=False)
    contact_method = fields.Selection(
        [
            ("phone", "Phone"),
            ("email", "Email"),
            ("portal", "Customer Portal"),
            ("in_person", "In Person"),
        ],
        string="Contact Method",
    )
    
    # Approval & Authorization
    customer_approval_required = fields.Boolean(string="Customer Approval Required", default=False)
    customer_approved = fields.Boolean(string="Customer Approved", default=False)
    approval_notes = fields.Text(string="Approval Notes")

    # Delivery Information
    delivery_method = fields.Selection(
        [
            ("pickup", "Customer Pickup"),
            ("delivery", "Delivery"),
            ("mail", "Mail"),
            ("email", "Email"),
            ("portal", "Portal Access"),
        ],
        string="Delivery Method",
        default="pickup",
    )
    
    delivery_address = fields.Text(string="Delivery Address")
    delivery_instructions = fields.Text(string="Delivery Instructions")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Records
    portal_request_id = fields.Many2one("portal.request", string="Portal Request")
    retrieval_items_ids = fields.One2many(
        "document.retrieval.item",
        "work_order_id",
        string="Retrieval Items",
    )
    
    # Project Integration
    project_id = fields.Many2one("project.project", string="Project")
    task_id = fields.Many2one("project.task", string="Related Task")

    # Chain of Custody
    custody_log_ids = fields.One2many(
        "records.chain.of.custody",
        "work_order_id",
        string="Chain of Custody",
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

    @api.depends("start_date", "completion_date")
    def _compute_processing_metrics(self):
        """Compute processing time metrics"""
        for record in self:
            if record.start_date and record.completion_date:
                delta = record.completion_date - record.start_date
                record.processing_time = delta.total_seconds() / 3600
            else:
                record.processing_time = 0.0

    @api.depends("deadline", "state")
    def _compute_overdue_status(self):
        """Compute if work order is overdue"""
        now = fields.Datetime.now()
        for record in self:
            record.is_overdue = (
                record.deadline 
                and record.deadline < now 
                and record.state not in ["completed", "cancelled"]
            )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_schedule(self):
        """Schedule the work order"""
        self.ensure_one()
        if not self.scheduled_date:
            raise UserError(_("Please set a scheduled date before scheduling."))
        
        self.write({
            "state": "scheduled",
        })
        
        # Create calendar event for technician
        self._create_calendar_event()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Work Order Scheduled"),
                "message": _("Work order has been scheduled successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_start_work(self):
        """Start work on the order"""
        self.ensure_one()
        self.write({
            "state": "in_progress",
            "start_date": fields.Datetime.now(),
        })
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Work Started"),
                "message": _("Work order execution has begun."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_complete_work(self):
        """Complete the work order"""
        self.ensure_one()
        if not self.completion_notes:
            raise UserError(_("Please enter completion notes before completing."))
        
        self.write({
            "state": "completed",
            "completion_date": fields.Datetime.now(),
        })
        
        # Notify customer of completion
        self._notify_customer_completion()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Work Completed"),
                "message": _("Work order has been completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_quality_check(self):
        """Perform quality check"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Check"),
            "res_model": "quality.check.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_work_order_id": self.id,
            },
        }

    def action_view_retrieval_items(self):
        """View retrieval items"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Retrieval Items"),
            "res_model": "document.retrieval.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("work_order_id", "=", self.id)],
        }

    def action_create_invoice(self):
        """Create invoice for work order"""
        self.ensure_one()
        if not self.is_billable:
            raise UserError(_("This work order is not billable."))
        
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

    def _create_calendar_event(self):
        """Create calendar event for scheduled work"""
        for record in self:
            if record.scheduled_date and record.user_id:
                self.env["calendar.event"].create({
                    "name": f"Work Order: {record.name}",
                    "description": f"Document retrieval work order for {record.partner_id.name}",
                    "start": record.scheduled_date,
                    "stop": record.scheduled_date + timedelta(hours=record.estimated_hours or 2),
                    "user_id": record.user_id.id,
                    "partner_ids": [(6, 0, [record.partner_id.id])],
                })

    def _notify_customer_completion(self):
        """Notify customer of work order completion"""
        for record in self:
            if record.partner_id.email:
                template = self.env.ref("records_management.mail_template_work_order_completion", False)
                if template:
                    template.send_mail(record.id, force_send=True)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("requested_date", "scheduled_date", "deadline")
    def _check_date_sequence(self):
        """Ensure dates are in logical sequence"""
        for record in self:
            if record.requested_date and record.scheduled_date:
                if record.scheduled_date < record.requested_date:
                    raise ValidationError(_("Scheduled date cannot be before requested date."))
            
            if record.scheduled_date and record.deadline:
                if record.deadline < record.scheduled_date:
                    raise ValidationError(_("Deadline cannot be before scheduled date."))

    @api.constrains("estimated_hours", "actual_hours")
    def _check_hours_positive(self):
        """Ensure hours are positive"""
        for record in self:
            if record.estimated_hours and record.estimated_hours <= 0:
                raise ValidationError(_("Estimated hours must be positive."))
            if record.actual_hours and record.actual_hours < 0:
                raise ValidationError(_("Actual hours cannot be negative."))

    @api.constrains("item_count")
    def _check_item_count_positive(self):
        """Ensure item count is positive"""
        for record in self:
            if record.item_count and record.item_count <= 0:
                raise ValidationError(_("Item count must be positive."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals):
        """Override create to set defaults and generate sequence"""
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("document.retrieval.work.order") or _("New")
        
        # Set default deadline if not provided
        if not vals.get("deadline") and vals.get("requested_date"):
            requested = fields.Datetime.from_string(vals["requested_date"])
            vals["deadline"] = requested + timedelta(days=7)  # Default 7-day deadline
        
        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Work order status changed from %s to %s") % (old_state, new_state)
                )
        
        return super().write(vals)
