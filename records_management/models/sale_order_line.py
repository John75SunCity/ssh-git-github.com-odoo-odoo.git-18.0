from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    records_service_type = fields.Selection([
        ('storage', 'Storage'),
        ('shredding', 'Shredding'),
        ('destruction', 'Destruction'),
        ('pickup', 'Pickup'),
        ('retrieval', 'Retrieval'),
    ], string='Records Service Type')
