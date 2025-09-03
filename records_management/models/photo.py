from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import base64
import io
from PIL import Image


class Photo(models.Model):
    _name = "photo"
    _description = "Photo Attachment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, name"
    _rec_name = "name"

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, default="New Photo")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)

    # Image and file data
    image = fields.Binary(string="Photo", attachment=True)
    image_filename = fields.Char(string="Image Filename")
    file_size = fields.Integer(string="File Size (bytes)", compute="_compute_file_info", store=True)
    file_type = fields.Char(string="File Type", compute="_compute_file_info", store=True)
    resolution = fields.Char(string="Resolution", compute="_compute_resolution", store=True)

    # Metadata
    description = fields.Text(string="Description")
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    location = fields.Char(string="Location")
    tags = fields.Char(string="Tags", help="Comma-separated tags")
    category = fields.Selection(
        [("general", "General"), ("work", "Work"), ("personal", "Personal")], default="general", string="Category"
    )
    state = fields.Selection(
        [("draft", "Draft"), ("validated", "Validated"), ("archived", "Archived")], default="draft", string="State"
    )
    active = fields.Boolean(default=True, string="Active")

    # Related records
    partner_id = fields.Many2one("res.partner", string="Customer")
    task_id = fields.Many2one("project.task", string="Related Task")
    invoice_id = fields.Many2one("account.move", string="Related Invoice")
    sale_order_id = fields.Many2one("sale.order", string="Related Sale Order")
    maintenance_request_id = fields.Many2one("maintenance.request", string="Related Maintenance Request")
    reference_model = fields.Char(string="Reference Model")
    mobile_wizard_reference = fields.Char(string="Mobile Wizard Reference", help="Reference to the mobile wizard")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("image")
    def _compute_file_info(self):
        """Compute file size and type from binary data"""
        for record in self:
            if record.image:
                try:
                    image_data = base64.b64decode(record.image)
                    record.file_size = len(image_data)
                    record.file_type = "image"
                except Exception as e:
                    record.file_size = 0
                    record.file_type = "unknown"
                    record.message_post(body=_("Error computing file info: %s", e))
            else:
                record.file_size = 0
                record.file_type = False

    @api.depends("image")
    def _compute_resolution(self):
        """Compute image resolution from binary data"""
        for record in self:
            if record.image:
                try:
                    image_data = base64.b64decode(record.image)
                    image = Image.open(io.BytesIO(image_data))
                    record.resolution = "%sx%s" % (image.width, image.height)
                except Exception as e:
                    record.resolution = "Unknown"
                    record.message_post(body=_("Error computing resolution: %s", str(e)))
            else:
                record.resolution = False

    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_archive_photo(self):
        """Archive the photo"""
        self.ensure_one()
        self.write({"state": "archived"})
        self.message_post(body=_("Photo archived: %s", self.name))

    def action_unarchive_photo(self):
        """Unarchive the photo"""
        self.ensure_one()
        self.write({"state": "draft"})
        self.message_post(body=_("Photo unarchived: %s", self.name))

    def action_view_metadata(self):
        """View photo metadata"""
        self.ensure_one()
        metadata = {
            "name": self.name,
            "company": self.company_id.name if self.company_id else None,
            "user": self.user_id.name if self.user_id else None,
            "task": self.task_id.name if self.task_id else None,
            "invoice": self.invoice_id.name if self.invoice_id else None,
            "sale_order": self.sale_order_id.name if self.sale_order_id else None,
            "maintenance_request": self.maintenance_request_id.name if self.maintenance_request_id else None,
            "reference_model": self.reference_model,
        }
        return metadata

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_photo_metadata(self):
        """Get comprehensive photo metadata for reporting or API use."""
        self.ensure_one()
        return {
            "name": self.name,
            "filename": self.image_filename,
            "date": self.date.isoformat() if self.date else None,
            "location": self.location,
            "tags": self.tags.split(",") if self.tags else [],
            "file_size": self.file_size,
            "file_type": self.file_type,
            "resolution": self.resolution,
            "category": self.category,
            "state": self.state,
            "user": self.user_id.name,
            "partner": self.partner_id.name if self.partner_id else None,
            "description": self.description,
            "task": self.task_id.name if self.task_id else None,
            "invoice": self.invoice_id.name if self.invoice_id else None,
            "sale_order": self.sale_order_id.name if self.sale_order_id else None,
            "maintenance_request": self.maintenance_request_id.name if self.maintenance_request_id else None,
            "reference_model": self.reference_model,
        }

    def duplicate_photo(self):
        """Create a duplicate of this photo, including its image."""
        self.ensure_one()
        return self.copy({"name": _(" %s (Copy)", self.name), "state": "draft"})

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
            image.save(output, format="JPEG", quality=85)
            thumbnail_data = output.getvalue()

            return base64.b64encode(thumbnail_data)
        except Exception:
            return False

    @api.model
    def get_photos_by_category(self, category):
        """Get active photos filtered by a specific category."""
        return self.search([("category", "=", category), ("active", "=", True)])

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create for automatic photo numbering and audit trail."""
        for vals in vals_list:
            if vals.get("name", "New Photo") == "New Photo":
                sequence = self.env["ir.sequence"].search([("code", "=", "photo")], limit=1)
                if sequence:
                    vals["name"] = sequence.next_by_code("photo") or _("New Photo")
                else:
                    vals["name"] = _("New Photo")

        photos = super().create(vals_list)
        for photo in photos:
            photo.message_post(body=_("Photo created: %s", photo.name))
        return photos

    def write(self, vals):
        """Override write for file info updates and detailed audit trail."""
        result = super().write(vals)

        # Log significant changes
        if "state" in vals:
            for record in self:
                record.message_post(body=_("Photo state changed to: %s", record.state))

        if "category" in vals:
            for record in self:
                record.message_post(body=_("Photo category changed to: %s", record.category))

        return result

    def unlink(self):
        """Override unlink to prevent deletion of validated or archived photos."""
        for photo in self:
            if photo.state in ["validated", "archived"]:
                raise UserError(
                    _(
                        "Cannot delete photo '%s' because it is in the '%s' state. Please reset it to draft first.",
                        photo.name,
                        photo.state,
                    )
                )
        return super().unlink()

    def name_get(self):
        """Custom name display with category and date for better context."""
        result = []
        for record in self:
            name = record.name or _("Unnamed Photo")
            if record.category and record.category != "general":
                category_dict = dict(self._fields["category"].selection)
                name = _(" [%s] %s", category_dict.get(record.category, "Unknown"), name)
            if record.date:
                name = _(" %s (%s)", name, record.date.strftime("%Y-%m-%d"))
            result.append((record.id, name))
        return result

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains("file_size")
    def _check_file_size(self):
        """Validate reasonable file size limits (e.g., 10MB)."""
        max_size = 10 * 1024 * 1024  # 10MB
        for record in self:
            if record.file_size and record.file_size > max_size:
                raise ValidationError(_("Image file size cannot exceed 10MB."))

    @api.constrains("image_filename")
    def _check_image_filename(self):
        """Validate image filename extension."""
        allowed_extensions = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
        for record in self:
            if record.image_filename:
                file_extension = record.image_filename.split(".")[-1].lower()
                if file_extension not in allowed_extensions:
                    raise ValidationError(
                        _("The image file must be one of the following types: %s.", ", ".join(allowed_extensions))
                    )

    @api.constrains("tags")
    def _check_tags(self):
        """Validate comma-separated tags format and length."""
        for record in self:
            if record.tags:
                tags = [tag.strip() for tag in record.tags.split(",")]
                if any(len(tag) > 50 for tag in tags):
                    raise ValidationError(_("Individual tags cannot exceed 50 characters."))

    # ============================================================================
    # SEARCH METHODS
    # ============================================================================
    @api.model
    def _search_tags(self, operator, value):
        """Allow searching for photos by tags."""
        if operator not in ("ilike", "like", "=", "!="):
            return [("id", "=", False)]
        return [("tags", operator, value)]
