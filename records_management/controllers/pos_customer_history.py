# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request

class PosCustomerHistoryController(http.Controller):
    """Lightweight JSON endpoint to fetch recent PoS order history for a customer.

    Returns up to 15 recent orders (newest first) including:
      - order name
      - date_order
      - amount_total
      - cashier (user) name
      - order lines: product name, qty, price_unit, price_subtotal
    Only accessible to authenticated users with PoS access. Respects company.
    """

    @http.route(['/records_management/pos/customer_history'], type='json', auth='user')
    def get_pos_customer_history(self, partner_id=None, limit=15):
        if not partner_id:
            return {'orders': []}
        user = request.env.user
        # Basic permission: ensure user has access to pos.order model
        if not user.has_group('point_of_sale.group_pos_user'):
            return {'error': _('Access denied')}
        domain = [
            ('partner_id', '=', int(partner_id)),
            ('company_id', '=', user.company_id.id)
        ]
        orders = request.env['pos.order'].sudo().search(domain, order='date_order desc', limit=min(int(limit), 50))
        data = []
        for o in orders:
            lines = []
            for l in o.lines:
                lines.append({
                    'product': l.product_id.display_name,
                    'qty': l.qty,
                    'price_unit': l.price_unit,
                    'subtotal': l.price_subtotal,
                })
            data.append({
                'name': o.name,
                'date_order': o.date_order,
                'amount_total': o.amount_total,
                'cashier': o.user_id.display_name,
                'lines': lines,
            })
        return {'orders': data}
