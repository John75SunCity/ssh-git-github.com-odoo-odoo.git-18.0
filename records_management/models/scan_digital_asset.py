from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ScanDigitalAsset(models.Model):
    _name = 'scan.digital.asset'
    _description = 'Scan Digital Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    work_order_id = fields.Many2one()
    file_name = fields.Char()
    file_size = fields.Integer()
    mime_type = fields.Char()
    resolution = fields.Char()
    page_count = fields.Integer()
    scan_date = fields.Datetime()
    state = fields.Selection()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    file_size_readable = fields.Char()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_file_size_readable(self):
            """Convert file size to human readable format"""
            for record in self:
                if record.file_size:
                    size = record.file_size
                    for unit in ['bytes', 'KB', 'MB', 'GB']:
                        if size < 1024.0:
                            record.file_size_readable = f"{size:.1f} {unit}"
                            break
                        size /= 1024.0
                else:
                    record.file_size_readable = "0 bytes"


    def action_process(self):
            """Start processing the digital asset"""
            self.ensure_one()
            if self.state != 'draft':
                raise UserError(_('Can only process draft assets'))
            self.write({'state': 'processing'})


    def action_mark_ready(self):
            """Mark asset as ready for delivery""":
                pass
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
