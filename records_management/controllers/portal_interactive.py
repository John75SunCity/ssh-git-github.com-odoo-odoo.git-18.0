# -*- coding: utf-8 -*-
"""
Portal Interactive Features Controller
Provides JSON endpoints for AJAX-powered portal widgets
"""

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import json


class PortalInteractiveController(CustomerPortal):
    """
    Controller for interactive portal features:
    - AJAX pagination and filtering
    - Real-time price calculation
    - Barcode scanning
    - Export functionality
    """

    @http.route(['/my/document-retrieval/calculate-price'], type='json', auth="user", website=True)
    def calculate_retrieval_price(self, container_ids=None, **kw):
        """
        Calculate price for document retrieval request
        
        :param container_ids: List of container IDs to retrieve
        :return: Dictionary with pricing breakdown
        """
        if not container_ids:
            return {'total_price': 0.0, 'breakdown': {}}
        
        try:
            Container = request.env['records.container']
            containers = Container.browse(container_ids)
            
            # Pricing logic - customize based on your business rules
            base_price = 25.00  # Base retrieval fee
            per_container = 5.00  # Per container fee
            
            # Calculate volume/weight based pricing if needed
            total_volume = sum(c.volume or 0 for c in containers)
            volume_surcharge = 0.0
            if total_volume > 10.0:  # Cubic feet
                volume_surcharge = (total_volume - 10.0) * 2.00
            
            # Same-day delivery surcharge
            same_day = kw.get('same_day_delivery', False)
            delivery_surcharge = 50.00 if same_day else 0.0
            
            subtotal = base_price + (len(containers) * per_container) + volume_surcharge
            total = subtotal + delivery_surcharge
            
            return {
                'success': True,
                'total_price': total,
                'breakdown': {
                    'base_fee': base_price,
                    'container_count': len(containers),
                    'per_container_fee': per_container,
                    'container_fees': len(containers) * per_container,
                    'volume_cubic_feet': total_volume,
                    'volume_surcharge': volume_surcharge,
                    'delivery_surcharge': delivery_surcharge,
                    'subtotal': subtotal,
                    'total': total,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'total_price': 0.0
            }

    @http.route(['/my/barcode/process/<string:scan_type>'], type='json', auth="user", website=True)
    def process_barcode(self, scan_type='container', barcode=None, **kw):
        """
        Process scanned barcode and return record details
        
        :param scan_type: Type of record to lookup (container, document, request)
        :param barcode: Scanned barcode value
        :return: Record details or error
        """
        if not barcode:
            return {
                'success': False,
                'message': _('No barcode provided')
            }
        
        try:
            if scan_type == 'container':
                Container = request.env['records.container']
                record = Container.search([
                    '|', ('barcode', '=', barcode),
                    ('name', '=', barcode)
                ], limit=1)
                
                if record:
                    return {
                        'success': True,
                        'record': {
                            'id': record.id,
                            'name': record.name,
                            'type': 'container',
                            'details': _('Location: %s | Status: %s | Contents: %s items') % (
                                record.location_id.name or _('Not Set'),
                                record.state.title() if hasattr(record.state, 'title') else record.state,
                                len(record.document_ids) if record.document_ids else 0
                            ),
                            'url': '/my/containers/%s' % record.id,
                            'barcode': record.barcode,
                        }
                    }
            
            elif scan_type == 'document':
                Document = request.env['records.document']
                record = Document.search([
                    '|', ('barcode', '=', barcode),
                    ('name', '=', barcode)
                ], limit=1)
                
                if record:
                    return {
                        'success': True,
                        'record': {
                            'id': record.id,
                            'name': record.name,
                            'type': 'document',
                            'details': _('Container: %s | Type: %s') % (
                                record.container_id.name if record.container_id else _('None'),
                                record.document_type_id.name if record.document_type_id else _('Unknown')
                            ),
                            'url': '/my/documents/%s' % record.id,
                            'barcode': record.barcode,
                        }
                    }
            
            elif scan_type == 'request':
                Request = request.env['portal.request']
                record = Request.search([
                    '|', ('barcode', '=', barcode),
                    ('name', '=', barcode)
                ], limit=1)
                
                if record:
                    return {
                        'success': True,
                        'record': {
                            'id': record.id,
                            'name': record.name,
                            'type': 'request',
                            'details': _('Type: %s | Status: %s | Date: %s') % (
                                record.request_type.title() if hasattr(record.request_type, 'title') else record.request_type,
                                record.state.title() if hasattr(record.state, 'title') else record.state,
                                fields.Date.to_string(record.create_date.date()) if record.create_date else ''
                            ),
                            'url': '/my/requests/%s' % record.id,
                            'barcode': record.barcode,
                        }
                    }
            
            return {
                'success': False,
                'message': _('No %s found with barcode: %s') % (scan_type, barcode)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': _('Error processing barcode: %s') % str(e)
            }

    @http.route(['/my/containers/export'], type='http', auth="user", website=True)
    def export_containers(self, format='xlsx', **kw):
        """
        Export container list to Excel/CSV
        
        :param format: Export format (xlsx, csv)
        :return: File download
        """
        try:
            # Get current user's containers with same filters as list view
            domain = self._get_containers_domain(**kw)
            Container = request.env['records.container']
            containers = Container.search(domain, order='name')
            
            if format == 'xlsx':
                return self._export_containers_xlsx(containers)
            elif format == 'csv':
                return self._export_containers_csv(containers)
            else:
                return request.redirect('/my/containers')
                
        except Exception as e:
            return request.redirect('/my/containers?error=' + str(e))

    def _get_containers_domain(self, search=None, filterby=None, **kw):
        """Build domain for container search"""
        domain = [('partner_id', '=', request.env.user.partner_id.id)]
        
        if search:
            domain += ['|', '|',
                      ('name', 'ilike', search),
                      ('description', 'ilike', search),
                      ('location_id.name', 'ilike', search)]
        
        if filterby and filterby != 'all':
            if filterby == 'active':
                domain.append(('state', '=', 'active'))
            elif filterby == 'destroyed':
                domain.append(('state', '=', 'destroyed'))
            elif filterby == 'pending':
                domain.append(('state', '=', 'pending'))
        
        return domain

    def _export_containers_xlsx(self, containers):
        """Export containers to Excel using Odoo's built-in export"""
        import io
        from odoo.tools.misc import xlsxwriter
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Containers')
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        # Write headers
        headers = ['Container #', 'Description', 'Location', 'Status', 'Created', 'Last Updated']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        for row, container in enumerate(containers, start=1):
            worksheet.write(row, 0, container.name or '')
            worksheet.write(row, 1, container.description or '')
            worksheet.write(row, 2, container.location_id.name or '')
            worksheet.write(row, 3, container.state or '')
            worksheet.write(row, 4, fields.Date.to_string(container.create_date.date()) if container.create_date else '')
            worksheet.write(row, 5, fields.Date.to_string(container.write_date.date()) if container.write_date else '')
        
        workbook.close()
        output.seek(0)
        
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="containers_export.xlsx"')
            ]
        )

    def _export_containers_csv(self, containers):
        """Export containers to CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Container #', 'Description', 'Location', 'Status', 'Created', 'Last Updated'])
        
        # Write data
        for container in containers:
            writer.writerow([
                container.name or '',
                container.description or '',
                container.location_id.name or '',
                container.state or '',
                fields.Date.to_string(container.create_date.date()) if container.create_date else '',
                fields.Date.to_string(container.write_date.date()) if container.write_date else ''
            ])
        
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename="containers_export.csv"')
            ]
        )

    @http.route(['/my/requests/export'], type='http', auth="user", website=True)
    def export_requests(self, format='xlsx', **kw):
        """Export requests list to Excel/CSV"""
        try:
            Request = request.env['portal.request']
            requests = Request.search([
                ('partner_id', '=', request.env.user.partner_id.id)
            ], order='create_date desc')
            
            if format == 'xlsx':
                return self._export_requests_xlsx(requests)
            else:
                return self._export_requests_csv(requests)
                
        except Exception as e:
            return request.redirect('/my/requests?error=' + str(e))

    def _export_requests_xlsx(self, requests):
        """Export requests to Excel"""
        import io
        from odoo.tools.misc import xlsxwriter
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Requests')
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        headers = ['Request #', 'Type', 'Status', 'Description', 'Created', 'Updated']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        for row, req in enumerate(requests, start=1):
            worksheet.write(row, 0, req.name or '')
            worksheet.write(row, 1, req.request_type or '')
            worksheet.write(row, 2, req.state or '')
            worksheet.write(row, 3, req.description or '')
            worksheet.write(row, 4, fields.Date.to_string(req.create_date.date()) if req.create_date else '')
            worksheet.write(row, 5, fields.Date.to_string(req.write_date.date()) if req.write_date else '')
        
        workbook.close()
        output.seek(0)
        
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="requests_export.xlsx"')
            ]
        )

    def _export_requests_csv(self, requests):
        """Export requests to CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Request #', 'Type', 'Status', 'Description', 'Created', 'Updated'])
        
        for req in requests:
            writer.writerow([
                req.name or '',
                req.request_type or '',
                req.state or '',
                req.description or '',
                fields.Date.to_string(req.create_date.date()) if req.create_date else '',
                fields.Date.to_string(req.write_date.date()) if req.write_date else ''
            ])
        
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename="requests_export.csv"')
            ]
        )
