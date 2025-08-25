"""Chain of Custody tracking for NAID AAA compliance in Records Management.

This model provides comprehensive audit trail tracking for document custody
from creation through destruction, ensuring full NAID AAA compliance.
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class ChainOfCustody(models.Model):
    """Comprehensive chain of custody tracking for NAID AAA compliance.

    This model tracks every custody transfer, location change, and handling event
    for documents and containers throughout their lifecycle.
    """

    _name = 'chain.of.custody'
    _description = 'Chain of Custody Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, transfer_date desc, id desc'
    _rec_name = 'display_name'

    # Core Identification
    name = fields.Char(
        string='Custody Reference',
        required=True,
        copy=False,
        index=True,
        default=lambda self: self._generate_reference(),
        help="Unique reference for this custody record"
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Human-readable display name"
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of custody transfers"
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="Uncheck to archive this custody record"
    )

    # Transfer Information
    transfer_date = fields.Datetime(
        string='Transfer Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time of custody transfer"
    )

    transfer_type = fields.Selection([
        ('creation', 'Initial Creation'),
        ('storage', 'Storage Transfer'),
        ('retrieval', 'Retrieval'),
        ('transport', 'Transportation'),
        ('destruction', 'Destruction'),
        ('return', 'Return to Customer'),
        ('internal', 'Internal Transfer'),
        ('audit', 'Audit/Inspection'),
        ('maintenance', 'Maintenance'),
        ('emergency', 'Emergency Access')
    ], string='Transfer Type', required=True, tracking=True)

    # Custody Parties
    from_custodian_id = fields.Many2one(
        comodel_name='res.users',
        string='From Custodian',
        tracking=True,
        help="Previous custodian releasing custody"
    )

    to_custodian_id = fields.Many2one(
        comodel_name='res.users',
        string='To Custodian',
        required=True,
        tracking=True,
        help="New custodian receiving custody"
    )

    witness_id = fields.Many2one(
        comodel_name='res.users',
        string='Witness',
        tracking=True,
        help="Witness to the custody transfer"
    )

    department_id = fields.Many2one(
        comodel_name='records.department',
        string='Department',
        tracking=True,
        help="Department responsible for custody"
    )

    # Location Tracking
    from_location_id = fields.Many2one(
        comodel_name='records.location',
        string='From Location',
        tracking=True,
        help="Previous location"
    )

    to_location_id = fields.Many2one(
        comodel_name='records.location',
        string='To Location',
        required=True,
        tracking=True,
        help="New location"
    )

    specific_location = fields.Char(
        string='Specific Location',
        help="Detailed location description (shelf, room, etc.)"
    )

    # Related Records
    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Container',
        ondelete='cascade',
        index=True,
        help="Related container if applicable"
    )

    document_id = fields.Many2one(
        comodel_name='records.document',
        string='Document',
        ondelete='cascade',
        index=True,
        help="Related document if applicable"
    )

    request_id = fields.Many2one(
        comodel_name='portal.request',
        string='Related Request',
        ondelete='set null',
        help="Request that triggered this custody transfer"
    )

    destruction_certificate_id = fields.Many2one(
        comodel_name='destruction.certificate',
        string='Destruction Certificate',
        ondelete='set null',
        help="Certificate if this was a destruction transfer"
    )

    # Transfer Details
    reason = fields.Text(
        string='Transfer Reason',
        required=True,
        tracking=True,
        help="Detailed reason for custody transfer"
    )

    conditions = fields.Text(
        string='Conditions/Notes',
        help="Special conditions or notes about the transfer"
    )

    transfer_method = fields.Selection([
        ('hand_delivery', 'Hand Delivery'),
        ('secure_transport', 'Secure Transport'),
        ('courier', 'Courier Service'),
        ('internal_move', 'Internal Move'),
        ('pickup_service', 'Pickup Service'),
        ('mail', 'Postal Mail'),
        ('electronic', 'Electronic Transfer')
    ], string='Transfer Method', tracking=True)

    # NAID AAA Compliance
    naid_compliant = fields.Boolean(
        string='NAID AAA Compliant',
        default=True,
        tracking=True,
        help="Whether this transfer meets NAID AAA standards"
    )

    security_level = fields.Selection([
        ('standard', 'Standard Security'),
        ('high', 'High Security'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'),
        ('top_secret', 'Top Secret')
    ], string='Security Level', default='standard', tracking=True)

    authorization_required = fields.Boolean(
        string='Authorization Required',
        default=False,
        help="Whether special authorization was required"
    )

    authorized_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Authorized By',
        help="User who authorized this transfer"
    )

    # Digital Signatures & Verification
    custodian_signature = fields.Binary(
        string='Custodian Signature',
        help="Digital signature of receiving custodian"
    )

    witness_signature = fields.Binary(
        string='Witness Signature',
        help="Digital signature of witness"
    )

    signature_date = fields.Datetime(
        string='Signature Date',
        help="Date and time signatures were captured"
    )

    verification_code = fields.Char(
        string='Verification Code',
        copy=False,
        help="Unique verification code for this transfer"
    )

    # Status and Validation
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    is_verified = fields.Boolean(
        string='Verified',
        default=False,
        tracking=True,
        help="Whether this transfer has been verified"
    )

    verified_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Verified By',
        help="User who verified this transfer"
    )

    verified_date = fields.Datetime(
        string='Verification Date',
        help="Date and time of verification"
    )

    # Audit Information
    audit_log_ids = fields.One2many(
        comodel_name='naid.audit.log',
        inverse_name='custody_id',
        string='Audit Logs',
        help="Related audit log entries"
    )

    audit_notes = fields.Text(
        string='Audit Notes',
        help="Special audit notes or observations"
    )

    # Computed Fields
    duration_hours = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True,
        help="Duration of custody transfer"
    )

    next_transfer_id = fields.Many2one(
        comodel_name='chain.of.custody',
        string='Next Transfer',
        compute='_compute_next_transfer',
        help="Next custody transfer in the chain"
    )

    previous_transfer_id = fields.Many2one(
        comodel_name='chain.of.custody',
        string='Previous Transfer',
        compute='_compute_previous_transfer',
        help="Previous custody transfer in the chain"
    )

    is_final_transfer = fields.Boolean(
        string='Final Transfer',
        compute='_compute_is_final',
        help="Whether this is the final transfer (destruction)"
    )

    # Related Record Counts
    related_container_count = fields.Integer(
        string='Related Containers',
        compute='_compute_related_counts'
    )

    related_document_count = fields.Integer(
        string='Related Documents',
        compute='_compute_related_counts'
    )

    # Computed Methods
    @api.depends('name', 'transfer_type', 'to_custodian_id')
    def _compute_display_name(self):
        """Compute display name for the custody record."""
        for record in self:
            if record.name and record.transfer_type and record.to_custodian_id:
                record.display_name = f"{record.name} - {dict(record._fields['transfer_type'].selection)[record.transfer_type]} to {record.to_custodian_id.name}"
            else:
                record.display_name = record.name or 'New Custody Record'

    @api.depends('transfer_date', 'state')
    def _compute_duration(self):
        """Compute duration of custody transfer."""
        for record in self:
            if record.transfer_date and record.state == 'completed':
                # Calculate based on next transfer or current time
                next_transfer = self.search([
                    ('sequence', '>', record.sequence),
                    ('container_id', '=', record.container_id.id),
                    ('document_id', '=', record.document_id.id)
                ], limit=1)

                if next_transfer:
                    end_time = next_transfer.transfer_date
                else:
                    end_time = fields.Datetime.now()

                duration = end_time - record.transfer_date
                record.duration_hours = duration.total_seconds() / 3600
            else:
                record.duration_hours = 0.0

    @api.depends('sequence', 'container_id', 'document_id')
    def _compute_next_transfer(self):
        """Compute next transfer in the chain."""
        for record in self:
            domain = [
                ('sequence', '>', record.sequence),
                '|',
                ('container_id', '=', record.container_id.id if record.container_id else False),
                ('document_id', '=', record.document_id.id if record.document_id else False)
            ]
            record.next_transfer_id = self.search(domain, limit=1)

    @api.depends('sequence', 'container_id', 'document_id')
    def _compute_previous_transfer(self):
        """Compute previous transfer in the chain."""
        for record in self:
            domain = [
                ('sequence', '<', record.sequence),
                '|',
                ('container_id', '=', record.container_id.id if record.container_id else False),
                ('document_id', '=', record.document_id.id if record.document_id else False)
            ]
            record.previous_transfer_id = self.search(domain, order='sequence desc', limit=1)

    @api.depends('transfer_type', 'next_transfer_id')
    def _compute_is_final(self):
        """Determine if this is the final transfer."""
        for record in self:
            record.is_final_transfer = (
                record.transfer_type == 'destruction' or
                not record.next_transfer_id
            )

    def _compute_related_counts(self):
        """Compute counts of related records."""
        for record in self:
            record.related_container_count = 1 if record.container_id else 0
            record.related_document_count = 1 if record.document_id else 0

    # Validation Methods
    @api.constrains('transfer_date')
    def _check_transfer_date(self):
        """Validate transfer date is not in the future."""
        for record in self:
            if record.transfer_date > fields.Datetime.now():
                raise ValidationError(_("Transfer date cannot be in the future."))

    @api.constrains('from_custodian_id', 'to_custodian_id')
    def _check_custodians(self):
        """Validate custodian assignment."""
        for record in self:
            if record.from_custodian_id and record.from_custodian_id == record.to_custodian_id:
                raise ValidationError(_("From and To custodians cannot be the same person."))

    @api.constrains('container_id', 'document_id')
    def _check_related_record(self):
        """Ensure at least one related record is specified."""
        for record in self:
            if not record.container_id and not record.document_id:
                raise ValidationError(_("Either Container or Document must be specified."))

    @api.constrains('security_level', 'naid_compliant')
    def _check_naid_compliance(self):
        """Validate NAID compliance requirements."""
        for record in self:
            if record.naid_compliant and record.security_level in ['secret', 'top_secret']:
                if not record.authorization_required or not record.authorized_by_id:
                    raise ValidationError(_(
                        "High security transfers require authorization and authorized by user."
                    ))

    # Generation Methods
    @api.model
    def _generate_reference(self):
        """Generate unique custody reference."""
        sequence = self.env['ir.sequence'].next_by_code('chain.of.custody') or 'COC'
        return f"COC-{sequence}-{datetime.now().strftime('%Y%m%d')}"

    def _generate_verification_code(self):
        """Generate verification code for transfer."""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Business Methods
    def action_confirm_transfer(self):
        """Confirm the custody transfer."""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft transfers can be confirmed."))

            record.write({
                'state': 'pending',
                'verification_code': record._generate_verification_code()
            })

            # Create audit log
            self.env['naid.audit.log'].create({
                'event_type': 'custody_transfer',
                'description': f"Custody transfer confirmed: {record.display_name}",
                'user_id': self.env.user.id,
                'custody_id': record.id,
                'container_id': record.container_id.id if record.container_id else False,
                'document_id': record.document_id.id if record.document_id else False,
            })

    def action_start_transfer(self):
        """Start the custody transfer process."""
        for record in self:
            if record.state != 'pending':
                raise UserError(_("Only pending transfers can be started."))

            record.write({'state': 'in_transit'})

    def action_complete_transfer(self):
        """Complete the custody transfer."""
        for record in self:
            if record.state != 'in_transit':
                raise UserError(_("Only in-transit transfers can be completed."))

            record.write({
                'state': 'completed',
                'signature_date': fields.Datetime.now()
            })

            # Update related records
            if record.container_id:
                record.container_id.write({
                    'current_custodian_id': record.to_custodian_id.id,
                    'current_location_id': record.to_location_id.id
                })

            if record.document_id:
                record.document_id.write({
                    'current_custodian_id': record.to_custodian_id.id,
                    'current_location_id': record.to_location_id.id
                })

    def action_verify_transfer(self):
        """Verify the custody transfer."""
        for record in self:
            if record.state != 'completed':
                raise UserError(_("Only completed transfers can be verified."))

            record.write({
                'state': 'verified',
                'is_verified': True,
                'verified_by_id': self.env.user.id,
                'verified_date': fields.Datetime.now()
            })

    def action_cancel_transfer(self):
        """Cancel the custody transfer."""
        for record in self:
            if record.state in ['verified', 'cancelled']:
                raise UserError(_("Verified or cancelled transfers cannot be cancelled."))

            record.write({'state': 'cancelled'})

    # Reporting Methods
    def generate_custody_report(self):
        """Generate comprehensive custody report."""
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.custody_chain_report',
            'model': 'chain.of.custody',
            'context': {'active_ids': self.ids}
        }

    def get_full_chain(self):
        """Get complete custody chain for related records."""
        domain = []
        if self.container_id:
            domain.append(('container_id', '=', self.container_id.id))
        if self.document_id:
            domain.append(('document_id', '=', self.document_id.id))

        if domain:
            return self.search(domain, order='sequence, transfer_date')
        return self.browse()

    # Integration Methods
    def create_destruction_record(self):
        """Create destruction certificate for final transfer."""
        if not self.is_final_transfer or self.transfer_type != 'destruction':
            raise UserError(_("This is not a destruction transfer."))

        certificate_vals = {
            'name': f"Destruction Certificate - {self.display_name}",
            'destruction_date': self.transfer_date,
            'custodian_id': self.to_custodian_id.id,
            'location_id': self.to_location_id.id,
            'container_id': self.container_id.id if self.container_id else False,
            'document_id': self.document_id.id if self.document_id else False,
            'custody_chain_id': self.id,
            'naid_compliant': self.naid_compliant,
            'security_level': self.security_level,
        }

        certificate = self.env['destruction.certificate'].create(certificate_vals)
        self.destruction_certificate_id = certificate.id

        return certificate

    # Override Methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add audit logging. Batch compatible."""
        records = super().create(vals_list)
        for record in records:
            self.env['naid.audit.log'].create({
                'event_type': 'custody_created',
                'description': f"New custody record created: {record.display_name}",
                'user_id': self.env.user.id,
                'custody_id': record.id,
                'container_id': record.container_id.id if record.container_id else False,
                'document_id': record.document_id.id if record.document_id else False,
            })
            _logger.info(f"Created custody record: {record.display_name}")
        return records

    def write(self, vals):
        """Override write to add audit logging."""
        result = super().write(vals)

        # Log significant changes
        tracked_fields = ['state', 'to_custodian_id', 'to_location_id', 'transfer_type']
        changed_fields = [field for field in tracked_fields if field in vals]

        if changed_fields:
            for record in self:
                self.env['naid.audit.log'].create({
                    'event_type': 'custody_modified',
                    'description': f"Custody record modified: {record.display_name} - Fields: {', '.join(changed_fields)}",
                    'user_id': self.env.user.id,
                    'custody_id': record.id,
                    'container_id': record.container_id.id if record.container_id else False,
                    'document_id': record.document_id.id if record.document_id else False,
                })

        return result

    def unlink(self):
        """Override unlink to prevent deletion of verified transfers."""
        for record in self:
            if record.is_verified:
                raise UserError(_(
                    "Verified custody transfers cannot be deleted for compliance reasons."
                ))

        return super().unlink()

    # Utility Methods
    @api.model
    def get_custody_statistics(self, date_from=None, date_to=None):
        """Get custody transfer statistics."""
        domain = []
        if date_from:
            domain.append(('transfer_date', '>=', date_from))
        if date_to:
            domain.append(('transfer_date', '<=', date_to))

        records = self.search(domain)

        return {
            'total_transfers': len(records),
            'completed_transfers': len(records.filtered(lambda r: r.state == 'completed')),
            'verified_transfers': len(records.filtered(lambda r: r.is_verified)),
            'naid_compliant_transfers': len(records.filtered(lambda r: r.naid_compliant)),
            'transfer_types': records.read_group(
                domain, ['transfer_type'], ['transfer_type']
            ),
        }
