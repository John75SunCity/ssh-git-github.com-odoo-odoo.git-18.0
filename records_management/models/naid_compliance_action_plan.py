# -*- coding: utf-8 -*-
"""
NAID Compliance Action Plan Model

Model for action plans for NAID compliance improvements with comprehensive
tracking, approval workflows, and audit trail capabilities.

Note:
- The `status` field tracks the business workflow state of the action plan (e.g., draft, approved, in progress, completed, etc.).
- The `state` field is used for technical record lifecycle management (e.g., draft, active, inactive, archived).
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NaidComplianceActionPlan(models.Model):
    """Action plans for NAID compliance improvements"""

    _name = "naid.compliance.action.plan"
    _description = "NAID Compliance Action Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, due_date"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Action Title",
        required=True,
        tracking=True,
        index=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # ACTION RELATIONSHIPS
    # ============================================================================
    compliance_id = fields.Many2one(
        "naid.compliance",
        string="Compliance Record",
        required=True,
        ondelete="cascade"
    )

    # ============================================================================
    # ACTION DETAILS
    # ============================================================================
    description = fields.Text(
        string="Action Description",
        required=True,
        help="Detailed description of the action to be taken"
    )
    action_type = fields.Selection([
        ("corrective", "Corrective Action"),
        ("preventive", "Preventive Action"),
        ("improvement", "Improvement Action"),
        ("training", "Training Action"),
        ("documentation", "Documentation Update"),
        ("process_change", "Process Change"),
    ], string="Action Type", required=True, tracking=True)

    # ============================================================================
    # PRIORITY & SCHEDULING
    # ============================================================================
    priority = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent")
    ], string="Priority", required=True, default="medium", tracking=True)

    due_date = fields.Date(
        string="Due Date",
        required=True,
        tracking=True
    )
    start_date = fields.Date(
        string="Start Date",
        tracking=True
    )
    completion_date = fields.Date(
        string="Completion Date",
        tracking=True
    )

    # ============================================================================
    # RESPONSIBILITY & APPROVAL
    # ============================================================================
    responsible_user_id = fields.Many2one(
        "res.users",
        string="Responsible Person",
        required=True,
        tracking=True
    )
    approval_required = fields.Boolean(
        string="Approval Required",
        default=False,
        help="Check if this action plan requires management approval"
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True
    )
    approval_date = fields.Date(
        string="Approval Date",
        tracking=True
    )

    # ============================================================================
    # STATUS TRACKING
    # ============================================================================
    status = fields.Selection([
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("overdue", "Overdue"),
    ], 
        string="Status",
        help="Business workflow state of the action plan (e.g., draft, approved, in progress, completed, etc.)",
        default="draft",
        tracking=True,
        required=True
    )

    progress_percentage = fields.Float(
        string="Progress %",
        default=0.0,
        help="Completion percentage (0-100)"
    )
    completion_notes = fields.Text(
        string="Completion Notes",
        help="Notes about the completion of this action"
    )

    # ============================================================================
    # IMPACT AND RISK ASSESSMENT
    # ============================================================================
    impact_assessment = fields.Text(
        string="Impact Assessment",
        help="Assessment of the impact this action will have on compliance"
    )
    risk_level = fields.Selection([
        ("low", "Low Risk"),
        ("medium", "Medium Risk"),
        ("high", "High Risk"),
        ("critical", "Critical Risk")
    ], string="Risk Level", default="medium")

    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        help="Estimated cost to implement this action"
    )
    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        help="Actual cost of implementing this action"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================================
    # TRACKING AND METRICS
    # ============================================================================
    days_overdue = fields.Integer(
        string="Days Overdue",
        compute="_compute_days_overdue",
        store=True,
        help="Number of days this action is overdue"
    )
    is_overdue = fields.Boolean(
        string="Is Overdue",
        compute="_compute_is_overdue",
        store=True
    )
    estimated_hours = fields.Float(
        string="Estimated Hours",
        help="Estimated hours to complete this action"
    )
    actual_hours = fields.Float(
        string="Actual Hours",
        help="Actual hours spent on this action"
    )

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ],
        string='Record Status',
        help="Technical record lifecycle state (e.g., draft, active, inactive, archived). Not to be confused with the business workflow `status` field.",
        default='draft',
        tracking=True,
        required=True,
        index=True
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    # The following fields are inherited from mail.thread and do not need to be redefined:
    # activity_ids, message_follower_ids, message_ids
    # If you want to explicitly define activity_ids, uncomment and adjust as needed:
    # activity_ids = fields.One2many(
    #     "mail.activity",
    #     "res_id",
    #     string="Activities",
    #     domain=lambda self: [("res_model", "=", self._name)]
    # )
    # message_follower_ids = fields.One2many(
    #     "mail.followers",
    #     "res_id",
    #     string="Followers",
    #     domain=lambda self: [("res_model", "=", self._name)]
    # )
    # message_ids = fields.One2many(
    #     "mail.message",
    #     "res_id",
    #     string="Messages",
    #     domain=lambda self: [("model", "=", self._name)]
    # )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("due_date", "status")
    def _compute_days_overdue(self):
        """Compute days overdue"""
        today = fields.Date.today()
        for record in self:
            if record.due_date and record.status not in ['completed', 'cancelled']:
                if today > record.due_date:
                    delta = today - record.due_date
                    record.days_overdue = delta.days
                else:
                    record.days_overdue = 0
            else:
                record.days_overdue = 0

    @api.depends("due_date", "status")
    def _compute_is_overdue(self):
        """Compute if action is overdue"""
        for record in self:
            record.is_overdue = (
                record.days_overdue > 0 and
                record.status not in ['completed', 'cancelled']
            )

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("compliance_id")
    def _onchange_compliance_id(self):
        """Set default values based on compliance record"""
        if self.compliance_id:
            # Set default priority based on compliance severity
            if hasattr(self.compliance_id, 'severity'):
                severity_priority_map = {
                    'critical': 'urgent',
                    'major': 'high',
                    'minor': 'medium',
                    'low': 'low'
                }
                self.priority = severity_priority_map.get(
                    self.compliance_id.severity, 'medium'
                )

    @api.onchange("status")
    def _onchange_status(self):
        """Update dates based on status changes"""
        if self.status == 'in_progress' and not self.start_date:
            self.start_date = fields.Date.today()
        elif self.status == 'completed' and not self.completion_date:
            self.completion_date = fields.Date.today()
            self.progress_percentage = 100.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve(self):
        """Approve action plan"""
        self.ensure_one()
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise ValidationError(_("Only managers can approve action plans"))

        self.write({
            "status": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Date.today(),
        })
        self.message_post(body=_("Action plan approved by %s", self.env.user.name))

    def action_start(self):
        """Start action plan execution"""
        self.ensure_one()
        if self.approval_required and self.status != 'approved':
            raise ValidationError(_("Action plan must be approved before starting"))

        self.write({
            "status": "in_progress",
            "start_date": fields.Date.today(),
        })
        self.message_post(body=_("Action plan started by %s", self.env.user.name))

    def action_complete(self):
        """Mark action plan as completed"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise ValidationError(_("Only in-progress actions can be completed"))

        self.write({
            "status": "completed",
            "completion_date": fields.Date.today(),
            "progress_percentage": 100.0,
        })
        self.message_post(body=_("Action plan completed by %s", self.env.user.name))

        # Update related compliance record
        if self.compliance_id:
            self.compliance_id._check_action_plan_completion()

    def action_cancel(self):
        """Cancel action plan"""
        self.ensure_one()
        self.write({"status": "cancelled"})
        self.message_post(body=_("Action plan cancelled by %s", self.env.user.name))

    def action_reset_to_draft(self):
        """Reset action plan to draft"""
        self.ensure_one()
        self.write({
            "status": "draft",
            "approved_by_id": False,
            "approval_date": False,
            "start_date": False,
            "completion_date": False,
            "progress_percentage": 0.0,
        })
        self.message_post(body=_("Action plan reset to draft by %s", self.env.user.name))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def update_progress(self, percentage, notes=None):
        """Update progress percentage and add notes"""
        self.ensure_one()
        vals = {"progress_percentage": percentage}
        if notes:
            vals["completion_notes"] = notes

        self.write(vals)

        message = _("Progress updated to %s%%", percentage)
        if notes:
            message += _(" - Notes: %s", notes)

        self.message_post(body=message)

    def send_overdue_notification(self):
        """Send notification for overdue actions"""
        self.ensure_one()
        if self.is_overdue and self.responsible_user_id:
            template = self.env.ref(
                'records_management.email_template_action_plan_overdue',
                raise_if_not_found=False
            )
            if template:
                template.send_mail(self.id, force_send=True)
            else:
                _logger = getattr(self, '_logger', None) or __import__('logging').getLogger(__name__)
                _logger.warning("Email template 'records_management.email_template_action_plan_overdue' not found. Overdue notification not sent for action plan ID %s.", self.id)

    @api.model
    def action_check_overdue_actions(self):
        """Cron job to check and notify overdue actions"""
        overdue_actions = self.search([
            ('is_overdue', '=', True),
            ('status', 'not in', ['completed', 'cancelled'])
        ])

        for action in overdue_actions:
            action.write({'status': 'overdue'})
            action.send_overdue_notification()

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("progress_percentage")
    def _check_progress_percentage(self):
        """Validate progress percentage is between 0 and 100"""
        for record in self:
            if record.progress_percentage < 0 or record.progress_percentage > 100:
                raise ValidationError(
                    _("Progress percentage must be between 0 and 100")
                )

    @api.constrains("due_date", "start_date")
    def _check_dates(self):
        """Validate date logic"""
        for record in self:
            if record.start_date and record.due_date:
                if record.start_date > record.due_date:
                    raise ValidationError(
                        _("Start date cannot be after due date")
                    )

            if record.completion_date and record.start_date:
                if record.completion_date < record.start_date:
                    raise ValidationError(
                        _("Completion date cannot be before start date")
                    )

    @api.constrains("estimated_cost", "actual_cost")
    def _check_costs(self):
        """Validate cost values"""
        for record in self:
            if record.estimated_cost < 0:
                raise ValidationError(_("Estimated cost cannot be negative"))
            if record.actual_cost < 0:
                raise ValidationError(_("Actual cost cannot be negative"))

    # ============================================================================
    # SEARCH AND FILTER METHODS
    # ============================================================================
    @api.model
    def action_get_overdue_actions(self, limit=None):
        """Get overdue action plans"""
        domain = [
            ('is_overdue', '=', True),
            ('status', 'not in', ['completed', 'cancelled'])
        ]
        return self.search(domain, limit=limit, order='days_overdue desc')

    @api.model
    def action_get_high_priority_actions(self, limit=None):
        """Get high priority action plans"""
        domain = [
            ('priority', 'in', ['high', 'urgent']),
            ('status', 'not in', ['completed', 'cancelled'])
        ]
        return self.search(domain, limit=limit, order='priority desc, due_date asc')

    @api.model
    def get_dashboard_data(self):
        """Get dashboard data for action plans"""
        company_id = self.env.company.id
        base_domain = [('company_id', '=', company_id)]

        return {
            'total_actions': self.search_count(base_domain),
            'draft_actions': self.search_count(base_domain + [('status', '=', 'draft')]),
            'in_progress_actions': self.search_count(base_domain + [('status', '=', 'in_progress')]),
            'completed_actions': self.search_count(base_domain + [('status', '=', 'completed')]),
            'overdue_actions': self.search_count(base_domain + [('is_overdue', '=', True)]),
            'high_priority_actions': self.search_count(
                base_domain + [('priority', 'in', ['high', 'urgent'])]
            ),
        }