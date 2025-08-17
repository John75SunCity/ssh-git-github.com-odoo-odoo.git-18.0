from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ShreddingServiceLog(models.Model):
    _name = 'shredding.service.log'
    _description = 'Shredding Service Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    partner_id = fields.Many2one()
    state = fields.Selection()
    date_created = fields.Datetime()
    date_modified = fields.Datetime()
    duration_minutes = fields.Float()
    shredding_service_id = fields.Many2one()
    operator_id = fields.Many2one()
    equipment_id = fields.Many2one()
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    weight_processed = fields.Float()
    container_count = fields.Integer()
    quality_check_passed = fields.Boolean()
    witness_present = fields.Boolean()
    witness_name = fields.Char()
    witness_signature = fields.Binary()
    notes = fields.Text()
    operational_notes = fields.Text()
    issues_encountered = fields.Text()
    display_name = fields.Char()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    end_time = fields.Datetime()
    date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name."""
            for record in self:
                if record.shredding_service_id:
                    record.display_name = (record.name or '') + ' - ' + (record.shredding_service_id.name or '')
                else:
                    record.display_name = record.name or _('New Shredding Log')


    def _compute_duration_minutes(self):
            """Compute operation duration in minutes"""
            for record in self:
                if record.start_time and record.end_time:
                    duration = record.end_time - record.start_time
                    record.duration_minutes = duration.total_seconds() / 60
                else:
                    record.duration_minutes = 0.0

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_activate(self):
            """Activate the log entry."""

            self.ensure_one()
            if self.state == 'active':
                return  # Already active

            self.write({'state': 'active'})
            self.message_post(body=_("Log entry activated"))


    def action_deactivate(self):
            """Deactivate the log entry."""

            self.ensure_one()
            if self.state == 'inactive':
                return  # Already inactive

            self.write({'state': 'inactive'})
            self.message_post(body=_("Log entry deactivated"))


    def action_archive(self):
            """Archive the log entry."""

            self.ensure_one()
            if self.state == 'archived':
                return  # Already archived

            self.write({'state': 'archived', 'active': False})
            self.message_post(body=_("Log entry archived"))


    def action_complete_operation(self):
            """Mark the operation as complete"""

            self.ensure_one()
            if not self.start_time:
                raise UserError(_("Please set start time before completing operation"))

            if not self.end_time:

    def action_record_witness_signature(self):
            """Open wizard to record witness signature"""

            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Record Witness Signature'),
                'res_model': 'witness.signature.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_log_id': self.id}


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_operation_summary(self):
            """Get operation summary for reporting""":
            self.ensure_one()
            return {}
                'name': self.name,
                'operator': self.operator_id.name if self.operator_id else None,:
                'start_time': self.start_time,
                'end_time': self.end_time,
                'duration_minutes': self.duration_minutes,
                'weight_processed': self.weight_processed,
                'container_count': self.container_count,
                'quality_passed': self.quality_check_passed,
                'witness_present': self.witness_present,



    def create_naid_audit_entry(self):
            """Create NAID compliance audit entry"""
            self.ensure_one()
            if self.env.get('naid.audit.log'):
                self.env['naid.audit.log').create({]}
                    'event_type': 'shredding_operation',
                    'model_name': self._name,
                    'record_id': self.id,
                    'description': "Shredding operation logged: %s" % self.name,
                    'operator_id': self.operator_id.id if self.operator_id else None,:
                    'timestamp': fields.Datetime.now(),
                    'weight_processed': self.weight_processed,
                    'witness_present': self.witness_present,


        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to set default values and audit trail."""
            for vals in vals_list:
                if not vals.get('name') or vals['name'] == 'New':
                    vals['name'] = self.env['ir.sequence'].next_by_code('shredding.service.log') or _('New Log')

    def write(self, vals):
            """Override write to update modification date and audit trail."""

    def _check_time_sequence(self):
            """Validate that end time is after start time"""
            for record in self:
                if record.start_time and record.end_time:
                    if record.end_time <= record.start_time:
                        raise ValidationError(_("End time must be after start time"))


    def _check_weight_processed(self):
            """Validate weight processed is positive"""
            for record in self:
                if record.weight_processed < 0:
                    raise ValidationError(_("Weight processed cannot be negative"))


    def _check_container_count(self):
            """Validate container count is positive"""
            for record in self:
                if record.container_count < 0:
                    raise ValidationError(_("Container count cannot be negative"))

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_daily_summary(self, date=None):
            """Get summary of operations for a specific date""":
            if not date:

    def toggle_active(self):
            """Toggle active state"""
            for record in self:
                if record.active:
                    record.action_deactivate()
                else:
                    record.action_activate()
