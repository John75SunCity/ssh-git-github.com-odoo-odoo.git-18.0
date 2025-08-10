# -*- coding: utf-8 -*-
"""
Photo Attachment Management Module

This module provides comprehensive photo attachment management for the Records
Management System with integration to mobile workflows and partner relationships.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class Photo(models.Model):
    """
    Photo Attachment Management

    Manages photo attachments with metadata, relationships, and mobile integration
    for comprehensive document and workflow support.
    """

    _name = "photo"
    _description = "Photo Attachment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Photo Name",
        required=True,
        tracking=True,
        index=True,
        default="New Photo",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # PHOTO CONTENT FIELDS
    # ============================================================================
    description = fields.Text(string="Description", tracking=True)

    # File attachment fields
    image = fields.Binary(string="Image", attachment=True, help="The photo image file")
    image_filename = fields.Char(
        string="Image Filename", help="Original filename of the uploaded image"
    )

    # ============================================================================
    # METADATA FIELDS
    # ============================================================================
    date = fields.Datetime(
        string="Date Taken", default=fields.Datetime.now, required=True, tracking=True
    )
    location = fields.Char(string="Location", help="Where the photo was taken")
    tags = fields.Char(string="Tags", help="Comma-separated tags for categorization")

    # ============================================================================
    # TECHNICAL METADATA FIELDS
    # ============================================================================
    file_size = fields.Integer(
        string="File Size (bytes)",
        readonly=True,
        compute="_compute_file_info",
        store=True,
    )
    file_type = fields.Char(
        string="File Type",
        readonly=True,
        help="MIME type of the image file",
        compute="_compute_file_info",
        store=True,
    )
    resolution = fields.Char(
        string="Resolution",
        readonly=True,
        help="Image resolution (width x height)",
        compute="_compute_resolution",
        store=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    mobile_bin_key_wizard_id = fields.Many2one(
        "mobile.bin.key.wizard",
        string="Mobile Bin Key Wizard",
        help="Related mobile workflow wizard",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Related Partner",
        tracking=True,
        help="Customer or partner associated with this photo",
    )

    # ============================================================================
    # WORKFLOW FIELDS
    # ============================================================================
    state = fields.Selection(
        [("draft", "Draft"), ("validated", "Validated"), ("archived", "Archived")],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CATEGORIZATION FIELDS
    # ============================================================================
    category = fields.Selection(
        [
            ("document", "Document Photo"),
            ("location", "Location Photo"),
            ("equipment", "Equipment Photo"),
            ("damage", "Damage Photo"),
            ("verification", "Verification Photo"),
            ("general", "General Photo"),
        ],
        string="Category",
        default="general",
        tracking=True,
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("image", "image_filename")
    def _compute_file_info(self):
        """Compute file size and type from binary data"""
        for record in self:
            if record.image:
                # Calculate file size
                record.file_size = len(record.image) if record.image else 0

                # Determine file type from filename
                if record.image_filename:
                    file_extension = record.image_filename.split(".")[-1].lower()
                    mime_types = {
                        "jpg": "image/jpeg",
                        "jpeg": "image/jpeg",
                        "png": "image/png",
                        "gif": "image/gif",
                        "bmp": "image/bmp",
                        "webp": "image/webp",
                    }
                    record.file_type = mime_types.get(file_extension, "unknown")
                else:
            pass
            pass
                    record.file_type = "unknown"
            else:
            pass
                record.file_size = 0
                record.file_type = False

    @api.depends("image")
    def _compute_resolution(self):
        """Compute image resolution from binary data"""
        for record in self:
            if not record.image:
                record.resolution = False
                continue

            try:
                # Try to use Pillow if available
                try:
                    from PIL import Image
                    import io

                    image_data = io.BytesIO(record.image)
                    img = Image.open(image_data)
                    record.resolution = f"{img.width}x{img.height}"
                except ImportError:
                    # Fallback if Pillow not available
                    _logger.warning(
                        "Pillow not installed, cannot compute image resolution"
                    )
                    record.resolution = "Unknown"
                except Exception as e:
                    _logger.warning(f"Failed to compute resolution: {e}")
                    record.resolution = "Error"
            except Exception:
                record.resolution = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_validate_photo(self):
        """Validate the photo and move to validated state"""
        self.ensure_one()
        if not self.image:
            raise UserError(_("Cannot validate photo without an image"))
        if self.state != "draft":
            raise UserError(_("Only draft photos can be validated"))

        self.write({"state": "validated"})
        self.message_post(body=_("Photo validated"))

    def action_archive_photo(self):
        """Archive the photo"""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Photo is already archived"))

        self.write({"state": "archived"})
        self.message_post(body=_("Photo archived"))

    def action_download_photo(self):
        """Download the photo"""
        self.ensure_one()
        if not self.image:
            raise UserError(_("No image to download"))

        filename = self.image_filename or f"photo_{self.id}.jpg"
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/photo/{self.id}/image/{filename}",
            "target": "new",
        }

    def action_view_metadata(self):
        """View detailed photo metadata"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Photo Metadata"),
            "res_model": "photo",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create for automatic photo numbering"""
        for vals in vals_list:
            if vals.get("name", "New Photo") == "New Photo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("photo") or "New Photo"
                )

        photos = super().create(vals_list)

        # Compute file info after creation
        photos._compute_file_info()
        photos._compute_resolution()

        return photos

    def write(self, vals):
        """Override write for file info updates"""
        result = super().write(vals)

        # Recompute file info if image changed
        if "image" in vals or "image_filename" in vals:
            self._compute_file_info()
            self._compute_resolution()

        return result

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name or _("Unnamed Photo")
            if record.category:
                category_dict = dict(record._fields["category"].selection)
                name += _(" (%s)"
            if record.date:
                name += _(" - %s"
            result.append((record.id, name))
        return result

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("image", "image_filename")
    def _check_image_requirements(self):
        """Validate image and filename consistency"""
        for record in self:
            if record.image and not record.image_filename:
                raise ValidationError(
                    _("Image filename is required when image is provided")
                )

            if record.image_filename and not record.image:
                raise ValidationError(_("Image is required when filename is provided"))

    @api.constrains("file_size")
    def _check_file_size(self):
        """Validate reasonable file size limits"""
        max_size = 10 * 1024 * 1024  # 10MB limit
        for record in self:
            if record.file_size and record.file_size > max_size:
                raise ValidationError(_("Image file size cannot exceed 10MB"))

    @api.constrains("date")
    def _check_date(self):
        """Validate photo date is not in the future"""
        for record in self:
            if record.date and record.date > fields.Datetime.now():
                raise ValidationError(_("Photo date cannot be in the future"))

    @api.constrains("tags")
    def _check_tags(self):
        """Validate tags format"""
        for record in self:
            if record.tags:
                # Basic validation - could be enhanced
                if len(record.tags) > 255:
                    raise ValidationError(
                        _("Tags field is too long (max 255 characters)")
                    )
