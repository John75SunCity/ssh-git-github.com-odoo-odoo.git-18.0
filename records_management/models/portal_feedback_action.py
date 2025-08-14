# -*- coding: utf-8 -*-
"""
Portal Feedback Action Model
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PortalFeedbackAction(models.Model):
    _name = "portal.feedback.action"
    _description = "Portal Feedback Action"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "feedback_id, priority desc, due_date"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Action Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    
    user_id = fields.Many2one(
        "res.users", 
        string="User", 
        default=lambda self: self.env.user, 
        tracking=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="feedback_id.partner_id",
        store=True,
        help="Associated partner for this record"
    )
    
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ACTION TRACKING
    # ============================================================================
    feedback_id = fields.Many2one(
        "portal.feedback",
        string="Feedback",
        required=True,
        ondelete="cascade",
        index=True
    )
    
    description = fields.Text(string="Action Description")
    action_type = fields.Selection([
        ("training", "Training"),
        ("process_improvement", "Process Improvement"),
        ("system_enhancement", "System Enhancement"),
        ("policy_update", "Policy Update"),
        ("communication", "Communication"),
        ("follow_up", "Follow-up")
    ],
        string="Action Type",
        required=True,
        tracking=True
    )
    
    assigned_to_id = fields.Many2one(
        "res.users", 
        string="Assigned To", 
        required=True, 
        tracking=True
    )
    due_date = fields.Date(string="Due Date", required=True, tracking=True)
    priority = fields.Selection([
        ("low", "Low"), 
        ("medium", "Medium"), 
        ("high", "High"), 
        ("urgent", "Urgent")
    ],
        string="Priority",
        default="medium",
        tracking=True
    )
    
    status = fields.Selection([
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled")
    ],
        string="Status",
        default="not_started",
        tracking=True
    )
    
    completion_date = fields.Date(string="Completion Date", tracking=True)
    completion_notes = fields.Text(string="Completion Notes")

    # ============================================================================
    # TIME TRACKING
    # ============================================================================
    estimated_hours = fields.Float(string="Estimated Hours", digits=(8, 2))
    actual_hours = fields.Float(string="Actual Hours", digits=(8, 2))

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    is_overdue = fields.Boolean(
        string="Is Overdue",
        compute="_compute_is_overdue",
        help="True if action is past due date and not completed"
    )
    
    days_remaining = fields.Integer(
        string="Days Remaining",
        compute="_compute_days_remaining",
        help="Days remaining until due date"
    )
    
    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived')
    ], 
        string='Status', 
        default='draft', 
        tracking=True, 
        required=True, 
        index=True,
        help='Current status of the record'
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("due_date", "status")
    def _compute_is_overdue(self):
        """Check if action is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                record.due_date
                and record.due_date < today
                and record.status not in ["completed", "cancelled"]
            )

    @api.depends("due_date")
    def _compute_days_remaining(self):
        """Calculate days remaining until due date"""
        today = fields.Date.today()
        for record in self:
            if record.due_date:
                delta = record.due_date - today
                record.days_remaining = delta.days
            else:
                record.days_remaining = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start(self):
        """Start working on the action"""
        self.ensure_one()
        if self.status != "not_started":
            raise UserError(_("Can only start actions that haven't been started yet."))

        self.write({"status": "in_progress"})
        self.message_post(
            body=_("Action has been started."), message_type="notification"
        )

    def action_complete(self):
        """Mark action as completed"""
        self.ensure_one()
        if self.status == "completed":
            raise UserError(_("Action is already completed."))

        self.write({"status": "completed", "completion_date": fields.Date.today()})
        self.message_post(
            body=_("Action has been completed."), message_type="notification"
        )

    def action_cancel(self):
        """Cancel the action"""
        self.ensure_one()
        if self.status == "completed":
            raise UserError(_("Cannot cancel a completed action."))

        self.write({"status": "cancelled"})
        self.message_post(
            body=_("Action has been cancelled."), message_type="notification"
        )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("estimated_hours", "actual_hours")
    def _check_hours(self):
        """Validate hour fields"""
        for record in self:
            if record.estimated_hours < 0:
                raise ValidationError(_("Estimated hours cannot be negative."))
            if record.actual_hours < 0:
                raise ValidationError(_("Actual hours cannot be negative."))

    @api.constrains("due_date")
    def _check_due_date(self):
        """Validate due date is not in the past for new actions"""
        for record in self:
            if (
                record.due_date
                and record.due_date < fields.Date.today()
                and record.status == "not_started"
            ):
                raise ValidationError(
                    _("Due date cannot be in the past for new actions.")
                )