from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PickupRequestItem(models.Model):
    _name = 'pickup.request.item'
    _description = 'Pickup Request Item'

    pickup_id = fields.Many2one('pickup.request', string='Pickup Request', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]"
    )
    notes = fields.Text(string='Notes')

    @api.constrains('quantity')
    def _check_quantity(self):
        for item in self:
            if item.quantity <= 0:
                raise ValidationError("Quantity must be positive.")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and self.lot_id and self.lot_id.product_id != self.product_id:
            self.lot_id = False

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)