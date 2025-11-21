# -*- coding: utf-8 -*-
"""
Barcode Batch Print Tracking
=============================

Tracks batch label printing operations for audit and reprint purposes.
"""

from odoo import api, fields, models, _


class BarcodeBatchPrint(models.Model):
    _name = 'barcode.batch.print'
    _description = 'Barcode Batch Print Tracking'
    _order = 'print_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Batch Reference',
        compute='_compute_name',
        store=True,
    )
    
    record_type = fields.Selection([
        ('container', 'Container Labels'),
        ('folder', 'File Folder Labels'),
    ], string='Record Type', required=True, tracking=True)
    
    record_count = fields.Integer(
        string='Label Count',
        required=True,
        tracking=True,
    )
    
    printed_by_id = fields.Many2one(
        'res.users',
        string='Printed By',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    
    print_date = fields.Datetime(
        string='Print Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='PDF Attachment',
        help='Link to the generated PDF for easy reprinting',
    )
    
    @api.depends('record_type', 'print_date', 'record_count')
    def _compute_name(self):
        """Generate reference name"""
        for record in self:
            if record.print_date:
                date_str = fields.Datetime.context_timestamp(record, record.print_date).strftime('%Y-%m-%d %H:%M')
                record.name = f"{record.record_type.upper()}-BATCH-{date_str} ({record.record_count} labels)"
            else:
                record.name = _("New Batch Print")
    
    def action_reprint(self):
        """Reprint the labels from this batch"""
        self.ensure_one()
        
        if not self.attachment_id:
            raise UserError(_("No PDF attachment found. Please regenerate the labels."))
        
        # Log reprint in chatter
        self.message_post(
            body=_("Batch labels reprinted by %s") % self.env.user.name,
            subject=_("Batch Reprinted"),
        )
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'new',
        }
