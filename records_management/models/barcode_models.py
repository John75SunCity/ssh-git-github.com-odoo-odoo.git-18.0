# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartnerDepartmentBilling(models.Model):
    """Partner department billing configuration"""
    _name = 'res.partner.department.billing'
    _description = 'Partner Department Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Billing Configuration Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    
    # Billing settings
    billing_method = fields.Selection([
        ('standard', 'Standard Billing'),
        ('consolidated', 'Consolidated Billing'),
        ('separate', 'Separate Billing')
    ], string='Billing Method', default='standard', required=True, tracking=True)
    
    # Contact information
    billing_contact_id = fields.Many2one('res.partner', string='Billing Contact', tracking=True)
    billing_email = fields.Char(string='Billing Email', tracking=True)
    
    # Terms
    payment_terms_id = fields.Many2one('account.payment.term', string='Payment Terms', tracking=True)
    
    # Special pricing
    has_special_pricing = fields.Boolean(string='Has Special Pricing', default=False, tracking=True)
    special_pricing_note = fields.Text(string='Special Pricing Notes')
    
    # Status
    active = fields.Boolean(string='Active', default=True, tracking=True)

class RecordsBarcodeConfig(models.Model):
    """Barcode configuration for records management"""
    _name = 'records.barcode.config'
    _description = 'Records Barcode Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    # Barcode format
    barcode_format = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('upc', 'UPC'),
        ('ean13', 'EAN-13'),
        ('qr', 'QR Code')
    ], string='Barcode Format', default='code128', required=True, tracking=True)
    
    # Generation settings
    auto_generate = fields.Boolean(string='Auto Generate Barcodes', default=True, tracking=True)
    prefix = fields.Char(string='Prefix', tracking=True)
    suffix = fields.Char(string='Suffix', tracking=True)
    length = fields.Integer(string='Total Length', default=12, tracking=True)
    
    # Numbering
    next_number = fields.Integer(string='Next Number', default=1, tracking=True)
    padding_zeros = fields.Integer(string='Padding Zeros', default=6, tracking=True)
    
    # Validation
    check_duplicates = fields.Boolean(string='Check for Duplicates', default=True, tracking=True)
    
    # Status

class RecordsBarcodeHistory(models.Model):
    """History of barcode scans and operations"""
    _name = 'records.barcode.history'
    _description = 'Records Barcode History'
    _order = 'scan_datetime desc'

    # Scan details
    barcode = fields.Char(string='Barcode', required=True, index=True)
    scan_datetime = fields.Datetime(string='Scan Date/Time', required=True, default=fields.Datetime.now)
    
    # Context
    scanned_by = fields.Many2one('res.users', string='Scanned By', required=True, default=lambda self: self.env.user)
    location_id = fields.Many2one('records.location', string='Location')
    
    # Related records
    box_id = fields.Many2one('records.box', string='Related Box')
    document_id = fields.Many2one('records.document', string='Related Document')
    
    # Operation details
    operation_type = fields.Selection([
        ('checkin', 'Check In'),
        ('checkout', 'Check Out'),
        ('inventory', 'Inventory'),
        ('movement', 'Movement'),
        ('verification', 'Verification'),
        ('other', 'Other')
    ], string='Operation Type', required=True)
    
    # Results
    scan_result = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('not_found', 'Not Found')
    ], string='Scan Result', default='success')
    
    error_message = fields.Text(string='Error Message')
    notes = fields.Text(string='Notes')
    
    # GPS coordinates if available
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    
    # Device information
    device_id = fields.Char(string='Device ID')
    app_version = fields.Char(string='App Version')
