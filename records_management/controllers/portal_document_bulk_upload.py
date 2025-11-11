# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import base64
import csv
import io

class PortalDocumentBulkUpload(http.Controller):
    @http.route(['/my/documents/bulk_upload'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_bulk_upload(self, **post):
        values = {}
        Wizard = request.env['records.document.bulk.upload.wizard'].sudo()
        if request.httprequest.method == 'POST' and post.get('partner_id') and post.get('upload_file'):
            # Portal submission
            partner_id = int(post.get('partner_id'))
            upload = post.get('upload_file')
            has_header = bool(post.get('has_header'))
            wizard = Wizard.create({
                'partner_id': partner_id,
                'has_header': has_header,
                'upload_file': base64.b64encode(upload.read()) if hasattr(upload, 'read') else upload,
                'filename': getattr(upload, 'filename', 'upload.csv'),
            })
            wizard.action_parse()
            values['wizard'] = wizard
        else:
            values['wizard'] = False
        # Get relevant partners/departments for the current user
        # Include: user's own partner + their commercial partner + any departments they have access to
        current_user = request.env.user
        base_partner = current_user.partner_id.commercial_partner_id
        
        # Start with the main commercial partner
        partner_domain = ['|', 
                         ('id', '=', base_partner.id),
                         ('parent_id', '=', base_partner.id)]
        
        # Also include any departments the user has access to via records.department
        departments = request.env['records.department'].sudo().search([
            '|', 
            ('partner_id', '=', base_partner.id),
            ('partner_id.parent_id', '=', base_partner.id)
        ])
        if departments:
            dept_partner_ids = departments.mapped('partner_id.id')
            partner_domain = ['|'] + partner_domain + [('id', 'in', dept_partner_ids)]
            
        partners = request.env['res.partner'].sudo().search(partner_domain, limit=50, order='name')
        values['partners'] = partners
        return request.render('records_management.portal_document_bulk_upload', values)

    @http.route(['/my/documents/bulk_upload/template'], type='http', auth='user', website=True)
    def portal_bulk_upload_template(self, **post):
        """Download CSV template for bulk upload"""
        # Create comprehensive CSV template with all available fields
        headers = [
            'name',              # Document/File name (REQUIRED)
            'description',       # Document description (REQUIRED) 
            'container',         # Container reference (REQUIRED)
            'temp_barcode',      # Temporary barcode (OPTIONAL)
            'document_type',     # Document type code (OPTIONAL)
            'received_date',     # Date received YYYY-MM-DD (OPTIONAL)
            'file_category',     # File category: administrative, financial, legal, hr, operational, compliance, other (OPTIONAL)
        ]
        
        # Sample data row to show format
        sample_rows = [
            [
                'Employee Personnel File - John Doe',  # name
                'Complete personnel file including contracts and evaluations',  # description
                'HR-2024-001',  # container
                'TF20241101001',  # temp_barcode
                'PERSONNEL',  # document_type
                '2024-11-01',  # received_date
                'hr'  # file_category
            ],
            [
                'Invoice Processing File - Q3 2024',  # name
                'Quarterly invoice batch for processing',  # description
                'FIN-2024-Q3',  # container
                '',  # temp_barcode (empty - will auto-generate)
                'INVOICE',  # document_type
                '2024-10-15',  # received_date
                'financial'  # file_category
            ]
        ]
        
        # Build CSV content
        import csv
        import io
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
        filename = f'bulk_upload_template_{request.env.user.partner_id.name.replace(" ", "_")}.csv'
        
        return request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
        )

    @http.route(['/my/documents/bulk_upload/commit/<int:wizard_id>'], type='http', auth='user', website=True, methods=['POST'])
    def portal_bulk_upload_commit(self, wizard_id, **post):
        wizard = request.env['records.document.bulk.upload.wizard'].sudo().browse(wizard_id)
        if not wizard or not wizard.exists():
            return request.not_found()
        if wizard.state == 'error':
            # Reparse not triggered here; user must correct file and re-upload
            return request.redirect('/my/documents/bulk_upload')
        if wizard.state == 'parsed':
            wizard.action_commit()
        return request.redirect('/my/documents/bulk_upload')
