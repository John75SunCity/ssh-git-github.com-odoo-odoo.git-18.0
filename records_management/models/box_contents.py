# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BoxContents(models.Model):
    """
    Model for tracking file folders and contents within document boxes.
    Used for organizing filed items within standard size storage boxes (Type 01).
    """
    _name = 'box.contents'
    _description = 'Box Contents - File Folders and Filed Items'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'box_id, name'

    # Core fields
    name = fields.Char(string='File Folder/Item Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    box_id = fields.Many2one('records.box', string='Parent Box', required=True, 
                             ondelete='cascade', tracking=True)
    
    # File folder details
    folder_type = fields.Selection([
        ('manila_folder', 'Manila Folder'),
        ('hanging_folder', 'Hanging Folder'),
        ('file_jacket', 'File Jacket'),
        ('binder', 'Binder'),
        ('envelope', 'Envelope'),
        ('loose_documents', 'Loose Documents'),
        ('other', 'Other')
    
    # Content tracking
    document_count = fields.Integer(string='Total Documents', compute='_compute_document_count')
    checked_out_count = fields.Integer(string='Checked Out', compute='_compute_checkout_status')
    available_count = fields.Integer(string='Available in Box', compute='_compute_checkout_status')
    
    # Box completion tracking
    contents_catalogued = fields.Boolean(string='All Contents Catalogued', default=False,
                                       help="Check when all items in box have been listed and barcoded")
    box_at_capacity = fields.Boolean(string='Box at Capacity', default=False,
                                   help="Check when box is full and no more items can be added")
    temp_barcodes_assigned = fields.Boolean(string='Temp Barcodes Assigned', default=False,
                                          help="Indicates if temporary barcodes have been assigned to contents")
    
    # Filing details
    filing_system = fields.Selection([
        ('alphabetical', 'Alphabetical'),
        ('numerical', 'Numerical'),
        ('chronological', 'Chronological'),
        ('subject', 'Subject-based'),
        ('employee_files', 'Employee Files'),
        ('mixed_contents', 'Mixed Contents'),
        ('other', 'Other')
    
    # Status tracking
    checkout_status = fields.Selection([
        ('in_box', 'In Box'),
        ('checked_out', 'Checked Out'),
        ('destroyed', 'Destroyed'),
        ('lost', 'Lost')
    
    checkout_date = fields.Datetime(string='Checkout Date')
    checkout_user_id = fields.Many2one('res.users', string='Checked Out By')
    expected_return_date = fields.Date(string='Expected Return Date')
    temp_barcode = fields.Char(string='Temporary Barcode', 
                              help="Temporary barcode assigned during cataloguing")
    
    # Standard fields
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color Index', default=0)
    
    # Relationships - Documents filed in this folder
    document_ids = fields.One2many('records.document', 'container_id', string='Filed Documents')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    
    # Computed fields
    box_name = fields.Char(related='box_id.name', string='Box Name', readonly=True)
    checkout_percentage = fields.Float(string='% Checked Out', 
                                      compute='_compute_checkout_status')
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute number of documents in this file folder/item"""
        for record in self:
            record.document_count = len(record.document_ids)
    
    @api.depends('document_ids', 'document_ids.checkout_status')
    def _compute_checkout_status(self):
        """Compute checkout statistics"""
        for record in self:
            total_docs = len(record.document_ids)
            checked_out_docs = len(record.document_ids.filtered(lambda d: d.checkout_status == 'checked_out'))
            
            record.checked_out_count = checked_out_docs
            record.available_count = total_docs - checked_out_docs
            
            if total_docs > 0:
                record.checkout_percentage = (checked_out_docs / total_docs) * 100
            else:
                record.checkout_percentage = 0.0
    
    def action_mark_catalogued(self):
        """Mark box contents as fully catalogued"""
        self.ensure_one()
        self.write({
            'contents_catalogued': True,
            'temp_barcodes_assigned': True
        })
    
    def action_mark_at_capacity(self):
        """Mark box as at capacity - no more items can be added"""
        self.ensure_one()
        self.write({'box_at_capacity': True})
    
    def action_checkout_item(self):
        """Checkout this item"""
        self.ensure_one()
        self.write({
            'checkout_status': 'checked_out',
            'checkout_date': fields.Datetime.now(),
            'checkout_user_id': self.env.user.id
        })
    
    def action_return_item(self):
        """Return this item to the box"""
        self.ensure_one()
        self.write({
            'checkout_status': 'in_box',
            'checkout_date': False,
            'checkout_user_id': False,
            'expected_return_date': False
        })
