# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ShreddingBinMovement(models.Model):
    """
    Tracks movement history for shredding service bins.
    
    Every status change or location change creates a movement record,
    providing full audit trail for bin lifecycle management.
    """
    _name = 'shredding.bin.movement'
    _description = 'Shredding Bin Movement History'
    _order = 'movement_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string="Bin",
        required=True,
        ondelete='cascade',
        index=True
    )

    # ============================================================================
    # MOVEMENT DETAILS
    # ============================================================================
    movement_date = fields.Datetime(
        string="Movement Date",
        required=True,
        default=fields.Datetime.now
    )

    from_status = fields.Selection([
        ('available', 'Available'),
        ('in_service', 'In Service'),
        ('full', 'Full - Ready for Pickup'),
        ('in_transit', 'In Transit'),
        ('being_serviced', 'Being Serviced'),
        ('maintenance', 'Maintenance'),
        ('lost', 'Lost/Written Off'),
        ('retired', 'Retired')
    ], string="From Status")

    to_status = fields.Selection([
        ('available', 'Available'),
        ('in_service', 'In Service'),
        ('full', 'Full - Ready for Pickup'),
        ('in_transit', 'In Transit'),
        ('being_serviced', 'Being Serviced'),
        ('maintenance', 'Maintenance'),
        ('warehouse', 'Warehouse'),
        ('lost', 'Lost/Written Off'),
        ('retired', 'Retired')
    ], string="To Status")

    from_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="From Location"
    )
    to_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="To Location"
    )

    from_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="From Customer"
    )
    to_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="To Customer"
    )

    # ============================================================================
    # METADATA
    # ============================================================================
    performed_by_id = fields.Many2one(
        comodel_name='res.users',
        string="Performed By",
        default=lambda self: self.env.user
    )
    reason = fields.Text(
        string="Reason/Notes"
    )

    # Related fields for reporting
    bin_barcode = fields.Char(
        related='bin_id.barcode',
        string="Bin Barcode",
        store=True
    )
    bin_size = fields.Selection(
        related='bin_id.bin_size',
        string="Bin Size",
        store=True
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('bin_id.barcode', 'from_status', 'to_status', 'movement_date')
    def _compute_display_name(self):
        for record in self:
            from_label = dict(record._fields['from_status'].selection).get(record.from_status, record.from_status or '')
            to_label = dict(record._fields['to_status'].selection).get(record.to_status, record.to_status or '')
            date_str = record.movement_date.strftime('%Y-%m-%d %H:%M') if record.movement_date else ''
            record.display_name = _("%s: %s → %s (%s)") % (
                record.bin_id.barcode or 'Unknown',
                from_label,
                to_label,
                date_str
            )
