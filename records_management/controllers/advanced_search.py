# -*- coding: utf-8 -*-
"""
Advanced Physical Inventory Search Controller

Provides comprehensive search functionality for physical records inventory:
- Multi-criteria search (barcode, location, date range, type, retention status)
- Saved search presets
- Export capabilities (Excel, CSV, PDF)
- Search across containers, file folders, and physical documents

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import json
from datetime import datetime, timedelta


class AdvancedInventorySearch(CustomerPortal):
    """Advanced search for physical inventory items"""

    @http.route(['/my/inventory/advanced_search'], type='http', auth="user", website=True)
    def advanced_inventory_search(self, page=1, **filters):
        """
        Advanced search for physical inventory items
        
        Supports multiple search criteria:
        - Barcode: Search by container, file, or document barcode
        - Location: Filter by warehouse location
        - Date Range: Filter by date created/received
        - Type: Container, file folder, or document
        - Retention Status: Active, eligible for destruction, etc.
        - Document Type: Filter documents by type classification
        """
        user = request.env.user
        partner = user.partner_id.commercial_partner_id

        # Build search domain from filters
        domain_filters = self._build_advanced_search_domain(partner, filters)

        # Search across all inventory types
        search_results = {
            'containers': [],
            'files': [],
            'documents': [],
        }

        # Search containers if requested
        if filters.get('search_type') in [False, 'all', 'container']:
            Container = request.env['records.container'].sudo()
            containers = Container.search(
                domain_filters.get('container', []),
                order='create_date desc',
                limit=100
            )
            search_results['containers'] = [{
                'id': c.id,
                'type': 'container',
                'name': c.name,
                'barcode': c.barcode or c.temp_barcode,
                'location': c.current_location_id.name if c.current_location_id else 'Unknown',
                'date_created': c.create_date,
                'state': c.state or 'active',
                'file_count': len(c.file_ids),
                'model': 'records.container',
            } for c in containers]

        # Search file folders if requested
        if filters.get('search_type') in [False, 'all', 'file']:
            File = request.env['records.file'].sudo()
            files = File.search(
                domain_filters.get('file', []),
                order='create_date desc',
                limit=100
            )
            search_results['files'] = [{
                'id': f.id,
                'type': 'file',
                'name': f.name,
                'barcode': f.barcode,
                'container': f.container_id.name if f.container_id else 'Not in container',
                'date_created': f.create_date,
                'state': f.state or 'draft',
                'document_count': len(f.document_ids),
                'model': 'records.file',
            } for f in files]

        # Search physical documents if requested
        if filters.get('search_type') in [False, 'all', 'document']:
            Document = request.env['records.document'].sudo()
            documents = Document.search(
                domain_filters.get('document', []),
                order='create_date desc',
                limit=100
            )
            search_results['documents'] = [{
                'id': d.id,
                'type': 'document',
                'name': d.name,
                'barcode': d.temp_barcode,
                'file_folder': d.file_id.name if d.file_id else 'Not in folder',
                'container': d.container_id.name if d.container_id else 'Not in container',
                'date_created': d.create_date,
                'document_type': d.document_type_id.name if d.document_type_id else 'Unclassified',
                'pdf_scans': request.env['ir.attachment'].search_count([
                    ('res_model', '=', 'records.document'),
                    ('res_id', '=', d.id),
                    ('mimetype', 'like', 'pdf')
                ]),
                'model': 'records.document',
            } for d in documents]

        # Combine all results
        total_results = (
            len(search_results['containers']) +
            len(search_results['files']) +
            len(search_results['documents'])
        )

        # Get saved searches for this user
        saved_searches = request.env['records.saved.search'].search([
            ('user_id', '=', user.id)
        ])

        values = {
            'page_name': 'Advanced Inventory Search',
            'search_results': search_results,
            'total_results': total_results,
            'filters': filters,
            'saved_searches': saved_searches,
            'can_export': True,
        }

        return request.render("records_management.portal_advanced_inventory_search", values)

    def _build_advanced_search_domain(self, partner, filters):
        """
        Build domain filters for advanced search
        
        Filters supported:
        - barcode: Search by barcode
        - location_id: Filter by warehouse location
        - date_from/date_to: Date range filter
        - retention_status: Active, eligible for destruction, etc.
        - document_type_id: Document type classification
        """
        base_domain = [('partner_id', '=', partner.id)]

        domains = {
            'container': list(base_domain),
            'file': list(base_domain),
            'document': list(base_domain),
        }

        # Barcode search (across all types)
        if filters.get('barcode'):
            barcode = filters['barcode']
            domains['container'].append('|')
            domains['container'].append(('barcode', 'ilike', barcode))
            domains['container'].append(('temp_barcode', 'ilike', barcode))

            domains['file'].append(('barcode', 'ilike', barcode))

            domains['document'].append(('temp_barcode', 'ilike', barcode))

        # Location filter
        if filters.get('location_id'):
            location_id = int(filters['location_id'])
            domains['container'].append(('current_location_id', '=', location_id))
            domains['file'].append(('container_id.current_location_id', '=', location_id))
            domains['document'].append(('container_id.current_location_id', '=', location_id))

        # Date range filter
        if filters.get('date_from'):
            date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
            for domain in domains.values():
                domain.append(('create_date', '>=', date_from))

        if filters.get('date_to'):
            date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
            for domain in domains.values():
                domain.append(('create_date', '<=', date_to))

        # State filter
        if filters.get('state'):
            state = filters['state']
            for domain in domains.values():
                domain.append(('state', '=', state))

        # Document type filter (documents only)
        if filters.get('document_type_id'):
            document_type_id = int(filters['document_type_id'])
            domains['document'].append(('document_type_id', '=', document_type_id))

        # Retention status filter
        if filters.get('retention_status'):
            status = filters['retention_status']
            if status == 'eligible_destruction':
                # Documents eligible for destruction based on retention policy
                today = datetime.today().date()
                domains['document'].append(('retention_end_date', '<=', today))
            elif status == 'active_retention':
                today = datetime.today().date()
                domains['document'].append(('retention_end_date', '>', today))

        return domains

    @http.route(['/my/inventory/save_search'], type='json', auth="user")
    def save_search_preset(self, name, filters):
        """
        Save search criteria as a preset for quick access
        
        Args:
            name (str): Name for the saved search
            filters (dict): Search filter criteria
        
        Returns:
            dict: Success status and saved search ID
        """
        user = request.env.user

        # Create saved search record using sudo() for portal user access
        SavedSearch = request.env['records.saved.search'].sudo()
        saved_search = SavedSearch.create({
            'user_id': user.id,
            'name': name,
            'filters': json.dumps(filters),
        })

        return {
            'success': True,
            'search_id': saved_search.id,
            'message': f'Search preset "{name}" saved successfully',
        }

    @http.route(['/my/inventory/export'], type='http', auth="user")
    def export_search_results(self, format='xlsx', **filters):
        """
        Export search results to Excel, CSV, or PDF
        
        Args:
            format (str): Export format - 'xlsx', 'csv', or 'pdf'
            **filters: Search filter criteria
        
        Returns:
            File download response
        """
        partner = request.env.user.partner_id.commercial_partner_id

        # Build search domain
        domain_filters = self._build_advanced_search_domain(partner, filters)

        # Get all matching records
        Container = request.env['records.container'].sudo()
        File = request.env['records.file'].sudo()
        Document = request.env['records.document'].sudo()

        containers = Container.search(domain_filters.get('container', []))
        files = File.search(domain_filters.get('file', []))
        documents = Document.search(domain_filters.get('document', []))

        if format == 'xlsx':
            return self._export_to_excel(containers, files, documents)
        elif format == 'csv':
            return self._export_to_csv(containers, files, documents)
        elif format == 'pdf':
            return self._export_to_pdf(containers, files, documents)
        else:
            return request.not_found()

    def _export_to_excel(self, containers, files, documents):
        """Export inventory to Excel format"""
        # Import required library
        try:
            import xlsxwriter
            from io import BytesIO
        except ImportError:
            return request.render('website.404')

        # Create Excel workbook
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })

        # Containers sheet
        if containers:
            sheet = workbook.add_worksheet('Containers')
            headers = ['Name', 'Barcode', 'Location', 'State', 'File Count', 'Created Date']
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_format)

            for row, container in enumerate(containers, start=1):
                sheet.write(row, 0, container.name)
                sheet.write(row, 1, container.barcode or container.temp_barcode or '')
                sheet.write(row, 2, container.current_location_id.name if container.current_location_id else '')
                sheet.write(row, 3, container.state or 'active')
                sheet.write(row, 4, len(container.file_ids))
                sheet.write(row, 5, str(container.create_date))

        # Files sheet
        if files:
            sheet = workbook.add_worksheet('File Folders')
            headers = ['Name', 'Barcode', 'Container', 'State', 'Document Count', 'Created Date']
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_format)

            for row, file_folder in enumerate(files, start=1):
                sheet.write(row, 0, file_folder.name)
                sheet.write(row, 1, file_folder.barcode or '')
                sheet.write(row, 2, file_folder.container_id.name if file_folder.container_id else '')
                sheet.write(row, 3, file_folder.state or 'draft')
                sheet.write(row, 4, len(file_folder.document_ids))
                sheet.write(row, 5, str(file_folder.create_date))

        # Documents sheet
        if documents:
            sheet = workbook.add_worksheet('Documents')
            headers = ['Name', 'Barcode', 'File Folder', 'Container', 'Document Type', 'PDF Scans', 'Created Date']
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_format)

            for row, document in enumerate(documents, start=1):
                pdf_count = request.env['ir.attachment'].search_count([
                    ('res_model', '=', 'records.document'),
                    ('res_id', '=', document.id),
                    ('mimetype', 'like', 'pdf')
                ])

                sheet.write(row, 0, document.name)
                sheet.write(row, 1, document.temp_barcode or '')
                sheet.write(row, 2, document.file_id.name if document.file_id else '')
                sheet.write(row, 3, document.container_id.name if document.container_id else '')
                sheet.write(row, 4, document.document_type_id.name if document.document_type_id else '')
                sheet.write(row, 5, pdf_count)
                sheet.write(row, 6, str(document.create_date))

        workbook.close()
        output.seek(0)

        # Return file download
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="inventory_export.xlsx"'),
            ]
        )

    def _export_to_csv(self, containers, files, documents):
        """Export inventory to CSV format"""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Type', 'Name', 'Barcode', 'Location/Container', 'State', 'Count', 'Created Date'])

        # Write containers
        for container in containers:
            writer.writerow([
                'Container',
                container.name,
                container.barcode or container.temp_barcode or '',
                container.current_location_id.name if container.current_location_id else '',
                container.state or 'active',
                len(container.file_ids),
                str(container.create_date)
            ])

        # Write files
        for file_folder in files:
            writer.writerow([
                'File Folder',
                file_folder.name,
                file_folder.barcode or '',
                file_folder.container_id.name if file_folder.container_id else '',
                file_folder.state or 'draft',
                len(file_folder.document_ids),
                str(file_folder.create_date)
            ])

        # Write documents
        for document in documents:
            writer.writerow([
                'Document',
                document.name,
                document.temp_barcode or '',
                document.file_id.name if document.file_id else '',
                document.document_type_id.name if document.document_type_id else '',
                0,
                str(document.create_date)
            ])

        # Return CSV download
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename="inventory_export.csv"'),
            ]
        )

    def _export_to_pdf(self, containers, files, documents):
        """Export inventory to PDF format"""
        # Use Odoo's QWeb reporting for PDF generation
        report = request.env.ref('records_management.report_inventory_export')
        pdf_content = report._render_qweb_pdf([1], data={
            'containers': containers,
            'files': files,
            'documents': documents,
        })[0]

        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="inventory_export.pdf"'),
            ]
        )
