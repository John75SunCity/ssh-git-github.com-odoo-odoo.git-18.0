from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class NAIDCustodyEvent(models.Model):
    _name = 'naid.custody.event'
    _description = 'NAID Custody Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_datetime desc, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Event Reference', compute='_compute_name', store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string='Event Recorder', default=lambda self: self.env.user, required=True, tracking=True)

    event_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('in_transit', 'In Transit'),
        ('received', 'Received at Facility'),
        ('destruction', 'Destruction'),
        ('witnessed_destruction', 'Witnessed Destruction'),
        ('exception', 'Exception'),
        ('other', 'Other'),
    ], string='Event Type', required=True, tracking=True)

    # Use lambda for default to match Odoo best practices and ensure consistency with other defaults
    event_datetime = fields.Datetime(
        string='Event Timestamp',
        default=lambda self: fields.Datetime.now(),
        required=True,
        tracking=True
    )

    # Polymorphic relationship to link to the primary custody chain document
    custody_id = fields.Many2one(comodel_name='naid.custody', string='Chain of Custody', ondelete='cascade', required=True)

    from_location_id = fields.Many2one(comodel_name='records.location', string='From Location')
    to_location_id = fields.Many2one(comodel_name='records.location', string='To Location')

    gps_latitude = fields.Float(string='GPS Latitude', digits=(10, 7))
    gps_longitude = fields.Float(string='GPS Longitude', digits=(10, 7))

    digital_signature = fields.Binary(string='Digital Signature', copy=False)
    signature_verified = fields.Boolean(string='Signature Verified', readonly=True, copy=False)

    photo_documentation = fields.Binary(string='Photo Documentation', attachment=True, copy=False)

    description = fields.Text(string='Event Description')
    notes = fields.Text(string='Additional Notes')

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('event_type', 'custody_id.description', 'event_datetime')
    def _compute_name(self):
        for event in self:
            event_type_display = dict(event.fields_get()['event_type']['selection']).get(event.event_type, '')
            custody_name = event.custody_id.description if event.custody_id else _('Unknown')
            timestamp = event.event_datetime.strftime('%Y-%m-%d %H:%M:%S') if event.event_datetime else ''
            event.name = f"{custody_name} - {event_type_display} ({timestamp})"

    @api.constrains('event_datetime', 'custody_id')
    def _check_event_chronology(self):
        for event in self:
            previous_events = self.search([
                ('custody_id', '=', event.custody_id.id),
                ('id', '!=', event.id),
                ('event_datetime', '>', event.event_datetime)
            ], limit=1)
            if previous_events:
                raise ValidationError(_("Event datetime must be after all previous events in the same custody chain."))

    @api.constrains('event_type', 'from_location_id', 'to_location_id')
    def _check_location_requirements(self):
        for event in self:
            if event.event_type == 'in_transit':
                if not event.from_location_id or not event.to_location_id:
                    raise ValidationError(_("Transfer events require both a source and destination location."))
                if event.from_location_id == event.to_location_id:
                    raise ValidationError(_("Source and destination locations must be different for transfers."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_verify_signature(self):
        self.ensure_one()
        if not self.digital_signature:
            raise UserError(_("No digital signature found to verify."))
        # In a real scenario, this would integrate with a cryptographic verification system.
        # For this implementation, we'll consider it verified upon action.
        self.write({
            'signature_verified': True,
        })
        self.message_post(body=_("Digital signature marked as verified by %s.", self.env.user.name))
        self._log_custody_event('signature_verified')

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _log_custody_event(self, action_type):
        """Helper to create a standardized audit log entry for the event."""
        self.ensure_one()
        log_description = _("Custody Event '%(event_name)s' for Chain '%(chain_name)s' had action '%(action)s'.") % {
            'event_name': self.name,
            'chain_name': self.custody_id.description or 'Unknown',
            'action': action_type,
        }
        self.env['naid.audit.log'].log_action(
            description=log_description,
            action_type='security',
            record=self,
        )

    @api.model
    def create_from_chain(self, custody_chain, event_type, **kwargs):
        """
        Standardized method to create a new event linked to a custody chain.
        This ensures consistency and proper logging.
        """
        vals = {
            'custody_id': custody_chain.id,
            'event_type': event_type,
            'user_id': self.env.user.id,
            'event_datetime': fields.Datetime.now(),
        }
        vals.update(kwargs)

        event = self.create(vals)

        # Post a message on the parent custody chain record
        custody_chain.message_post(
            body=_("New Custody Event Created: <strong>%(event_name)s</strong> (Type: %(event_type)s)") % {
                'event_name': event.name,
                'event_type': event.event_type,
            }
        )
        event._log_custody_event('created')
        return event


