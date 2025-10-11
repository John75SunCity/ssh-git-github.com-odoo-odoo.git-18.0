from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class RecordsContainerMovement(models.Model):
    _name = 'records.container.movement'
    _description = 'Records Container Movement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'movement_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Movement Reference", required=True, copy=False, readonly=True, default=lambda self: "New")
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    container_id = fields.Many2one('records.container', string="Container", required=True, ondelete='cascade', tracking=True)
    partner_id = fields.Many2one(related='container_id.partner_id', string="Customer", store=True, readonly=True, comodel_name='res.partner')
    from_location_id = fields.Many2one(comodel_name='stock.location', string="From Location", required=True, tracking=True)
    to_location_id = fields.Many2one(comodel_name='stock.location', string="To Location", required=True, tracking=True)
    assigned_technician_id = fields.Many2one(comodel_name='res.users', string="Assigned Technician", tracking=True)
    authorized_by_id = fields.Many2one(comodel_name='res.users', string="Authorized By", readonly=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('authorized', 'Authorized'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('exception', 'Exception'),
        ('cancelled', 'Cancelled'),
    ], string="Movement Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # MOVEMENT DETAILS
    # ============================================================================
    movement_date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now, required=True, tracking=True)
    movement_type = fields.Selection([
        ('retrieval', 'Retrieval'),
        ('storage', 'Storage'),
        ('destruction', 'To Destruction'),
        ('internal', 'Internal Transfer'),
        ('return', 'Return to Customer'),
    ], string="Movement Type", required=True, tracking=True)
    movement_reason = fields.Text(string="Reason for Movement")
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], string='Priority', default='0')

    # ============================================================================
    # EXECUTION & TIMING
    # ============================================================================
    actual_start_time = fields.Datetime(string='Actual Start Time', readonly=True)
    actual_end_time = fields.Datetime(string='Actual End Time', readonly=True)
    duration_hours = fields.Float(string="Duration (Hours)", compute='_compute_duration', store=True)

    # ============================================================================
    # VERIFICATION & COMPLIANCE (NAID)
    # ============================================================================
    requires_authorization = fields.Boolean(string="Requires Authorization", compute='_compute_authorization_required', store=True)
    authorization_date = fields.Datetime(string="Authorization Date", readonly=True)
    completion_verified = fields.Boolean(string="Completion Verified", readonly=True)
    verification_date = fields.Datetime(string="Verification Date", readonly=True)
    verified_by_id = fields.Many2one(comodel_name='res.users', string="Verified By", readonly=True)
    barcode_scanned = fields.Boolean(string="Barcode Scanned", help="Indicates if the container barcode was scanned during movement.")
    # Batch 3 label disambiguation
    notes = fields.Text(string="Movement Notes")  # retained wording already specific, kept for consistency
    exception_notes = fields.Text(string="Exception Notes")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('actual_start_time', 'actual_end_time')
    def _compute_duration(self):
        for record in self:
            if record.actual_start_time and record.actual_end_time:
                duration = record.actual_end_time - record.actual_start_time
                record.duration_hours = duration.total_seconds() / 3600
            else:
                record.duration_hours = 0.0

    @api.depends('movement_type', 'from_location_id', 'to_location_id')
    def _compute_authorization_required(self):
        for record in self:
            # Example logic: movements to destruction always require authorization
            if record.movement_type == 'destruction':
                record.requires_authorization = True
            else:
                record.requires_authorization = False

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.container.movement') or _('New')
            # Automatically set the 'from_location_id' based on the container's current location
            if vals.get('container_id') and not vals.get('from_location_id'):
                container = self.env['records.container'].browse(vals['container_id'])
                if container.location_id:
                    vals['from_location_id'] = container.location_id.id
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'completed':
            for record in self:
                # Update the container's location upon movement completion
                if record.container_id and record.to_location_id:
                    record.container_id.location_id = record.to_location_id
        return res

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_authorize(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft movements can be authorized."))
        self.write({
            'state': 'authorized',
            'authorized_by_id': self.env.user.id,
            'authorization_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Movement authorized by %s.", self.env.user.name))

    def action_start_movement(self):
        self.ensure_one()
        if self.requires_authorization and self.state != 'authorized':
            raise UserError(_("This movement requires authorization before starting."))
        if self.state not in ['draft', 'authorized']:
            raise UserError(_("Movement can only be started from 'Draft' or 'Authorized' state."))
        self.write({'state': 'in_progress', 'actual_start_time': fields.Datetime.now()})
        self.message_post(body=_("Movement started by %s.", self.env.user.name))

    def action_complete_movement(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only movements in progress can be completed."))
        self.write({'state': 'completed', 'actual_end_time': fields.Datetime.now()})
        self.message_post(body=_("Movement completed by %s.", self.env.user.name))

    def action_verify_movement(self):
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed movements can be verified."))
        self.write({
            'state': 'verified',
            'completion_verified': True,
            'verification_date': fields.Datetime.now(),
            'verified_by_id': self.env.user.id,
        })
        self.message_post(body=_("Movement verified by %s.", self.env.user.name))

    def action_cancel_movement(self):
        self.ensure_one()
        if self.state in ['completed', 'verified']:
            raise UserError(_("Completed or verified movements cannot be cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Movement cancelled by %s.", self.env.user.name))

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.state in ['completed', 'verified']:
            raise UserError(_("Completed or verified movements cannot be reset to draft."))
        self.write({
            'state': 'draft',
            'authorized_by_id': False,
            'authorization_date': False,
            'actual_start_time': False,
            'actual_end_time': False,
            'verified_by_id': False,
            'verification_date': False,
            'completion_verified': False,
        })
        self.message_post(body=_("Movement reset to draft."))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('from_location_id', 'to_location_id')
    def _check_movement_locations(self):
        for record in self:
            if record.from_location_id == record.to_location_id:
                raise ValidationError(_("The 'From' and 'To' locations cannot be the same."))

    @api.constrains('actual_start_time', 'actual_end_time')
    def _check_movement_times(self):
        for record in self:
            if record.actual_start_time and record.actual_end_time and record.actual_start_time > record.actual_end_time:
                raise ValidationError(_("The start time cannot be after the end time."))

    # =========================================================================
    # DEFAULT VIEW FALLBACK (Test Support)
    # =========================================================================
    def _get_default_tree_view(self):  # Odoo core still asks for 'tree' in some test helpers
        """Provide a minimal fallback list (tree) view structure for automated tests.

        Odoo 19 uses <list/> arch tag, but internal test utilities may still request
        a default 'tree' view for x2many placeholders when no explicit list view is
        preloaded. Returning a valid list arch prevents UserError during base tests.
        """
        from lxml import etree
        arch = etree.fromstring(
            "<list string='Container Movements'>"
            "<field name='movement_date'/>"
            "<field name='movement_type'/>"
            "<field name='container_id'/>"
            "<field name='state'/>"
            "</list>"
        )
        return arch
