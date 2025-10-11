from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ChainOfCustodyEvent(models.Model):
    """Individual custody event linked to a chain.of.custody record.

    Enhanced implementation for comprehensive audit tracking, customer inventory
    management, and NAID AAA compliance integration.
    """

    _name = 'chain.of.custody.event'
    _description = 'Chain of Custody Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc, id desc'

    # Core relationships
    custody_id = fields.Many2one(
        comodel_name='chain.of.custody',
        string='Chain of Custody',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )

    # Customer and inventory integration
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        related='custody_id.partner_id',
        store=True,
        readonly=True,
        help="Customer related to this custody event"
    )

    # Location tracking
    from_location_id = fields.Many2one(
        comodel_name='records.location',
        string='From Location',
        help="Location where event originated"
    )
    to_location_id = fields.Many2one(
        comodel_name='records.location',
        string='To Location',
        help="Destination location for this event"
    )

    # Enhanced event details
    event_date = fields.Datetime(
        string='Event Date',
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time when the event occurred"
    )
    event_type = fields.Selection([
        ('creation', 'Record Creation'),
        ('pickup', 'Pickup'),
        ('handoff', 'Handoff'),
        ('inspection', 'Inspection'),
        ('transport', 'Transport'),
        ('arrival', 'Arrival'),
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('exception', 'Exception'),
        ('inventory_check', 'Inventory Check'),
        ('customer_request', 'Customer Request'),
    ], string='Event Type', default='pickup', required=True, tracking=True)

    # Personnel and responsibility
    responsible_person = fields.Char(
        string='Responsible Person',
        help="Person responsible for this custody event"
    )
    # Renamed label to avoid duplication with possible similarly named fields
    responsible_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible System User',
        default=lambda self: self.env.user,
        help="System user responsible for this event"
    )

    # Location and environmental data
    location = fields.Char(string='Location Description')
    gps_coordinates = fields.Char(string='GPS Coordinates')
    signature_verified = fields.Boolean(string='Signature Verified', tracking=True)
    signature_data = fields.Binary(string='Digital Signature')
    temperature = fields.Float(string='Temperature (°C)')
    humidity = fields.Float(string='Humidity (%)')

    # Item tracking
    affected_items = fields.Text(
        string='Affected Items',
        help="Description of items affected by this event"
    )
    item_count = fields.Integer(
        string='Item Count',
        help="Number of items involved in this event"
    )

    # Audit and compliance
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('pending_review', 'Pending Review'),
    ], string='Compliance Status', default='compliant')

    audit_reference = fields.Char(
        string='Audit Reference',
        help="Reference number for audit purposes"
    )

    # Documentation
    notes = fields.Text(string='Notes', tracking=True)
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Attachments',
        help="Photos, documents, or other evidence related to this event"
    )

    # Computed fields
    duration_since_previous = fields.Float(
        string='Duration Since Previous (hours)',
        compute='_compute_duration_since_previous',
        store=True,
        help="Hours elapsed since the previous event in this custody chain"
    )

    # Unified display name (stored) for Odoo 19 compliance.
    # Previous intermediate non-stored field display_name_computed removed to avoid
    # registry warnings about inconsistent compute/store attributes.

    @api.depends('event_date', 'custody_id.custody_event_ids')
    def _compute_duration_since_previous(self):
        """Calculate time elapsed since previous event"""
        for event in self:
            if not event.custody_id or not event.event_date:
                event.duration_since_previous = 0.0
                continue

            previous_events = event.custody_id.custody_event_ids.filtered(
                lambda e: e.event_date < event.event_date and e.id != event.id
            ).sorted('event_date', reverse=True)

            if previous_events:
                previous_date = previous_events[0].event_date
                duration = (event.event_date - previous_date).total_seconds() / 3600
                event.duration_since_previous = duration
            else:
                event.duration_since_previous = 0.0

    @api.depends('event_type', 'event_date', 'responsible_person', 'location')
    def _compute_display_name(self):
        """Compute enhanced display name for better readability.

        Consolidated logic: builds the stored display_name directly.
        Format: "YYYY-MM-DD HH:MM - Event Type - Location" (components optional).
        """
        for event in self:
            parts = []
            if event.event_date:
                try:
                    parts.append(event.event_date.strftime('%Y-%m-%d %H:%M'))
                except Exception:
                    # Defensive: event_date might be bogus/None during partial updates
                    pass
            if event.event_type:
                parts.append(dict(event._fields['event_type'].selection).get(event.event_type, event.event_type))
            if event.location:
                parts.append(event.location)
            event.display_name = ' - '.join(parts) if parts else _('Chain of Custody Event')

    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create method with audit logging"""
        events = super().create(vals_list)

        for event in events:
            # Create audit log entry
            if hasattr(self.env, 'naid.audit.log'):
                try:
                    self.env['naid.audit.log'].create({
                        'custody_id': event.custody_id.id,
                        'action': 'custody_event_created',
                        'event_type': event.event_type,
                        'user_id': event.responsible_user_id.id or self.env.user.id,
                        'timestamp': event.event_date,
                        'location_id': event.to_location_id.id if event.to_location_id else False,
                        # Translation pattern per project policy: interpolate after _()
                        'notes': _('Custody event created: %s') % event.event_type,
                    })
                except Exception as e:
                    _logger.warning("Failed to create audit log for custody event: %s", e)

            # Update related custody chain status if needed
            if event.event_type in ['destruction', 'completion'] and hasattr(event.custody_id, '_update_completion_status'):
                # Guarded call: parent model may not implement this helper in simplified configuration
                try:
                    event.custody_id._update_completion_status()
                except Exception as e:  # broad guard to avoid breaking creation flow
                    _logger.debug("Skipped _update_completion_status during custody event create: %s", e)

            # Notify stakeholders for critical events
            if event.event_type in ['exception', 'destruction']:
                event._notify_stakeholders()

        return events

    def write(self, vals):
        """Enhanced write method with change tracking"""
        # Track significant changes
        tracked_fields = ['event_type', 'location', 'compliance_status', 'signature_verified']
        changes = {}

        for field in tracked_fields:
            if field in vals:
                for event in self:
                    old_value = getattr(event, field, None)
                    if old_value != vals[field]:
                        changes[field] = {'old': old_value, 'new': vals[field]}

        result = super().write(vals)

        # Log changes to audit trail
        if changes and hasattr(self.env, 'naid.audit.log'):
            for event in self:
                try:
                    self.env['naid.audit.log'].create({
                        'custody_id': event.custody_id.id,
                        'action': 'custody_event_modified',
                        'user_id': self.env.user.id,
                        'timestamp': fields.Datetime.now(),
                        'notes': _('Custody event modified: %s') % str(changes),
                    })
                except Exception as e:
                    _logger.warning("Failed to create audit log for custody event modification: %s", e)

        return result

    def _notify_stakeholders(self):
        """Notify relevant stakeholders about critical events"""
        self.ensure_one()

        if not self.custody_id.partner_id:
            return

        # Prepare notification context
        notification_context = {
            'event_type': self.event_type,
            'event_date': self.event_date,
            'custody_reference': self.custody_id.reference,
            'customer_name': self.custody_id.partner_id.name,
            'location': self.location or 'Unknown',
            'notes': self.notes or '',
        }

        # Send email notification for critical events
        if self.event_type in ['exception', 'destruction']:
            template_ref = 'records_management.custody_event_notification_template'
            try:
                template = self.env.ref(template_ref, raise_if_not_found=False)
                if template:
                    template.with_context(**notification_context).send_mail(self.custody_id.id)
            except Exception as e:
                _logger.warning("Failed to send custody event notification: %s", e)

    def action_verify_signature(self):
        """Action to verify digital signature"""
        self.ensure_one()

        if not self.signature_data:
            raise ValidationError(_("No signature data available for verification."))

        # Mark signature as verified
        self.signature_verified = True

        # Create audit log
        if hasattr(self.env, 'naid.audit.log'):
            self.env['naid.audit.log'].create({
                'custody_id': self.custody_id.id,
                'action': 'signature_verified',
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'notes': _('Digital signature verified for event: %s') % self.event_type,
            })

        return True

    def action_mark_compliant(self):
        """Action to mark event as compliant"""
        self.ensure_one()
        self.compliance_status = 'compliant'

        # Auto-verify signature if present
        if self.signature_data and not self.signature_verified:
            self.signature_verified = True

        return True

    def action_flag_non_compliant(self):
        """Action to flag event as non-compliant"""
        self.ensure_one()
        self.compliance_status = 'non_compliant'

        # Create escalation record
        self._create_compliance_escalation()

        return True

    def _create_compliance_escalation(self):
        """Create compliance escalation for non-compliant events"""
        self.ensure_one()

        # Create activity for compliance review
        self.activity_schedule(
            'mail.mail_activity_data_warning',
            summary=_('Compliance Review Required'),
            note=_('Chain of custody event flagged as non-compliant: %s') % self.event_type,
            user_id=self.env.user.id,
        )

    # Stored display name for Odoo 19 compliance (definition moved above compute)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    @api.constrains('event_date', 'custody_id')
    def _check_event_date(self):
        """Ensure event dates are logical within custody chain"""
        for event in self:
            if event.custody_id and event.custody_id.transfer_date:
                if event.event_date < event.custody_id.transfer_date:
                    raise ValidationError(
                        _("Event date cannot be earlier than custody transfer date.")
                    )

    @api.constrains('from_location_id', 'to_location_id')
    def _check_location_consistency(self):
        """Ensure location changes are logical"""
        for event in self:
            if event.from_location_id and event.to_location_id:
                if event.from_location_id == event.to_location_id:
                    raise ValidationError(
                        _("From and To locations cannot be the same.")
                    )

    # =========================================================================
    # DEFAULT VIEW FALLBACK (Test Support)
    # =========================================================================
    def _get_default_tree_view(self):  # Odoo core still asks for 'tree' in some test helpers
        """Provide a minimal fallback list (tree) view structure for automated tests.

        Odoo 19 uses <list/> arch tag, but internal test utilities may still request
        a default 'tree' view for x2many placeholders when no explicit list view is
        preloaded. Returning a valid list arch prevents UserError during base tests.
        """
        return (
            "<list string='Chain of Custody Events'>"
            "<field name='event_date'/>"
            "<field name='event_type'/>"
            "<field name='custody_id'/>"
            "<field name='notes'/>"
            "</list>"
        )
