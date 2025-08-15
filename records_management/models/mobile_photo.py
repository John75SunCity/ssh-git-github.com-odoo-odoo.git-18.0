# -*- coding: utf-8 -*-
"""
Mobile Photo Model

Photo attachments for mobile bin key operations and field service work.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MobilePhoto(models.Model):
    """Photo attachment for mobile operations"""

    _name = "mobile.photo"
    _description = "Mobile Photo"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Photo Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or description of the photo"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this photo"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    wizard_id = fields.Many2one(
        "mobile.bin.key.wizard",
        string="Bin Key Wizard",
        help="Associated mobile bin key wizard"
    )

    mobile_bin_key_wizard_id = fields.Many2one(
        "mobile.bin.key.wizard",
        string="Mobile Bin Key Wizard",
        help="Associated mobile bin key wizard (alternative field name)"
    )

    # ============================================================================
    # PHOTO FIELDS
    # ============================================================================
    photo_data = fields.Binary(
        string="Photo",
        required=True,
        help="Photo image data"
    )

    photo_filename = fields.Char(
        string="Filename",
        help="Original photo filename"
    )

    photo_date = fields.Datetime(
        string="Photo Date",
        default=fields.Datetime.now,
        required=True,
        help="Date and time when photo was taken"
    )

    gps_latitude = fields.Float(
        string="GPS Latitude",
        help="GPS latitude where photo was taken"
    )

    gps_longitude = fields.Float(
        string="GPS Longitude", 
        help="GPS longitude where photo was taken"
    )

    photo_type = fields.Selection([
        ('before', 'Before'),
        ('during', 'During Work'),
        ('after', 'After'),
        ('evidence', 'Evidence'),
        ('damage', 'Damage Documentation'),
        ('other', 'Other')
    ], string='Photo Type', default='other', required=True)

    # ============================================================================
    # METADATA FIELDS
    # ============================================================================
    device_info = fields.Char(
        string="Device Info",
        help="Information about the device used to take the photo"
    )

    file_size = fields.Integer(
        string="File Size (bytes)",
        help="Size of the photo file"
    )

    resolution = fields.Char(
        string="Resolution",
        help="Photo resolution (e.g., '1920x1080')"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('gps_latitude', 'gps_longitude')
    def _compute_has_gps(self):
        """Check if photo has GPS coordinates"""
        for record in self:
            record.has_gps = bool(record.gps_latitude and record.gps_longitude)

    has_gps = fields.Boolean(
        string="Has GPS",
        compute='_compute_has_gps',
        help="Whether photo has GPS coordinates"
    )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('gps_latitude')
    def _check_gps_latitude(self):
        """Validate GPS latitude range"""
        for record in self:
            if record.gps_latitude and not (-90 <= record.gps_latitude <= 90):
                raise ValidationError(_('GPS latitude must be between -90 and 90 degrees'))

    @api.constrains('gps_longitude')
    def _check_gps_longitude(self):
        """Validate GPS longitude range"""
        for record in self:
            if record.gps_longitude and not (-180 <= record.gps_longitude <= 180):
                raise ValidationError(_('GPS longitude must be between -180 and 180 degrees'))
