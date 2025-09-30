from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class NaidComplianceActionPlan(models.Model):
    _name = 'naid.compliance.action.plan'
    _description = 'NAID Compliance Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, due_date'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Action Plan Title', required=True, tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)

    # Link to the source of the action plan (e.g., an alert or checklist)
    res_model = fields.Char(string='Related Model', readonly=True)
    res_id = fields.Integer(string='Related Record ID', readonly=True)

    description = fields.Text(string='Description', required=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', required=True, tracking=True)

    due_date = fields.Date(string='Due Date', required=True, tracking=True)
    start_date = fields.Date(string='Start Date', readonly=True)
    completion_date = fields.Date(string='Completion Date', readonly=True)

    responsible_user_id = fields.Many2one(comodel_name='res.users', string='Plan Manager', required=True, tracking=True, default=lambda self: self.env.user)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    progress_percentage = fields.Float(string='Progress (%)', compute='_compute_progress_percentage', store=True)
    completion_notes = fields.Text(string='Completion Notes')

    estimated_cost = fields.Monetary(string='Estimated Cost', currency_field='currency_id')
    actual_cost = fields.Monetary(string='Actual Cost', currency_field='currency_id')
    currency_id = fields.Many2one(comodel_name='res.currency', related='company_id.currency_id', readonly=True)

    days_overdue = fields.Integer(string='Days Overdue', compute='_compute_days_overdue', store=True)
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_days_overdue', store=True)

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('due_date', 'state')
    def _compute_days_overdue(self):
        today = fields.Date.context_today(self)
        for plan in self:
            plan.is_overdue = False
            plan.days_overdue = 0
            if plan.due_date and plan.state not in ('completed', 'cancelled') and plan.due_date < today:
                plan.is_overdue = True
                plan.days_overdue = (today - plan.due_date).days

    @api.depends('state')
    def _compute_progress_percentage(self):
        for plan in self:
            if plan.state == 'completed':
                plan.progress_percentage = 100.0
            elif plan.state == 'draft':
                plan.progress_percentage = 0.0
            # For other states, progress is manual or based on related tasks (not implemented here)

    @api.constrains('start_date', 'due_date', 'completion_date')
    def _check_dates(self):
        for plan in self:
            if plan.start_date and plan.due_date and plan.start_date > plan.due_date:
                raise ValidationError(_("Start date cannot be after the due date."))
            if plan.completion_date and plan.start_date and plan.completion_date < plan.start_date:
                raise ValidationError(_("Completion date cannot be before the start date."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit_for_approval(self):
        self.write({'state': 'awaiting_approval'})
        self.message_post(body=_("Submitted for approval."))

    def action_approve(self):
        self.write({'state': 'approved'})
        self.message_post(body=_("Action plan approved by %s.", self.env.user.name))

    def action_start(self):
        self.write({
            'state': 'in_progress',
            'start_date': fields.Date.context_today(self),
        })
        self.message_post(body=_("Action plan execution started."))

    def action_complete(self):
        if any(not plan.completion_notes for plan in self):
            raise UserError(_("Please provide completion notes before marking the plan as complete."))
        self.write({
            'state': 'completed',
            'completion_date': fields.Date.context_today(self),
        })
        self.message_post(body=_("Action plan marked as complete."))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Action plan has been cancelled."))

    def action_reset_to_draft(self):
        self.write({
            'state': 'draft',
            'start_date': False,
            'completion_date': False,
        })
        self.message_post(body=_("Action plan reset to draft."))

