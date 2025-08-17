# -*- coding: utf-8 -*-

Scan Digital Asset Model

Digital assets created from document scanning operations.


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ScanDigitalAsset(models.Model):
    """Digital asset created from scanning operations"""

    _name = "scan.digital.asset"
    _description = "Scan Digital Asset"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Asset Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the digital asset"


    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True


    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this asset"


        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    work_order_id = fields.Many2one(
        "scan.retrieval.work.order",
        string="Scan Work Order",
        help="Associated scan retrieval work order"


        # ============================================================================
    # DIGITAL ASSET FIELDS
        # ============================================================================
    file_name = fields.Char(
        string="File Name",
        required=True,
        help="Original file name of the digital asset"


    file_size = fields.Integer(
        ,
    string="File Size (bytes)",
        help="Size of the digital asset file"


    mime_type = fields.Char(
        string="MIME Type",
        help="MIME type of the digital asset"


    resolution = fields.Char(
        string="Resolution",
        ,
    help="Image resolution (e.g., '300 DPI')"


    page_count = fields.Integer(
        string="Page Count",
        default=1,
        help="Number of pages in the asset"


    scan_date = fields.Datetime(
        string="Scan Date",
        default=fields.Datetime.now,
        required=True,
        help="Date and time when asset was scanned"


        # ============================================================================
    # STATUS FIELDS
        # ============================================================================
    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('error', 'Error')


        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
            pass
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('file_size')
    def _compute_file_size_readable(self):
        """Convert file size to human readable format"""
        for record in self:
            if record.file_size:
                size = record.file_size
                for unit in ['bytes', 'KB', 'MB', 'GB'):
                    if size < 1024.0:
                        record.file_size_readable = f"{size:.1f} {unit}"
                        break
                    size /= 1024.0
            else:
                record.file_size_readable = "0 bytes"

    file_size_readable = fields.Char(
        string="File Size",
        compute='_compute_file_size_readable',
        ,
    help="Human readable file size"


        # ============================================================================
    # ACTION METHODS
        # ============================================================================
    def action_process(self):
        """Start processing the digital asset"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Can only process draft assets'))
        self.write({'state': 'processing'})

    def action_mark_ready(self):
        """Mark asset as ready for delivery""":
        self.ensure_one()
        if self.state != 'processing':
            raise UserError(_('Can only mark processing assets as ready'))
        self.write({'state': 'ready'})

    def action_deliver(self):
        """Mark asset as delivered"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_('Can only deliver ready assets'))
        self.write({'state': 'delivered'})
)))))))))
