from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class ShreddingServiceLog(models.Model):
    _name = 'shredding.service.log'
    _description = 'Shredding Service Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_time desc, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Log Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Logged By', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # RELATIONSHIPS & CONTEXT
    # ============================================================================
    shredding_service_id = fields.Many2one('project.task', string="Shredding Service", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Customer", related='shredding_service_id.partner_id', store=True, readonly=True)
    operator_id = fields.Many2one('res.users', string="Operator", tracking=True)
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment", tracking=True)

    # ============================================================================
    # TIMING & PERFORMANCE
    # ============================================================================
    start_time = fields.Datetime(string="Start Time", tracking=True)
    end_time = fields.Datetime(string="End Time", tracking=True)
    duration_minutes = fields.Float(string="Duration (minutes)", compute='_compute_duration_minutes', store=True)
    weight_processed = fields.Float(string="Weight Processed (kg)", tracking=True)
    container_count = fields.Integer(string="Container Count", tracking=True)

    # ============================================================================
    # COMPLIANCE & VERIFICATION
    # ============================================================================
    quality_check_passed = fields.Boolean(string="Quality Check Passed")
    witness_present = fields.Boolean(string="Witness Present")
    witness_name = fields.Char(string="Witness Name")
    witness_signature = fields.Binary(string="Witness Signature", attachment=True)
    notes = fields.Text(string="Internal Notes")
    issues_encountered = fields.Text(string="Issues Encountered")

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.service.log') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('skip_audit'):
            return super().write(vals)

        res = super().write(vals)
        for log in self:
            log._create_naid_audit_entry(f"Log updated. Fields changed: {', '.join(vals.keys())}")
        return res

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('start_time', 'end_time')
    def _compute_duration_minutes(self):
        for record in self:
            if record.start_time and record.end_time:
                duration = record.end_time - record.start_time
                record.duration_minutes = duration.total_seconds() / 60.0
            else:
                record.duration_minutes = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_operation(self):
        self.ensure_one()
        self.write({'state': 'in_progress', 'start_time': fields.Datetime.now()})
        self.message_post(body=_("Shredding operation started."))

    def action_complete_operation(self):
        self.ensure_one()
        if not self.start_time:
            raise UserError(_("Please set the start time before completing the operation."))
        self.write({'state': 'completed', 'end_time': fields.Datetime.now()})
        self.message_post(body=_("Shredding operation completed."))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Log entry has been cancelled."))

    def action_reset_to_draft(self):
        self.write({'state': 'draft', 'start_time': False, 'end_time': False})
        self.message_post(body=_("Log entry reset to draft."))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('start_time', 'end_time')
    def _check_time_sequence(self):
        for record in self:
            if record.start_time and record.end_time and record.end_time < record.start_time:
                raise ValidationError(_("End time must be after start time."))

    @api.constrains('weight_processed', 'container_count')
    def _check_positive_values(self):
        for record in self:
            if record.weight_processed < 0:
                raise ValidationError(_("Weight processed cannot be negative."))
            if record.container_count < 0:
                raise ValidationError(_("Container count cannot be negative."))

    # ============================================================================
    # HELPER & PRIVATE METHODS
    # ============================================================================
    def _create_naid_audit_entry(self, description):
        """Create a NAID compliance audit entry for the log."""
        self.ensure_one()
        if 'naid.audit.log' not in self.env:
            return

        self.env['naid.audit.log'].create({
            'event_type': 'shredding_operation',
            'model_name': self._name,
            'record_id': self.id,
            'description': description,
            'operator_id': self.operator_id.id,
            'timestamp': fields.Datetime.now(),
            'weight_processed': self.weight_processed,
            'witness_present': self.witness_present,
        })
