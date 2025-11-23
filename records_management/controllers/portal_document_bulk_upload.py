# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import base64
import csv
import io

class PortalBulkUpload(http.Controller):
    """Bulk upload controller for Containers, Files, and Digital Documents"""
    
    @http.route(['/my/bulk-upload'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=False)
    def portal_bulk_upload(self, **post):
        """Unified bulk upload for Containers, Files, or Documents"""
        values = {}
        upload_type = post.get('upload_type', 'container')  # container, file, or document
        
        # Get partner info
        current_user = request.env.user
        base_partner = current_user.partner_id.commercial_partner_id
        
        if request.httprequest.method == 'POST' and post.get('upload_file'):
            upload = post.get('upload_file')
            has_header = bool(post.get('has_header', True))
            
            # Process based on upload type
            if upload_type == 'container':
                result = self._process_container_upload(upload, base_partner, has_header)
            elif upload_type == 'file':
                result = self._process_file_upload(upload, base_partner, has_header)
            elif upload_type == 'document':
                result = self._process_document_upload(upload, base_partner, has_header)
            else:
                result = {'success': False, 'error': 'Invalid upload type'}
            
            values.update(result)
        
        # Load departments for the dropdown
        departments = request.env['records.department'].sudo().search([
            ('company_id', '=', base_partner.id)
        ])
        
        values.update({
            'partner': base_partner,
            'partners': departments,  # Template expects 'partners' for the dropdown
            'upload_type': upload_type,
            'page_name': 'bulk_upload',
        })
        
        return request.render('records_management.portal_document_bulk_upload', values)
    
    def _process_container_upload(self, upload, partner, has_header):
        """Process container CSV upload"""
        try:
            content = upload.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content)) if has_header else csv.reader(io.StringIO(content))
            
            containers_created = []
            errors = []
            
            for idx, row in enumerate(csv_reader, start=1):
                try:
                    if has_header:
                        vals = {
                            'name': row.get('name') or row.get('container_name'),
                            'container_number': row.get('container_number') or row.get('barcode'),
                            'partner_id': partner.id,
                            'contents_type': row.get('contents_type', 'general'),
                            'content_description': row.get('content_description', ''),
                        }
                        
                        # Optional fields
                        if row.get('alpha_range'):
                            vals['alpha_range'] = row['alpha_range']
                        if row.get('storage_start_date'):
                            vals['storage_start_date'] = row['storage_start_date']
                        if row.get('destruction_due_date'):
                            vals['destruction_due_date'] = row['destruction_due_date']
                    else:
                        # Assume positional: name, container_number, contents_type, description
                        vals = {
                            'name': row[0],
                            'container_number': row[1] if len(row) > 1 else False,
                            'partner_id': partner.id,
                            'contents_type': row[2] if len(row) > 2 else 'general',
                            'content_description': row[3] if len(row) > 3 else '',
                        }
                    
                    container = request.env['records.container'].sudo().create(vals)
                    containers_created.append(container)
                    
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
            
            return {
                'success': True,
                'containers_created': len(containers_created),
                'errors': errors,
                'records': containers_created,
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_file_upload(self, upload, partner, has_header):
        """Process file CSV upload"""
        try:
            content = upload.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content)) if has_header else csv.reader(io.StringIO(content))
            
            files_created = []
            errors = []
            
            for idx, row in enumerate(csv_reader, start=1):
                try:
                    if has_header:
                        # Find or create container
                        container = None
                        if row.get('container_number'):
                            container = request.env['records.container'].sudo().search([
                                ('container_number', '=', row['container_number']),
                                ('partner_id', '=', partner.id)
                            ], limit=1)
                        
                        vals = {
                            'name': row.get('name') or row.get('file_name'),
                            'partner_id': partner.id,
                            'container_id': container.id if container else False,
                            'file_category': row.get('file_category', 'active'),
                        }
                        
                        if row.get('description'):
                            vals['description'] = row['description']
                        if row.get('date_created'):
                            vals['date_created'] = row['date_created']
                    else:
                        vals = {
                            'name': row[0],
                            'partner_id': partner.id,
                            'file_category': row[1] if len(row) > 1 else 'active',
                        }
                    
                    file_record = request.env['records.file'].sudo().create(vals)
                    files_created.append(file_record)
                    
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
            
            return {
                'success': True,
                'files_created': len(files_created),
                'errors': errors,
                'records': files_created,
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_document_upload(self, upload, partner, has_header):
        """Process document CSV upload"""
        try:
            content = upload.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content)) if has_header else csv.reader(io.StringIO(content))
            
            documents_created = []
            errors = []
            
            for idx, row in enumerate(csv_reader, start=1):
                try:
                    if has_header:
                        # Find file folder
                        file_record = None
                        if row.get('file_name'):
                            file_record = request.env['records.file'].sudo().search([
                                ('name', '=', row['file_name']),
                                ('partner_id', '=', partner.id)
                            ], limit=1)
                        
                        vals = {
                            'name': row.get('name') or row.get('document_name'),
                            'partner_id': partner.id,
                            'file_id': file_record.id if file_record else False,
                        }
                        
                        if row.get('description'):
                            vals['description'] = row['description']
                        if row.get('scan_date'):
                            vals['scan_date'] = row['scan_date']
                        if row.get('file_format'):
                            vals['file_format'] = row['file_format']
                    else:
                        vals = {
                            'name': row[0],
                            'partner_id': partner.id,
                        }
                    
                    document = request.env['records.document'].sudo().create(vals)
                    documents_created.append(document)
                    
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
            
            return {
                'success': True,
                'documents_created': len(documents_created),
                'errors': errors,
                'records': documents_created,
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/bulk-upload/template/<string:upload_type>'], type='http', auth='user', website=True)
    def portal_bulk_upload_template(self, upload_type='container', **post):
        """Download CSV template for bulk upload - Containers, Files, or Documents"""
        
        if upload_type == 'container':
            headers = [
                'name',                    # Container name (REQUIRED)
                'container_number',        # Barcode/Container # (REQUIRED - will auto-generate if empty)
                'contents_type',           # Type: documents, files, records, medical, legal, financial, personnel, other (OPTIONAL)
                'content_description',     # Description of contents (OPTIONAL)
                'alpha_range',             # Alphabetical range (e.g., A-F) (OPTIONAL)
                'storage_start_date',      # YYYY-MM-DD format (OPTIONAL)
                'destruction_due_date',    # YYYY-MM-DD format (OPTIONAL)
                'permanent_retention',     # true/false (OPTIONAL)
            ]
            
            sample_rows = [
                ['HR Files 2024 Q1', 'HR-2024-001', 'personnel', 'Employee personnel files for Q1 2024', 'A-D', '2024-01-01', '2031-01-01', 'false'],
                ['Financial Records Q3', 'FIN-2024-Q3', 'financial', 'Quarterly financial documents', '', '2024-07-01', '2031-07-01', 'false'],
                ['Legal Contracts', 'LEG-2024-CONTRACTS', 'legal', 'Active legal contracts', '', '2024-01-01', '', 'true'],
            ]
            filename_prefix = 'containers'
            
        elif upload_type == 'file':
            headers = [
                'name',                    # File folder name (REQUIRED)
                'container_number',        # Container barcode to assign file to (OPTIONAL)
                'file_category',           # permanent, temporary, archived, active (OPTIONAL - defaults to active)
                'description',             # File description (OPTIONAL)
                'date_created',            # YYYY-MM-DD format (OPTIONAL)
                'received_date',           # YYYY-MM-DD format (OPTIONAL)
            ]
            
            sample_rows = [
                ['Employee File - John Doe', 'HR-2024-001', 'permanent', 'Complete personnel file including contracts', '2024-01-15', '2024-01-15'],
                ['Invoice Batch Q3-2024', 'FIN-2024-Q3', 'active', 'Q3 invoices for processing', '2024-10-01', '2024-10-01'],
                ['Legal Case Files', 'LEG-2024-CONTRACTS', 'permanent', 'Active litigation files', '2024-03-20', '2024-03-20'],
            ]
            filename_prefix = 'files'
            
        elif upload_type == 'document':
            headers = [
                'name',                    # Document name (REQUIRED)
                'file_name',               # File folder name to assign document to (OPTIONAL)
                'description',             # Document description (OPTIONAL)
                'scan_date',               # YYYY-MM-DD HH:MM:SS format (OPTIONAL)
                'file_format',             # pdf, jpg, png, tiff (OPTIONAL)
                'resolution',              # DPI (e.g., 300) (OPTIONAL)
                'file_size',               # Size in MB (e.g., 2.5) (OPTIONAL)
                'scan_quality',            # low, medium, high, premium (OPTIONAL)
            ]
            
            sample_rows = [
                ['Employment Contract - John Doe', 'Employee File - John Doe', 'Signed employment contract', '2024-01-15 09:30:00', 'pdf', '300', '1.2', 'high'],
                ['Invoice #12345', 'Invoice Batch Q3-2024', 'Vendor invoice for processing', '2024-10-01 14:15:00', 'pdf', '300', '0.8', 'high'],
                ['Legal Brief Document', 'Legal Case Files', 'Case brief and supporting documents', '2024-03-20 11:00:00', 'pdf', '600', '5.3', 'premium'],
            ]
            filename_prefix = 'documents'
        else:
            return request.not_found()
        
        # Build CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow(headers)
        
        # Write sample rows
        for row in sample_rows:
            writer.writerow(row)
            
        csv_content = output.getvalue()
        output.close()
        
        # Return as file download
        partner_name = request.env.user.partner_id.name.replace(" ", "_")
        filename = f'bulk_upload_{filename_prefix}_template_{partner_name}.csv'
        
        return request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
        )
