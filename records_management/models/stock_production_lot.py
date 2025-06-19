from odoo import fields, models

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Tracks ownership. Customer-owned items (boxes, files) have a customer_id; company-owned bins may leave it empty or use it for assignment.'
    )
