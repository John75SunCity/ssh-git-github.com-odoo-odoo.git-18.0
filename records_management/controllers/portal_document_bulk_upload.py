# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import base64

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
        # Provide partner options limited to user's companies/partners (simple: own company + commercial partner children)
        partner_domain = [('id', 'child_of', request.env.user.partner_id.commercial_partner_id.id)]
        partners = request.env['res.partner'].sudo().search(partner_domain, limit=50)
        values['partners'] = partners
        return request.render('records_management.portal_document_bulk_upload', values)

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
