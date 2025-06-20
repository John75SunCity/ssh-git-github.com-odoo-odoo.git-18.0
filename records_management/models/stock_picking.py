from odoo import api, models  # type: ignore

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Overrides the core button_validate to create a sale order for retrieval fees
        when an outgoing picking is validated and items are grouped by customer.
        """
        res = super().button_validate()
        if self.state == 'done' and self.picking_type_id.code == 'outgoing':
            # Filter move lines that have a lot with a customer
            customer_items = self.move_line_ids.filtered(lambda l: l.lot_id and l.lot_id.customer_id)
            if customer_items:
                # Group items by customer
                customers = {}
                for item in customer_items:
                    customer = item.lot_id.customer_id
                    customers.setdefault(customer, []).append(item)
                for customer, items in customers.items():
                    self.env['sale.order'].create({
                        'partner_id': customer.id,
                        'order_line': [(0, 0, {
                            'product_id': self.env.ref('records_management.retrieval_fee_product').id,
                            'product_uom_qty': len(items),
                        })],
                    })
        return res