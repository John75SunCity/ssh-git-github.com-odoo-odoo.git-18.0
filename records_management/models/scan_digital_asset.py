from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ScanDigitalAsset(models.Model):
    _name = 'scan.digital.asset'
    _description = 'Scanned Digital Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Asset Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)
    work_order_id = fields.Many2one('fsm.order', string="Work Order", ondelete='cascade', help="The work order that generated this digital asset.")

    # ============================================================================
    # FILE METADATA
    # ============================================================================
    file_name = fields.Char(string="File Name", tracking=True)
    file_size = fields.Integer(string="File Size (bytes)", tracking=True)
    file_size_readable = fields.Char(string="File Size", compute='_compute_file_size_readable', store=True)
    mime_type = fields.Char(string="MIME Type", tracking=True)
    resolution = fields.Char(string="Resolution (DPI)", help="e.g., 300x300", tracking=True)
    page_count = fields.Integer(string="Page Count", tracking=True)
    scan_date = fields.Datetime(string="Scan Date", default=fields.Datetime.now, required=True, tracking=True)

    # ============================================================================
    # LIFECYCLE & STATUS
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('ready', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('file_size')
    def _compute_file_size_readable(self):
        """Convert file size to a human-readable format."""
        for record in self:
            if record.file_size:
                size = record.file_size
                for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                    if size < 1024.0:
                        record.file_size_readable = f"{size:.2f} {unit}"
                        break
                    size /= 1024.0
            else:
                record.file_size_readable = "0 bytes"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_process(self):
        """Start processing the digital asset."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Can only process draft assets.'))
        self.write({'state': 'processing'})
        self.message_post(body=_("Asset processing started."))

    def action_mark_ready(self):
        """Mark asset as ready for delivery."""
        self.ensure_one()
        if self.state != 'processing':
            raise UserError(_('Can only mark processing assets as ready.'))
        self.write({'state': 'ready'})
        self.message_post(body=_("Asset marked as ready for delivery."))

    def action_deliver(self):
        """Mark asset as delivered."""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_('Can only deliver assets that are ready.'))
        self.write({'state': 'delivered'})
        self.message_post(body=_("Asset has been delivered."))

    def action_reset_to_draft(self):
        """Reset the asset back to draft state."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Asset reset to draft state."))
