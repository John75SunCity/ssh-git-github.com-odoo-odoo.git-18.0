from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class NaidComplianceActionPlan(models.Model):
    _name = 'naid.compliance.action.plan'
    _description = 'NAID Compliance Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, due_date'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    compliance_id = fields.Many2one()
    description = fields.Text()
    action_type = fields.Selection()
    priority = fields.Selection()
    due_date = fields.Date()
    start_date = fields.Date()
    completion_date = fields.Date()
    responsible_user_id = fields.Many2one()
    approval_required = fields.Boolean()
    approved_by_id = fields.Many2one()
    approval_date = fields.Date()
    status = fields.Selection()
    progress_percentage = fields.Float()
    completion_notes = fields.Text()
    impact_assessment = fields.Text()
    risk_level = fields.Selection()
    estimated_cost = fields.Monetary()
    actual_cost = fields.Monetary()
    currency_id = fields.Many2one()
    days_overdue = fields.Integer()
    is_overdue = fields.Boolean()
    estimated_hours = fields.Float()
    actual_hours = fields.Float()
    state = fields.Selection()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    today = fields.Date()
    start_date = fields.Date()
    completion_date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_days_overdue(self):
            """Compute days overdue"""

    def _compute_is_overdue(self):
            """Compute if action is overdue""":
            for record in self:
                record.is_overdue = ()
                    record.days_overdue > 0 and
                    record.status not in ['completed', 'cancelled']


        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================

    def _onchange_compliance_id(self):
            """Set default values based on compliance record"""
            if self.compliance_id:
                # Set default priority based on compliance severity
                if hasattr(self.compliance_id, 'severity'):
                    severity_priority_map = {}
                        'critical': 'urgent',
                        'major': 'high',
                        'minor': 'medium',
                        'low': 'low'

                    self.priority = severity_priority_map.get()
                        self.compliance_id.severity, 'medium'



    def _onchange_status(self):
            """Update dates based on status changes"""
            if self.status == 'in_progress' and not self.start_date:

    def action_approve(self):
            """Approve action plan"""
            self.ensure_one()
            if not self.env.user.has_group('records_management.group_records_manager'):
                raise ValidationError(_("Only managers can approve action plans"))

            self.write({)}
                "status": "approved",
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Date.today(),

            self.message_post(body=_("Action plan approved by %s", self.env.user.name))


    def action_start(self):
            """Start action plan execution"""
            self.ensure_one()
            if self.approval_required and self.status != 'approved':
                raise ValidationError(_("Action plan must be approved before starting"))

            self.write({)}
                "status": "in_progress",
                "start_date": fields.Date.today(),

            self.message_post(body=_("Action plan started by %s", self.env.user.name))


    def action_complete(self):
            """Mark action plan as completed"""
            self.ensure_one()
            if self.status != 'in_progress':
                raise ValidationError(_("Only in-progress actions can be completed"))

            self.write({)}
                "status": "completed",
                "completion_date": fields.Date.today(),
                "progress_percentage": 100.0,

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
            self.write({)}
                "status": "draft",
                "approved_by_id": False,
                "approval_date": False,
                "start_date": False,
                "completion_date": False,
                "progress_percentage": 0.0,

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
            """Send notification for overdue actions""":
            self.ensure_one()
            if self.is_overdue and self.responsible_user_id:
                template = self.env.ref()
                    'records_management.email_template_action_plan_overdue',
                    raise_if_not_found=False

                if template:
                    template.send_mail(self.id, force_send=True)
                else:
                    _logger = getattr(self, '_logger', None) or __import__('logging').getLogger(__name__)
                    _logger.warning("Email template 'records_management.email_template_action_plan_overdue' not found. Overdue notification not sent for action plan ID %s.", self.id):

    def action_check_overdue_actions(self):
            """Cron job to check and notify overdue actions"""
            overdue_actions = self.search([)]
                ('is_overdue', '=', True),
                ('status', 'not in', ['completed', 'cancelled'])


            for action in overdue_actions:
                action.write({'status': 'overdue'})
                action.send_overdue_notification()

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_progress_percentage(self):
            """Validate progress percentage is between 0 and 100"""
            for record in self:
                if record.progress_percentage < 0 or record.progress_percentage > 100:
                    raise ValidationError()
                        _("Progress percentage must be between 0 and 100")



    def _check_dates(self):
            """Validate date logic"""
            for record in self:
                if record.start_date and record.due_date:
                    if record.start_date > record.due_date:
                        raise ValidationError()
                            _("Start date cannot be after due date")


                if record.completion_date and record.start_date:
                    if record.completion_date < record.start_date:
                        raise ValidationError()
                            _("Completion date cannot be before start date")



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

    def action_get_overdue_actions(self, limit=None):
            """Get overdue action plans"""
            domain = []
                ('is_overdue', '=', True),
                ('status', 'not in', ['completed', 'cancelled'])

            return self.search(domain, limit=limit, order='days_overdue desc')


    def action_get_high_priority_actions(self, limit=None):
            """Get high priority action plans"""
            domain = []
                ('priority', 'in', ['high', 'urgent']),
                ('status', 'not in', ['completed', 'cancelled'])

            return self.search(domain, limit=limit, order='priority desc, due_date asc')


    def get_dashboard_data(self):
            """Get dashboard data for action plans""":
            company_id = self.env.company.id
            base_domain = [('company_id', '=', company_id)]

            return {}
                'total_actions': self.search_count(base_domain),
                'draft_actions': self.search_count(base_domain + [('status', '=', 'draft')]),
                'in_progress_actions': self.search_count(base_domain + [('status', '=', 'in_progress')]),
                'completed_actions': self.search_count(base_domain + [('status', '=', 'completed')]),
                'overdue_actions': self.search_count(base_domain + [('is_overdue', '=', True)]),
                'high_priority_actions': self.search_count()
                    base_domain + [('priority', 'in', ['high', 'urgent'])]

            ))))))))))))))))

