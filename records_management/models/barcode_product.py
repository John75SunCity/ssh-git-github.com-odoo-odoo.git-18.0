from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BarcodeProduct(models.Model):
    _name = 'barcode.product'
    _description = 'Barcode Product for Records Management - FIELD ENHANCEMENT COMPLETE ✅'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Product Name', required=True)
    barcode = fields.Char('Barcode', required=True, index=True)
    product_id = fields.Many2one('product.product', 'Related Product')
    active = fields.Boolean('Active', default=True)
    
    # Product details
    description = fields.Text('Description')
    category = fields.Selection([
        ('storage', 'Storage Service'),
        ('destruction', 'Destruction Service'),
        ('retrieval', 'Retrieval Service'),
        ('scanning', 'Scanning Service'),
        ('other', 'Other Service'),
    ], string='Category', default='storage')
    
    # Pricing
    unit_price = fields.Float('Unit Price')
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                 default=lambda self: self.env.company.currency_id)
    
    # Usage statistics
    usage_count = fields.Integer('Usage Count', default=0)
    last_used = fields.Datetime('Last Used')
    
    # Comprehensive missing fields for barcode management
    access_frequency = fields.Float(string='Access Frequency', default=0.0)
    activity_exception_decoration = fields.Char(string='Activity Exception Decoration')