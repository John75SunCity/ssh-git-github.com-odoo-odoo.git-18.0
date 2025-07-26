# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsDigitalCopy(models.Model):
    """Model for tracking digital copies of documents."""
    _name = 'records.digital.copy'
    _description = 'Digital Copy of Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'document_id, copy_date desc'

    # Core fields
    name = fields.Char('Copy Reference', required=True, default='/')
    description = fields.Text('Description')
    
    # Document relationship
    document_id = fields.Many2one('records.document', string='Original Document', 
                                  required=True, ondelete='cascade')
    
    # Digital copy details
    file_format = fields.Selection([
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
        ('docx', 'Word Document'),
        ('xlsx', 'Excel Spreadsheet'),
        ('other', 'Other')
    
    file_size_mb = fields.Float('File Size (MB)', digits=(10, 2))
    resolution_dpi = fields.Integer('Resolution (DPI)', default=300)
    color_mode = fields.Selection([
        ('color', 'Color'),
        ('grayscale', 'Grayscale'),
        ('bw', 'Black & White')
    
    # Quality and compression
    quality_level = fields.Selection([
        ('high', 'High Quality'),
        ('medium', 'Medium Quality'),
        ('low', 'Low Quality'),
        ('archive', 'Archive Quality')
    
    compressed = fields.Boolean('Compressed', default=True)
    ocr_enabled = fields.Boolean('OCR Enabled', default=False,
                                help='Whether text recognition was applied')
    searchable = fields.Boolean('Searchable', default=False,
                               help='Whether the content is text-searchable')
    
    # Storage and access
    storage_location = fields.Selection([
        ('local', 'Local Storage'),
        ('cloud', 'Cloud Storage'),
        ('archive', 'Archive Storage'),
        ('backup', 'Backup Storage')
    
    file_path = fields.Char('File Path', help='Path to the digital file')
    access_url = fields.Char('Access URL', help='URL to access the digital copy')
    
    # Dates and tracking
    copy_date = fields.Datetime('Copy Date', default=fields.Datetime.now, required=True)
    last_accessed = fields.Datetime('Last Accessed')
    created_by = fields.Many2one('res.users', string='Created By', 
                                default=lambda self: self.env.user, required=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('corrupted', 'Corrupted'),
        ('deleted', 'Deleted')
    
    # Security and compliance
    encrypted = fields.Boolean('Encrypted', default=False)
    access_restricted = fields.Boolean('Access Restricted', default=False)
    retention_date = fields.Date('Retention Date', 
                                help='Date when this digital copy should be reviewed for deletion')
    
    # Attachments
    attachment_id = fields.Many2one('ir.attachment', string='File Attachment')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True)
    
    @api.model
    def create(self, vals):
        """Generate sequence for copy reference"""
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('records.digital.copy') or '/'
        return super().create(vals)
    
    def action_mark_accessed(self):
        """Mark the digital copy as accessed"""
        self.write({'last_accessed': fields.Datetime.now()})
    
    def action_archive_copy(self):
        """Archive the digital copy"""
        self.write({'state': 'archived'})
    
    def action_mark_corrupted(self):
        """Mark the digital copy as corrupted"""
        self.write({'state': 'corrupted'})
