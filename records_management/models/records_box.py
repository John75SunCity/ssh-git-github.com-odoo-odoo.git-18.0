# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsBox(models.Model):
    """Model for document storage boxes with enhanced fields."""
    _name = 'records.box'
    _description = 'Document Storage Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Box Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    alternate_code = fields.Char(string='Alternate Code', copy=False)
    description = fields.Char(string='Description', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft')
    item_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('permanent_out', 'Permanent Out'),
        ('destroyed', 'Destroyed'),
        ('archived', 'Archived')
    ], string='Item Status', default='active')
    status_date = fields.Datetime(
        string='Status Date',
        default=fields.Datetime.now
    )
    add_date = fields.Datetime(
        string='Add Date',
        default=fields.Datetime.now,
        readonly=True
    )
    storage_date = fields.Date(
        string='Storage Date',
        help='Date when the box was placed in storage location'
    )
    destroy_date = fields.Date(string='Destroy Date')
    access_count = fields.Integer(string='Access Count', default=0)
    perm_flag = fields.Boolean(string='Permanent Flag', default=False)
    product_id = fields.Many2one('product.product', string='Box Product')
    location_id = fields.Many2one(
        'records.location',
        string='Storage Location',
        index=True
    )
    location_code = fields.Char(
        related='location_id.code',
        string='Location Code',
        readonly=True
    )
    customer_inventory_id = fields.Many2one(
        'customer.inventory.report',
        string='Customer Inventory Report',
        ondelete='cascade'
    )
    container_type = fields.Selection([
        ('standard', 'Standard Box'),
        ('map_box', 'Map Box'),
        ('specialty', 'Specialty Box'),
        ('pallet', 'Pallet'),
        ('other', 'Other')
    ], string='Container Type', default='standard')
    
    # Business-specific box type codes for pricing and location management
    box_type_code = fields.Selection([
        ('01', 'Type 01 - Standard File Box'),
        ('03', 'Type 03 - Map Box'),
        ('04', 'Type 04 - Oversize/Odd-shaped Box'),
        ('06', 'Type 06 - Specialty/Vault Box'),
    ], string='Box Type Code', default='01', required=True,
       help="Box type determines pricing, storage location, and handling requirements")
    
    # Computed field for customer-friendly display
    box_type_display = fields.Char(
        string='Box Type',
        compute='_compute_box_type_display',
        store=True,
        help="Customer-friendly display name for invoicing and reports"
    )
    
    # Pricing related to box type
    monthly_rate = fields.Float(
        string='Monthly Storage Rate',
        compute='_compute_monthly_rate',
        store=True,
        help="Monthly storage rate based on box type"
    )
    security_code = fields.Char(string='Security Code')
    category_code = fields.Char(string='Category Code')
    record_series = fields.Char(string='Record Series')
    object_code = fields.Char(string='Object Code')
    account_level1 = fields.Char(string='Account Level 1')
    account_level2 = fields.Char(string='Account Level 2')
    account_level3 = fields.Char(string='Account Level 3')
    sequence_from = fields.Integer(string='Sequence From')
    sequence_to = fields.Integer(string='Sequence To')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    custom_metadata_1 = fields.Char(string='Custom Metadata 1')
    custom_metadata_2 = fields.Char(string='Custom Metadata 2')
    custom_metadata_3 = fields.Char(string='Custom Metadata 3')
    custom_metadata_4 = fields.Char(string='Custom Metadata 4')
    custom_date = fields.Date(string='Custom Date')
    charge_for_storage = fields.Boolean(
        string='Charge for Storage',
        default=True
    )
    charge_for_add = fields.Boolean(string='Charge for Add', default=True)
    capacity = fields.Integer(string='Capacity (documents)', default=100)
    used_capacity = fields.Float(
        string='Used Capacity (%)',
        compute='_compute_used_capacity',
        store=False
    )
    barcode = fields.Char(string='Barcode', copy=False, index=True)
    barcode_length = fields.Integer(string='Barcode Length', default=12)
    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('upc', 'UPC'),
        ('ean13', 'EAN-13'),
        ('qr', 'QR Code'),
        ('other', 'Other')
    ], string='Barcode Type', default='code128')
    document_ids = fields.One2many(
        'records.document',
        'box_id',
        string='Documents'
    )
    document_count = fields.Integer(
        compute='_compute_document_count',
        string='Document Count',
        store=True
    )
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('is_company', '=', True)]",
        index=True
    )
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user
    )
    create_date = fields.Datetime(string='Created on', readonly=True)
    destruction_date = fields.Date(string='Destruction Date')
    color = fields.Integer(string='Color Index')
    tag_ids = fields.Many2many('records.tag', string='Tags')

    # One2many relations referenced in views
    movement_ids = fields.One2many(
        'records.box.movement', 'box_id',
        string='Movement History'
    )
    service_request_ids = fields.One2many(
        'pickup.request', 'box_id',
        string='Service Requests'
    )
    
    # Additional One2many relationships for document and container tracking
    contents_ids = fields.One2many(
        'records.document', 'box_id',
        string='Box Contents'
    )
    container_contents_ids = fields.One2many(
        'box.contents', 'box_id',
        string='Box Contents'
    )

    # Phase 1 Critical Fields - Added by automated script
    
    @api.depends('box_type_code')
    def _compute_box_type_display(self):
        """Compute display name for box type"""
        for record in self:
            if record.box_type_code:
                record.box_type_display = dict(record._fields['box_type_code'].selection).get(record.box_type_code, record.box_type_code)
            else:
                record.box_type_display = ''
    
    @api.depends('box_type_code')
    def _compute_monthly_rate(self):
        """Compute monthly storage rate based on box type"""
        for record in self:
            # Basic rate calculation based on box type code
            base_rate = 10.0  # Base monthly rate for Type 01
            if record.box_type_code == '01':  # Standard File Box
                base_rate = 10.0
            elif record.box_type_code == '03':  # Map Box
                base_rate = 15.0
            elif record.box_type_code == '04':  # Oversize/Odd-shaped Box
                base_rate = 18.0
            elif record.box_type_code == '06':  # Specialty/Vault Box
                base_rate = 25.0
                
            record.monthly_rate = base_rate
    
    @api.depends('capacity', 'documents_stored')
    def _compute_used_capacity(self):
        """Compute used capacity percentage"""
        for record in self:
            if record.capacity and record.capacity > 0:
                record.used_capacity = (record.documents_stored / record.capacity) * 100
            else:
                record.used_capacity = 0.0
    
    @api.depends()
    def _compute_document_count(self):
        """Compute number of documents in this box"""
        for record in self:
            documents = self.env['records.document'].search([('box_id', '=', record.id)])
            record.document_count = len(documents)