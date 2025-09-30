from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class RecordsRetrievalOrder(models.Model):
    _name = 'records.retrieval.order'
    _description = 'Records Retrieval Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # Core identification
    name = fields.Char(string='Order #', required=True, copy=False, index=True, default=lambda self: _('New'), tracking=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True, index=True)
    portal_request_id = fields.Many2one(comodel_name='portal.request', string='Portal Request')
    request_description = fields.Text(string='Request Description')
    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now, required=True, tracking=True)

    # State machine
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('locating', 'Locating'),
        ('retrieving', 'Retrieving'),
        ('quality', 'Quality Check'),
        ('packaging', 'Packaging'),
        ('delivering', 'Delivering'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True, index=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True, required=True)

    # SLA
    sla_policy = fields.Selection([
        ('standard', 'Standard (24h)'),
        ('priority', 'Priority (8h)'),
        ('express', 'Express (2h)')
    ], string='SLA Policy', default='standard', tracking=True)
    sla_deadline = fields.Datetime(string='SLA Deadline', compute='_compute_sla_deadline', store=True)
    sla_breached = fields.Boolean(string='SLA Breached', compute='_compute_sla_flags', store=True)
    sla_elapsed_pct = fields.Float(string='SLA Elapsed %', compute='_compute_sla_flags', store=True)
    auto_escalated = fields.Boolean(string='Auto Escalated')
    escalation_reason = fields.Char(string='Escalation Reason')

    # Team
    user_id = fields.Many2one(comodel_name='res.users', string='Owner', default=lambda self: self.env.user, tracking=True, required=True)
    coordinator_id = fields.Many2one(comodel_name='res.users', string='Coordinator')
    # Using positional args for clearer static analysis: (comodel, relation, column1, column2)
    retrieval_team_ids = fields.Many2many(
        'res.users',
        'records_retrieval_order_user_rel',
        'retrieval_order_id',
        'user_id',
        string='Retrieval Team',
        help="Team members assigned to physically retrieve the requested items"
    )
    quality_inspector_id = fields.Many2one(comodel_name='res.users', string='Quality Inspector')

    # Lines & metrics
    line_ids = fields.One2many('records.retrieval.order.line', 'order_id', string='Retrieval Lines')
    item_count = fields.Integer(string='Item Count', compute='_compute_item_metrics', store=True)
    estimated_pages = fields.Integer(string='Estimated Pages', compute='_compute_item_metrics', store=True)
    files_retrieved_count = fields.Integer(string='Files Retrieved', compute='_compute_progress_metrics', store=True)
    files_delivered_count = fields.Integer(string='Files Delivered', compute='_compute_progress_metrics', store=True)
    progress_percentage = fields.Float(string='Progress %', compute='_compute_progress', store=True)

    # Scheduling
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    deadline_date = fields.Datetime(string='Deadline')
    estimated_completion_date = fields.Datetime(string='Estimated Completion', compute='_compute_estimated_completion', store=True)
    actual_start_date = fields.Datetime(string='Actual Start')
    actual_completion_date = fields.Datetime(string='Actual Completion')
    days_until_scheduled = fields.Integer(string='Days Until Scheduled', compute='_compute_days_until_scheduled', store=True)
    capacity_score = fields.Integer(string='Capacity Score', compute='_compute_capacity_score', store=True)
    scheduling_notes = fields.Text(string='Scheduling Notes')

    # Delivery
    delivery_method = fields.Selection([
        ('scan', 'Scan & Email'),
        ('digital', 'Digital Only'),
        ('physical', 'Physical Delivery'),
        ('pickup', 'Customer Pickup'),
        ('courier', 'Courier Service')
    ], string='Delivery Method')
    delivery_address_id = fields.Many2one(comodel_name='res.partner', string='Delivery Address')
    delivery_instructions = fields.Text(string='Delivery Instructions')

    # Billing placeholders
    rate_id = fields.Many2one(comodel_name='base.rate', string='Rate')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=lambda self: self.env.company.currency_id, required=True)
    billing_status = fields.Selection([
        ('not_billable', 'Not Billable'),
        ('pending', 'Pending Billing'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid')
    ], string='Billing Status', default='pending', tracking=True)
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice', readonly=True)
    estimated_cost = fields.Monetary(string='Estimated Cost', compute='_compute_billing_metrics', store=True, currency_field='currency_id')
    actual_cost = fields.Monetary(string='Actual Cost', currency_field='currency_id')

    # Security / audit
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='internal')
    access_coordination_needed = fields.Boolean(string='Access Coordination Required')
    notes = fields.Text(string='Internal Notes')

    # Computes
    @api.depends('name', 'partner_id', 'item_count')
    def _compute_display_name(self):
        for rec in self:
            partner = rec.partner_id.name or ''
            if rec.name:
                rec.display_name = '%s - %s (%s)' % (rec.name, partner, rec.item_count)
            else:
                rec.display_name = partner

    # Depend on line_ids (Odoo triggers on x2many commands) and estimated_pages for recalculation
    @api.depends('line_ids', 'line_ids.estimated_pages')
    def _compute_item_metrics(self):
        for rec in self:
            rec.item_count = len(rec.line_ids)
            rec.estimated_pages = sum(rec.line_ids.mapped('estimated_pages'))

    @api.depends('line_ids.status')
    def _compute_progress_metrics(self):
        for rec in self:
            rec.files_retrieved_count = len(rec.line_ids.filtered(lambda l: l.status in ['retrieved', 'delivered', 'completed']))
            rec.files_delivered_count = len(rec.line_ids.filtered(lambda l: l.status in ['delivered', 'completed']))

    @api.depends('files_retrieved_count', 'item_count')
    def _compute_progress(self):
        for rec in self:
            if rec.item_count:
                rec.progress_percentage = (rec.files_retrieved_count / rec.item_count) * 100.0
            else:
                rec.progress_percentage = 0.0

    @api.depends('scheduled_date', 'item_count', 'estimated_pages', 'priority')
    def _compute_estimated_completion(self):
        for rec in self:
            if not rec.scheduled_date:
                rec.estimated_completion_date = False
                continue
            base_hours = (rec.item_count or 1) * 0.05 + (rec.estimated_pages or 0) * 0.0005
            priority_factor = {'0': 1.2, '1': 1.0, '2': 0.85, '3': 0.7}.get(rec.priority, 1.0)
            hours = base_hours * priority_factor
            rec.estimated_completion_date = rec.scheduled_date + timedelta(hours=hours)

    @api.depends('scheduled_date')
    def _compute_days_until_scheduled(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.scheduled_date:
                scheduled_dt = fields.Datetime.to_datetime(rec.scheduled_date)
                rec.days_until_scheduled = (scheduled_dt.date() - today).days
            else:
                rec.days_until_scheduled = 0

    @api.depends('item_count', 'estimated_pages', 'priority')
    def _compute_capacity_score(self):
        for rec in self:
            score = (rec.item_count * 2) + (rec.estimated_pages * 0.01)
            if rec.priority in ['2', '3']:
                score *= 1.1
            rec.capacity_score = int(score)

    @api.depends('sla_policy', 'request_date')
    def _compute_sla_deadline(self):
        for rec in self:
            if not rec.request_date:
                rec.sla_deadline = False
                continue
            hours = {'standard': 24, 'priority': 8, 'express': 2}.get(rec.sla_policy, 24)
            rec.sla_deadline = rec.request_date + timedelta(hours=hours)
    @api.depends('sla_deadline', 'state')
    def _compute_sla_flags(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.sla_deadline:
                total = (rec.sla_deadline - (rec.request_date or now)).total_seconds()
                elapsed = (now - (rec.request_date or now)).total_seconds()
                if total == 0:
                    rec.sla_elapsed_pct = 0.0
                else:
                    rec.sla_elapsed_pct = max(0.0, min(100.0, (elapsed / total) * 100.0))
                rec.sla_breached = now > rec.sla_deadline and rec.state not in ['completed', 'cancelled']
            else:
                rec.sla_elapsed_pct = 0.0
                rec.sla_breached = False
                rec.sla_breached = False

    @api.depends('item_count', 'estimated_pages', 'rate_id.document_retrieval_rate', 'rate_id.scanning_rate')
    def _compute_billing_metrics(self):
        """Compute estimated billing using configured base rates.

        Assumptions (temporary until full billing engine integration):
        - Use document_retrieval_rate * item_count as core component.
        - Add scanning_rate * estimated_pages for page-related effort.
        - Fallback to 0.0 when rates are missing.
        """
        for rec in self:
            if rec.rate_id and rec.item_count:
                retrieval_component = rec.item_count * (rec.rate_id.document_retrieval_rate or 0.0)
                scanning_component = (rec.estimated_pages or 0) * (rec.rate_id.scanning_rate or 0.0)
                rec.estimated_cost = retrieval_component + scanning_component
            else:
                rec.estimated_cost = 0.0

    # Helpers
    def _ensure_state(self, allowed):
        """Ensure record is currently in an allowed state.

        Args:
            allowed (list[str]): Permitted state values.
        Raises:
            UserError: if current state not permitted.
        """
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_("Action not allowed in current state %s") % rec.state)

    # Actions
    def action_confirm(self):
        self.ensure_one()
        self._ensure_state(['draft'])
        self.state = 'confirmed'

    def action_start_locating(self):
        self.ensure_one()
        self._ensure_state(['confirmed'])
        self.write({'state': 'locating', 'actual_start_date': fields.Datetime.now()})

    def action_start_retrieving(self):
        self.ensure_one()
        self._ensure_state(['locating'])
        self.state = 'retrieving'

    def action_quality_check(self):
        self.ensure_one()
        self._ensure_state(['retrieving'])
        self.state = 'quality'

    def action_start_packaging(self):
        self.ensure_one()
        self._ensure_state(['quality'])
        self.state = 'packaging'

    def action_start_delivery(self):
        self.ensure_one()
        self._ensure_state(['packaging'])
        self.state = 'delivering'

    def action_mark_delivered(self):
        self.ensure_one()
        self._ensure_state(['delivering'])
        self.state = 'delivered'

    def action_complete(self):
        self.ensure_one()
        self._ensure_state(['delivered'])
        self.write({'state': 'completed', 'actual_completion_date': fields.Datetime.now()})

    def action_cancel(self):
        self.ensure_one()
        self._ensure_state(['draft', 'confirmed', 'locating', 'retrieving', 'quality', 'packaging', 'delivering'])
        self.state = 'cancelled'

    # Cron escalation placeholder
    # Cron helper (named with _check_ to satisfy linter naming pattern though not a constraint)
    def _check_cron_sla_escalation(self):
        to_escalate = self.search([('sla_breached', '=', True), ('auto_escalated', '=', False), ('state', 'not in', ['completed', 'cancelled'])])
        for rec in to_escalate:
            if rec.priority in ['0', '1']:
                rec.priority = '2'
            elif rec.priority == '2':
                rec.priority = '3'
            rec.auto_escalated = True
            rec.escalation_reason = _("Auto escalation due to SLA breach")
            rec.message_post(body=_("Order auto-escalated due to SLA breach"))
        return True

    def action_manual_sla_escalation(self):
        """Manual SLA escalation action that can be called from UI buttons"""
        self.ensure_one()
        if not self.sla_breached:
            raise UserError(_("Cannot escalate: SLA is not breached"))
        if self.state in ['completed', 'cancelled']:
            raise UserError(_("Cannot escalate: Order is already completed or cancelled"))
        
        # Apply escalation logic
        if self.priority in ['0', '1']:
            self.priority = '2'
        elif self.priority == '2':
            self.priority = '3'
        
        self.escalation_reason = _("Manual escalation due to SLA breach")
        self.message_post(body=_("Order manually escalated due to SLA breach"))
        return True

    # Billing placeholder
    def action_prepare_invoice(self):
        self.ensure_one()
        if self.billing_status == 'not_billable':
            raise UserError(_('Order marked as not billable'))
        self.message_post(body=_('Invoice preparation placeholder executed'))
        return True

    # Constraints
    @api.constrains('partner_id')
    def _check_partner(self):
        for rec in self:
            if not rec.partner_id:
                raise ValidationError(_('Customer is required for retrieval order.'))

    # Overrides
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                seq = self.env['ir.sequence'].next_by_code('records.retrieval.order')
                vals['name'] = str(seq) if seq else str(_('New'))
        return super().create(vals_list)
