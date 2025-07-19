# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Customer tracking for records management
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Customer associated with this lot/serial number'
    )
    
    # Extensions for shredding integration (e.g., link to shredding service)
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service'
    )
