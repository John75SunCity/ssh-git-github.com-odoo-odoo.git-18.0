from odoo import api, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        if self.state == 'done' and self.picking_type_id.code == 'outgoing':
            customer_items = self.move_line_ids.filtered(lambda ml: ml.lot_id and ml.lot_id.customer_id)
            if customer_items:
                customer = customer_items[0].lot_id.customer_id
                self.env['sale.order'].create({
                    'partner_id': customer.id,
                    'order_line': [(0, 0, {
                        'product_id': self.env.ref('records_management.retrieval_fee_product').id,
                        'product_uom_qty': len(customer_items),
                    })],
                })
        return res