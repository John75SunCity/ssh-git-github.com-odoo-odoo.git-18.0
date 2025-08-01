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
    action_confirm = fields.Char(string='Action Confirm')
    action_done = fields.Char(string='Action Done')
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    confirmed = fields.Boolean(string='Confirmed', default=False)
    done = fields.Char(string='Done')
    draft = fields.Char(string='Draft')
    group_document = fields.Char(string='Group Document')
    group_format = fields.Char(string='Group Format')
    group_scanned_by = fields.Char(string='Group Scanned By')
    group_state = fields.Selection([], string='Group State')  # TODO: Define selection options
    help = fields.Char(string='Help')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    my_scans = fields.Char(string='My Scans')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    view_mode = fields.Char(string='View Mode')

def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

def action_done(self):
            """Mark as done"""
            self.write({'state': 'done'})
