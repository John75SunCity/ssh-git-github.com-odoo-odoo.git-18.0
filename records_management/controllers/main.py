from odoo import http
from odoo.http import request

class RecordsManagementController(http.Controller):
    @http.route('/records/dashboard', type='http', auth='user', website=True)
    def records_dashboard(self):
        boxes = request.env['records.box'].search([])
        documents = request.env['records.document'].search([])
        locations = request.env['records.location'].search([])

        return request.render('records_management.dashboard', {
            'boxes': boxes,
            'documents': documents,
            'locations': locations,
        })
