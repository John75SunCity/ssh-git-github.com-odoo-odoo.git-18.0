from odoo import http
from odoo.http import request

class InventoryPortal(http.Controller):
    @http.route('/my/inventory', type='http', auth='user', website=True)
    def inventory(self, **kw):
        partner = request.env.user.partner_id
        serials = request.env['stock.production.lot'].search([('customer_id', '=', partner.id)])
        quants = request.env['stock.quant'].search([
            ('lot_id', 'in', serials.ids), 
            ('location_id.usage', '=', 'internal')
        ])
        return request.render('records_management.inventory_template', {'quants': quants})

    @http.route('/my/request_pickup', type='http', auth='user', website=True, methods=['POST'])
    def request_pickup(self, **post):
        partner = request.env.user.partner_id
        item_ids = [int(id) for id in request.httprequest.form.getlist('item_ids')]
        items = request.env['stock.production.lot'].search([
            ('id', 'in', item_ids),
            ('customer_id', '=', partner.id)
        ])
        if items:
            request.env['pickup.request'].create({
                'customer_id': partner.id,
                'item_ids': [(6, 0, items.ids)],
            })
        return request.redirect('/my/inventory')
