# -*- coding: utf-8 -*-
"""
Barcode Pre-Print Wizard
========================

Allows users to pre-print batches of barcode labels for future use.
Features:
- Generate sequential barcodes in advance
- Print blank container/folder labels with barcodes
- Track which barcodes have been pre-printed
- Prevent accidental reprinting
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BarcodePreprintWizard(models.TransientModel):
    _name = 'barcode.preprint.wizard'
    _description = 'Barcode Pre-Print Wizard'
    
    label_type = fields.Selection([
        ('container', 'Container Labels'),
        ('folder', 'File Folder Labels'),
    ], string='Label Type', required=True, default='container')
    
    quantity = fields.Integer(
        string='Quantity to Print',
        required=True,
        default=14,
        help='Number of labels to pre-print. Default is 14 (one sheet of container labels).'
    )
    
    start_number = fields.Integer(
        string='Starting Number',
        help='Starting sequence number for barcodes. Leave blank to use next available.',
    )
    
    prefix = fields.Char(
        string='Barcode Prefix',
        help='Optional prefix for pre-printed barcodes (e.g., "TEMP-" or "PRE-")',
        default='PRE-',
    )
    
    notes = fields.Text(
        string='Notes',
        help='Optional notes about this pre-print batch (e.g., "For warehouse expansion")',
    )
    
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is reasonable"""
        for wizard in self:
            if wizard.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))
            if wizard.quantity > 500:
                raise ValidationError(_("Maximum 500 labels per batch. Please print in smaller batches."))
    
    def action_print_preprint_labels(self):
        """
        Generate and print blank barcode labels for future use.
        
        Creates a tracking record and generates PDF with sequential barcodes.
        """
        self.ensure_one()
        
        # Get next sequence number if not specified
        if not self.start_number:
            if self.label_type == 'container':
                seq = self.env['ir.sequence'].next_by_code('records.container.temp.barcode')
                # Extract number from sequence (e.g., "BOX-00001" -> 1)
                import re
                match = re.search(r'\d+', seq)
                self.start_number = int(match.group()) if match else 1
            else:
                seq = self.env['ir.sequence'].next_by_code('records.file.temp.barcode')
                match = re.search(r'\d+', seq)
                self.start_number = int(match.group()) if match else 1
        
        # Generate barcode list
        barcodes = []
        for i in range(self.quantity):
            barcode_num = self.start_number + i
            if self.prefix:
                barcode = f"{self.prefix}{barcode_num:05d}"
            else:
                barcode = f"{barcode_num:05d}"
            barcodes.append(barcode)
        
        # Create tracking record
        tracking = self.env['barcode.preprint.tracking'].create({
            'label_type': self.label_type,
            'quantity': self.quantity,
            'start_number': self.start_number,
            'prefix': self.prefix,
            'barcode_list': ','.join(barcodes),
            'notes': self.notes,
            'printed_by_id': self.env.user.id,
            'print_date': fields.Datetime.now(),
        })
        
        # Generate PDF with blank labels
        generator = self.env['zpl.label.generator']
        
        if self.label_type == 'container':
            result = generator.generate_preprint_container_labels(barcodes)
        else:
            result = generator.generate_preprint_folder_labels(barcodes)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': result['filename'],
            'type': 'binary',
            'datas': result['pdf_data'],
            'res_model': tracking._name,
            'res_id': tracking.id,
            'mimetype': 'application/pdf',
        })
        
        # Link attachment to tracking
        tracking.attachment_id = attachment.id
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }


class BarcodePreprintTracking(models.Model):
    _name = 'barcode.preprint.tracking'
    _description = 'Barcode Pre-Print Tracking'
    _order = 'print_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Batch Reference',
        compute='_compute_name',
        store=True,
    )
    
    label_type = fields.Selection([
        ('container', 'Container Labels'),
        ('folder', 'File Folder Labels'),
    ], string='Label Type', required=True, tracking=True)
    
    quantity = fields.Integer(string='Quantity', required=True, tracking=True)
    start_number = fields.Integer(string='Start Number', tracking=True)
    prefix = fields.Char(string='Prefix')
    
    barcode_list = fields.Text(
        string='Barcode List',
        help='Comma-separated list of pre-printed barcodes',
    )
    
    notes = fields.Text(string='Notes')
    
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
    
    used_count = fields.Integer(
        string='Used Count',
        compute='_compute_used_count',
        help='Number of barcodes from this batch that have been assigned to records',
    )
    
    @api.depends('label_type', 'print_date', 'quantity')
    def _compute_name(self):
        """Generate reference name"""
        for record in self:
            if record.print_date:
                date_str = fields.Datetime.context_timestamp(record, record.print_date).strftime('%Y-%m-%d')
                record.name = f"{record.label_type.upper()}-{date_str}-{record.quantity}pcs"
            else:
                record.name = _("New Pre-Print Batch")
    
    def _compute_used_count(self):
        """Count how many barcodes have been assigned"""
        for record in self:
            if not record.barcode_list:
                record.used_count = 0
                continue
            
            barcodes = record.barcode_list.split(',')
            
            if record.label_type == 'container':
                used = self.env['records.container'].search_count([
                    '|',
                    ('barcode', 'in', barcodes),
                    ('temp_barcode', 'in', barcodes),
                ])
            else:
                used = self.env['records.file'].search_count([
                    '|',
                    ('barcode', 'in', barcodes),
                    ('temp_barcode', 'in', barcodes),
                ])
            
            record.used_count = used
    
    def action_reprint(self):
        """Reprint the labels from this batch"""
        self.ensure_one()
        
        if not self.attachment_id:
            raise UserError(_("No PDF attachment found. Please regenerate the labels."))
        
        # Log reprint in chatter
        self.message_post(
            body=_("Labels reprinted by %s") % self.env.user.name,
            subject=_("Labels Reprinted"),
        )
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'new',
        }
