# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    Photo Attachment Management Module
    This module provides comprehensive photo attachment management for the Records:
    pass
Management System with integration to mobile workflows and partner relationships.
    import logging
    import io
    try:
    from PIL import Image
except ImportError:
    Image = None
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    _logger = logging.getLogger(__name__)
    class Photo(models.Model):

        Photo Attachment Management

    Manages photo attachments with metadata, relationships, and mobile integration
        for comprehensive document and workflow support.:


    _name = "photo"

"
    _description = "photo"

"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "photo"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Photo Attachment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, name"
    _rec_name = "name"
""
        # ============================================================================""
    # CORE IDENTIFICATION FIELDS""
        # ============================================================================""
    name = fields.Char(""
        string="Photo Name",
        required=True,""
        tracking=True,""
        index=True,""
        default="New Photo",
    ""
    company_id = fields.Many2one(""
        "res.company",
        string="Company",
        default=lambda self: self.env.company,""
        required=True,""
    ""
    user_id = fields.Many2one(""
        "res.users",
        string="User",
        default=lambda self: self.env.user,""
        tracking=True""
    ""
    active = fields.Boolean(""
        string="Active",
        default=True,""
        tracking=True""
    ""
""
        # ============================================================================""
    # PHOTO CONTENT FIELDS""
        # ============================================================================""
    description = fields.Text(""
        string="Description",
        tracking=True""
    ""
""
        # File attachment fields""
    image = fields.Binary(""
        string="Image",
        attachment=True,""
        help="The photo image file"
    ""
    image_filename = fields.Char(""
        string="Image Filename",
        help="Original filename of the uploaded image"
    ""
""
        # ============================================================================""
    # METADATA FIELDS""
        # ============================================================================""
    date = fields.Datetime(""
        string="Date Taken",
        default=fields.Datetime.now,""
        required=True,""
        tracking=True""
    ""
    location = fields.Char(""
        string="Location",
        help="Where the photo was taken"
    ""
    tags = fields.Char(""
        string="Tags",
        help="Comma-separated tags for categorization":
    ""
""
        # ============================================================================""
    # TECHNICAL METADATA FIELDS""
        # ============================================================================""
    file_size = fields.Integer(""
    string="File Size (bytes)",
        readonly=True,""
        compute="_compute_file_info",
        store=True,""
    ""
    file_type = fields.Char(""
        string="File Type",
        readonly=True,""
        help="MIME type of the image file",
        compute="_compute_file_info",
        store=True,""
    ""
    resolution = fields.Char(""
        string="Resolution",
        readonly=True,""
        ,""
    help="Image resolution (width x height)",
        compute="_compute_resolution",
        store=True,""
    ""
""
        # ============================================================================""
    # RELATIONSHIP FIELDS""
        # ============================================================================""
    mobile_bin_key_wizard_id = fields.Many2one(""
        "mobile.bin.key.wizard",
        string="Mobile Bin Key Wizard",
        help="Related mobile workflow wizard",
    ""
    partner_id = fields.Many2one(""
        "res.partner",
        string="Related Partner",
        tracking=True,""
        help="Customer or partner associated with this photo",
    ""
""
        # ============================================================================""
    # WORKFLOW FIELDS""
        # ============================================================================""
    ,""
    state = fields.Selection(""
        [)""
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("archived", "Archived")
        ""
        string="Status",
        default="draft",
        tracking=True,""
    ""
""
        # ============================================================================""
    # CATEGORIZATION FIELDS""
        # ============================================================================""
    category = fields.Selection(""
        [)""
            ("document", "Document Photo"),
            ("location", "Location Photo"),
            ("equipment", "Equipment Photo"),
            ("damage", "Damage Photo"),
            ("verification", "Verification Photo"),
            ("general", "General Photo"),
        ""
        string="Category",
        default="general",
        tracking=True,""
    ""
""
        # ============================================================================""
    # MAIL THREAD FRAMEWORK FIELDS""
        # ============================================================================""
    activity_ids = fields.One2many(""
        "mail.activity",
        "res_id",
        string="Activities",
    ""
    message_follower_ids = fields.One2many(""
        "mail.followers",
        "res_id",
        string="Followers",
    ""
    message_ids = fields.One2many(""
        "mail.message",
        "res_id",
        string="Messages",
    ""
    ,""
    context = fields.Char(string='Context'),""
    domain = fields.Char(string='Domain'),""
    help = fields.Char(string='Help'),""
    res_model = fields.Char(string='Res Model'),""
    type = fields.Selection([), string='Type')  # TODO: Define selection options""
    view_mode = fields.Char(string='View Mode')""
""
        # ============================================================================""
    # COMPUTE METHODS""
        # ============================================================================""
    @api.depends("image", "image_filename")
    def _compute_file_info(self):""
        """Compute file size and type from binary data"""
"""
""""
"""                    file_extension = record.image_filename.split(".")[-1).lower()
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                    mime_types = {}""
                        "jpg": "image/jpeg",
                        "jpeg": "image/jpeg",
                        "png": "image/png",
                        "gif": "image/gif",
                        "bmp": "image/bmp",
                        "webp": "image/webp",
                    ""
                    record.file_type = mime_types.get(file_extension, "unknown")
                else:""
                    record.file_type = "unknown"
            else:""
                record.file_size = 0""
                record.file_type = False""
""
    @api.depends("image")
    def _compute_resolution(self):""
        """Compute image resolution from binary data"""
    """"
"""                _logger.warning("Pillow library not installed, cannot compute image resolution.")"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
                record.resolution = "Unknown"
                continue""
""
            try:""
                image_data = io.BytesIO(record.image)""
                img = Image.open(image_data)""
                record.resolution = f"{img.width}x{img.height}"
            except Exception as e""
                _logger.warning("Failed to compute resolution for photo %s: %s", record.name, e)
                record.resolution = "Error"
""
    # ============================================================================""
        # ACTION METHODS""
    # ============================================================================""
    def action_validate_photo(self):""
        """Validate the photo and move to validated state"""
"""
""""
"""            raise UserError(_("Cannot validate a photo without an image."))
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        if self.state != "draft":
            raise UserError(_("Only draft photos can be validated."))
""
        self.write({"state": "validated"})
        self.message_post(body=_("Photo validated."))
""
    def action_archive_photo(self):""
        """Archive the photo"""
"""        if self.state == "archived":"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
            raise UserError(_("This photo is already archived."))
""
        self.write({"state": "archived"})
        self.message_post(body=_("Photo archived."))
""
    def action_unarchive_photo(self):""
        """Unarchive the photo"""
"""        if self.state != "archived":"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            raise UserError(_("Only archived photos can be unarchived."))
""
        self.write({"state": "validated"})
        self.message_post(body=_("Photo unarchived and set to validated."))
""
    def action_download_photo(self):""
        """Download the photo"""
""""
""""
"""            raise UserError(_("There is no image to download."))"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""
        filename = self.image_filename or _("photo_%s.jpg", self.id)
        return {}""
            "type": "ir.actions.act_url",
            "url": f"/web/content/photo/{self.id}/image?download=true&filename={filename}",
            "target": "new",
        ""
""
    def action_view_metadata(self):""
        """View detailed photo metadata"""
"""
""""
"""            "type": "ir.actions.act_window",
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            "name": _("Photo Metadata"),
            "res_model": "photo",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        ""
""
    def action_set_category(self):""
        """Open wizard to set photo category"""
""""
""""
"""            "type": "ir.actions.act_window","
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
            "name": _("Set Photo Category"),
            "res_model": "photo.category.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_photo_id": self.id, "default_category": self.category},
        ""
""
    def action_bulk_tag_photos(self):""
        """Bulk tag multiple photos"""
"""
""""
"""            "type": "ir.actions.act_window",
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            "name": _("Bulk Tag Photos"),
            "res_model": "photo.bulk.tag.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_photo_ids": [(6, 0, self.ids)},
        ""
""
    # ============================================================================""
        # BUSINESS METHODS""
    # ============================================================================""
    def get_photo_metadata(self):""
        """Get comprehensive photo metadata for reporting or API use."""
"""            "name": self.name,"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
            "category": self.category,
            "date": self.date,
            "location": self.location,
            "tags": self.tags.split(",") if self.tags else [],:
            "file_size": self.file_size,
            "file_type": self.file_type,
            "resolution": self.resolution,
            "partner": self.partner_id.name if self.partner_id else None,:
        ""
""
    def duplicate_photo(self):""
        """Create a duplicate of this photo, including its image."""
"""            "name": _("%s (Copy)", self.name),
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        new_photo.message_post(body=_("Duplicated from photo %s", self.name))
        return new_photo""
""
    def get_image_thumbnail(self, size=(150, 150)):""
        """Get a thumbnail version of the image."""
    """"
"""            _logger.warning("Pillow library not installed, cannot generate thumbnail.")"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
            _logger.warning("Failed to generate thumbnail for photo %s: %s", self.name, e)
            return False""
""
    # ============================================================================ """"
        # ORM OVERRIDES"""""
    # ============================================================================ """"
    @api.model_create_multi"""""
    def create(self, vals_list):""
        """Override create for automatic photo numbering and audit trail."""
            if vals.get("name", "New Photo") == "New Photo":
                vals["name"] = self.env["ir.sequence"].next_by_code("photo") or _("New Photo")
        photos = super().create(vals_list)""
        for photo in photos:""
            photo.message_post(body=_("Photo created: %s", photo.name))
        return photos""
""
    def write(self, vals):""
        """Override write for file info updates and detailed audit trail."""
""""
"""                        "State changed from %s to %s.",
                        old_state_label,""
                        new_state_label,""
                    ""
                ""
""
            if 'category' in vals and old_values[record.id]['category'] != record.category:"
                old_cat_label = category_label_map.get(old_values[record.id]['category'], _('N/A'))"
                new_cat_label = category_label_map.get(record.category, _('N/A'))"
                record.message_post()""
                    body=_()""
                        "Category changed from %s to %s.",
                        old_cat_label,""
                        new_cat_label,""
                    ""
                ""
        return True""
""
    def unlink(self):""
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
""
    def name_get(self):""
        """Custom name display with category and date for better context."""
""""
"""
"""            name = record.name or _("Unnamed Photo")"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                if category_label:""
                    name = f"{name} ({category_label})"
            if record.date:""
                name = f"{name} - {record.date.strftime('%Y-%m-%d')}"
            result.append((record.id, name))""
        return result""
""
    # ============================================================================""
        # VALIDATION METHODS""
    # ============================================================================""
    @api.constrains("image", "image_filename")
    def _check_image_requirements(self):""
        """Validate image and filename consistency."""
"""                raise ValidationError(_("An image filename is required when an image is provided."))"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
                raise ValidationError(_("An image is required when a filename is provided."))
""
    @api.constrains("file_size")
    def _check_file_size(self):""
        """Validate reasonable file size limits (e.g., 10MB)."""
"""
""""
"""                raise ValidationError(_("Image file size cannot exceed 10MB."))"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""
    @api.constrains("date")
    def _check_date(self):""
        """Validate photo date is not in the future."""
"""                raise ValidationError(_("The photo date cannot be in the future."))"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
    @api.constrains("tags")
    def _check_tags(self):""
        """Validate tags format and length."""
"""                raise ValidationError(_("The tags field is too long (maximum 255 characters)."))"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
    @api.constrains("image_filename")
    def _check_image_filename(self):""
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
""
    # ============================================================================ """"
        # UTILITY & SEARCH METHODS""""""
    # ============================================================================ """"
    @api.model""""""
    def get_photos_by_category(self, category):""
        """Get active photos filtered by a specific category."""
        return self.search((("category", "=", category), ("active", "= """""
""""
""""
        """"""Get active photos associated with a specific partner.""""
        return self.search((("partner_id", "=", partner_id), ("active", "= """""
""""
""""
        """"""Get the most recently uploaded active photos.""""
        return self.search([("active", "=", True), limit=limit, order="date desc")
""
    @api.model""
    def _search_tags(self, operator, value):""
        """Allow searching for photos by tags."""
        if operator not in ('ilike', 'like', '=', '!= """"
            return [('"""id', '= """
        return [('"""tags', operator, value)"
""
    @api.model""
""""
""""
        """Get statistics about photos for reporting dashboards."""
            [('active', '= """', True),"
            ['""""
"""            [('active', '= """', True),""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
""""
            ['""""
"""            "total_photos": self.search_count((('active', '= """
            """"by_category": {res['category'][1]: res['category_count'] for res in read_group_category if res['category']},:"
            "by_state": {res['state'][1]: res['state_count'] for res in read_group_state if res['state']},:
            "total_file_size": sum(self.search((('active', '=', True)).mapped('file_size')),
        ""
        if stats["total_photos"] > 0:
            stats["average_file_size"] = stats["total_file_size"] / stats["total_photos"]
        else:""
            stats["average_file_size"] = 0
        return stats""
    ))))))))))))))))""
""""
""""
""""