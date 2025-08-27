from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class NaidDestructionRecord(models.Model):
    _name = 'naid.destruction.record'
    _description = 'NAID Destruction Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'destruction_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Record Number', required=True, tracking=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)

    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    destruction_date = fields.Date(string='Destruction Date', required=True, tracking=True, index=True)
    certificate_id = fields.Many2one('naid.certificate', string='NAID Certificate', tracking=True)
    items_destroyed = fields.Integer(string='Items Destroyed', compute='_compute_items_destroyed', store=True)

    method = fields.Selection([
        ('shredding', 'Paper Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('incineration', 'Incineration'),
        ('pulping', 'Pulping'),
        ('disintegration', 'Disintegration'),
        ('other', 'Other Method')
    ], string='Destruction Method', required=True, tracking=True)

    responsible_user_id = fields.Many2one('res.users', string='Responsible Technician', required=True, tracking=True)
    notes = fields.Text(string='Destruction Notes')
    witness_ids = fields.Many2many('res.users', string='Witnesses', help='Users who witnessed the destruction process')
    destruction_item_ids = fields.One2many('destruction.item', 'destruction_record_id', string='Destruction Items')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('certified', 'Certified'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # NAID COMPLIANCE FIELDS
    # ============================================================================
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True)
    chain_of_custody_id = fields.Many2one('naid.custody', string='Chain of Custody')
    security_level = fields.Selection([
        ('level_1', 'Level 1 - Strip Cut'),
        ('level_2', 'Level 2 - Cross Cut'),
        ('level_3', 'Level 3 - Micro Cut'),
        ('level_4', 'Level 4 - High Security'),
        ('level_5', 'Level 5 - NSA/CSS'),
        ('level_6', 'Level 6 - EAL4+')
    ], string='Security Level', required=True)

    equipment_used = fields.Char(string='Equipment Used')
    temperature = fields.Float(string='Temperature (°F)', help='Temperature during destruction process')
    humidity = fields.Float(string='Humidity (%)', help='Humidity during destruction process')

    # ============================================================================
    # WEIGHT AND VOLUME TRACKING
    # ============================================================================
    total_weight = fields.Float(string='Total Weight (lbs)', compute='_compute_totals', store=True, digits=(12, 2))
    total_volume = fields.Float(string='Total Volume (CF)', compute='_compute_totals', store=True, digits=(12, 3))

    # ============================================================================
    # TIMING FIELDS
    # ============================================================================
    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)

    # ============================================================================
    # CERTIFICATION FIELDS
    # ============================================================================
    certificate_number = fields.Char(string='Certificate Number', readonly=True)
    certificate_issued_date = fields.Date(string='Certificate Issued Date')
    certificate_issued_by = fields.Many2one('res.users', string='Certificate Issued By')

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('destruction_item_ids')
    def _compute_items_destroyed(self):
        """Calculate total number of items destroyed"""
        for record in self:
            record.items_destroyed = len(record.destruction_item_ids)

    @api.depends('destruction_item_ids', 'destruction_item_ids.weight')
    def _compute_totals(self):
        """Calculate total weight"""
        for record in self:
            record.total_weight = sum(record.destruction_item_ids.mapped('weight'))
            # Note: Volume calculation removed as volume field doesn't exist in destruction.item model
            record.total_volume = 0.0  # Default value since volume field is not available

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Calculate destruction duration in hours"""
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds() / 3600
            else:
                record.duration = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_schedule_destruction(self):
        """Schedule the destruction process"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Can only schedule draft destruction records'))

        self.write({'state': 'scheduled'})
        self.message_post(body=_('Destruction scheduled for %s', self.destruction_date))

    def action_start_destruction(self):
        """Start the destruction process"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_('Can only start scheduled destructions'))

        self.write({
            'state': 'in_progress',
            'start_time': fields.Datetime.now()
        })
        self.message_post(body=_('Destruction process started'))

    def action_complete_destruction(self):
        """Complete the destruction process"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Can only complete in-progress destructions'))

        if not self.destruction_item_ids:
            raise UserError(_('Cannot complete destruction without items'))

        self.write({
            'state': 'completed',
            'end_time': fields.Datetime.now()
        })
        self.message_post(body=_('Destruction process completed'))

    def action_generate_certificate(self):
        """Generate NAID compliance certificate"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_('Can only generate certificates for completed destructions'))

        # Generate certificate number
        if not self.certificate_number:
            sequence = self.env['ir.sequence'].next_by_code('naid.certificate') or 'CERT-NEW'
            self.certificate_number = sequence

        # Create certificate record
        certificate_vals = {
            'name': self.certificate_number,
            'destruction_record_id': self.id,
            'partner_id': self.partner_id.id,
            'issue_date': fields.Date.today(),
            'issued_by': self.env.user.id,
        }

        certificate = self.env['naid.certificate'].create(certificate_vals)

        self.write({
            'state': 'certified',
            'certificate_id': certificate.id,
            'certificate_issued_date': fields.Date.today(),
            'certificate_issued_by': self.env.user.id
        })

        self.message_post(body=_('NAID Certificate generated: %s', self.certificate_number))
        return certificate

    def action_cancel_destruction(self):
        """Cancel the destruction record"""
        self.ensure_one()
        if self.state in ('completed', 'certified'):
            raise UserError(_('Cannot cancel completed or certified destructions'))

        self.write({'state': 'cancelled'})
        self.message_post(body=_('Destruction cancelled'))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('destruction_date')
    def _check_destruction_date(self):
        """Validate destruction date is not in the future"""
        for record in self:
            if record.destruction_date and record.destruction_date > fields.Date.today():
                raise ValidationError(_('Destruction date cannot be in the future'))

    @api.constrains('start_time', 'end_time')
    def _check_destruction_times(self):
        """Validate destruction timing"""
        for record in self:
            if record.start_time and record.end_time:
                if record.end_time <= record.start_time:
                    raise ValidationError(_('End time must be after start time'))

    @api.constrains('temperature', 'humidity')
    def _check_environmental_conditions(self):
        """Validate environmental conditions"""
        for record in self:
            if record.temperature and (record.temperature < -40 or record.temperature > 200):
                raise ValidationError(_('Temperature must be between -40°F and 200°F'))
            if record.humidity and (record.humidity < 0 or record.humidity > 100):
                raise ValidationError(_('Humidity must be between 0% and 100%'))

    @api.constrains('witness_ids')
    def _check_witnesses(self):
        """Validate witness requirements for high security levels"""
        for record in self:
            if record.security_level in ('level_5', 'level_6') and len(record.witness_ids) < 2:
                raise ValidationError(_('High security destruction requires at least 2 witnesses'))

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('method')
    def _onchange_method(self):
        """Set default security level based on destruction method"""
        if self.method == 'hard_drive':
            self.security_level = 'level_6'
        elif self.method == 'shredding':
            self.security_level = 'level_3'
        elif self.method in ('incineration', 'disintegration'):
            self.security_level = 'level_4'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update domain for destruction items based on customer"""
        if self.partner_id:
            return {'domain': {'destruction_item_ids': [('partner_id', '=', self.partner_id.id)]}}

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _create_audit_log(self, action):
        """Create NAID audit log entry"""
        self.env['naid.audit.log'].create({
            'name': f"Destruction {action}: {self.name}",
            'model_name': self._name,
            'record_id': self.id,
            'action': action,
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
            'details': f"Destruction record {self.name} - {action}"
        })

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence and audit log"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('naid.destruction.record') or 'DEST-NEW'

        records = super().create(vals_list)

        for record in records:
            record._create_audit_log('created')

        return records

    def write(self, vals):
        """Override write to create audit logs for state changes"""
        result = super().write(vals)

        if 'state' in vals:
            for record in self:
                record._create_audit_log(f"state_changed_to_{vals['state']}")

        return result

    def unlink(self):
        """Override unlink to prevent deletion of certified records"""
        for record in self:
            if record.state == 'certified':
                raise UserError(_('Cannot delete certified destruction records'))
            record._create_audit_log('deleted')

        return super().unlink()
