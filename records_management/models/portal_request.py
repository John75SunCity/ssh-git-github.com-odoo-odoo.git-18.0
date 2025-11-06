from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PortalRequest(models.Model):
    _name = 'portal.request'
    _inherit = ['portal.request', 'mail.thread', 'mail.activity.mixin']
    _description = 'Portal Customer Request'
    _order = 'priority desc, create_date desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string='Request #', required=True, copy=False, readonly=True, default=lambda self: "New")
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned To', tracking=True)
    # Contextual label disambiguation (Batch 2)
    description = fields.Html(string='Request Details', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    request_type = fields.Selection([
        ('destruction', 'Destruction'),
        ('pickup', 'Pickup'),
        ('retrieval', 'File Retrieval'),
        ('shredding', 'Shredding Service'),
        ('audit', 'Audit Request'),
        ('consultation', 'Consultation'),
        ('other', 'Other'),
    ], string='Request Type', required=True, default='other', tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', tracking=True)

    # ============================================================================
    # DATE & TIME TRACKING
    # ============================================================================
    requested_date = fields.Datetime(string='Requested Date', readonly=True)
    deadline = fields.Datetime(string='Deadline', tracking=True)
    completion_date = fields.Datetime(string='Completion Date', readonly=True)
    estimated_hours = fields.Float(string='Estimated Hours', tracking=True)
    actual_hours = fields.Float(string='Actual Hours', readonly=True)
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_is_overdue', store=True)

    # --------------------------------------------------------------------------
    # VIRTUAL / SEARCH OPTIMIZATION FIELDS (Dynamic date domain refactor)
    # --------------------------------------------------------------------------
    requested_last_7d = fields.Boolean(
        string='Requested Last 7 Days',
        compute='_compute_requested_period_flags',
        search='_search_requested_last_7d',
        help='Indicates the request was created (requested) within the past 7 days.'
    )
    requested_last_30d = fields.Boolean(
        string='Requested Last 30 Days',
        compute='_compute_requested_period_flags',
        search='_search_requested_last_30d',
        help='Indicates the request was created (requested) within the past 30 days.'
    )

    # ============================================================================
    # BILLING & COST
    # ============================================================================
    currency_id = fields.Many2one(comodel_name='res.currency', related='company_id.currency_id', string='Currency')
    estimated_cost = fields.Monetary(string='Estimated Cost', currency_field='currency_id', tracking=True)
    actual_cost = fields.Monetary(string='Actual Cost', currency_field='currency_id', readonly=True)
    billing_status = fields.Selection([
        ('not_billable', 'Not Billable'),
        ('to_bill', 'To Bill'),
        ('billed', 'Billed'),
    ], string='Billing Status', default='not_billable', tracking=True)

    # ============================================================================
    # COMPLIANCE & SIGNATURES (NAID AAA)
    # ============================================================================
    requires_naid_compliance = fields.Boolean(string='NAID Compliance Required')
    customer_signature = fields.Binary(string='Customer Signature', copy=False)
    customer_signature_date = fields.Datetime(string='Customer Signature Date', readonly=True)
    technician_signature = fields.Binary(string='Technician Signature', copy=False)
    technician_signature_date = fields.Datetime(string='Technician Signature Date', readonly=True)
    certificate_of_destruction_id = fields.Many2one(comodel_name='ir.attachment', string='Certificate of Destruction', readonly=True)

    # ============================================================================
    # RELATIONAL & COMPUTED FIELDS
    # ============================================================================
    work_order_id = fields.Many2one(comodel_name='project.task', string='Work Order', readonly=True)
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service',
        help='Selected shredding service for this request'
    )
    assigned_operator_id = fields.Many2one(
        'naid.operator.certification',
        string='Assigned Operator',
        help='NAID certified operator assigned to this service request'
    )
    retrieval_items = fields.Text(
        string='Retrieval Items JSON',
        help='JSON data containing retrieval item details (containers, documents, files)'
    )

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('deadline', 'requested_date')
    def _check_deadline_dates(self):
        for record in self:
            if record.deadline and record.requested_date and record.deadline < record.requested_date:
                raise ValidationError(_("Deadline cannot be before the requested date."))

    @api.constrains('estimated_cost', 'actual_cost')
    def _check_cost_values(self):
        for record in self:
            if (record.estimated_cost and record.estimated_cost < 0) or (record.actual_cost and record.actual_cost < 0):
                raise ValidationError(_("Costs cannot be negative."))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        for record in self:
            record.is_overdue = (
                record.deadline and
                record.deadline < fields.Datetime.now() and
                record.state not in ('completed', 'cancelled', 'rejected')
            )

    @api.depends('requested_date')
    def _compute_requested_period_flags(self):
        """Compute recency flags for requested_date to remove Python arithmetic from view domains."""
        today = fields.Date.context_today(self)
        # Define date thresholds
        from datetime import timedelta as _td
        last_7 = today - _td(days=7)
        last_30 = today - _td(days=30)
        for rec in self:
            rd = rec.requested_date.date() if rec.requested_date else None
            rec.requested_last_7d = bool(rd and rd >= last_7)
            rec.requested_last_30d = bool(rd and rd >= last_30)

    # ------------------------------------------------------------------
    # SEARCH HELPERS
    # ------------------------------------------------------------------
    def _search_requested_last_7d(self, operator, value):
        truthy = {True, '1', 1, 'true', 'True'}
        today = fields.Date.context_today(self)
        from datetime import timedelta as _td
        last_7 = today - _td(days=7)
        if operator in ('=', '==') and value in truthy:
            return [('requested_date', '>=', fields.Datetime.to_datetime(str(last_7) + ' 00:00:00'))]
        if operator in ('!=', '<>') and value in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_7) + ' 00:00:00'))]
        if operator in ('=', '==') and value not in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_7) + ' 00:00:00'))]
        return [('id', '!=', 0)]

    def _search_requested_last_30d(self, operator, value):
        truthy = {True, '1', 1, 'true', 'True'}
        today = fields.Date.context_today(self)
        from datetime import timedelta as _td
        last_30 = today - _td(days=30)
        if operator in ('=', '==') and value in truthy:
            return [('requested_date', '>=', fields.Datetime.to_datetime(str(last_30) + ' 00:00:00'))]
        if operator in ('!=', '<>') and value in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_30) + ' 00:00:00'))]
        if operator in ('=', '==') and value not in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_30) + ' 00:00:00'))]
        return [('id', '!=', 0)]

    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name), ('res_id', '=', record.id)
            ])

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('portal.request') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        self.ensure_one()
        self.write({'state': 'submitted', 'requested_date': fields.Datetime.now()})
        self.message_post(body=_("Request submitted by %s.", self.env.user.name))
        return True

    def action_approve(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_("Only submitted requests can be approved."))
        self.write({'state': 'approved'})
        self.message_post(body=_("Request approved by %s.", self.env.user.name))
        self._create_work_order()
        return True

    def action_reject(self):
        # This would typically open a wizard to ask for a rejection reason
        self.ensure_one()
        self.write({'state': 'rejected'})
        self.message_post(body=_("Request rejected by %s.", self.env.user.name))
        return True

    def action_start_progress(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Only approved requests can be started."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Work has started on this request."))

    def action_complete(self):
        self.ensure_one()
        self.write({'state': 'completed', 'completion_date': fields.Datetime.now()})
        self.message_post(body=_("Request has been completed."))

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['completed']:
            raise UserError(_("Completed requests cannot be cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Request has been cancelled."))

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Attachments'),
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    def _create_work_order(self):
        """Create an FSM task for service-type requests."""
        self.ensure_one()
        if self.request_type in ['destruction', 'pickup', 'retrieval', 'shredding'] and not self.work_order_id:
            fsm_project = self.env.ref('industry_fsm.fsm_project', raise_if_not_found=False)
            if not fsm_project:
                raise UserError(_("FSM Project not found. Please ensure the Field Service module is installed correctly."))

            task_vals = {
                "name": _("Request: %s", self.name),
                "project_id": fsm_project.id,
                "partner_id": self.partner_id.id,
                "user_ids": [(6, 0, [self.user_id.id])] if self.user_id else [],
                "date_deadline": self.deadline.date() if self.deadline else fields.Date.today(),
                "description": self.description,
            }
            task = self.env['project.task'].create(task_vals)
            self.work_order_id = task.id
            self.message_post(body=_("Work Order %s created.", task.name))
