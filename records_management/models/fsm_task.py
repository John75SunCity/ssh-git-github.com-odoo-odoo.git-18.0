# -*- coding: utf-8 -*-
"""
FSM Task Extensions - Field Service Management Integration

This module provides comprehensive field service management functionality including
task scheduling, assignment, progress tracking, and integration with customer
portal workflows for the Records Management System.

BUSINESS MODEL DESIGN:
- Current Implementation: ONE TASK = ONE CUSTOMER
- DYNAMIC SERVICE ADDITIONS: Task supports adding services on-site
- Service line items can be added/modified during task execution
- For multi-customer routes, either:
  1. Create separate tasks for each customer, or
  2. Extend with fsm.task.stop model for route management

DYNAMIC WORKFLOW SCENARIOS:
1. Technician arrives for "pickup" → customer adds "shredding" → update same task
2. Route preparation → customer calls to add services → modify existing task
3. On-site discoveries → additional services needed → real-time task updates

FUTURE ENHANCEMENT OPTIONS:
- Multi-stop routes with fsm.task.stop model
- Route optimization integration
- Customer grouping by geographic area
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FsmTask(models.Model):
    """
    FSM Task Management for Field Service Operations

    Provides comprehensive task management including scheduling, assignment,
    progress tracking, and integration with Odoo's mail and activity systems.
    """

    _name = "fsm.task"
    _description = "FSM Task - Field Service Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Task Name",
        required=True,
        tracking=True,
        index=True,
        default="New",
    )
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
    active = fields.Boolean(string="Active", default=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)

    # ============================================================================
    # TASK CLASSIFICATION AND PRIORITY
    # ============================================================================
    task_type = fields.Selection(
        [
            ("pickup", "Item Pickup"),
            ("delivery", "Item Delivery"),
            ("shredding", "On-Site Shredding"),
            ("scanning", "Document Scanning"),
            ("storage", "Storage Service"),
            ("retrieval", "Item Retrieval"),
            ("maintenance", "Equipment Maintenance"),
            ("consultation", "Customer Consultation"),
        ],
        string="Task Type",
        required=True,
        tracking=True,
    )

    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Very High")],
        string="Priority",
        default="1",
        tracking=True,
    )

    status = fields.Selection(
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
    # SCHEDULING AND ASSIGNMENT
    # ============================================================================
    scheduled_date = fields.Datetime(
        string="Scheduled Date", required=True, tracking=True
    )
    start_date = fields.Datetime(string="Start Date", tracking=True)
    end_date = fields.Datetime(string="End Date", tracking=True)
    deadline = fields.Date(string="Deadline", tracking=True)
    assigned_technician_id = fields.Many2one(
        "res.users", string="Assigned Technician", tracking=True
    )
    team_name = fields.Char(string="Service Team")

    # ============================================================================
    # CUSTOMER AND LOCATION
    # NOTE: Current design is ONE TASK = ONE CUSTOMER
    # For multi-customer routes, create separate tasks or implement fsm.task.stop model
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Primary customer for this service task. For multi-customer routes, "
        "create separate tasks or extend with fsm.task.stop model.",
    )
    customer_location_id = fields.Many2one(
        "res.partner",
        string="Service Location",
        help="Specific service address (if different from customer's main address)",
    )
    customer_contact_id = fields.Many2one(
        "res.partner",
        string="Customer Contact",
        help="Primary contact person at the service location",
    )

    # ============================================================================
    # SERVICE SPECIFICATIONS
    # ============================================================================
    service_type = fields.Selection(
        [
            ("regular", "Regular Service"),
            ("emergency", "Emergency Service"),
            ("scheduled", "Scheduled Maintenance"),
            ("one_time", "One-Time Service"),
        ],
        string="Service Type",
        default="regular",
    )

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

    # ============================================================================
    # TRACKING AND PROGRESS
    # ============================================================================
    completion_percentage = fields.Float(
        string="Completion %", default=0.0, digits=(5, 2)
    )
    estimated_hours = fields.Float(string="Estimated Hours", digits=(5, 2))
    actual_hours = fields.Float(string="Actual Hours", digits=(5, 2))

    # ============================================================================
    # QUALITY AND FEEDBACK
    # ============================================================================
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

    quality_rating = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("average", "Average"),
            ("poor", "Poor"),
        ],
        string="Quality Rating",
    )

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    estimated_cost = fields.Monetary(
        string="Estimated Cost", currency_field="currency_id"
    )
    actual_cost = fields.Monetary(string="Actual Cost", currency_field="currency_id")
    invoice_status = fields.Selection(
        [("to_invoice", "To Invoice"), ("invoiced", "Invoiced"), ("paid", "Paid")],
        string="Invoice Status",
        default="to_invoice",
    )

    # ============================================================================
    # COMMUNICATION AND NOTES
    # ============================================================================
    internal_notes = fields.Text(string="Internal Notes")
    customer_notes = fields.Text(string="Customer Notes")
    completion_notes = fields.Text(string="Completion Notes")
    special_instructions = fields.Text(string="Special Instructions")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    duration_hours = fields.Float(
        string="Duration (Hours)",
        compute="_compute_duration",
        store=True,
        digits=(5, 2),
    )
    is_overdue = fields.Boolean(string="Is Overdue", compute="_compute_overdue")
    progress_status = fields.Char(
        string="Progress Status", compute="_compute_progress_status"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS - DYNAMIC SERVICE SUPPORT
    # ============================================================================
    related_project_task_id = fields.Many2one(
        "project.task", string="Related Project Task"
    )
    equipment_ids = fields.Many2many("maintenance.equipment", string="Equipment Used")

    # DYNAMIC SERVICE LINE ITEMS - Support adding services on-site
    service_line_ids = fields.One2many(
        "fsm.task.service.line",
        "task_id",
        string="Service Line Items",
        help="Services that can be added/modified during task execution",
    )

    # DYNAMIC PRICING AND BILLING
    allow_on_site_additions = fields.Boolean(
        string="Allow On-Site Service Additions",
        default=True,
        help="Technician can add services while on-site",
    )
    requires_customer_approval = fields.Boolean(
        string="Requires Customer Approval",
        default=True,
        help="Additional services need customer signature/approval",
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[("res_model", "=", "fsm.task")],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=[("res_model", "=", "fsm.task")],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=[("res_model", "=", "fsm.task")],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("start_date", "end_date")
    def _compute_duration(self):
        """Calculate task duration in hours"""
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration_hours = delta.total_seconds() / 3600.0
            else:
                record.duration_hours = 0.0

    @api.depends("deadline", "status")
    def _compute_overdue(self):
        """Check if task is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                record.deadline
                and record.deadline < today
                and record.status not in ["completed", "cancelled"]
            )

    @api.depends("completion_percentage", "status")
    def _compute_progress_status(self):
        """Generate readable progress status"""
        for record in self:
            if record.status == "completed":
                record.progress_status = _("Completed")
            elif record.status == "cancelled":
                record.progress_status = _("Cancelled")
            else:
                record.progress_status = _("%s%% Complete", f"{record.completion_percentage:.0f}")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_task(self):
        """Start the task"""
        self.ensure_one()
        if self.status != "scheduled":
            raise UserError(_("Only scheduled tasks can be started"))
        self.write({"status": "in_progress", "start_date": fields.Datetime.now()})
        self.message_post(body=_("Task started"))

    def action_complete_task(self):
        """Complete the task"""
        self.ensure_one()
        if self.status != "in_progress":
            raise UserError(_("Only in-progress tasks can be completed"))
        self.write(
            {
                "status": "completed",
                "end_date": fields.Datetime.now(),
                "completion_percentage": 100.0,
            }
        )
        self.message_post(body=_("Task completed"))

    def action_cancel_task(self):
        """Cancel the task"""
        self.ensure_one()
        if self.status == "completed":
            raise UserError(_("Cannot cancel completed tasks"))
        self.write({"status": "cancelled"})
        self.message_post(body=_("Task cancelled"))

    def action_reschedule_task(self):
        """Open reschedule wizard"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Task"),
            "res_model": "fsm.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_task_id": self.id},
        }

    def action_view_work_orders(self):
        """View related work orders"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Work Orders"),
            "res_model": "fsm.work.order",
            "view_mode": "tree,form",
            "domain": [("task_id", "=", self.id)],
            "context": {"default_task_id": self.id},
        }

    def action_add_service_on_site(self):
        """Add service while technician is on-site"""
        self.ensure_one()
        if self.status not in ["scheduled", "in_progress"]:
            raise UserError(
                _("Can only add services to scheduled or in-progress tasks")
            )

        return {
            "type": "ir.actions.act_window",
            "name": _("Add Service On-Site"),
            "res_model": "fsm.add.service.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_task_id": self.id,
                "default_customer_id": self.customer_id.id,
                "on_site_addition": True,
            },
        }

    def action_modify_service_scope(self):
        """Modify service scope during task execution"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Modify Service Scope"),
            "res_model": "fsm.task.service.line",
            "view_mode": "tree,form",
            "domain": [("task_id", "=", self.id)],
            "context": {"default_task_id": self.id},
        }

    def action_customer_approval_required(self):
        """Request customer approval for additional services"""
        self.ensure_one()
        # Send notification/email to customer for approval
        template = self.env.ref(
            "records_management.email_template_service_approval", False
        )
        if template:
            template.send_mail(self.id)
        self.message_post(body=_("Customer approval requested for additional services"))

    def _calculate_total_service_cost(self):
        """Calculate total cost including dynamically added services"""
        self.ensure_one()
        base_cost = self.estimated_cost or 0.0
        additional_cost = sum(self.service_line_ids.mapped("total_price"))
        return base_cost + additional_cost

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create for automatic task numbering"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("fsm.task") or _(
                    "New"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Override write for status change tracking"""
        if "status" in vals:
            for record in self:
                old_status = record.status
                new_status = vals["status"]
                if old_status != new_status:
                    record.message_post(
                        body=_("Status changed from %s to %s", old_status, new_status)
                    )
        return super().write(vals)

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name or _("New")
            if record.customer_id:
                name += _(" - %s", record.customer_id.name)
            if record.task_type:
                task_type_dict = dict(record._fields["task_type"].selection)
                name += _(" (%s)", task_type_dict.get(record.task_type))
            result.append((record.id, name))
        return result

    @api.model
    def _search_name(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, customer, or task type"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                "|",
                ("name", operator, name),
                ("customer_id.name", operator, name),
                ("task_type", operator, name),
                ("description", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        """Validate date consistency"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(_("Start date cannot be after end date"))

    @api.constrains("completion_percentage")
    def _check_completion_percentage(self):
        """Validate completion percentage"""
        for record in self:
            if not (0 <= record.completion_percentage <= 100):
                raise ValidationError(
                    _("Completion percentage must be between 0 and 100")
                )

    @api.constrains("estimated_hours", "actual_hours")
    def _check_hours(self):
        """Validate hour values"""
        for record in self:
            if record.estimated_hours and record.estimated_hours < 0:
                raise ValidationError(_("Estimated hours cannot be negative"))
            if record.actual_hours and record.actual_hours < 0:
                raise ValidationError(_("Actual hours cannot be negative"))

    @api.constrains("scheduled_date", "deadline")
    def _check_schedule(self):
        """Validate schedule consistency"""
        for record in self:
            if record.scheduled_date and record.deadline:
                if record.scheduled_date.date() > record.deadline:
                    raise ValidationError(_("Scheduled date cannot be after deadline"))


class FsmTaskServiceLine(models.Model):
    """
    Service Line Items for Dynamic FSM Task Updates

    Allows technicians to add services on-site or during route preparation.
    Supports real-time service scope modifications with customer approval workflows.
    """

    _name = "fsm.task.service.line"
    _description = "FSM Task Service Line Item"
    _order = "task_id, sequence"
    _rec_name = "service_name"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    task_id = fields.Many2one(
        "fsm.task", string="FSM Task", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(string="Sequence", default=10)

    service_name = fields.Char(string="Service Name", required=True)
    service_type = fields.Selection(
        [
            ("pickup", "Item Pickup"),
            ("delivery", "Item Delivery"),
            ("shredding", "On-Site Shredding"),
            ("scanning", "Document Scanning"),
            ("storage", "Storage Service"),
            ("retrieval", "Item Retrieval"),
            ("consultation", "Consultation"),
            ("additional", "Additional Service"),
        ],
        string="Service Type",
        required=True,
    )

    description = fields.Text(string="Service Description")

    # ============================================================================
    # DYNAMIC ADDITION TRACKING
    # ============================================================================
    added_on_site = fields.Boolean(string="Added On-Site", default=False)
    added_by_id = fields.Many2one("res.users", string="Added By")
    added_date = fields.Datetime(string="Added Date", default=fields.Datetime.now)

    customer_approved = fields.Boolean(string="Customer Approved", default=False)
    approval_method = fields.Selection(
        [
            ("verbal", "Verbal Approval"),
            ("signature", "Electronic Signature"),
            ("email", "Email Confirmation"),
            ("sms", "SMS Confirmation"),
        ],
        string="Approval Method",
    )

    # ============================================================================
    # PRICING FIELDS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="task_id.currency_id"
    )
    unit_price = fields.Monetary(string="Unit Price", currency_field="currency_id")
    quantity = fields.Float(string="Quantity", default=1.0, digits=(10, 2))
    total_price = fields.Monetary(
        string="Total Price",
        currency_field="currency_id",
        compute="_compute_total_price",
        store=True,
    )

    # ============================================================================
    # STATUS TRACKING
    # ============================================================================
    status = fields.Selection(
        [
            ("pending", "Pending Approval"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="pending",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("unit_price", "quantity")
    def _compute_total_price(self):
        """Calculate total price for service line"""
        for line in self:
            line.total_price = line.unit_price * line.quantity

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_request_approval(self):
        """Request customer approval for this service addition"""
        self.ensure_one()
        if self.customer_approved:
            raise UserError(_("Service already approved"))

        # Logic to send approval request
        self.write({"status": "pending"})
        self.task_id.message_post(
            body=_("Approval requested for additional service: %s", self.service_name)
        )

    def action_approve_service(self):
        """Approve the additional service"""
        self.ensure_one()
        self.write({"status": "approved", "customer_approved": True})
        self.task_id.message_post(
            body=_("Additional service approved: %s", self.service_name)
        )
        self.write({"status": "approved", "customer_approved": True})
        self.task_id.message_post(
            body=_("Additional service approved: %s", self.service_name)
        )
