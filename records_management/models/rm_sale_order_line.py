# -*- coding: utf-8 -*-
"""
Records Management Work Order Line Extension of sale.order.line

Extends sale.order.line to track which containers, bins, files, or documents
are associated with each line item.
"""

from odoo import api, fields, models, _


class RMSaleOrderLine(models.Model):
    """
    Extends sale.order.line for Records Management tracking.
    """
    _inherit = 'sale.order.line'

    # ============================================================================
    # RECORDS MANAGEMENT LINKS
    # ============================================================================
    container_id = fields.Many2one(
        comodel_name='records.container',
        string="Container",
        help="Container associated with this line item"
    )

    shredding_bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string="Shredding Bin",
        help="Shredding bin associated with this line item"
    )

    file_id = fields.Many2one(
        comodel_name='records.file',
        string="File",
        help="File associated with this line item"
    )

    document_id = fields.Many2one(
        comodel_name='records.document',
        string="Document",
        help="Document associated with this line item"
    )

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    service_date = fields.Date(
        string="Service Date",
        help="Date this specific service was performed"
    )

    weight_lbs = fields.Float(
        string="Weight (lbs)",
        digits=(10, 2),
        help="Weight in pounds for this line item"
    )

    bin_size = fields.Selection([
        ('23', '23 Gallon'),
        ('32g', '32 Gallon Bin'),
        ('32c', '32 Gallon Console'),
        ('64', '64 Gallon'),
        ('96', '96 Gallon'),
    ], string="Bin Size",
       help="Size of shredding bin for bin service lines"
    )

    fill_level = fields.Selection([
        ('0', 'Empty'),
        ('25', '25%'),
        ('50', '50%'),
        ('75', '75%'),
        ('100', 'Full'),
    ], string="Fill Level",
       help="Fill level of bin when serviced"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    is_rm_line = fields.Boolean(
        string="Is RM Line",
        compute='_compute_is_rm_line',
        store=True,
        help="Line is associated with records management"
    )

    @api.depends('container_id', 'shredding_bin_id', 'file_id', 'document_id')
    def _compute_is_rm_line(self):
        for line in self:
            line.is_rm_line = bool(
                line.container_id or
                line.shredding_bin_id or
                line.file_id or
                line.document_id
            )

    # ============================================================================
    # HELPERS
    # ============================================================================
    def _get_rm_description_suffix(self):
        """Get additional description based on RM links."""
        self.ensure_one()
        parts = []
        if self.container_id:
            parts.append(f"Container: {self.container_id.name or self.container_id.barcode}")
        if self.shredding_bin_id:
            parts.append(f"Bin: {self.shredding_bin_id.barcode}")
        if self.file_id:
            parts.append(f"File: {self.file_id.name}")
        if self.weight_lbs:
            parts.append(f"Weight: {self.weight_lbs} lbs")
        return ' | '.join(parts) if parts else ''
