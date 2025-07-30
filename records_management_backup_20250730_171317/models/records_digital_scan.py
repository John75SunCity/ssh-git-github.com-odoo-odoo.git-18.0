# -*- coding: utf-8 -*-
"""
Digital Scan of Document
"""

from odoo import models, fields, api, _


class RecordsDigitalScan(models.Model):
    """
    Digital Scan of Document
    """

    _name = "records.digital.scan"
    _description = "Digital Scan of Document"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    
    # Relationships
    document_id = fields.Many2one('records.document', string='Document', required=True)
    
    # Digital scan specific fields
    scan_date = fields.Datetime(string='Scan Date', default=fields.Datetime.now)
    file_format = fields.Selection([
        ('pdf', 'PDF'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
        ('tiff', 'TIFF'),
        ('bmp', 'BMP')
    ], string='File Format', default='pdf')
    resolution = fields.Integer(string='Resolution (DPI)', default=300)
    file_size = fields.Float(string='File Size (MB)')
    scan_quality = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal'),
        ('high', 'High Quality'),
        ('archive', 'Archive Quality')
    ], string='Scan Quality', default='normal')
    scanner_id = fields.Char(string='Scanner ID')
    scanned_by = fields.Many2one('res.users', string='Scanned By', default=lambda self: self.env.user)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
