from odoo import fields, models

class PickupRequest(models.Model):
    _name = 'pickup.request'
    _description = 'Pickup Request'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], default='draft', string='Status')
    item_ids = fields.Many2many(
        'stock.production.lot',
        string='Items',
        domain="[('customer_id', '=', customer_id)]"
    )
