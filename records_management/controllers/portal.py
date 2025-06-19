from odoo import http

class InventoryPortal(http.Controller):
    @http.route('/my/inventory', type='http', auth='user', website=True)
    def inventory(self):
        # Authorization check
        if not http.request.env.user.has_group('records_management.group_inventory_access'):
            return http.request.redirect('/web/login?error=access_denied')
        partner = http.request.env.user.partner_id
        if not partner:
            return http.request.redirect('/my/inventory?error=partner_not_found')
        serials = http.request.env['stock.production.lot'].search([('customer_id', '=', partner.id)])
        quants = http.request.env['stock.quant'].search([
            ('lot_id', 'in', serials.ids), 
            ('location_id.usage', '=', 'internal')
        ])
        return http.request.render('records_management.inventory_template', {'quants': quants})

    @http.route('/my/request_pickup', type='http', auth='user', website=True, methods=['POST'])
    def request_pickup(self):
        # Authorization check
        if not http.request.env.user.has_group('records_management.group_inventory_access'):
            return http.request.redirect('/web/login?error=access_denied')
        partner = http.request.env.user.partner_id
        if not partner:
            return http.request.redirect('/my/inventory?error=partner_not_found')
        item_ids = [int(id) for id in http.request.httprequest.form.getlist('item_ids')]
        if not item_ids:
            return http.request.redirect('/my/inventory?error=no_items_selected')
        items = http.request.env['stock.production.lot'].search([
            ('id', 'in', item_ids),
            ('customer_id', '=', partner.id)
        ])
        if items:
            http.request.env['pickup.request'].create({
                'customer_id': partner.id,
                'item_ids': [(6, 0, items.ids)],
            })
        return http.request.redirect('/my/inventory')
