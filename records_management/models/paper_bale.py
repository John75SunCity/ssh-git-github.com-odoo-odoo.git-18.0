# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class PaperBale(models.Model):
    """Model for paper bales in recycling workflow."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Core fields
    name = fields.Char('Bale Reference', required=True, default='/')
    description = fields.Text('Description')
    
    # Relationship fields
    shredding_id = fields.Many2one('shredding.service', string='Shredding Service',
                                   help='The shredding service this bale is associated with')
    
    # Weight and measurement
    weight_kg = fields.Float('Weight (kg)', digits=(10, 2))
    volume_m3 = fields.Float('Volume (m³)', digits=(10, 3))
    
    # Status and tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready for Processing'),
        ('processed', 'Processed'),
        ('shipped', 'Shipped'),
        ('complete', 'Complete')
    ], string='Status', default='draft', tracking=True)
    
    # Dates
    creation_date = fields.Datetime('Creation Date', default=fields.Datetime.now)
    processing_date = fields.Datetime('Processing Date')
    shipping_date = fields.Datetime('Shipping Date')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True)