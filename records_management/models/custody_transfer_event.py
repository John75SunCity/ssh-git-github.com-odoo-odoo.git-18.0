# -*- coding: utf-8 -*-
"""
Custody Transfer Event Model

Tracks individual custody transfer events for NAID AAA compliance, ensuring
a secure and auditable chain of custody for all physical records.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CustodyTransferEvent(models.Model):
    """
    Custody Transfer Event Management

    Logs each time physical custody of records is transferred from one
    party to another. This is a critical component of the NAID AAA
    compliant chain of custody system.
    """
    _name = 'custody.transfer.event'
    _description = 'Custody Transfer Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transfer_date desc, id desc'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Transfer Reference',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    active = fields.Boolean(string='Active', default=True)

    # ============================================================================
    # RELATIONSHIP & CONTEXT FIELDS
    # ============================================================================
    custody_record_id = fields.Many2one(
        'chain.of.custody',
        string='Chain of Custody Record',
        required=True,
        ondelete='cascade',
        index=True
    )
    work_order_id = fields.Many2one(
        'container.access.work.order',
        string='Related Work Order',
        help='Work order associated with this transfer.'
    )
    from_party_id = fields.Many2one(
        'res.partner',
        string='From Party',
        required=False,
        help='Party transferring custody.'
    )
    to_party_id = fields.Many2one(
        'res.partner',
        string='To Party',
        required=False,
        help='Party receiving custody.'
    )
    destruction_work_order_id = fields.Many2one(comodel_name='container.destruction.work.order', string="Destruction Work Order")
    picking_extension_id = fields.Many2one(
        'stock.picking.records.extension',
        string='Stock Picking Extension',
        help='Related stock picking records extension'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Customer associated with this custody transfer event'
    )

    # ============================================================================
    # TRANSFER DETAILS
    # ============================================================================
    transfer_date = fields.Date(
        string='Transfer Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    transfer_time = fields.Datetime(
        string='Transfer Time',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    transfer_type = fields.Selection([
        ('pickup', 'Customer Pickup'),
        ('delivery', 'Customer Delivery'),
        ('internal', 'Internal Movement'),
        ('destruction', 'Transfer for Destruction'),
        ('archiving', 'Transfer to Archive')
    ], string='Transfer Type', required=True, tracking=True)

    # ============================================================================
    # PERSONNEL
    # ============================================================================
    transferred_from_id = fields.Many2one(
        'hr.employee',
        string='Transferred From (Employee)',
        required=True,
        tracking=True,
        help="Employee relinquishing custody."
    )
    transferred_to_id = fields.Many2one(
        'hr.employee',
        string='Transferred To (Employee)',
        required=True,
        tracking=True,
        help="Employee receiving custody."
    )
    witness_id = fields.Many2one(
        'hr.employee',
        string='Witness',
        tracking=True,
        help="Employee witnessing the transfer."
    )

    # ============================================================================
    # LOCATION & ASSET DETAILS
    # ============================================================================
    from_location = fields.Char(string='From Location', help="Origin location of the items.")
    to_location = fields.Char(string='To Location', help="Destination location of the items.")
    gps_latitude = fields.Float(string='GPS Latitude', digits=(10, 7))
    gps_longitude = fields.Float(string='GPS Longitude', digits=(10, 7))
    items_description = fields.Text(string='Items Description', required=True)
    item_count = fields.Integer(string='Item Count', help="Number of containers or items.")
    total_weight = fields.Float(string='Total Weight (lbs)', digits='Stock Weight')
    total_volume = fields.Float(string='Total Volume (cubic feet)', digits=(12, 3))
    container_numbers = fields.Text(string='Container Numbers', help="Comma-separated list of container barcodes.")

    # ============================================================================
    # VERIFICATION & SECURITY
    # ============================================================================
    verification_method = fields.Selection([
        ('barcode_scan', 'Barcode Scan'),
        ('manual_count', 'Manual Count'),
        ('document_check', 'Document Check')
    ], string='Verification Method', required=True, default='barcode_scan')
    security_seal_number = fields.Char(string='Security Seal Number', tracking=True)
    transfer_authorized = fields.Boolean(string='Transfer Authorized', default=True)
    authorization_code = fields.Char(string='Authorization Code', copy=False)
    transfer_document = fields.Binary(string='Transfer Document', attachment=True)
    transfer_document_filename = fields.Char(string='Document Filename')
    photos_taken = fields.Boolean(string='Photos Taken')
    notes = fields.Text(string='Notes')

    # ============================================================================
    # SIGNATURES
    # ============================================================================
    transferred_from_signature = fields.Binary(string='Transferor Signature', copy=False)
    transferred_to_signature = fields.Binary(string='Receiver Signature', copy=False)
    witness_signature = fields.Binary(string='Witness Signature', copy=False)

    # ============================================================================
    # STATUS & COMPLIANCE
    # ============================================================================
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    naid_compliant = fields.Boolean(
        string='NAID Compliant',
        compute='_compute_naid_compliant',
        store=True,
        help="Indicates if the transfer meets NAID compliance requirements."
    )
    compliance_issues = fields.Text(string='Compliance Issues')

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
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

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('transferred_from_signature', 'transferred_to_signature', 'transfer_authorized', 'verification_method', 'status')
    def _compute_naid_compliant(self):
        """Check NAID compliance requirements for completed transfers."""
        for record in self:
            if record.status in ['completed', 'verified']:
                is_compliant = all([
                    record.transferred_from_signature,
                    record.transferred_to_signature,
                    record.transfer_authorized,
                    record.verification_method
                ])
                record.naid_compliant = is_compliant
            else:
                record.naid_compliant = False

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('custody.transfer.event') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_transfer(self):
        """Start the custody transfer."""
        self.ensure_one()
        if self.status != 'draft':
            raise UserError(_('Can only start draft transfers.'))
        self.write({'status': 'in_progress'})
        self.message_post(body=_('Custody transfer started.'))

    def action_complete_transfer(self):
        """Complete the custody transfer."""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_('Can only complete transfers that are in progress.'))

        # Validate required signatures
        if not self.transferred_from_signature or not self.transferred_to_signature:
            raise UserError(_('Both transferor and receiver signatures are required to complete.'))

        self.write({
            'status': 'completed',
            'transfer_time': fields.Datetime.now()
        })
        self.message_post(body=_('Custody transfer completed.'))

    def action_verify_transfer(self):
        """Verify the custody transfer."""
        self.ensure_one()
        if self.status != 'completed':
            raise UserError(_('Can only verify completed transfers.'))
        self.write({'status': 'verified'})
        self.message_post(body=_('Custody transfer verified by %s', self.env.user.name))

    def action_dispute_transfer(self):
        """Mark transfer as disputed."""
        self.ensure_one()
        if self.status in ('cancelled', 'disputed'):
            raise UserError(_('Cannot dispute cancelled or already disputed transfers.'))
        self.write({'status': 'disputed'})
        self.message_post(body=_('Custody transfer marked as disputed.'))

    def action_cancel_transfer(self):
        """Cancel the custody transfer."""
        self.ensure_one()
        if self.status in ('completed', 'verified', 'cancelled'):
            raise UserError(_('Cannot cancel completed, verified, or already cancelled transfers.'))
        self.write({'status': 'cancelled'})
        self.message_post(body=_('Custody transfer cancelled.'))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('gps_latitude', 'gps_longitude')
    def _check_gps_coordinates(self):
        """Validate GPS coordinates."""
        for record in self:
            if record.gps_latitude and not (-90 <= record.gps_latitude <= 90):
                raise ValidationError(_('GPS latitude must be between -90 and 90 degrees.'))
            if record.gps_longitude and not (-180 <= record.gps_longitude <= 180):
                raise ValidationError(_('GPS longitude must be between -180 and 180 degrees.'))

    @api.constrains('item_count', 'total_weight', 'total_volume')
    def _check_quantities(self):
        """Validate quantities are positive."""
        for record in self:
            if record.item_count < 0:
                raise ValidationError(_('Item count cannot be negative.'))
            if record.total_weight < 0:
                raise ValidationError(_('Total weight cannot be negative.'))
            if record.total_volume < 0:
                raise ValidationError(_('Total volume cannot be negative.'))

    @api.constrains('transferred_from_id', 'transferred_to_id')
    def _check_transfer_personnel(self):
        """Ensure transferor and receiver are not the same person."""
        for record in self:
            if record.transferred_from_id and record.transferred_from_id == record.transferred_to_id:
                raise ValidationError(_('The person transferring custody cannot be the same as the person receiving it.'))
