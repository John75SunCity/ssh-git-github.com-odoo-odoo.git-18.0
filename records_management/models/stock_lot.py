# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Extensions for shredding integration (e.g., link to shredding service)
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service'
    )
