from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class MobilePhoto(models.Model):
    _name = 'mobile.photo'
    _description = 'Mobile Photo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    wizard_id = fields.Many2one()
    mobile_bin_key_wizard_id = fields.Many2one()
    photo_data = fields.Binary()
    photo_filename = fields.Char()
    photo_date = fields.Datetime()
    gps_latitude = fields.Float()
    gps_longitude = fields.Float()
    photo_type = fields.Selection()
    device_info = fields.Char()
    file_size = fields.Integer()
    resolution = fields.Char()
    has_gps = fields.Boolean()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_has_gps(self):
            """Check if photo has GPS coordinates""":
            for record in self:
                record.has_gps = bool(record.gps_latitude and record.gps_longitude)

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_gps_latitude(self):
            """Validate GPS latitude range"""
            for record in self:
                if record.gps_latitude and not -90 <= record.gps_latitude <= 90:
                    raise ValidationError(_('GPS latitude must be between -90 and 90 degrees'))


    def _check_gps_longitude(self):
            """Validate GPS longitude range"""
            for record in self:
                if record.gps_longitude and not -180 <= record.gps_longitude <= 180:
                    raise ValidationError(_('GPS longitude must be between -180 and 180 degrees'))


    def _check_file_size(self):
            """Validate reasonable file size limits"""
            for record in self:
                if record.file_size and record.file_size > 50 * 1024 * 1024:  # 50MB limit
                    raise ValidationError(_('Photo file size cannot exceed 50MB'))
                if record.file_size and record.file_size < 0:
                    raise ValidationError(_('Photo file size cannot be negative'))

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_view_photo(self):
            """Open photo in full view"""
            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Photo: %s', self.name),
                'res_model': 'mobile.photo',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',



    def action_download_photo(self):
            """Download photo file"""
            self.ensure_one()
            if not self.photo_data:
                raise ValidationError(_('No photo data available to download'))

            return {}
                'type': 'ir.actions.act_url',
                'url': '/web/content/mobile.photo/%s/photo_data/%s?download=true' % ()
                    self.id, self.photo_filename or 'photo.jpg'

                'target': 'self',


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_gps_coordinates_string(self):
            """Get formatted GPS coordinates string"""
            self.ensure_one()
            if self.has_gps:
                return _("Lat: %s, Lon: %s", self.gps_latitude, self.gps_longitude)
            return _("No GPS coordinates available")


    def create_from_mobile_data(self, mobile_data):
            """Create photo from mobile device data"""
            vals = {}
                'name': mobile_data.get('name', _('Mobile Photo')),
                'photo_data': mobile_data.get('photo_data'),
                'photo_filename': mobile_data.get('filename'),
                'photo_type': mobile_data.get('photo_type', 'other'),
                'gps_latitude': mobile_data.get('gps_latitude'),
                'gps_longitude': mobile_data.get('gps_longitude'),
                'device_info': mobile_data.get('device_info'),
                'file_size': mobile_data.get('file_size'),
                'resolution': mobile_data.get('resolution'),


            # Associate with wizard if provided:
            if mobile_data.get('wizard_id'):
                vals['wizard_id'] = mobile_data['wizard_id']
                vals['mobile_bin_key_wizard_id'] = mobile_data['wizard_id']

            return self.create(vals)

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom display name"""
            result = []
            for record in self:
                name_parts = [record.name]

                if record.photo_type:
                    type_label = dict(record._fields['photo_type'].selection).get()
                        record.photo_type, record.photo_type

                    name_parts.append(_("(%s)", type_label))

                if record.photo_date:
                    name_parts.append(record.photo_date.strftime("- %Y-%m-%d"))

                result.append((record.id, " ".join(name_parts)))
            return result


    def get_photos_for_wizard(self, wizard_id):
            """Get all photos for a specific wizard""":
            domain = []
                '|',
                ('wizard_id', '=', wizard_id),
                ('mobile_bin_key_wizard_id', '=', wizard_id)

            return self.search(domain, order='photo_date desc')


    def get_photo_metadata(self):
            """Get comprehensive photo metadata"""
            self.ensure_one()
            return {}
                'name': self.name,
                'type': self.photo_type,
                'date': self.photo_date,
                'has_gps': self.has_gps,
                'gps_coordinates': self.get_gps_coordinates_string(),
                'device_info': self.device_info or _('Unknown device'),
                'file_size': self.file_size,
                'resolution': self.resolution,
                'filename': self.photo_filename)))))))))))))

