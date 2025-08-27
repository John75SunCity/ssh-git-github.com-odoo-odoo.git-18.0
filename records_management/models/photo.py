import base64
import io

from PIL import Image

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class Photo(models.Model):
    _name = 'photo'
    _description = 'Photo Attachment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True, default='New Photo')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    image = fields.Binary(string='Image', required=True)
    image_filename = fields.Char(string='Image Filename')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    location = fields.Char(string='Location')
    tags = fields.Char(string='Tags', help='Comma-separated tags')
    file_size = fields.Integer(string='File Size (bytes)', compute='_compute_file_info', store=True)
    file_type = fields.Char(string='File Type', compute='_compute_file_info', store=True)
    resolution = fields.Char(string='Resolution', compute='_compute_resolution', store=True)
    mobile_wizard_reference = fields.Char(string='Mobile Wizard Reference', help="Reference to the mobile wizard")
    partner_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('archived', 'Archived')
    ], string='State', default='draft', tracking=True)
    category = fields.Selection([
        ('compliance', 'Compliance'),
        ('before', 'Before Service'),
        ('during', 'During Service'),
        ('after', 'After Service'),
        ('damage', 'Damage Documentation'),
        ('general', 'General')
    ], string='Category', default='general')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('image')
    def _compute_file_info(self):
        """Compute file size and type from binary data"""
        for record in self:
            if record.image:
                # Decode base64 to get actual file size
                try:
                    image_data = base64.b64decode(record.image)
                    record.file_size = len(image_data)
                    record.file_type = 'image'
                except Exception:
                    record.file_size = 0
                    record.file_type = 'unknown'
            else:
                record.file_size = 0
                record.file_type = False

    @api.depends('image')
    def _compute_resolution(self):
        """Compute image resolution from binary data"""
        for record in self:
            if record.image:
                try:
                    image_data = base64.b64decode(record.image)
                    image = Image.open(io.BytesIO(image_data))
                    record.resolution = f"{image.width}x{image.height}"
                except Exception:
                    record.resolution = 'Unknown'
            else:
                record.resolution = False

    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_validate_photo(self):
        """Validate the photo and move to validated state"""
        self.ensure_one()
        for record in self:
            record.state = 'validated'
            record.message_post(body=_("Photo validated: %s") % record.name)

    def action_archive_photo(self):
        """Archive the photo"""
        self.ensure_one()
        for record in self:
            record.state = 'archived'
            record.active = False
            record.message_post(body=_("Photo archived: %s") % record.name)

    def action_unarchive_photo(self):
        """Unarchive the photo"""
        self.ensure_one()
        for record in self:
            record.state = 'draft'
            record.active = True
            record.message_post(body=_("Photo unarchived: %s") % record.name)

    def action_download_photo(self):
        """Download the photo"""
        self.ensure_one()
        if not self.image:
            raise UserError(_('No image attached to this photo.'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=photo&id={self.id}&field=image&download=true&filename={self.image_filename or "photo.jpg"}',
            'target': 'self',
        }

    def action_view_metadata(self):
        """View detailed photo metadata"""
        self.ensure_one()
        metadata = self.get_photo_metadata()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Photo Metadata'),
            'res_model': 'photo.metadata.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_metadata': str(metadata)}
        }

    def action_set_category(self):
        """Open wizard to set photo category"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Set Photo Category'),
            'res_model': 'photo.category.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_photo_ids': [(6, 0, self.ids)]}
        }

    def action_bulk_tag_photos(self):
        """Bulk tag multiple photos"""
        # Note: This method is for bulk operations, so no ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bulk Tag Photos'),
            'res_model': 'photo.tag.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_photo_ids': [(6, 0, self.ids)]}
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_photo_metadata(self):
        """Get comprehensive photo metadata for reporting or API use."""
        self.ensure_one()
        return {
            'name': self.name,
            'filename': self.image_filename,
            'date': self.date.isoformat() if self.date else None,
            'location': self.location,
            'tags': self.tags.split(',') if self.tags else [],
            'file_size': self.file_size,
            'file_type': self.file_type,
            'resolution': self.resolution,
            'category': self.category,
            'state': self.state,
            'user': self.user_id.name,
            'partner': self.partner_id.name if self.partner_id else None,
            'description': self.description,
        }

    def duplicate_photo(self):
        """Create a duplicate of this photo, including its image."""
        self.ensure_one()
        return self.copy({
            'name': _('%s (Copy)') % self.name,
            'state': 'draft'
        })

    def get_image_thumbnail(self, size=(150, 150)):
        """Get a thumbnail version of the image."""
        self.ensure_one()
        if not self.image:
            return False

        try:
            image_data = base64.b64decode(self.image)
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            thumbnail_data = output.getvalue()

            return base64.b64encode(thumbnail_data)
        except Exception:
            return False

    @api.model
    def get_photos_by_category(self, category):
        """Get active photos filtered by a specific category."""
        return self.search([('category', '=', category), ('active', '=', True)])

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create for automatic photo numbering and audit trail."""
        for vals in vals_list:
            if vals.get('name', 'New Photo') == 'New Photo':
                vals['name'] = self.env['ir.sequence'].next_by_code('photo') or _('New Photo')

        photos = super().create(vals_list)
        for photo in photos:
            photo.message_post(body=_("Photo created: %s") % photo.name)
        return photos

    def write(self, vals):
        """Override write for file info updates and detailed audit trail."""
        result = super().write(vals)

        # Log significant changes
        if 'state' in vals:
            for record in self:
                record.message_post(body=_("Photo state changed to: %s") % record.state)

        if 'category' in vals:
            for record in self:
                record.message_post(body=_("Photo category changed to: %s") % record.category)

        return result

    def unlink(self):
        """Override unlink to prevent deletion of validated or archived photos."""
        for photo in self:
            if photo.state in ['validated', 'archived']:
                raise UserError(_(
                    "Cannot delete photo '%s' because it is in the '%s' state. Please reset it to draft first."
                ) % (photo.name, photo.state))
        return super().unlink()

    def name_get(self):
        """Custom name display with category and date for better context."""
        result = []
        for record in self:
            name = record.name or _('Unnamed Photo')
            if record.category and record.category != 'general':
                name = f"[{dict(self._fields['category'].selection)[record.category]}] {name}"
            if record.date:
                name = f"{name} ({record.date.strftime('%Y-%m-%d')})"
            result.append((record.id, name))
        return result

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('image', 'image_filename')
    def _check_image_requirements(self):
        """Validate image and filename consistency."""
        for record in self:
            if record.image and not record.image_filename:
                raise ValidationError(_('Image filename is required when an image is uploaded.'))

    @api.constrains('file_size')
    def _check_file_size(self):
        """Validate reasonable file size limits (e.g., 10MB)."""
        max_size = 10 * 1024 * 1024  # 10MB
        for record in self:
            if record.file_size and record.file_size > max_size:
                raise ValidationError(_('Image file size cannot exceed 10MB.'))

    @api.constrains('date')
    def _check_date(self):
        """Validate photo date is not in the future."""
        for record in self:
            if record.date and record.date > fields.Datetime.now():
                raise ValidationError(_('Photo date cannot be in the future.'))

    @api.constrains('tags')
    def _check_tags(self):
        """Validate tags format and length."""
        for record in self:
            if record.tags:
                if record.tags and len(record.tags) > 500:
                    raise ValidationError(_('Tags cannot exceed 500 characters.'))
                # Validate comma-separated format
                tags = [tag.strip() for tag in record.tags.split(',')]
                if any(len(tag) > 50 for tag in tags):
                    raise ValidationError(_('Individual tags cannot exceed 50 characters.'))

    @api.constrains('image_filename')
    def _check_image_filename(self):
        """Validate image filename extension."""
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        for record in self:
            if record.image_filename:
                file_extension = record.image_filename.split('.')[-1].lower()
                if file_extension not in allowed_extensions:
                    raise ValidationError(_(
                        "The image file must be one of the following types: %s."
                    ) % ', '.join(allowed_extensions))

    # ============================================================================
    # SEARCH METHODS
    # ============================================================================
    @api.model
    def _search_tags(self, operator, value):
        """Allow searching for photos by tags."""
        if operator not in ('ilike', 'like', '=', '!='):
            return [('id', '=', False)]
        return [('tags', operator, value)]
