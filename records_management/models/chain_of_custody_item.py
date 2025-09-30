from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ChainOfCustodyItem(models.Model):
    """Item line belonging to a chain.of.custody transfer.

    Captures documents/containers with quantity & valuation for insurance.
    """

    _name = 'chain.of.custody.item'
    _description = 'Chain of Custody Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'custody_id desc, sequence, id desc'

    # Core relationships
    custody_id = fields.Many2one(
        comodel_name='chain.of.custody',
        string='Chain of Custody',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    document_id = fields.Many2one(
        comodel_name='records.document',
        string='Document',
        tracking=True,
    )
    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Container',
        tracking=True,
    )
    box_id = fields.Many2one(
        comodel_name='records.storage.box',
        string='Storage Box',
        tracking=True,
        help='Storage box containing this item'
    )

    # Sequence for ordering items within custody
    sequence = fields.Integer(string='Sequence', default=10)

    # Related fields from custody for easier access
    partner_id = fields.Many2one(
        related='custody_id.partner_id',
        string='Customer',
        store=True,
        readonly=True,
    )
    from_custodian_id = fields.Many2one(
        related='custody_id.from_custodian_id',
        string='From Custodian',
        store=True,
        readonly=True,
    )
    to_custodian_id = fields.Many2one(
        related='custody_id.to_custodian_id',
        string='To Custodian',
        store=True,
        readonly=True,
    )
    transfer_date = fields.Datetime(
        related='custody_id.transfer_date',
        string='Transfer Date',
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        related='custody_id.state',
        string='Transfer State',
        store=True,
        readonly=True,
    )

    # Item details
    item_type = fields.Selection([
        ('document', 'Document'),
        ('container', 'Container'),
        ('asset', 'Asset'),
        ('other', 'Other'),
    ], string='Item Type', default='document', required=True, tracking=True)

    quantity = fields.Integer(string='Quantity', default=1, tracking=True)

    condition = fields.Selection([
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('sealed', 'Sealed'),
        ('opened', 'Opened'),
        ('missing', 'Missing'),
        ('destroyed', 'Destroyed'),
    ], string='Condition', default='good', tracking=True)

    serial_number = fields.Char(string='Serial Number', tracking=True)
    barcode = fields.Char(string='Barcode', tracking=True)

    # Monetary fields with proper currency handling
    value = fields.Monetary(
        string='Value',
        currency_field='currency_id',
        tracking=True,
        help="Estimated value for insurance purposes"
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id
    )

    # Computed total value
    total_value = fields.Monetary(
        string='Total Value',
        compute='_compute_total_value',
        store=True,
        currency_field='currency_id',
    )

    # Location tracking
    from_location_id = fields.Many2one(
        comodel_name='records.location',
        string='From Location',
        tracking=True,
    )
    to_location_id = fields.Many2one(
        comodel_name='records.location',
        string='To Location',
        tracking=True,
    )

    # Additional tracking fields
    weight = fields.Float(string='Weight (kg)', tracking=True)
    dimensions = fields.Char(string='Dimensions', tracking=True)
    special_handling = fields.Text(string='Special Handling Instructions')
    notes = fields.Text(string='Notes', tracking=True)

    # Status and verification
    verified = fields.Boolean(string='Verified', default=False, tracking=True)
    verified_by = fields.Many2one(comodel_name='res.users', string='Verified By', tracking=True)
    verified_date = fields.Datetime(string='Verified Date', tracking=True)

    # Unified stored display name (removed legacy non-stored display_name_computed to avoid
    # inconsistent compute/store warnings).

    @api.depends('quantity', 'value')
    def _compute_total_value(self):
        """Compute total value based on quantity and unit value"""
        for item in self:
            item.total_value = item.quantity * (item.value or 0.0)

    @api.depends('document_id', 'container_id', 'item_type', 'serial_number', 'barcode', 'quantity')
    def _compute_display_name(self):
        """Compute unified stored display name.

        Format example: "DocumentName (document) S/N:123 Qty: 2".
        """
        for item in self:
            parts = []
            base = False
            if item.document_id:
                base = item.document_id.display_name
            elif item.container_id:
                base = item.container_id.display_name
            if not base:
                base = _('Item')
            parts.append(base)
            parts.append('(%s)' % dict(item._fields['item_type'].selection).get(item.item_type, item.item_type))
            if item.serial_number:
                parts.append(_('S/N: %s') % item.serial_number)
            elif item.barcode:
                parts.append(_('BC: %s') % item.barcode)
            if item.quantity and item.quantity > 1:
                parts.append(_('Qty: %d') % item.quantity)
            item.display_name = ' '.join(parts)

    @api.constrains('document_id', 'container_id', 'item_type')
    def _check_item_consistency(self):
        """Ensure item type matches the selected document/container"""
        for item in self:
            if item.item_type == 'document' and not item.document_id:
                raise ValidationError(_("Document must be selected for document type items."))
            if item.item_type == 'container' and not item.container_id:
                raise ValidationError(_("Container must be selected for container type items."))
            if item.document_id and item.container_id:
                raise ValidationError(_("Item cannot be both a document and container."))

    @api.constrains('quantity')
    def _check_quantity(self):
        """Ensure quantity is positive"""
        for item in self:
            if item.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))

    @api.onchange('document_id')
    def _onchange_document_id(self):
        """Auto-fill fields when document is selected"""
        if self.document_id:
            self.item_type = 'document'
            self.container_id = False
            # Auto-fill from document if available
            if self.document_id.container_id:
                self.from_location_id = self.document_id.container_id.location_id
            if hasattr(self.document_id, 'barcode'):
                self.barcode = self.document_id.barcode

    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Auto-fill fields when container is selected"""
        if self.container_id:
            self.item_type = 'container'
            self.document_id = False
            # Auto-fill from container
            self.from_location_id = self.container_id.location_id
            if hasattr(self.container_id, 'barcode'):
                self.barcode = self.container_id.barcode
            if hasattr(self.container_id, 'weight'):
                self.weight = self.container_id.weight

    @api.onchange('item_type')
    def _onchange_item_type(self):
        """Clear incompatible fields when item type changes"""
        if self.item_type == 'document':
            self.container_id = False
        elif self.item_type == 'container':
            self.document_id = False
        elif self.item_type in ('asset', 'other'):
            self.document_id = False
            self.container_id = False

    def action_verify_item(self):
        """Mark item as verified by current user"""
        self.ensure_one()
        self.write({
            'verified': True,
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now(),
        })

        # Log verification in chatter
        self.message_post(
            body=_("Item verified by %s") % self.env.user.name,
            message_type='notification',
        )

        return True

    def action_update_location(self, new_location_id):
        """Update item location and track in audit log"""
        self.ensure_one()
        if not new_location_id:
            return False

        old_location = self.to_location_id
        self.to_location_id = new_location_id

        # Create audit log entry
        if hasattr(self.env, 'naid.audit.log'):
            self.env['naid.audit.log'].create({
                'custody_id': self.custody_id.id,
                'item_id': self.id,
                'action': 'location_update',
                'old_location_id': old_location.id if old_location else False,
                'new_location_id': new_location_id,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'notes': _('Location updated via chain of custody item'),
            })

        return True

    # Stored display name for Odoo 18 compliance (definition placed after compute)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update related records"""
        items = super().create(vals_list)

        # Update document/container location if transferring
        for item in items:
            if item.to_location_id:
                if item.document_id and hasattr(item.document_id, 'location_id'):
                    item.document_id.location_id = item.to_location_id
                elif item.container_id and hasattr(item.container_id, 'location_id'):
                    item.container_id.location_id = item.to_location_id

        return items

    def write(self, vals):
        """Override write to track location changes"""
        if 'to_location_id' in vals and vals['to_location_id']:
            for item in self:
                # Update related document/container location
                if item.document_id and hasattr(item.document_id, 'location_id'):
                    item.document_id.location_id = vals['to_location_id']
                elif item.container_id and hasattr(item.container_id, 'location_id'):
                    item.container_id.location_id = vals['to_location_id']

        return super().write(vals)
