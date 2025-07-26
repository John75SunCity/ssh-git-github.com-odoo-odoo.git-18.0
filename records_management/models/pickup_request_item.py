# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List, Optional
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PickupRequestItem(models.Model):
    """Model for items in pickup requests."""
    _name = 'pickup.request.item'
    _description = 'Pickup Request Item'
    _order = 'product_id'

    pickup_id = fields.Many2one(
        'pickup.request',
        string='Pickup Request',
        required=True,
        ondelete='cascade'
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        change_default=True
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
        digits=(16, 2)
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]"
    notes = fields.Text(string='Notes')

    @api.constrains('quantity')
    def _check_quantity(self) -> None:
        for item in self:
            if item.quantity <= 0:
                error_msg = _("Quantity must be positive for item %s.")
                raise ValidationError(error_msg % item.product_id.name)

    @api.onchange('product_id')
    def _onchange_product_id(self) -> Optional[dict]:
        if (self.product_id and self.lot_id and
                self.lot_id.product_id != self.product_id):
            self.lot_id = False
        return {
            'domain': {
                'lot_id': [('product_id', '=', self.product_id.id)]
            }
        }

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'PickupRequestItem':
        return super().create(vals_list)
