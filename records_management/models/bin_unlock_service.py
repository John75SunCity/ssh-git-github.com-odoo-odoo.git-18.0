from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BinUnlockService(models.Model):
    _name = 'bin.unlock.service'
    _description = 'Bin Unlock Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # IDENTITY
    # ============================================================================
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        default=lambda self: "New Unlock Service",
        tracking=True,
    )
    service_number = fields.Char(string='Service Number', copy=False, tracking=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )

    user_id = fields.Many2one(
        'res.users',
        string='Service Technician',
        default=lambda self: self.env.user,
        tracking=True
    )

    # ============================================================================
    # WORKFLOW AND STATUS
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    service_type = fields.Selection([
        ('standard', 'Standard Unlock'),
        ('emergency', 'Emergency Unlock'),
        ('maintenance', 'Maintenance Access'),
        ('audit', 'Audit Access')
    ], string='Service Type', default='standard', required=True, tracking=True)

    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )

    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    completion_date = fields.Datetime(string='Completion Date', readonly=True, tracking=True)
    service_start_time = fields.Datetime(string='Service Start Time', readonly=True, tracking=True)

    # ============================================================================
    # CUSTOMER AND BIN INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    bin_id = fields.Many2one(
        'shred.bin',
        string='Bin',
        required=True,
        domain="[('partner_id', '=', partner_id)]",
        help="The physical bin to be unlocked"
    )
    key_id = fields.Many2one(comodel_name='bin.key', string='Key Used', help="The key used for the unlock operation")
    bin_location = fields.Char(string='Bin Location', related='bin_id.customer_location', readonly=True)
    key_serial_number = fields.Char(string='Key Serial Number', related='key_id.key_code', readonly=True)

    # ============================================================================
    # OPERATIONAL DETAILS
    # ============================================================================
    unlock_method = fields.Selection([
        ('physical_key', 'Physical Key'),
        ('electronic_code', 'Electronic Code'),
        ('master_override', 'Master Override'),
        ('forced_entry', 'Forced Entry')
    ], string='Unlock Method', tracking=True)

    assigned_technician_id = fields.Many2one(
        'hr.employee',
        string='Assigned Technician',
        tracking=True,
        help="Technician responsible for the service"
    )
    backup_technician_id = fields.Many2one(comodel_name='hr.employee', string='Backup Technician')

    estimated_duration = fields.Float(string='Estimated Duration (hours)', digits=(4, 2))
    actual_duration = fields.Float(
        string='Actual Duration (hours)',
        compute='_compute_service_duration',
        store=True,
        digits=(4, 2),
        help="Calculated duration from start to completion"
    )

    reason_for_unlock = fields.Text(string='Reason for Unlock', required=True)
    special_instructions = fields.Text(string='Special Instructions')

    # ============================================================================
    # SECURITY AND COMPLIANCE
    # ============================================================================
    security_notes = fields.Text(string='Security Notes')
    requires_escort = fields.Boolean(string='Requires Escort', default=False)
    witness_required = fields.Boolean(string='Witness Required', default=False)
    witness_name = fields.Char(string='Witness Name')
    authorization_code = fields.Char(string='Authorization Code', copy=False)
    naid_compliant = fields.Boolean(string="NAID Compliant", default=True)

    # ============================================================================
    # DOCUMENTATION AND REPORTING
    # ============================================================================
    service_report = fields.Text(string='Service Report')
    completion_notes = fields.Text(string='Completion Notes')
    photo_before = fields.Binary(string='Photo Before', attachment=True)
    photo_after = fields.Binary(string='Photo After', attachment=True)
    service_certificate = fields.Binary(string='Service Certificate', readonly=True, copy=False)

    # ============================================================================
    # BILLING INFORMATION
    # ============================================================================
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True
    )
    service_cost = fields.Monetary(string='Service Cost', tracking=True, currency_field='currency_id')
    emergency_surcharge = fields.Monetary(string='Emergency Surcharge', tracking=True, currency_field='currency_id')
    total_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        tracking=True,
        currency_field='currency_id'
    )
    service_rate = fields.Float(string='Service Rate (per hour)')
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice', readonly=True, copy=False)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    related_request_ids = fields.Many2many(
        'portal.request',
        'unlock_service_portal_request_rel',
        'unlock_id', 'request_id',
        string='Related Portal Requests'
    )
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', string='Activities',
        domain=lambda self: [('res_model', '=', self._name)]
    )
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers',
        domain=lambda self: [('res_model', '=', self._name)]
    )
    message_ids = fields.One2many(
        'mail.message', 'res_id', string='Messages',
        domain=lambda self: [('model', '=', self._name)]
    )

    # ------------------------------------------------------------------
    # PARTS RELATION
    # ------------------------------------------------------------------
    part_ids = fields.One2many('unlock.service.part', 'service_id', string='Parts Used')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('service_cost', 'emergency_surcharge')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = (record.service_cost or 0.0) + (record.emergency_surcharge or 0.0)

    @api.depends('name', 'service_number', 'bin_id.name', 'partner_id.name')
    def _compute_display_name(self):
        for record in self:
            base = record.service_number or record.name
            bin_part = record.bin_id.name if record.bin_id else ''
            partner_part = record.partner_id.name if record.partner_id else ''
            parts = [p for p in [base, bin_part, partner_part] if p]
            record.display_name = " - ".join(parts) if parts else _('New')

    @api.depends('service_start_time', 'completion_date')
    def _compute_service_duration(self):
        for record in self:
            if record.service_start_time and record.completion_date:
                duration = record.completion_date - record.service_start_time
                record.actual_duration = duration.total_seconds() / 3600.0
            else:
                record.actual_duration = 0.0

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('scheduled_date', 'request_date', 'completion_date')
    def _check_dates(self):
        for record in self:
            if record.scheduled_date and record.request_date and record.scheduled_date < record.request_date:
                raise ValidationError(_('Scheduled date cannot be before the request date.'))
            if record.service_start_time and record.scheduled_date and record.service_start_time < record.scheduled_date:
                raise ValidationError(_('Start time cannot be before the scheduled date.'))
            if record.completion_date and record.service_start_time and record.completion_date < record.service_start_time:
                raise ValidationError(_('Completion date cannot be before the start time.'))

    @api.constrains('estimated_duration', 'actual_duration')
    def _check_duration(self):
        for record in self:
            if record.estimated_duration and record.estimated_duration < 0:
                raise ValidationError(_('Estimated duration cannot be negative.'))
            if record.actual_duration and record.actual_duration < 0:
                raise ValidationError(_('Actual duration cannot be negative.'))

    @api.constrains('service_cost', 'emergency_surcharge')
    def _check_costs(self):
        for record in self:
            if record.service_cost and record.service_cost < 0:
                raise ValidationError(_('Service cost cannot be negative.'))
            if record.emergency_surcharge and record.emergency_surcharge < 0:
                raise ValidationError(_('Emergency surcharge cannot be negative.'))

    @api.constrains('witness_required', 'witness_name')
    def _check_witness_requirements(self):
        for record in self:
            if record.witness_required and not record.witness_name:
                raise ValidationError(_('A witness name is required when a witness is marked as required.'))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] in (_('New Unlock Service'), _('New'), 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bin.unlock.service') or _('New')
            if not vals.get('service_number'):
                vals['service_number'] = vals['name']
        records = super().create(vals_list)
        for rec in records:
            rec.message_post(body=_('Service created.'))
        return records

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        self.ensure_one()
        self.write({'state': 'submitted'})
        self.message_post(body=_("Service submitted for scheduling."))

    def action_schedule(self):
        self.ensure_one()
        if not self.scheduled_date:
            raise UserError(_("Please set a scheduled date first."))
        if not self.assigned_technician_id:
            raise UserError(_("Please assign a technician before scheduling."))
        self.write({'state': 'scheduled'})
        self.message_post(body=_("Service scheduled for %s" % self.scheduled_date))

    def action_start_service(self):
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled services can be started."))
        self.write({
            'state': 'in_progress',
            'service_start_time': fields.Datetime.now()
        })
        self.message_post(body=_("Service started by %s" % (self.assigned_technician_id.name or self.env.user.name)))
        self._create_audit_log('service_started')

    def action_complete(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Can only complete services that are in progress."))
        if not self.completion_notes:
            raise UserError(_("Please add completion notes before completing the service."))
        self.write({
            'state': 'completed',
            'completion_date': fields.Datetime.now()
        })
        self.message_post(body=_("Service completed."))
        self._create_audit_log('service_completed')

    def action_cancel(self):
        self.ensure_one()
        if self.state in ('completed', 'invoiced'):
            raise UserError(_("Cannot cancel a completed or invoiced service."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Service cancelled."))
        self._create_audit_log('service_cancelled')

    def action_generate_certificate(self):
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("A service certificate can only be generated for completed services."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Generate Service Certificate"),
            'res_model': 'service.certificate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_service_id': self.id},
        }

    def action_create_invoice(self):
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Can only invoice completed services."))
        if self.invoice_id:
            raise UserError(_("An invoice already exists for this service."))
        if self.total_cost <= 0:
            raise UserError(_("Cannot create an invoice with zero or negative cost."))

        invoice_line_vals = {
            'name': self.display_name,
            'quantity': 1,
            'price_unit': self.total_cost,
        }
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, invoice_line_vals)],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({'invoice_id': invoice.id, 'state': 'invoiced'})
        self.message_post(body=_("Invoice %s created." % invoice.name))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    # ------------------------------------------------------------------
    # VIEW SUPPORT PLACEHOLDERS
    # ------------------------------------------------------------------
    def action_view_access_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unlock Service'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_view_service_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unlock Services'),
            'res_model': self._name,
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id}
        }

    # ============================================================================
    # BUSINESS LOGIC AND VALIDATION
    # ============================================================================
    def get_service_summary(self):
        self.ensure_one()
        return {
            'service_number': self.service_number,
            'reference': self.name,
            'customer': self.partner_id.name,
            'bin': self.bin_id.name,
            'technician': self.assigned_technician_id.name,
            'status': self.state,
            'total_cost': self.total_cost,
        }

    def _create_audit_log(self, action):
        self.ensure_one()
        if 'naid.audit.log' in self.env:
            self.env['naid.audit.log'].create({
                'action_type': action,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'description': _("Bin Unlock Service: %s for %s" % (action, self.name)),
                'naid_compliant': self.naid_compliant,
            })
