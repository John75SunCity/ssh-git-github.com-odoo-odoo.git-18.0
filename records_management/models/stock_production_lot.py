"""
Developer Note:
To optimize database queries, prefer using search_read or read_group instead of multiple .search() calls.
Example:
serials = request.env['stock.lot'].search_read(
    [('customer_id', '=', partner.id)], ['id']
)
quants = request.env['stock.quant'].search_read(
    [('lot_id', 'in', [s['id'] for s in serials]), ('location_id.usage', '=', 'internal')],
    ['id', 'lot_id', 'location_id']
)
"""

from odoo import fields, models

class StockLot(models.Model):
    _inherit = 'stock.lot'

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Tracks ownership. Customer-owned items (boxes, files) have a customer_id; company-owned bins may leave it empty or use it for assignment.'
    )
