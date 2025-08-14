# -*- coding: utf-8 -*-
"""
NAID Compliance Action Plan Model

Model for action plans for NAID compliance improvements.
"""

from odoo import _, api, fields, models

from odoo.exceptions import ValidationError




class NaidComplianceActionPlan(models.Model):
    """Action plans for NAID compliance improvements"""

    _name = "naid.compliance.action.plan"
    _description = "NAID Compliance Action Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, due_date"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Action Title", required=True, tracking=True,),

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ACTION RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )

    # ============================================================================
    # ACTION DETAILS
    # ============================================================================

    description = fields.Text(string="Action Description", required=True,),

    action_type = fields.Selection(
        [
            ("corrective", "Corrective Action"),
            ("preventive", "Preventive Action"),
            ("improvement", "Improvement Action"),
        ],
        string="Action Type",
        required=True,
    )

    # ============================================================================
    # PRIORITY & SCHEDULING
    # ============================================================================

    priority = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        required=True,
        default="medium",
        tracking=True,
    )

    due_date = fields.Date(string="Due Date", required=True, tracking=True,),

    start_date = fields.Date(string="Start Date"),

    completion_date = fields.Date(string="Completion Date")

    # ============================================================================
    # RESPONSIBILITY
    # ============================================================================

    responsible_user_id = fields.Many2one(
        "res.users", string="Responsible Person", required=True, tracking=True,)

    approval_required = fields.Boolean(string="Approval Required", default=False),

    approved_by_id = fields.Many2one("res.users", string="Approved By"),

    approval_date = fields.Date(string="Approval Date")

    # ============================================================================
    # STATUS TRACKING
    # ============================================================================

    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    progress_percentage = fields.Float(string="Progress %", default=0.0),

    completion_notes = fields.Text(string="Completion Notes")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        auto_join=True,
        groups="base.group_user",
    )

    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", groups="base.group_user"
    )

    message_ids = fields.One2many(

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        "mail.message", "res_id", string="Messages", groups="base.group_user"
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_approve(self):
        """Approve action plan"""

        self.ensure_one()
        self.write(
            {
                "status": "approved",
                "approved_by": self.env.user.id,
                "approval_date": fields.Date.today(),
            }
        }
        self.message_post(body=_("Action plan approved by %s", self.env.user.name))

    def action_start(self):
        """Start action plan execution"""

        self.ensure_one()
        self.write(
            {
                "status": "in_progress",
                "start_date": fields.Date.today(),
            }
        }
        self.message_post(body=_("Action plan started by %s", self.env.user.name))

    def action_complete(self):
        """Mark action plan as completed"""

        self.ensure_one()
        self.write(
            {
                "status": "completed",
                "completion_date": fields.Date.today(),
                "progress_percentage": 100.0,
            }
        }
        self.message_post(body=_("Action plan completed by %s", self.env.user.name))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("progress_percentage")
    def _check_progress_percentage(self):
        """Validate progress percentage is between 0 and 100"""
        for record in self:
            if record.progress_percentage < 0 or record.progress_percentage > 100:
                raise ValidationError(
                    _("Progress percentage must be between 0 and 100.")
                    )

    @api.constrains("due_date", "start_date")
    def _check_dates(self):
        """Validate date logic"""
        for record in self:
            if record.start_date and record.due_date:
                if record.start_date > record.due_date:
                    raise ValidationError(_("Start date cannot be after due date."))
                if record.start_date > record.due_date:
                    raise ValidationError(_("Start date cannot be after due date."))
