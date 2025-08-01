# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Photo(models.Model):
    _name = 'photo'
    _description = 'Photo Attachment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(string='Photo Name', required=True, tracking=True)
    description = fields.Text(string='Description')

    # File attachment
    image = fields.Binary(string='Photo', required=True)
    filename = fields.Char(string='Filename')

    # Related Mobile Bin Key Wizard (the inverse field that was missing)
    mobile_bin_key_wizard_id = fields.Many2one(
        'mobile.bin.key.wizard', 
        string='Mobile Bin Key Wizard', 
        ondelete='cascade'
    )

    # User who uploaded the photo
    user_id = fields.Many2one(
        'res.users', 
        string='Uploaded By', 
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )

    # Timestamps
    date_created = fields.Datetime(
        string='Upload Date', 
        default=fields.Datetime.now,
        required=True
    )

    # Photo metadata
    photo_type = fields.Selection([
        ('identification', 'Identification'),
        ('verification', 'Verification'),
        ('documentation', 'Documentation'),
        ('evidence', 'Evidence')
    ], string='Photo Type', default='documentation')

    # Company
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # Control fields
    active = fields.Boolean(default=True)

    # Computed fields
    display_name = fields.Char(
        string='Display Name', 
        compute='_compute_display_name', 
        store=True
    )

    @api.depends('name', 'date_created')
    def _compute_display_name(self):
        """Compute display name for photo records."""
        for record in self:
            if record.name and record.date_created:
                date_str = record.date_created.strftime('%Y-%m-%d')
                record.display_name = f"{record.name} ({date_str})"
            else:
                record.display_name = record.name or _('New Photo')
