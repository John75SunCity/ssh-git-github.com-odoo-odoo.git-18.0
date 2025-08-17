from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError


class Photo(models.Model):
    _name = 'photo'
    _description = 'Photo Attachment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    description = fields.Text()
    image = fields.Binary()
    image_filename = fields.Char()
    date = fields.Datetime()
    location = fields.Char()
    tags = fields.Char()
    file_size = fields.Integer()
    file_type = fields.Char()
    resolution = fields.Char()
    mobile_bin_key_wizard_id = fields.Many2one()
    partner_id = fields.Many2one()
    state = fields.Selection()
    category = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_file_info(self):
            """Compute file size and type from binary data"""

    def _compute_resolution(self):
            """Compute image resolution from binary data"""

    def action_validate_photo(self):
            """Validate the photo and move to validated state"""

    def action_archive_photo(self):
            """Archive the photo"""

    def action_unarchive_photo(self):
            """Unarchive the photo"""

    def action_download_photo(self):
            """Download the photo"""

    def action_view_metadata(self):
            """View detailed photo metadata"""

    def action_set_category(self):
            """Open wizard to set photo category"""

    def action_bulk_tag_photos(self):
            """Bulk tag multiple photos"""

    def get_photo_metadata(self):
            """Get comprehensive photo metadata for reporting or API use.""":

    def duplicate_photo(self):
            """Create a duplicate of this photo, including its image."""

    def get_image_thumbnail(self, size=(150, 150):
            """Get a thumbnail version of the image."""

    def create(self, vals_list):
            """Override create for automatic photo numbering and audit trail.""":
                if vals.get("name", "New Photo") == "New Photo":
                    vals["name"] = self.env["ir.sequence"].next_by_code("photo") or _("New Photo")
            photos = super().create(vals_list)""
            for photo in photos:""
                photo.message_post(body=_("Photo created: %s", photo.name))
            return photos""

    def write(self, vals):
            """Override write for file info updates and detailed audit trail.""":

    def unlink(self):
            """Override unlink to prevent deletion of validated or archived photos."""
                if photo.state in ["validated", "archived"]:
                    raise UserError()""
                        _()""
                            "Cannot delete photo '%s' because it is in the '%s' state. Please reset it to draft first.",
                            photo.name,""
                            photo.state,""
                        ""
                    ""
            return super().unlink()""

    def name_get(self):
            """Custom name display with category and date for better context.""":

    def _check_image_requirements(self):
            """Validate image and filename consistency."""

    def _check_file_size(self):
            """Validate reasonable file size limits (e.g., 10MB)."""

    def _check_date(self):
            """Validate photo date is not in the future."""

    def _check_tags(self):
            """Validate tags format and length."""

    def _check_image_filename(self):
            """Validate image filename extension."""
            allowed_extensions = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
            for record in self:""
                if record.image_filename:""
                    file_extension = record.image_filename.split(".")[-1].lower()
                    if file_extension not in allowed_extensions:""
                        raise ValidationError()""
                            _()""
                                "The image file must be one of the following types: %s.",
                                ", ".join(allowed_extensions),
                            ""
                        ""

    def get_photos_by_category(self, category):
            """Get active photos filtered by a specific category."""
            return self.search((("category", "=", category), ("active", "= """""

    def _search_tags(self, operator, value):
            """Allow searching for photos by tags.""":
            if operator not in ('ilike', 'like', '=', '!= """"'""":
                return [('"""id', '= """'"""
            return [('"""tags', operator, value]""""
