from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsDeletionRequest(models.Model):
    _name = 'records.deletion.request'
    _description = 'Records Deletion Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Request ID", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Requested By", default=lambda self: self.env.user, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'High'), ('2', 'Urgent')], string="Priority", default='0')

    # ============================================================================
    # DATES & SCHEDULING
    # ============================================================================
    request_date = fields.Date(string="Request Date", default=fields.Date.context_today, required=True, tracking=True)
    scheduled_deletion_date = fields.Date(string="Scheduled Deletion Date", tracking=True)
    actual_deletion_date = fields.Date(string="Actual Deletion Date", readonly=True, tracking=True)
    days_since_request = fields.Integer(string="Days Since Request", compute='_compute_days_since_request', store=True)

    # ============================================================================
    # ITEMS FOR DELETION
    # ============================================================================
    deletion_type = fields.Selection([
        ('container', 'Containers'),
        ('document', 'Documents'),
        ('mixed', 'Mixed'),
    ], string="Deletion Type", default='container', required=True)
    document_ids = fields.Many2many('records.document', 'deletion_request_document_rel', 'request_id', 'document_id', string="Documents to Delete")
    container_ids = fields.Many2many('records.container', 'deletion_request_container_rel', 'request_id', 'container_id', string="Containers to Delete")
    total_items_count = fields.Integer(string="Total Items", compute='_compute_total_items', store=True)

    # ============================================================================
    # DETAILS & INSTRUCTIONS
    # ============================================================================
    description = fields.Text(string="Description")
    reason = fields.Text(string="Reason for Deletion", required=True)
    notes = fields.Text(string="Internal Notes")
    special_instructions = fields.Text(string="Special Instructions")

    # ============================================================================
    # APPROVAL & COMPLIANCE
    # ============================================================================
    approved_by_id = fields.Many2one('res.users', string="Approved By", readonly=True, tracking=True)
    approval_date = fields.Datetime(string="Approval Date", readonly=True, tracking=True)
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True, tracking=True)
    legal_hold_check = fields.Boolean(string="Legal Hold Cleared", default=False)
    retention_policy_verified = fields.Boolean(string="Retention Policy Verified", default=False, tracking=True)
    customer_authorization = fields.Boolean(string="Customer Authorization Received", default=False, tracking=True)
    naid_compliant = fields.Boolean(string="NAID Compliant Process", default=True)
    chain_of_custody_id = fields.Many2one('naid.custody', string="Chain of Custody")
    certificate_of_deletion_id = fields.Many2one('shredding.certificate', string="Certificate of Deletion", readonly=True)
    can_approve = fields.Boolean(compute='_compute_can_approve', string="Can Approve")

    # ============================================================================
    # BILLING
    # ============================================================================
    billable = fields.Boolean(string="Billable", default=True)
    estimated_cost = fields.Monetary(string="Estimated Cost", tracking=True)
    actual_cost = fields.Monetary(string="Actual Cost", tracking=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.deletion.request') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals:
            self.message_post_with_view(
                'mail.message_activity_done',
                values={'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id},
                subtype_id=self.env.ref('mail.mt_activities').id,
            )
        return super().write(vals)

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('name', 'request_date', 'state')
    def _compute_display_name(self):
        for record in self:
            state_label = dict(self._fields['state'].selection).get(record.state, '')
            record.display_name = f"{record.name or ''} ({record.request_date or ''}) - {state_label}"

    @api.depends('document_ids', 'container_ids')
    def _compute_total_items(self):
        for record in self:
            record.total_items_count = len(record.document_ids) + len(record.container_ids)

    @api.depends('request_date')
    def _compute_days_since_request(self):
        today = date.today()
        for record in self:
            if record.request_date:
                record.days_since_request = (today - record.request_date).days
            else:
                record.days_since_request = 0

    def _compute_can_approve(self):
        for record in self:
            record.can_approve = self.env.user.has_group('records_management.group_records_manager')

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft requests can be submitted."))
        if not self.container_ids and not self.document_ids:
            raise UserError(_("You must select at least one container or document to delete."))
        self.write({'state': 'submitted'})
        self.message_post(body=_("Request submitted for approval."))

    def action_approve(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_("Only submitted requests can be approved."))
        if not self.can_approve:
            raise UserError(_("You do not have the necessary rights to approve this request."))
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })
        self.message_post(body=_("Request approved."))

    def action_reject(self):
        self.ensure_one()
        # This should open a wizard to ask for rejection_reason
        # For now, we'll just change the state
        if self.state not in ['submitted', 'approved']:
            raise UserError(_("Only submitted or approved requests can be rejected."))
        self.write({'state': 'rejected'})
        self.message_post(body=_("Request rejected."))

    def action_schedule(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Only approved requests can be scheduled."))
        if not self.scheduled_deletion_date:
            raise UserError(_("Please set a scheduled deletion date."))
        self.write({'state': 'scheduled'})
        self.message_post(body=_("Deletion scheduled for %s") % self.scheduled_deletion_date)

    def action_start_deletion(self):
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled requests can be started."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Deletion process started."))

    def action_complete_deletion(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress requests can be completed."))

        # Deactivate the actual records
        self.container_ids.write({'active': False, 'state': 'destroyed'})
        self.document_ids.write({'active': False, 'state': 'destroyed'})

        self.write({
            'state': 'completed',
            'actual_deletion_date': fields.Date.today()
        })
        self.message_post(body=_("Deletion process completed."))
        # Here you would typically generate the Certificate of Deletion
        # certificate = self.env['records.destruction.certificate'].create({...})
        # self.certificate_of_deletion_id = certificate.id

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['completed', 'in_progress']:
            raise UserError(_("Cannot cancel completed or in-progress deletions."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Request cancelled."))

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.state in ['completed', 'in_progress']:
            raise UserError(_("Cannot reset completed or in-progress requests."))
        self.write({'state': 'draft'})
        self.message_post(body=_("Request reset to draft."))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('scheduled_deletion_date', 'request_date')
    def _check_dates(self):
        for record in self:
            if record.scheduled_deletion_date and record.request_date and record.scheduled_deletion_date < record.request_date:
                raise ValidationError(_("Scheduled deletion date cannot be before the request date."))

    @api.constrains('estimated_cost', 'actual_cost')
    def _check_costs(self):
        for record in self:
            if record.estimated_cost < 0 or record.actual_cost < 0:
                raise ValidationError(_("Costs cannot be negative."))
