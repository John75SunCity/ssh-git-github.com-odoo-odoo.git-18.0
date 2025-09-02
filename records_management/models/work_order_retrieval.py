from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class WorkOrderRetrieval(models.Model):
    _name = 'work.order.retrieval'
    _description = 'Work Order Retrieval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Work Order', required=True, readonly=True, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # Partner and Customer Information
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string='Related Customer', related='partner_id', store=True)
    portal_request_id = fields.Many2one('portal.request', string='Portal Request', ondelete='set null')

    # Assignment and Team
    user_id = fields.Many2one('res.users', string='Assigned To', default=lambda self: self.env.user, tracking=True)
    assigned_team_id = fields.Many2one('hr.department', string='Assigned Team')
    team_leader_id = fields.Many2one('res.users', string='Team Leader')
    technician_ids = fields.Many2many('res.users', 'work_order_retrieval_technician_rel', 'work_order_id', 'user_id', string='Technicians')

    # Scheduling and Dates
    scheduled_date = fields.Datetime(string='Scheduled Start Date', tracking=True)
    start_date = fields.Datetime(string='Start Date')
    completion_date = fields.Datetime(string='Completion Date')
    estimated_duration = fields.Float(string='Estimated Duration (Hours)', help='Estimated time in hours')
    actual_duration = fields.Float(string='Actual Duration (Hours)', help='Actual time spent in hours')

    # Status and Priority
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent'),
        ('3', 'Critical')
    ], string='Priority', default='0', tracking=True)

    urgency_reason = fields.Text(string='Urgency Reason')

    # Work Order Details
    work_order_type = fields.Selection([
        ('file_retrieval', 'File Retrieval'),
        ('document_retrieval', 'Document Retrieval'),
        ('box_retrieval', 'Box Retrieval'),
        ('bulk_retrieval', 'Bulk Retrieval')
    ], string='Retrieval Type', default='file_retrieval')

    # Location and Access
    service_location_id = fields.Many2one('records.location', string='Service Location')
    customer_address = fields.Text(string='Customer Address')
    access_instructions = fields.Text(string='Access Instructions')
    access_restrictions = fields.Text(string='Access Restrictions')
    contact_person = fields.Char(string='Contact Person')
    contact_phone = fields.Char(string='Contact Phone')

    # Equipment and Vehicle
    equipment_ids = fields.Many2many('maintenance.equipment', 'work_order_retrieval_equipment_rel', 'work_order_id', 'equipment_id', string='Equipment Required')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')

    # Items to Retrieve
    item_count = fields.Integer(string='Number of Items', default=1)
    item_descriptions = fields.Text(string='Item Descriptions')
    special_instructions = fields.Text(string='Special Instructions')

    # Completion and Quality
    completion_notes = fields.Text(string='Completion Notes')
    customer_signature = fields.Binary(string='Customer Signature')
    customer_satisfaction = fields.Selection([
        ('1', 'Very Dissatisfied'),
        ('2', 'Dissatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied')
    ], string='Customer Satisfaction')

    quality_check_passed = fields.Boolean(string='Quality Check Passed', default=True)
    supervisor_approval = fields.Boolean(string='Supervisor Approval')

    # Financial
    estimated_cost = fields.Monetary(string="Estimated Cost", currency_field="currency_id")
    actual_cost = fields.Monetary(string="Actual Cost", currency_field="currency_id")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    billable = fields.Boolean(string='Billable', default=True)

    # Related Records
    coordinator_id = fields.Many2one('work.order.coordinator', string='Work Order Coordinator')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('name', 'partner_id', 'work_order_type')
    def _compute_display_name(self):
        for record in self:
            parts = [record.name or 'New']
            if record.partner_id:
                parts.append(f"({record.partner_id.name})")
            if record.work_order_type:
                type_label = dict(record._fields['work_order_type'].selection).get(record.work_order_type, '')
                parts.append(f"- {type_label}")
            record.display_name = ' '.join(parts)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('start_date', 'completion_date')
    def _check_date_sequence(self):
        for record in self:
            if record.start_date and record.completion_date:
                if record.start_date > record.completion_date:
                    raise ValidationError(_("Start date cannot be after completion date."))

    @api.constrains('estimated_duration', 'actual_duration')
    def _check_duration_positive(self):
        for record in self:
            if record.estimated_duration is not None and record.estimated_duration < 0:
                raise ValidationError(_("Estimated duration cannot be negative."))
            if record.actual_duration is not None and record.actual_duration < 0:
                raise ValidationError(_("Actual duration cannot be negative."))

    @api.constrains('item_count')
    def _check_item_count_positive(self):
        for record in self:
            if record.item_count < 0:
                raise ValidationError(_("Item count cannot be negative."))

    # ============================================================================
    # CRUD METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('work.order.retrieval') or _('New')
        return super().create(vals_list)

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name_parts = [record.name]
            if record.partner_id:
                name_parts.append(f"({record.partner_id.name})")
            if record.state != 'draft':
                state_label = dict(record._fields['state'].selection)[record.state]
                name_parts.append(f"- {state_label}")
            result.append((record.id, ' '.join(name_parts)))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enhanced search by name or customer"""
        args = args or []
        domain = []
        if name:
            domain = [
                '|', '|', '|',
                ('name', operator, name),
                ('partner_id.name', operator, name),
                ('portal_request_id.name', operator, name),
                ('contact_person', operator, name)
            ]
        ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the work order(s)"""
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft work orders can be confirmed."))
            record.state = "confirmed"
            record.message_post(body=_("Work order confirmed."))

    def action_assign(self):
        """Assign the work order to a team"""
        self.ensure_one()
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_("Only confirmed work orders can be assigned."))
            record.state = 'assigned'
            record.message_post(body=_("Work order assigned."))

    def action_start(self):
        """Start the work order"""
        for record in self:
            if record.state != 'assigned':
                raise UserError(_("Only assigned work orders can be started."))
            record.state = 'in_progress'
            record.start_date = fields.Datetime.now()
            record.message_post(body=_("Work order started."))

    def action_complete(self):
        """Complete the work order"""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_("Only in-progress work orders can be completed."))
            record.state = 'completed'
            record.completion_date = fields.Datetime.now()
            if record.start_date:
                duration = (record.completion_date - record.start_date).total_seconds() / 3600
                record.actual_duration = duration
            record.message_post(body=_("Work order completed."))

    def action_cancel(self):
        """Cancel the work order"""
        for record in self:
            if record.state == 'completed':
                raise UserError(_("Completed work orders cannot be cancelled."))
            record.state = 'cancelled'
            record.message_post(body=_("Work order cancelled."))

    def action_reset_to_draft(self):
        """Reset to draft state"""
        for record in self:
            if record.state == 'completed':
                raise UserError(_("Completed work orders cannot be reset to draft."))
            record.state = 'draft'
            record.start_date = False
            record.completion_date = False
            record.actual_duration = 0
            record.message_post(body=_("Work order reset to draft."))

    @api.model
    def get_priority_work_orders(self):
        """Get high priority work orders requiring attention"""
        return self.search([
            ('priority', 'in', ['2', '3']),
            ('state', 'in', ['confirmed', 'assigned', 'in_progress']),
        ], order='priority desc, scheduled_date asc')

    def action_bulk_confirm(self):
        """Bulk confirm selected work orders"""
        for record in self:
            if record.state == 'draft':
                record.action_confirm()

    def action_bulk_start(self):
        """Bulk start selected work orders"""
        for record in self:
            if record.state == 'assigned':
                record.action_start()
