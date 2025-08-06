# -*- coding: utf-8 -*-
# FSM Task Extensions - Field Service Management Integration

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class FsmTask(models.Model):
    """
    FSM Task model for managing field service operations, including scheduling, assignment,
    progress tracking, and integration with Odoo's mail and activity systems.
    """
    _name = "fsm.task"
    _description = "FSM Task - Field Service Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Task Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    description = fields.Text(string="Description")

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
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    deadline = fields.Date(string="Deadline")

    assigned_technician = fields.Many2one(
        "res.users", string="Assigned Technician", tracking=True
    )
    team_name = fields.Char(string="Service Team")

    # ============================================================================
    # CUSTOMER AND LOCATION
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    customer_location_id = fields.Many2one("res.partner", string="Service Location")
    customer_contact_id = fields.Many2one("res.partner", string="Customer Contact")

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
    completion_percentage = fields.Float(string="Completion %", default=0.0)
    estimated_hours = fields.Float(string="Estimated Hours")
    actual_hours = fields.Float(string="Actual Hours")

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
    estimated_cost = fields.Monetary(
        string="Estimated Cost", currency_field="currency_id"
    )
    actual_cost = fields.Monetary(string="Actual Cost", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True)

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
        string="Duration (Hours)", compute="_compute_duration", store=True
    )
    is_overdue = fields.Boolean(string="Is Overdue", compute="_compute_overdue")
    progress_status = fields.Char(
        string="Progress Status", compute="_compute_progress_status"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    related_project_task_id = fields.Many2one(
        "project.task", string="Related Project Task"
    )
    equipment_ids = fields.Many2many("maintenance.equipment", string="Equipment Used")

    # ============================================================================
    # COMPUTED METHODS
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
                record.progress_status = "Completed"
            elif record.status == "cancelled":
                record.progress_status = "Cancelled"
            else:
                record.progress_status = f"{record.completion_percentage:.0f}% Complete"

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_start_task(self):
        """Start the task"""
        self.ensure_one()
        if self.status != "scheduled":
            raise UserError("Only scheduled tasks can be started")
        self.write({"status": "in_progress", "start_date": fields.Datetime.now()})
        self.message_post(body="Task started")

    def action_complete_task(self):
        """Complete the task"""
        self.ensure_one()
        if self.status != "in_progress":
            raise UserError("Only in-progress tasks can be completed")
        self.write(
            {
                "status": "completed",
                "end_date": fields.Datetime.now(),
                "completion_percentage": 100.0,
            }
        )
        self.message_post(body="Task completed")

    def action_cancel_task(self):
        """Cancel the task"""
        self.ensure_one()
        if self.status == "completed":
            raise UserError("Cannot cancel completed tasks")
        self.write({"status": "cancelled"})
        self.message_post(body="Task cancelled")

    def action_reschedule_task(self):
        """Open reschedule wizard"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reschedule Task",
            "res_model": "fsm.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_task_id": self.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        """Validate date consistency"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise UserError("Start date cannot be after end date")

    @api.constrains("completion_percentage")
    def _check_completion_percentage(self):
        """Validate completion percentage"""
        for record in self:
            if not (0 <= record.completion_percentage <= 100):
                raise UserError("Completion percentage must be between 0 and 100")

    # ============================================================================
    # ODOO FRAMEWORK INTEGRATION
    # ============================================================================
    @api.model_create_multi
    def create(self, vals):
        """Override create for automatic task numbering"""
        if "name" not in vals or vals["name"] == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("fsm.task") or "/"
        return super().create(vals)

    def write(self, vals):
        """Override write for status change tracking"""
        if "status" in vals:
            for record in self:
                old_status = record.status
                new_status = vals["status"]
                if old_status != new_status:
                    record.message_post(
                        body=f"Status changed from {old_status} to {new_status}"
                    )
        return super().write(vals)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name}"
            if record.customer_id:
                name += f" - {record.customer_id.name}"
            if record.task_type:
                name += f" ({record.task_type})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
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
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[('res_model', '=', 'fsm.task')]
    )
    """List of mail.activity records related to this FSM task, used for scheduling and tracking activities."""

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=[('res_model', '=', 'fsm.task')]
    )
    """List of mail.followers records for this FSM task, representing users who follow updates on the task."""

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=[('res_model', '=', 'fsm.task')]
    )
    """List of mail.message records associated with this FSM task, storing all related messages and communications."""

    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    task_status = fields.Selection([('draft', 'Draft')], string='Task Status', default='draft', tracking=True)
    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (Batch 1)
    # ============================================================================
    def action_reschedule(self):
        """Reschedule - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule"),
            "res_model": "fsm.task",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_view_work_orders(self):
        """View Work Orders - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Work Orders"),
            "res_model": "fsm.task",
            "view_mode": "tree,form",
            "domain": [("task_id", "=", self.id)],
            "context": {"default_task_id": self.id},
        }