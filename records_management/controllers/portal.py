from odoo import http, fields
from odoo.http import request


class RecordsPortal(http.Controller):
    
    @http.route('/my/inventory', type='http', auth='user', website=True)
    def my_records_inventory(self):
        """Portal page for customers to view their records inventory"""
        partner = request.env.user.partner_id
        
        # Get customer's boxes
        boxes = request.env['records.box'].search([
            ('customer_id', '=', partner.id)
        ])
        
        # Get customer's documents
        documents = request.env['records.document'].search([
            ('customer_id', '=', partner.id)
        ])
        
        # Get recent documents (last 10)
        recent_documents = request.env['records.document'].search([
            ('customer_id', '=', partner.id)
        ], order='create_date desc', limit=10)
        
        # Get active pickup requests
        pickup_requests = request.env['pickup.request'].search([
            ('customer_id', '=', partner.id),
            ('state', 'in', ['draft', 'confirmed', 'scheduled'])
        ])
        
        # Get active shredding requests
        shredding_requests = request.env['shredding.service'].search([
            ('customer_id', '=', partner.id),
            ('status', 'in', ['draft', 'confirmed', 'scheduled'])
        ])
        
        # Combine active requests
        requests = list(pickup_requests) + list(shredding_requests)
        
        # Calculate statistics
        boxes_count = len(boxes)
        documents_count = len(documents)
        locations_count = len(boxes.mapped('location_id'))
        requests_count = len(requests)
        
        values = {
            'boxes': boxes,
            'documents': documents,
            'recent_documents': recent_documents,
            'requests': requests,
            'boxes_count': boxes_count,
            'documents_count': documents_count,
            'locations_count': locations_count,
            'requests_count': requests_count,
        }
        
        return request.render('records_management.portal_my_inventory', values)

    @http.route('/my/request_pickup', type='http', auth='user', website=True,
                methods=['POST'])
    def request_pickup(self):
        """Create a pickup request from portal"""
        partner = request.env.user.partner_id
        
        # Get selected box IDs from form
        box_ids = [int(id) for id in
                   request.httprequest.form.getlist('box_ids')]
        
        if not box_ids:
            return request.redirect('/my/inventory?error=no_boxes_selected')
        
        # Verify boxes belong to this customer
        boxes = request.env['records.box'].search([
            ('id', 'in', box_ids),
            ('customer_id', '=', partner.id),
            ('state', '=', 'stored')
        ])
        
        if boxes:
            # Create pickup request
            request.env['pickup.request'].create({
                'customer_id': partner.id,
                'request_date': request.env.context.get('request_date',
                                                        fields.Date.today()),
                'state': 'draft',
            })
            
        return request.redirect('/my/inventory?success=pickup_requested')

    @http.route('/my/request_shredding', type='http', auth='user',
                website=True, methods=['POST'])
    def request_shredding(self):
        """Create a shredding request from portal"""
        partner = request.env.user.partner_id
        
        # Get selected box IDs from form
        box_ids = [int(id) for id in
                   request.httprequest.form.getlist('shredding_box_ids')]
        
        if not box_ids:
            return request.redirect('/my/inventory?error=no_boxes_selected')
        
        # Verify boxes belong to this customer
        boxes = request.env['records.box'].search([
            ('id', 'in', box_ids),
            ('customer_id', '=', partner.id)
        ])
        
        if boxes:
            # Create shredding service request
            request.env['shredding.service'].create({
                'customer_id': partner.id,
                'name': f'Shredding Request - {partner.name}',
                'scheduled_date': request.env.context.get('scheduled_date'),
                'status': 'draft',
                'total_boxes': len(boxes),
            })
            
        return request.redirect('/my/inventory?success=shredding_requested')
