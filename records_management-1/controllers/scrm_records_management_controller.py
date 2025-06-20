from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError
from odoo import _

class ScrmRecordsManagementController(http.Controller):

    @http.route('/my/inventory', type='http', auth='user', website=True)
    def inventory(self, **kw):
        partner = request.env.user.partner_id
        if not partner:
            raise AccessError(_("No partner associated with this user."))
        
        serials = request.env['stock.production.lot'].search([('customer_id', '=', partner.id)])
        quants = request.env['stock.quant'].search([('lot_id', 'in', serials.ids), ('location_id.usage', '=', 'internal')])
        
        return request.render('records_management.inventory_template', {'quants': quants})

    @http.route('/my/request_pickup', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def request_pickup(self, **post):
        partner = request.env.user.partner_id
        error = None
        
        if request.httprequest.method == 'POST':
            try:
                raw_ids = request.httprequest.form.getlist('item_ids')
                item_ids = [int(id) for id in raw_ids if id.isdigit()]
                if not item_ids:
                    error = _("Please select at least one item for pickup.")
                else:
                    request.env['pickup.request'].sudo().create_pickup_request(partner, item_ids)
                    return request.redirect('/my/inventory')
            except (ValidationError, Exception) as e:
                error = str(e)
        
        serials = request.env['stock.production.lot'].search([('customer_id', '=', partner.id)])
        return request.render('records_management.pickup_request_form', {
            'serials': serials,
            'error': error,
            'pickup_item_ids_field': 'item_ids',
            'partner': partner,
            'pickup_request': request.env['pickup.request'].new({
                'customer_id': partner.id,
                'item_ids': [(6, 0, [])]
            }),
        })