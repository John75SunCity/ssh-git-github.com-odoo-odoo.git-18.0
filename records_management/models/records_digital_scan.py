# -*- coding: utf-8 -*-
"""
Digital Scan of Document
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class RecordsDigitalScan(models.Model):
    """
    Digital Scan of Document
    """

    _name = "records.digital.scan"
    _description = "Digital Scan of Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Name", required=True, tracking=True, index=True, unique=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
        index=True,
    )

    # ============================================================================
    # DOCUMENT RELATIONSHIP
    # ============================================================================
    document_id = fields.Many2one(
        "records.document", string="Document", required=True, tracking=True
    )

    # ============================================================================
    # DIGITAL SCAN FIELDS
    # ============================================================================
    description = fields.Text(string="Description")
    notes = fields.Text(string="Notes")
    record_date = fields.Date(
        string="Record Date",
        default=lambda self: fields.Date.context_today(self),
        tracking=True,
    )
    scan_date = fields.Datetime(
        string="Scan Date",
        default=lambda self: fields.Datetime.context_timestamp(self, datetime.now()),
        tracking=True,
    )

    file_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("jpeg", "JPEG"),
            ("png", "PNG"),
            ("tiff", "TIFF"),
            ("bmp", "BMP"),
        ],
        string="File Format",
        default="pdf",
        tracking=True,
    )

    resolution = fields.Integer(string="Resolution (DPI)", default=300)
    file_size = fields.Float(string="File Size (MB)")

    scan_quality = fields.Selection(
        [
            ("draft", "Draft"),
            ("normal", "Normal"),
            ("high", "High Quality"),
            ("archive", "Archive Quality"),
        ],
        string="Scan Quality",
        default="normal",
        tracking=True,
    )

    scanner_id = fields.Char(
        string="Scanner ID",
        help="Identifier of the scanner device used for this digital scan.",
    )
    scanned_by_id = fields.Many2one(
        "res.users",
        string="Scanned By",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # OPERATIONAL FIELDS
    # ============================================================================
    sequence = fields.Integer(string="Sequence", default=10)
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date", default=fields.Datetime.now)
    confirmed = fields.Boolean(string="Confirmed", default=False, tracking=True)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS (REQUIRED)
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the digital scan record"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only confirm draft scans"))

        self.write(
            {
                "state": "confirmed",
                "confirmed": True,
                "updated_date": fields.Datetime.now(),
            }
        )

        # Log activity
        self.message_post(
            body=_("Digital scan confirmed by %s", self.env.user.name),
            message_type="notification",
        )

    def action_done(self):
        """Mark the digital scan as completed"""
        self.ensure_one()
        if self.state not in ["draft", "confirmed"]:
            raise UserError(_("Can only complete draft or confirmed scans"))

        self.write({"state": "done", "updated_date": fields.Datetime.now()})

        # Log activity
        self.message_post(
            body=_("Digital scan completed by %s", self.env.user.name),
            message_type="notification",
        )

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.ensure_one()
        self.write(
            {
                "state": "draft",
                "confirmed": False,
                "updated_date": fields.Datetime.now(),
            }
        )

        # Log activity
        self.message_post(
            body=_("Digital scan reset to draft by %s", self.env.user.name),
            message_type="notification",
        )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("file_size", "resolution")
    def _compute_scan_info(self):
        """Compute scan information display"""
        for record in self:
            info_parts = []
            if record.resolution:
                info_parts.append(_("%s DPI", record.resolution))
            if record.file_size:
                info_parts.append(_("%.2f MB", record.file_size))
            record.scan_info = (
                " - ".join(info_parts) if info_parts else _("No scan info")
            )

    scan_info = fields.Char(
        string="Scan Info",
        compute="_compute_scan_info",
        store=True,
        readonly=True,
        help="Displays a summary of the scan's resolution and file size.",
    )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("file_size")
    def _check_file_size(self):
        for record in self:
            if record.file_size and record.file_size < 0:
                raise ValidationError(_("File size cannot be negative"))
            if record.file_size and record.file_size > 1000:  # 1GB limit
                raise ValidationError(_("File size cannot exceed 1000 MB"))

    @api.constrains("resolution")
    def _check_resolution(self):
        for record in self:
            if record.resolution and record.resolution < 50:
                raise ValidationError(_("Resolution must be at least 50 DPI"))
            if record.resolution and record.resolution > 10000:
                raise ValidationError(_("Resolution cannot exceed 10000 DPI"))
